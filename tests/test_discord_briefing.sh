#!/bin/bash

# Discord 브리핑 테스트 스크립트
# 수동으로 브리핑을 생성하고 Discord로 전송합니다.

echo "🧪 Discord 브리핑 테스트 시작..."
echo "======================================"

# .env 파일 확인
if [ ! -f ".env" ]; then
    echo "❌ .env 파일이 없습니다. .env.example을 복사하여 생성하세요."
    exit 1
fi

# DISCORD_WEBHOOK_URL 확인
if ! grep -q "DISCORD_WEBHOOK_URL=https://" .env; then
    echo "❌ .env 파일에 DISCORD_WEBHOOK_URL이 설정되지 않았습니다."
    echo "   Discord 채널에서 Webhook URL을 생성하여 .env 파일에 추가하세요."
    exit 1
fi

echo "✅ .env 파일 확인 완료"
echo ""

# Python 스크립트로 브리핑 전송 테스트
cd backend

echo "📊 브리핑 생성 중..."
.venv/bin/python << EOF
import os
import sys
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv("../.env")

from app.core.database import SessionLocal
from app.services.briefing_service import BriefingService

db = SessionLocal()

try:
    service = BriefingService(db)

    # 지난 7일 브리핑 생성 및 전송
    print("📤 Discord로 브리핑 전송 중...")
    result = service.send_briefing(
        days=7,
        to_slack=False,
        to_discord=True
    )

    if result.get('success'):
        print("✅ Discord 브리핑 전송 성공!")
        print(f"   전송 결과: {result.get('results')}")
    elif result.get('skipped'):
        print(f"ℹ️  브리핑 건너뜀: {result.get('reason')}")
        print("   (변동사항이 없거나 읽음 처리된 경우)")
    else:
        print(f"❌ 브리핑 전송 실패: {result.get('error')}")
        sys.exit(1)

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()

EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ 테스트 완료!"
    echo ""
    echo "📱 Discord 채널을 확인하여 브리핑 메시지가 도착했는지 확인하세요."
    echo ""
    echo "💡 팁:"
    echo "   - 변동사항이 없으면 브리핑이 전송되지 않습니다."
    echo "   - 크롤링을 먼저 실행하여 변동사항을 생성하세요."
    echo "   - 스케줄러: 매주 월요일 06:00 자동 실행"
else
    echo ""
    echo "======================================"
    echo "❌ 테스트 실패"
    echo ""
    echo "🔍 확인사항:"
    echo "   1. .env 파일의 DISCORD_WEBHOOK_URL이 올바른지 확인"
    echo "   2. Discord Webhook URL이 유효한지 확인 (채널 설정 > 연동 > 웹후크)"
    echo "   3. 데이터베이스 연결 상태 확인 (PostgreSQL 실행 여부)"
    echo "   4. Python 가상환경 활성화 상태 확인"
    exit 1
fi
