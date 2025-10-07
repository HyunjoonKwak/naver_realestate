"""
자동 크롤링 스케줄러 태스크
"""
import asyncio
import logging
import uuid
import traceback
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.complex import Complex, ArticleSnapshot, CrawlJob
from app.services.crawler_service import NaverRealEstateCrawler

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.scheduler.crawl_all_complexes", bind=True)
def crawl_all_complexes(self, job_type='scheduled'):
    """
    등록된 모든 단지를 크롤링하는 태스크

    Args:
        job_type: 작업 유형 ('scheduled' 또는 'manual')

    Returns:
        dict: 크롤링 결과 요약
    """
    job_id = str(uuid.uuid4())
    db = SessionLocal()

    # CrawlJob 레코드 생성
    job = CrawlJob(
        job_id=job_id,
        job_type=job_type,
        status='running',
        started_at=datetime.now(timezone.utc),
        celery_task_id=self.request.id
    )
    db.add(job)
    db.commit()

    logger.info("=" * 80)
    logger.info(f"🤖 자동 크롤링 시작 (Job ID: {job_id})")
    logger.info("=" * 80)

    results = {
        "job_id": job_id,
        "started_at": job.started_at.isoformat(),
        "total_complexes": 0,
        "success": 0,
        "failed": 0,
        "errors": [],
        "total_articles_collected": 0,
        "total_articles_new": 0,
        "total_articles_updated": 0
    }

    try:
        # 모든 단지 조회
        complexes = db.query(Complex).all()
        results["total_complexes"] = len(complexes)
        job.complex_name = f"전체 {len(complexes)}개 단지"
        db.commit()

        logger.info(f"📋 크롤링 대상: {len(complexes)}개 단지")

        # 각 단지별로 크롤링 실행
        for idx, complex_obj in enumerate(complexes, 1):
            complex_id = complex_obj.complex_id
            complex_name = complex_obj.complex_name

            try:
                logger.info(f"[{idx}/{len(complexes)}] 크롤링 시작: {complex_name} (ID: {complex_id})")

                # 개별 단지 크롤링 (결과 포함)
                crawl_result = asyncio.run(crawl_single_complex_with_result(complex_id, db))

                results["success"] += 1
                results["total_articles_collected"] += crawl_result.get("articles_collected", 0)
                results["total_articles_new"] += crawl_result.get("articles_new", 0)
                results["total_articles_updated"] += crawl_result.get("articles_updated", 0)

                logger.info(f"✅ [{idx}/{len(complexes)}] 완료: {complex_name}")

            except Exception as e:
                results["failed"] += 1
                error_msg = f"단지 {complex_id} ({complex_name}) 크롤링 실패: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(f"❌ [{idx}/{len(complexes)}] 실패: {complex_name} - {str(e)}")

            # 단지 간 딜레이 (봇 차단 방지)
            if idx < len(complexes):
                import time
                time.sleep(5)  # 5초 대기

        # 작업 완료 처리
        job.status = 'success' if results["failed"] == 0 else 'failed'
        job.finished_at = datetime.now(timezone.utc)
        job.duration_seconds = int((job.finished_at - job.started_at).total_seconds())
        job.articles_collected = results["total_articles_collected"]
        job.articles_new = results["total_articles_new"]
        job.articles_updated = results["total_articles_updated"]

        if results["errors"]:
            job.error_message = "\n".join(results["errors"][:10])  # 최대 10개만

        db.commit()

        results["finished_at"] = job.finished_at.isoformat()
        results["duration_seconds"] = job.duration_seconds

        logger.info("=" * 80)
        logger.info(f"🏁 자동 크롤링 완료")
        logger.info(f"   총 {results['total_complexes']}개 중 {results['success']}개 성공, {results['failed']}개 실패")
        logger.info(f"   수집: {results['total_articles_collected']}건, 신규: {results['total_articles_new']}건")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"자동 크롤링 중 오류 발생: {str(e)}")
        results["errors"].append(f"전체 작업 오류: {str(e)}")

        # 작업 실패 처리
        job.status = 'failed'
        job.finished_at = datetime.now(timezone.utc)
        job.duration_seconds = int((job.finished_at - job.started_at).total_seconds())
        job.error_message = str(e)
        job.error_traceback = traceback.format_exc()
        db.commit()

    finally:
        db.close()

    return results


async def crawl_single_complex(complex_id: str, db: Session):
    """
    단일 단지 크롤링 (비동기)

    Args:
        complex_id: 단지 ID
        db: 데이터베이스 세션
    """
    crawler = NaverRealEstateCrawler()
    await crawler.crawl_complex(complex_id)


async def crawl_single_complex_with_result(complex_id: str, db: Session):
    """
    단일 단지 크롤링 (결과 포함)

    Args:
        complex_id: 단지 ID
        db: 데이터베이스 세션

    Returns:
        dict: 크롤링 결과 (articles_collected, articles_new, articles_updated)
    """
    # 크롤링 전 매물 수
    from app.models.complex import Article
    before_count = db.query(Article).filter(Article.complex_id == complex_id).count()

    # 크롤링 실행
    crawler = NaverRealEstateCrawler()
    await crawler.crawl_complex(complex_id)

    # 크롤링 후 매물 수
    after_count = db.query(Article).filter(Article.complex_id == complex_id).count()

    # 간단한 통계 (정확한 신규/업데이트 구분은 복잡하므로 근사치)
    articles_new = max(0, after_count - before_count)

    return {
        "articles_collected": after_count,
        "articles_new": articles_new,
        "articles_updated": min(before_count, after_count)
    }


@celery_app.task(name="app.tasks.scheduler.cleanup_old_snapshots")
def cleanup_old_snapshots():
    """
    90일 이상 된 오래된 스냅샷을 정리하는 태스크 (분기별 1회 실행 권장)

    - 매물 스냅샷이 계속 쌓이면 DB 용량 증가
    - 90일(약 3개월) 이전 스냅샷은 삭제하여 용량 절약
    - 권장 실행: 분기별 1회 (예: 1월, 4월, 7월, 10월 1일 새벽 3시)

    Returns:
        dict: 정리 결과
    """
    logger.info("=" * 80)
    logger.info("🧹 오래된 스냅샷 정리 시작")
    logger.info("=" * 80)

    db = SessionLocal()
    results = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "deleted_count": 0,
        "errors": []
    }

    try:
        # 90일 이전 날짜 계산 (분기별 1회 실행)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)

        # 오래된 스냅샷 조회 (snapshot_date 기준)
        old_snapshots = db.query(ArticleSnapshot).filter(
            ArticleSnapshot.snapshot_date < cutoff_date
        ).all()

        logger.info(f"📊 삭제 대상: {len(old_snapshots)}개 스냅샷 (90일 이전)")

        # 스냅샷 삭제
        if len(old_snapshots) > 0:
            for snapshot in old_snapshots:
                db.delete(snapshot)

            db.commit()
            results["deleted_count"] = len(old_snapshots)
            logger.info(f"✅ {len(old_snapshots)}개 스냅샷 삭제 완료")
        else:
            logger.info("ℹ️  삭제할 스냅샷이 없습니다")

        results["finished_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("=" * 80)

    except Exception as e:
        db.rollback()
        error_msg = f"스냅샷 정리 중 오류 발생: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(error_msg)
        logger.error(traceback.format_exc())
    finally:
        db.close()

    return results


@celery_app.task(name="app.tasks.scheduler.crawl_complex_async", bind=True)
def crawl_complex_async(self, complex_id: str):
    """
    특정 단지를 비동기로 크롤링하는 태스크 (API에서 호출용)

    Args:
        complex_id: 단지 ID

    Returns:
        dict: 크롤링 결과
    """
    job_id = str(uuid.uuid4())
    db = SessionLocal()

    # 단지 정보 조회
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()
    complex_name = complex_obj.complex_name if complex_obj else complex_id

    # CrawlJob 레코드 생성
    job = CrawlJob(
        job_id=job_id,
        job_type='manual',
        complex_id=complex_id,
        complex_name=complex_name,
        status='running',
        started_at=datetime.now(timezone.utc),
        celery_task_id=self.request.id
    )
    db.add(job)
    db.commit()

    logger.info(f"🤖 백그라운드 크롤링 시작: {complex_name} (Job ID: {job_id})")

    result = {
        "job_id": job_id,
        "complex_id": complex_id,
        "complex_name": complex_name,
        "started_at": job.started_at.isoformat(),
        "success": False,
        "error": None
    }

    try:
        # 크롤링 실행 (결과 포함)
        crawl_result = asyncio.run(crawl_single_complex_with_result(complex_id, db))

        # 작업 성공 처리
        job.status = 'success'
        job.finished_at = datetime.now(timezone.utc)
        job.duration_seconds = int((job.finished_at - job.started_at).total_seconds())
        job.articles_collected = crawl_result["articles_collected"]
        job.articles_new = crawl_result["articles_new"]
        job.articles_updated = crawl_result["articles_updated"]
        db.commit()

        result["success"] = True
        result["finished_at"] = job.finished_at.isoformat()
        result["duration_seconds"] = job.duration_seconds
        result["articles_collected"] = job.articles_collected
        result["articles_new"] = job.articles_new

        logger.info(f"✅ 백그라운드 크롤링 완료: {complex_name} (수집: {job.articles_collected}건)")

    except Exception as e:
        # 작업 실패 처리
        job.status = 'failed'
        job.finished_at = datetime.now(timezone.utc)
        job.duration_seconds = int((job.finished_at - job.started_at).total_seconds())
        job.error_message = str(e)
        job.error_traceback = traceback.format_exc()
        db.commit()

        result["error"] = str(e)
        logger.error(f"❌ 백그라운드 크롤링 실패: {complex_name} - {str(e)}")

    finally:
        db.close()

    return result
