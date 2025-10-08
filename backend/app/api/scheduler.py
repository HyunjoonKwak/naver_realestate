"""
스케줄러 관리 API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from celery.schedules import crontab
from app.core.celery_app import celery_app
from app.core.database import get_db
from app.models.complex import CrawlJob
from app.tasks.scheduler import crawl_all_complexes, crawl_complex_async
from app.core.schedule_manager import (
    update_schedule_in_file,
    delete_schedule_from_file,
    get_schedule_raw_data
)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


class ScheduleCreate(BaseModel):
    """스케줄 생성/수정 모델"""
    name: str
    task: str
    hour: int
    minute: int
    day_of_week: Optional[str] = "*"  # 0-6 or * for every day
    description: Optional[str] = None


class ScheduleUpdate(BaseModel):
    """스케줄 업데이트 모델"""
    task: Optional[str] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    day_of_week: Optional[str] = None
    enabled: Optional[bool] = None


@router.post("/trigger/all", response_model=Dict[str, Any])
def trigger_crawl_all():
    """
    모든 단지 크롤링을 즉시 실행 (수동 실행)

    Returns:
        작업 ID 및 상태
    """
    try:
        # 비동기 태스크 실행 (수동 실행이므로 job_type='manual')
        task = crawl_all_complexes.delay(job_type='manual')

        return {
            "task_id": task.id,
            "status": "started",
            "message": "모든 단지 크롤링이 백그라운드에서 시작되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"크롤링 시작 실패: {str(e)}")


@router.post("/trigger/{complex_id}", response_model=Dict[str, Any])
def trigger_crawl_complex(complex_id: str):
    """
    특정 단지 크롤링을 백그라운드에서 실행

    Args:
        complex_id: 단지 ID

    Returns:
        작업 ID 및 상태
    """
    try:
        # 비동기 태스크 실행
        task = crawl_complex_async.delay(complex_id)

        return {
            "task_id": task.id,
            "status": "started",
            "complex_id": complex_id,
            "message": f"단지 {complex_id} 크롤링이 백그라운드에서 시작되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"크롤링 시작 실패: {str(e)}")


@router.get("/task/{task_id}", response_model=Dict[str, Any])
def get_task_status(task_id: str):
    """
    태스크 상태 조회

    Args:
        task_id: Celery 태스크 ID

    Returns:
        태스크 상태 및 결과
    """
    try:
        task = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": task.state,
            "ready": task.ready(),
        }

        # 작업이 완료된 경우 결과 포함
        if task.ready():
            if task.successful():
                response["result"] = task.result
            else:
                response["error"] = str(task.info)

        # 진행 중인 경우 메타 정보 포함
        if task.state == "PROGRESS":
            response["progress"] = task.info

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"태스크 조회 실패: {str(e)}")


@router.get("/schedule", response_model=Dict[str, Any])
def get_schedule():
    """
    현재 스케줄 설정 조회 (Redis에서 실시간 조회)

    Returns:
        등록된 주기 작업 목록
    """
    try:
        from redbeat import RedBeatSchedulerEntry
        import redis

        # Redis에서 직접 조회
        r = redis.from_url(celery_app.conf.redbeat_redis_url)
        keys = r.keys("redbeat:*")

        result = {}
        for key in keys:
            key_str = key.decode('utf-8')
            # 메타 키는 제외
            if key_str in ["redbeat::statics", "redbeat::schedule"]:
                continue

            try:
                entry = RedBeatSchedulerEntry.from_key(key_str, app=celery_app)
                schedule_name = key_str.replace("redbeat:", "")
                result[schedule_name] = {
                    "task": entry.task,
                    "schedule": str(entry.schedule),
                    "options": entry.options or {}
                }
            except Exception as e:
                # 로드 실패한 스케줄은 건너뜀
                continue

        return {
            "schedule": result,
            "timezone": celery_app.conf.timezone
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄 조회 실패: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
def get_scheduler_status():
    """
    스케줄러 상태 확인

    Returns:
        Celery worker 및 beat 상태
    """
    try:
        # Celery inspect 객체 생성
        inspect = celery_app.control.inspect()

        # Worker 상태 확인
        active_workers = inspect.active()
        registered_tasks = inspect.registered()

        return {
            "workers": {
                "active": active_workers is not None,
                "count": len(active_workers) if active_workers else 0,
                "details": active_workers
            },
            "registered_tasks": registered_tasks,
            "beat_schedule": list(celery_app.conf.beat_schedule.keys())
        }
    except Exception as e:
        return {
            "workers": {"active": False, "count": 0},
            "error": str(e),
            "message": "Celery worker가 실행되지 않았습니다. 'celery -A app.core.celery_app worker' 명령으로 시작하세요."
        }


@router.post("/schedule", response_model=Dict[str, Any])
def create_schedule(schedule: ScheduleCreate):
    """
    새로운 스케줄 생성 (RedBeat 사용 - 재시작 불필요!)

    Args:
        schedule: 스케줄 정보

    Returns:
        생성된 스케줄 정보
    """
    try:
        from redbeat import RedBeatSchedulerEntry
        # 태스크 이름 검증
        available_tasks = [
            "app.tasks.scheduler.crawl_all_complexes",
            "app.tasks.scheduler.cleanup_old_snapshots",
            "app.tasks.briefing_tasks.send_weekly_briefing",
            "app.tasks.briefing_tasks.send_custom_briefing"
        ]

        if schedule.task not in available_tasks:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 태스크입니다. 사용 가능한 태스크: {available_tasks}"
            )

        # 스케줄 이름 중복 확인
        if schedule.name in celery_app.conf.beat_schedule:
            raise HTTPException(
                status_code=400,
                detail=f"'{schedule.name}' 스케줄이 이미 존재합니다."
            )

        # Crontab 생성 (특수 스케줄 처리)
        if schedule.day_of_week == "*":
            schedule_obj = crontab(hour=schedule.hour, minute=schedule.minute)
        elif schedule.day_of_week == 'QUARTERLY_1':
            # 분기별 1일 (1월, 4월, 7월, 10월 1일)
            schedule_obj = crontab(
                hour=schedule.hour,
                minute=schedule.minute,
                day_of_month='1',
                month_of_year='1,4,7,10'
            )
        elif schedule.day_of_week == 'QUARTERLY_15':
            # 분기별 15일 (1월, 4월, 7월, 10월 15일)
            schedule_obj = crontab(
                hour=schedule.hour,
                minute=schedule.minute,
                day_of_month='15',
                month_of_year='1,4,7,10'
            )
        elif schedule.day_of_week == 'MONTHLY_1':
            # 매월 1일
            schedule_obj = crontab(
                hour=schedule.hour,
                minute=schedule.minute,
                day_of_month='1'
            )
        elif schedule.day_of_week == 'MONTHLY_15':
            # 매월 15일
            schedule_obj = crontab(
                hour=schedule.hour,
                minute=schedule.minute,
                day_of_month='15'
            )
        else:
            # 일반 요일 (0-6)
            schedule_obj = crontab(
                hour=schedule.hour,
                minute=schedule.minute,
                day_of_week=schedule.day_of_week
            )

        # RedBeat Entry로 Redis에 직접 저장 (즉시 반영!)
        entry = RedBeatSchedulerEntry(
            name=schedule.name,
            task=schedule.task,
            schedule=schedule_obj,
            app=celery_app,
            options={"expires": 3600}
        )
        entry.save()  # Redis에 저장

        # JSON 파일에도 저장 (Beat 재시작 시 유지용)
        schedule_data = {
            "task": schedule.task,
            "schedule": {
                "hour": schedule.hour,
                "minute": schedule.minute,
                "day_of_week": int(schedule.day_of_week) if isinstance(schedule.day_of_week, str) and schedule.day_of_week.isdigit() else schedule.day_of_week
            },
            "enabled": True,
            "description": schedule.description or ""
        }

        if not update_schedule_in_file(schedule.name, schedule_data):
            raise HTTPException(status_code=500, detail="스케줄 파일 저장에 실패했습니다.")

        return {
            "message": f"스케줄 '{schedule.name}'이 생성되었습니다.",
            "schedule": {
                "name": schedule.name,
                "task": schedule.task,
                "hour": schedule.hour,
                "minute": schedule.minute,
                "day_of_week": schedule.day_of_week,
                "description": schedule.description
            },
            "note": "✅ Redis에 저장! 5초 이내 자동 반영됩니다 (재시작 불필요)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄 생성 실패: {str(e)}")


@router.put("/schedule/{schedule_name}", response_model=Dict[str, Any])
def update_schedule(schedule_name: str, schedule_update: ScheduleUpdate):
    """
    기존 스케줄 수정 (Redis 기반)

    Args:
        schedule_name: 수정할 스케줄 이름
        schedule_update: 수정할 정보

    Returns:
        수정된 스케줄 정보
    """
    try:
        from redbeat import RedBeatSchedulerEntry

        # Redis에서 기존 스케줄 로드
        try:
            entry = RedBeatSchedulerEntry.from_key(
                f"redbeat:{schedule_name}",
                app=celery_app
            )
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"'{schedule_name}' 스케줄을 찾을 수 없습니다."
            )

        # 작업 유형 검증 (변경하려는 경우)
        if schedule_update.task is not None:
            available_tasks = [
                "app.tasks.scheduler.crawl_all_complexes",
                "app.tasks.scheduler.cleanup_old_snapshots",
                "app.tasks.briefing_tasks.send_weekly_briefing",
                "app.tasks.briefing_tasks.send_custom_briefing"
            ]
            if schedule_update.task not in available_tasks:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 태스크입니다. 사용 가능한 태스크: {available_tasks}"
                )

        # 현재 값에서 업데이트할 값 가져오기
        task = schedule_update.task if schedule_update.task is not None else entry.task

        # crontab에서 현재 값 추출
        current_cron = entry.schedule
        hour = schedule_update.hour if schedule_update.hour is not None else list(current_cron.hour)[0] if hasattr(current_cron, 'hour') else 0
        minute = schedule_update.minute if schedule_update.minute is not None else list(current_cron.minute)[0] if hasattr(current_cron, 'minute') else 0

        # day_of_week 처리
        if schedule_update.day_of_week is not None:
            day_of_week = schedule_update.day_of_week
        else:
            if hasattr(current_cron, 'day_of_week'):
                dow_set = current_cron.day_of_week
                if isinstance(dow_set, set) and len(dow_set) == 7:
                    day_of_week = "*"
                elif isinstance(dow_set, set):
                    day_of_week = str(list(dow_set)[0])
                else:
                    day_of_week = "*"
            else:
                day_of_week = "*"

        # 새 Crontab 생성
        if day_of_week == "*":
            new_schedule = crontab(hour=hour, minute=minute)
        else:
            new_schedule = crontab(hour=hour, minute=minute, day_of_week=int(day_of_week) if day_of_week.isdigit() else day_of_week)

        # Redis에 업데이트된 Entry 저장
        entry.task = task
        entry.schedule = new_schedule
        entry.save()

        # JSON 파일에도 저장 (영구 저장)
        schedules_data = get_schedule_raw_data()
        if schedule_name in schedules_data:
            schedules_data[schedule_name]["task"] = task
            schedules_data[schedule_name]["schedule"]["hour"] = hour
            schedules_data[schedule_name]["schedule"]["minute"] = minute
            schedules_data[schedule_name]["schedule"]["day_of_week"] = int(day_of_week) if isinstance(day_of_week, str) and day_of_week.isdigit() else day_of_week
            update_schedule_in_file(schedule_name, schedules_data[schedule_name])

        return {
            "message": f"스케줄 '{schedule_name}'이 수정되었습니다.",
            "schedule": {
                "name": schedule_name,
                "task": task,
                "hour": hour,
                "minute": minute,
                "day_of_week": day_of_week
            },
            "note": "✅ Redis에 저장! 5초 이내 자동 반영됩니다 (재시작 불필요)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄 수정 실패: {str(e)}")


@router.delete("/schedule/{schedule_name}", response_model=Dict[str, Any])
def delete_schedule(schedule_name: str):
    """
    스케줄 삭제

    Args:
        schedule_name: 삭제할 스케줄 이름

    Returns:
        삭제 결과
    """
    try:
        from redbeat import RedBeatSchedulerEntry

        # RedBeat Entry 로드 시도
        try:
            entry = RedBeatSchedulerEntry.from_key(
                f"redbeat:{schedule_name}",
                app=celery_app
            )
            entry.delete()  # Redis에서 삭제 (즉시 반영!)
        except KeyError:
            # Redis에 없으면 무시
            pass

        # JSON 파일에서도 삭제 (영구 삭제)
        if not delete_schedule_from_file(schedule_name):
            raise HTTPException(status_code=500, detail="스케줄 파일 저장에 실패했습니다.")

        return {
            "message": f"스케줄 '{schedule_name}'이 삭제되었습니다.",
            "note": "✅ Redis에서 삭제! 5초 이내 자동 반영됩니다 (재시작 불필요)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄 삭제 실패: {str(e)}")

# ========== 작업 이력 관리 API ==========

@router.get("/jobs", response_model=Dict[str, Any])
def get_job_history(
    limit: int = 50,
    status: Optional[str] = None,
    job_type: Optional[str] = None
):
    """
    크롤링 작업 이력 조회

    Args:
        limit: 조회할 작업 수 (기본: 50)
        status: 상태 필터 (pending, running, success, failed)
        job_type: 작업 유형 필터 (manual, scheduled, all)

    Returns:
        작업 이력 목록
    """
    from app.core.database import SessionLocal
    from app.models.complex import CrawlJob
    from sqlalchemy import desc

    try:
        db = SessionLocal()

        query = db.query(CrawlJob)

        # 필터 적용
        if status:
            query = query.filter(CrawlJob.status == status)
        if job_type:
            query = query.filter(CrawlJob.job_type == job_type)

        # 최신순 정렬 및 limit
        jobs = query.order_by(desc(CrawlJob.created_at)).limit(limit).all()

        # 결과 변환
        result = []
        for job in jobs:
            result.append({
                "job_id": job.job_id,
                "job_type": job.job_type,
                "status": job.status,
                "complex_id": job.complex_id,
                "complex_name": job.complex_name,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "duration_seconds": job.duration_seconds,
                "articles_collected": job.articles_collected,
                "articles_new": job.articles_new,
                "articles_updated": job.articles_updated,
                "error_message": job.error_message,
                "celery_task_id": job.celery_task_id
            })

        db.close()

        return {
            "total": len(result),
            "jobs": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 이력 조회 실패: {str(e)}")


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
def get_job_detail(job_id: str):
    """
    특정 작업 상세 조회

    Args:
        job_id: 작업 ID

    Returns:
        작업 상세 정보
    """
    from app.core.database import SessionLocal
    from app.models.complex import CrawlJob

    try:
        db = SessionLocal()
        job = db.query(CrawlJob).filter(CrawlJob.job_id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail=f"작업 ID '{job_id}'를 찾을 수 없습니다.")

        result = {
            "job_id": job.job_id,
            "job_type": job.job_type,
            "status": job.status,
            "complex_id": job.complex_id,
            "complex_name": job.complex_name,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "duration_seconds": job.duration_seconds,
            "articles_collected": job.articles_collected,
            "articles_new": job.articles_new,
            "articles_updated": job.articles_updated,
            "articles_removed": job.articles_removed,
            "error_message": job.error_message,
            "error_traceback": job.error_traceback,
            "celery_task_id": job.celery_task_id,
            "created_at": job.created_at.isoformat() if job.created_at else None
        }

        db.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 조회 실패: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
def get_crawl_stats():
    """
    크롤링 통계 조회

    Returns:
        전체 통계 (성공률, 평균 시간 등)
    """
    from app.core.database import SessionLocal
    from app.models.complex import CrawlJob
    from sqlalchemy import func
    from datetime import datetime, timedelta

    try:
        db = SessionLocal()

        # 전체 작업 수
        total_jobs = db.query(func.count(CrawlJob.id)).scalar()

        # 상태별 통계
        success_count = db.query(func.count(CrawlJob.id)).filter(CrawlJob.status == 'success').scalar()
        failed_count = db.query(func.count(CrawlJob.id)).filter(CrawlJob.status == 'failed').scalar()
        running_count = db.query(func.count(CrawlJob.id)).filter(CrawlJob.status == 'running').scalar()

        # 성공률
        success_rate = (success_count / total_jobs * 100) if total_jobs > 0 else 0

        # 평균 소요 시간 (성공한 작업만)
        avg_duration = db.query(func.avg(CrawlJob.duration_seconds)).filter(
            CrawlJob.status == 'success',
            CrawlJob.duration_seconds.isnot(None)
        ).scalar()

        # 최근 24시간 통계
        since_24h = datetime.now() - timedelta(hours=24)
        recent_jobs = db.query(func.count(CrawlJob.id)).filter(
            CrawlJob.created_at >= since_24h
        ).scalar()

        recent_success = db.query(func.count(CrawlJob.id)).filter(
            CrawlJob.created_at >= since_24h,
            CrawlJob.status == 'success'
        ).scalar()

        # 최근 성공/실패 작업
        latest_success = db.query(CrawlJob).filter(
            CrawlJob.status == 'success'
        ).order_by(CrawlJob.finished_at.desc()).first()

        latest_failure = db.query(CrawlJob).filter(
            CrawlJob.status == 'failed'
        ).order_by(CrawlJob.finished_at.desc()).first()

        db.close()

        return {
            "total_jobs": total_jobs,
            "success_count": success_count,
            "failed_count": failed_count,
            "running_count": running_count,
            "success_rate": round(success_rate, 2),
            "avg_duration_seconds": int(avg_duration) if avg_duration else None,
            "recent_24h": {
                "total": recent_jobs,
                "success": recent_success,
                "failed": recent_jobs - recent_success
            },
            "latest_success": {
                "job_id": latest_success.job_id,
                "complex_name": latest_success.complex_name,
                "finished_at": latest_success.finished_at.isoformat() if latest_success.finished_at else None
            } if latest_success else None,
            "latest_failure": {
                "job_id": latest_failure.job_id,
                "complex_name": latest_failure.complex_name,
                "finished_at": latest_failure.finished_at.isoformat() if latest_failure.finished_at else None,
                "error_message": latest_failure.error_message
            } if latest_failure else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.get("/jobs/running/current", response_model=Dict[str, Any])
def get_running_jobs():
    """
    현재 실행 중인 작업 조회

    Returns:
        실행 중인 작업 목록
    """
    from app.core.database import SessionLocal
    from app.models.complex import CrawlJob

    try:
        db = SessionLocal()

        running_jobs = db.query(CrawlJob).filter(
            CrawlJob.status == 'running'
        ).all()

        result = []
        for job in running_jobs:
            # 경과 시간 계산
            elapsed_seconds = None
            if job.started_at:
                # started_at이 timezone-aware면 now도 같은 timezone으로
                from datetime import timezone
                job_now = datetime.now(timezone.utc) if job.started_at.tzinfo else datetime.now()
                elapsed_seconds = int((job_now - job.started_at).total_seconds())

            result.append({
                "job_id": job.job_id,
                "job_type": job.job_type,
                "complex_id": job.complex_id,
                "complex_name": job.complex_name,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "elapsed_seconds": elapsed_seconds,
                "celery_task_id": job.celery_task_id
            })

        db.close()

        return {
            "count": len(result),
            "jobs": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실행 중인 작업 조회 실패: {str(e)}")


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """
    작업 이력 삭제

    Args:
        job_id: 삭제할 작업 ID

    Returns:
        삭제 결과
    """
    try:
        # 작업 조회
        job = db.query(CrawlJob).filter(CrawlJob.job_id == job_id).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"작업 ID '{job_id}'를 찾을 수 없습니다."
            )

        # 작업 삭제
        db.delete(job)
        db.commit()

        return {
            "message": f"작업 '{job.complex_name or job_id}'이(가) 삭제되었습니다.",
            "job_id": job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"작업 삭제 실패: {str(e)}")


@router.get("/jobs/{job_id}/detail", response_model=Dict[str, Any])
def get_job_detail(job_id: str, db: Session = Depends(get_db)):
    """
    작업 상세 정보 조회 (스냅샷 및 변경사항 포함)

    Args:
        job_id: 작업 ID

    Returns:
        작업 상세 정보, 스냅샷, 변경사항
    """
    from app.models.complex import ArticleSnapshot, ArticleChange
    from sqlalchemy import and_

    try:
        # 작업 조회
        job = db.query(CrawlJob).filter(CrawlJob.job_id == job_id).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"작업 ID '{job_id}'를 찾을 수 없습니다."
            )

        # 작업 기본 정보
        job_data = {
            "job_id": job.job_id,
            "job_type": job.job_type,
            "status": job.status,
            "complex_id": job.complex_id,
            "complex_name": job.complex_name,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "duration_seconds": job.duration_seconds,
            "articles_collected": job.articles_collected,
            "articles_new": job.articles_new,
            "articles_updated": job.articles_updated,
            "error_message": job.error_message,
            "error_traceback": job.error_traceback,
            "celery_task_id": job.celery_task_id,
            "created_at": job.created_at.isoformat() if job.created_at else None
        }

        # 해당 작업 시간대의 스냅샷 조회 (작업 시작~종료 시간 사이)
        snapshots = []
        changes = []

        if job.complex_id and job.started_at:
            # 스냅샷 조회
            snapshot_query = db.query(ArticleSnapshot).filter(
                ArticleSnapshot.complex_id == job.complex_id
            )

            if job.finished_at:
                snapshot_query = snapshot_query.filter(
                    and_(
                        ArticleSnapshot.snapshot_date >= job.started_at,
                        ArticleSnapshot.snapshot_date <= job.finished_at
                    )
                )
            else:
                snapshot_query = snapshot_query.filter(
                    ArticleSnapshot.snapshot_date >= job.started_at
                )

            snapshot_records = snapshot_query.order_by(ArticleSnapshot.snapshot_date.desc()).limit(100).all()

            for snapshot in snapshot_records:
                snapshots.append({
                    "snapshot_id": snapshot.id,
                    "article_no": snapshot.article_no,
                    "article_name": snapshot.area_name or f"{snapshot.building_name} {snapshot.floor_info}",
                    "trade_type": snapshot.trade_type,
                    "price": snapshot.price,
                    "area": snapshot.area1,
                    "floor": snapshot.floor_info,
                    "direction": snapshot.direction,
                    "is_active": True,  # 스냅샷은 기본적으로 활성
                    "captured_at": snapshot.snapshot_date.isoformat() if snapshot.snapshot_date else None
                })

            # 변경사항 조회
            change_query = db.query(ArticleChange).filter(
                ArticleChange.complex_id == job.complex_id
            )

            if job.finished_at:
                change_query = change_query.filter(
                    and_(
                        ArticleChange.detected_at >= job.started_at,
                        ArticleChange.detected_at <= job.finished_at
                    )
                )
            else:
                change_query = change_query.filter(
                    ArticleChange.detected_at >= job.started_at
                )

            change_records = change_query.order_by(ArticleChange.detected_at.desc()).limit(100).all()

            for change in change_records:
                changes.append({
                    "change_id": change.change_id,
                    "article_no": change.article_no,
                    "change_type": change.change_type,
                    "article_name": change.article_name,
                    "trade_type": change.trade_type,
                    "old_price": change.old_price,
                    "new_price": change.new_price,
                    "price_diff": change.price_diff,
                    "detected_at": change.detected_at.isoformat() if change.detected_at else None
                })

        return {
            "job": job_data,
            "snapshots": {
                "count": len(snapshots),
                "data": snapshots
            },
            "changes": {
                "count": len(changes),
                "data": changes
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 상세 조회 실패: {str(e)}")
