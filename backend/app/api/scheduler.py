"""
스케줄러 관리 API
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from celery.schedules import crontab
from app.core.celery_app import celery_app
from app.tasks.scheduler import crawl_all_complexes, crawl_complex_async

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
    모든 단지 크롤링을 즉시 실행

    Returns:
        작업 ID 및 상태
    """
    try:
        # 비동기 태스크 실행
        task = crawl_all_complexes.delay()

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
    현재 스케줄 설정 조회

    Returns:
        등록된 주기 작업 목록
    """
    try:
        schedule = celery_app.conf.beat_schedule

        result = {}
        for name, config in schedule.items():
            result[name] = {
                "task": config["task"],
                "schedule": str(config["schedule"]),
                "options": config.get("options", {})
            }

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
    새로운 스케줄 생성

    Args:
        schedule: 스케줄 정보

    Returns:
        생성된 스케줄 정보
    """
    try:
        # 태스크 이름 검증
        available_tasks = [
            "app.tasks.scheduler.crawl_all_complexes",
            "app.tasks.scheduler.cleanup_old_snapshots"
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

        # Crontab 생성
        if schedule.day_of_week == "*":
            schedule_obj = crontab(hour=schedule.hour, minute=schedule.minute)
        else:
            schedule_obj = crontab(
                hour=schedule.hour,
                minute=schedule.minute,
                day_of_week=schedule.day_of_week
            )

        # 스케줄 추가
        celery_app.conf.beat_schedule[schedule.name] = {
            "task": schedule.task,
            "schedule": schedule_obj,
            "options": {"expires": 3600}
        }

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
            "note": "변경사항을 적용하려면 Celery Beat를 재시작해야 합니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄 생성 실패: {str(e)}")


@router.put("/schedule/{schedule_name}", response_model=Dict[str, Any])
def update_schedule(schedule_name: str, schedule_update: ScheduleUpdate):
    """
    기존 스케줄 수정

    Args:
        schedule_name: 수정할 스케줄 이름
        schedule_update: 수정할 정보

    Returns:
        수정된 스케줄 정보
    """
    try:
        # 스케줄 존재 확인
        if schedule_name not in celery_app.conf.beat_schedule:
            raise HTTPException(
                status_code=404,
                detail=f"'{schedule_name}' 스케줄을 찾을 수 없습니다."
            )

        current_schedule = celery_app.conf.beat_schedule[schedule_name]
        current_cron = current_schedule["schedule"]

        # 작업 유형 검증 (변경하려는 경우)
        if schedule_update.task is not None:
            available_tasks = [
                "app.tasks.scheduler.crawl_all_complexes",
                "app.tasks.scheduler.cleanup_old_snapshots"
            ]
            if schedule_update.task not in available_tasks:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 태스크입니다. 사용 가능한 태스크: {available_tasks}"
                )

        # 현재 설정에서 값 가져오기
        task = schedule_update.task if schedule_update.task is not None else current_schedule["task"]
        hour = schedule_update.hour if schedule_update.hour is not None else current_cron.hour
        minute = schedule_update.minute if schedule_update.minute is not None else current_cron.minute
        day_of_week = schedule_update.day_of_week if schedule_update.day_of_week is not None else str(current_cron.day_of_week)

        # 새 Crontab 생성
        if day_of_week == "*":
            new_schedule = crontab(hour=hour, minute=minute)
        else:
            new_schedule = crontab(hour=hour, minute=minute, day_of_week=day_of_week)

        # 스케줄 업데이트
        celery_app.conf.beat_schedule[schedule_name]["schedule"] = new_schedule
        celery_app.conf.beat_schedule[schedule_name]["task"] = task

        return {
            "message": f"스케줄 '{schedule_name}'이 수정되었습니다.",
            "schedule": {
                "name": schedule_name,
                "task": task,
                "hour": hour,
                "minute": minute,
                "day_of_week": day_of_week
            },
            "note": "변경사항을 적용하려면 Celery Beat를 재시작해야 합니다."
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
        # 스케줄 존재 확인
        if schedule_name not in celery_app.conf.beat_schedule:
            raise HTTPException(
                status_code=404,
                detail=f"'{schedule_name}' 스케줄을 찾을 수 없습니다."
            )

        # 스케줄 삭제
        del celery_app.conf.beat_schedule[schedule_name]

        return {
            "message": f"스케줄 '{schedule_name}'이 삭제되었습니다.",
            "note": "변경사항을 적용하려면 Celery Beat를 재시작해야 합니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스케줄 삭제 실패: {str(e)}")
