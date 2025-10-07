"""
주간 브리핑 Celery 작업
"""
import logging
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.briefing_service import BriefingService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.briefing_tasks.send_weekly_briefing")
def send_weekly_briefing(days: int = 7):
    """
    주간 브리핑 생성 및 발송 작업

    Args:
        days: 조회할 일수 (기본: 7일)

    Returns:
        발송 결과 딕셔너리
    """
    logger.info(f"📧 주간 브리핑 작업 시작 (지난 {days}일)")

    db = SessionLocal()
    try:
        service = BriefingService(db)
        result = service.send_briefing(days=days)

        if result.get('success'):
            logger.info(f"✅ 주간 브리핑 발송 완료: {result.get('results', {})}")
        elif result.get('skipped'):
            logger.info(f"ℹ️  변동사항 없음: {result.get('reason')}")
        else:
            logger.error(f"❌ 주간 브리핑 발송 실패: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"❌ 주간 브리핑 작업 중 오류 발생: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.briefing_tasks.send_custom_briefing")
def send_custom_briefing(days: int, to_slack: bool = True, to_discord: bool = True):
    """
    커스텀 기간의 브리핑 발송 (수동 실행용)

    Args:
        days: 조회할 일수
        to_slack: Slack 전송 여부
        to_discord: Discord 전송 여부

    Returns:
        발송 결과 딕셔너리
    """
    logger.info(f"📧 커스텀 브리핑 작업 시작 (지난 {days}일)")

    db = SessionLocal()
    try:
        service = BriefingService(db)
        result = service.send_briefing(
            days=days,
            to_slack=to_slack,
            to_discord=to_discord
        )

        logger.info(f"✅ 커스텀 브리핑 발송 완료: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ 커스텀 브리핑 작업 중 오류 발생: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.close()
