"""
브리핑 기능 테스트 스크립트
"""
import sys
import os

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.services.briefing_service import BriefingService


def test_generate_briefing():
    """브리핑 생성 테스트 (발송하지 않음)"""
    print("=" * 60)
    print("📊 브리핑 생성 테스트 (지난 7일)")
    print("=" * 60)

    db = SessionLocal()
    try:
        service = BriefingService(db)

        # 브리핑 생성 (읽음 표시 안 함)
        briefing = service.generate_weekly_briefing(days=7, mark_as_read=False)

        print(f"\n✅ 브리핑 생성 완료")
        print(f"📅 기간: {briefing['period']['start']} ~ {briefing['period']['end']}")
        print(f"🏢 단지 수: {len(briefing['complexes'])}개")
        print(f"📊 총 변동: {briefing['total_summary']['total']}건")
        print(f"   - 신규: {briefing['total_summary']['new']}건")
        print(f"   - 삭제: {briefing['total_summary']['removed']}건")
        print(f"   - 가격상승: {briefing['total_summary']['price_up']}건")
        print(f"   - 가격하락: {briefing['total_summary']['price_down']}건")

        print("\n" + "=" * 60)
        print("📝 생성된 마크다운:")
        print("=" * 60)
        print(briefing['markdown'])

        return briefing

    finally:
        db.close()


def test_send_briefing_preview():
    """브리핑 발송 테스트 (실제로는 발송하지 않음, 프리뷰만)"""
    print("\n" + "=" * 60)
    print("📧 브리핑 발송 시뮬레이션")
    print("=" * 60)
    print("⚠️  실제 발송을 위해서는 환경변수 설정이 필요합니다:")
    print("   - SLACK_WEBHOOK_URL")
    print("   - DISCORD_WEBHOOK_URL")
    print("=" * 60)


if __name__ == "__main__":
    try:
        briefing = test_generate_briefing()
        test_send_briefing_preview()

        print("\n✅ 모든 테스트 완료!")

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
