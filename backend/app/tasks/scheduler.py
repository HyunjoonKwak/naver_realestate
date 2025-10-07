"""
자동 크롤링 스케줄러 태스크
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.complex import Complex, ArticleSnapshot
from app.services.crawler_service import NaverRealEstateCrawler

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.scheduler.crawl_all_complexes")
def crawl_all_complexes():
    """
    등록된 모든 단지를 크롤링하는 태스크

    Returns:
        dict: 크롤링 결과 요약
    """
    logger.info("=" * 80)
    logger.info("🤖 자동 크롤링 시작")
    logger.info("=" * 80)

    db = SessionLocal()
    results = {
        "started_at": datetime.now().isoformat(),
        "total_complexes": 0,
        "success": 0,
        "failed": 0,
        "errors": []
    }

    try:
        # 모든 단지 조회
        complexes = db.query(Complex).all()
        results["total_complexes"] = len(complexes)

        logger.info(f"📋 크롤링 대상: {len(complexes)}개 단지")

        # 각 단지별로 크롤링 실행
        for idx, complex_obj in enumerate(complexes, 1):
            complex_id = complex_obj.complex_id
            complex_name = complex_obj.complex_name

            try:
                logger.info(f"[{idx}/{len(complexes)}] 크롤링 시작: {complex_name} (ID: {complex_id})")

                # 비동기 크롤링 실행
                asyncio.run(crawl_single_complex(complex_id, db))

                results["success"] += 1
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

        results["finished_at"] = datetime.now().isoformat()

        logger.info("=" * 80)
        logger.info(f"🏁 자동 크롤링 완료")
        logger.info(f"   총 {results['total_complexes']}개 중 {results['success']}개 성공, {results['failed']}개 실패")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"자동 크롤링 중 오류 발생: {str(e)}")
        results["errors"].append(f"전체 작업 오류: {str(e)}")
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


@celery_app.task(name="app.tasks.scheduler.cleanup_old_snapshots")
def cleanup_old_snapshots():
    """
    30일 이상 된 오래된 스냅샷을 정리하는 태스크

    Returns:
        dict: 정리 결과
    """
    logger.info("=" * 80)
    logger.info("🧹 오래된 스냅샷 정리 시작")
    logger.info("=" * 80)

    db = SessionLocal()
    results = {
        "started_at": datetime.now().isoformat(),
        "deleted_count": 0,
        "errors": []
    }

    try:
        # 30일 이전 날짜 계산
        cutoff_date = datetime.now() - timedelta(days=30)

        # 오래된 스냅샷 조회
        old_snapshots = db.query(ArticleSnapshot).filter(
            ArticleSnapshot.captured_at < cutoff_date
        ).all()

        logger.info(f"📊 삭제 대상: {len(old_snapshots)}개 스냅샷")

        # 스냅샷 삭제
        for snapshot in old_snapshots:
            db.delete(snapshot)

        db.commit()
        results["deleted_count"] = len(old_snapshots)
        results["finished_at"] = datetime.now().isoformat()

        logger.info(f"✅ {len(old_snapshots)}개 스냅샷 삭제 완료")
        logger.info("=" * 80)

    except Exception as e:
        db.rollback()
        error_msg = f"스냅샷 정리 중 오류 발생: {str(e)}"
        results["errors"].append(error_msg)
        logger.error(error_msg)
    finally:
        db.close()

    return results


@celery_app.task(name="app.tasks.scheduler.crawl_complex_async")
def crawl_complex_async(complex_id: str):
    """
    특정 단지를 비동기로 크롤링하는 태스크 (API에서 호출용)

    Args:
        complex_id: 단지 ID

    Returns:
        dict: 크롤링 결과
    """
    logger.info(f"🤖 백그라운드 크롤링 시작: {complex_id}")

    db = SessionLocal()
    result = {
        "complex_id": complex_id,
        "started_at": datetime.now().isoformat(),
        "success": False,
        "error": None
    }

    try:
        asyncio.run(crawl_single_complex(complex_id, db))
        result["success"] = True
        result["finished_at"] = datetime.now().isoformat()
        logger.info(f"✅ 백그라운드 크롤링 완료: {complex_id}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"❌ 백그라운드 크롤링 실패: {complex_id} - {str(e)}")
    finally:
        db.close()

    return result
