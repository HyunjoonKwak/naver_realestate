import os
import sys
from dotenv import load_dotenv

# .env 로드
load_dotenv()

webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
if not webhook_url:
    print("❌ DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
    sys.exit(1)

print(f"✅ Discord Webhook URL: {webhook_url[:50]}...")

# 간단한 테스트 메시지 전송
import requests

test_message = """# 🏠 크롤링 완료 브리핑 (테스트)

📅 **실행 시간**: 2025-10-08 20:44

## ✅ 변동사항 없음

✨ 모니터링 대상 단지의 매물 가격 및 매물 수에 변동이 없습니다.

- 신규 매물: 없음
- 삭제된 매물: 없음  
- 가격 변동: 없음

💡 시장이 안정적인 상태를 유지하고 있습니다.

---

📊 **크롤링 통계**
- 총 6개 단지 크롤링 완료
- 296건 매물 수집
- 소요 시간: 252초
"""

response = requests.post(webhook_url, json={"content": test_message})
if response.status_code == 204:
    print("✅ Discord 테스트 메시지 전송 성공!")
else:
    print(f"❌ Discord 메시지 전송 실패: {response.status_code}")
    print(response.text)
