"""
주간 브리핑 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.services.briefing_service import BriefingService
from app.tasks.briefing_tasks import send_weekly_briefing, send_custom_briefing

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("/preview")
async def preview_briefing(
    days: int = Query(default=7, ge=1, le=30, description="조회할 일수 (1-30일)"),
    db: Session = Depends(get_db)
):
    """
    주간 브리핑 미리보기 (발송하지 않음, 읽음 표시 안 함)

    - **days**: 조회할 일수 (기본: 7일)

    Returns:
        브리핑 데이터 (마크다운, 통계 등)
    """
    try:
        service = BriefingService(db)

        # mark_as_read=False로 미리보기만 수행
        briefing = service.generate_weekly_briefing(days=days, mark_as_read=False)

        return {
            "success": True,
            "briefing": briefing,
            "message": f"지난 {days}일간의 브리핑 미리보기"
        }

    except Exception as e:
        logger.error(f"브리핑 미리보기 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_briefing_now(
    days: int = Query(default=7, ge=1, le=30, description="조회할 일수"),
    to_slack: bool = Query(default=True, description="Slack 전송 여부"),
    to_discord: bool = Query(default=True, description="Discord 전송 여부"),
    async_mode: bool = Query(default=False, description="비동기 실행 여부 (Celery 태스크)"),
    db: Session = Depends(get_db)
):
    """
    주간 브리핑 즉시 발송

    - **days**: 조회할 일수 (기본: 7일)
    - **to_slack**: Slack 전송 여부
    - **to_discord**: Discord 전송 여부
    - **async_mode**: True면 Celery 태스크로 백그라운드 실행, False면 즉시 실행

    Returns:
        발송 결과
    """
    try:
        if async_mode:
            # Celery 태스크로 비동기 실행
            task = send_custom_briefing.delay(
                days=days,
                to_slack=to_slack,
                to_discord=to_discord
            )
            return {
                "success": True,
                "async": True,
                "task_id": task.id,
                "message": f"브리핑 발송 작업이 백그라운드에서 실행 중입니다 (Task ID: {task.id})"
            }
        else:
            # 즉시 실행
            service = BriefingService(db)
            result = service.send_briefing(
                days=days,
                to_slack=to_slack,
                to_discord=to_discord
            )
            return {
                "success": result.get('success', False),
                "async": False,
                "result": result,
                "message": "브리핑 발송 완료" if result.get('success') else "브리핑 발송 실패"
            }

    except Exception as e:
        logger.error(f"브리핑 발송 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_notification(
    message: str = Query(default="테스트 메시지", description="테스트할 메시지"),
    to_slack: bool = Query(default=True, description="Slack 전송 여부"),
    to_discord: bool = Query(default=True, description="Discord 전송 여부"),
):
    """
    알림 시스템 테스트 (간단한 메시지 발송)

    Webhook URL이 올바르게 설정되었는지 확인하는 용도

    - **message**: 발송할 테스트 메시지
    - **to_slack**: Slack 전송 여부
    - **to_discord**: Discord 전송 여부

    Returns:
        발송 결과
    """
    try:
        from app.integrations.notifications import NotificationManager

        manager = NotificationManager()
        results = {}

        if to_slack and manager.slack:
            slack_result = manager.slack.send(message, username="부동산 봇 (테스트)")
            results['slack'] = slack_result

        if to_discord and manager.discord:
            discord_result = manager.discord.send(message, username="부동산 봇 (테스트)")
            results['discord'] = discord_result

        success = any(results.values()) if results else False

        return {
            "success": success,
            "results": results,
            "message": "테스트 메시지 발송 완료" if success else "발송 실패 또는 설정되지 않음"
        }

    except Exception as e:
        logger.error(f"알림 테스트 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_briefing_config():
    """
    브리핑 설정 정보 조회

    환경변수 설정 상태 확인

    Returns:
        설정 상태 (민감 정보는 마스킹)
    """
    import os

    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

    return {
        "slack": {
            "configured": bool(slack_webhook),
            "webhook_preview": slack_webhook[:50] + "..." if slack_webhook else None
        },
        "discord": {
            "configured": bool(discord_webhook),
            "webhook_preview": discord_webhook[:50] + "..." if discord_webhook else None
        },
        "schedule": {
            "enabled": True,
            "cron": "매주 월요일 09:00 (KST)",
            "task_name": "send-weekly-briefing"
        }
    }


@router.get("/stats")
async def get_briefing_stats(
    days: int = Query(default=30, ge=1, le=90, description="조회할 일수"),
    db: Session = Depends(get_db)
):
    """
    브리핑 통계 조회

    - **days**: 조회할 일수

    Returns:
        변동사항 통계
    """
    try:
        from app.models.complex import ArticleChange
        from datetime import datetime, timedelta
        from sqlalchemy import func

        since = datetime.now() - timedelta(days=days)

        # 전체 변동사항 수
        total_changes = db.query(func.count(ArticleChange.id)).filter(
            ArticleChange.detected_at >= since
        ).scalar()

        # 읽지 않은 변동사항
        unread_changes = db.query(func.count(ArticleChange.id)).filter(
            ArticleChange.detected_at >= since,
            ArticleChange.is_read == False
        ).scalar()

        # 타입별 통계
        type_stats = db.query(
            ArticleChange.change_type,
            func.count(ArticleChange.id).label('count')
        ).filter(
            ArticleChange.detected_at >= since
        ).group_by(ArticleChange.change_type).all()

        type_breakdown = {row.change_type: row.count for row in type_stats}

        return {
            "period_days": days,
            "total_changes": total_changes,
            "unread_changes": unread_changes,
            "type_breakdown": type_breakdown,
            "next_scheduled_briefing": "매주 월요일 09:00"
        }

    except Exception as e:
        logger.error(f"브리핑 통계 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
