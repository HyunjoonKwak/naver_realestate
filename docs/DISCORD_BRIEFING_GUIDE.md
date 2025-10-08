# Discord 브리핑 설정 가이드

스케줄러에 의해 자동 크롤링이 완료되면 내용을 요약하여 Discord로 브리핑 메시지를 전송하는 기능입니다.

## 📋 기능 개요

### 자동 브리핑 전송
- **타이밍**: 스케줄러 크롤링 완료 직후
- **채널**: Discord (Slack은 비활성화)
- **내용**:
  1. 크롤링 통계 (시작/완료 시간, 성공/실패 단지 수, 수집 매물 수)
  2. 주간 변동사항 요약 (신규/삭제 매물, 가격 변동)
  3. 단지별 상세 정보

### 브리핑 구성
```
🤖 자동 크롤링 완료
⏰ 시작: 2024-01-15 06:00:00
⏰ 완료: 2024-01-15 06:15:30
⏱️ 소요시간: 930초 (15분 30초)

📊 크롤링 결과
- 대상 단지: 5개
- 성공: 5개 ✅
- 실패: 0개 ❌
- 수집 매물: 127건
- 신규 매물: 3건 🆕

---

🏠 주간 부동산 브리핑
📅 기간: 2024-01-08 ~ 2024-01-15

📊 전체 요약
- 총 단지 수: 5개
- 신규 매물: 12건 🆕
- 삭제 매물: 8건 ❌
- 가격 변동: 5건 (↑3건, ↓2건)

---

🏢 단지별 상세 정보
...
```

## 🚀 설정 방법

### 1. Discord Webhook URL 생성

1. Discord 서버 선택 → 채널 설정(⚙️) 클릭
2. **연동** 메뉴 → **웹후크** 클릭
3. **새 웹후크** 버튼 클릭
4. 웹후크 이름 설정 (예: "부동산 봇")
5. **웹후크 URL 복사** 클릭

### 2. 환경변수 설정

`.env` 파일에 Discord Webhook URL 추가:

```bash
# Discord 웹훅 URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz
```

### 3. 서버 재시작

환경변수 변경 후 FastAPI 서버와 Celery Worker 재시작:

```bash
# FastAPI 서버 재시작
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Celery Worker 재시작
cd backend
./run_celery_worker.sh

# Celery Beat (스케줄러) 재시작
cd backend
./run_celery_beat.sh
```

## 📅 스케줄 설정

### 기본 스케줄
`backend/app/config/schedules.json`:

```json
{
  "주간업데이트": {
    "task": "app.tasks.scheduler.crawl_all_complexes",
    "schedule": {
      "hour": 6,
      "minute": 0,
      "day_of_week": "1"
    },
    "enabled": true,
    "description": "매주 월요일 오전 6시 - 모든 단지 크롤링 + 브리핑 전송"
  }
}
```

### 스케줄 수정 방법
1. `schedules.json` 파일 수정
2. Celery Beat 재시작 (자동으로 새 스케줄 로드)

**스케줄 옵션:**
- `hour`: 실행 시간(시)
- `minute`: 실행 시간(분)
- `day_of_week`: 요일 (0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일)

## 🔧 아키텍처

### 데이터 흐름
```
1. Celery Beat (스케줄러)
   → 매주 월요일 06:00 실행

2. crawl_all_complexes (Celery Task)
   → 모든 단지 크롤링 실행
   → 통계 수집 (성공/실패, 매물 수)

3. BriefingService
   → 크롤링 통계 + 변동사항 집계
   → 마크다운 포맷 생성

4. DiscordNotifier
   → Discord Webhook으로 전송
```

### 주요 파일
- **스케줄러 태스크**: `backend/app/tasks/scheduler.py`
- **브리핑 서비스**: `backend/app/services/briefing_service.py`
- **Discord 통합**: `backend/app/integrations/notifications.py`
- **스케줄 설정**: `backend/app/config/schedules.json`

## 🧪 테스트

### 수동 브리핑 전송 테스트

Python 스크립트로 즉시 테스트:

```python
from app.core.database import SessionLocal
from app.services.briefing_service import BriefingService

db = SessionLocal()
service = BriefingService(db)

# 지난 7일 브리핑 전송
result = service.send_briefing(
    days=7,
    to_slack=False,
    to_discord=True
)

print(result)
db.close()
```

### Celery Task 직접 실행

```bash
cd backend

# Python 인터프리터 실행
.venv/bin/python

# 태스크 실행
>>> from app.tasks.scheduler import crawl_all_complexes
>>> result = crawl_all_complexes.delay(job_type='manual')
>>> print(result.get())
```

## ⚙️ 커스터마이징

### 브리핑 주기 변경
`BriefingService.send_briefing()` 호출 시 `days` 파라미터 조정:

```python
# scheduler.py 수정
briefing_result = briefing_service.send_briefing(
    days=14,  # 2주간 변동사항
    to_slack=False,
    to_discord=True,
    crawl_stats=results
)
```

### Slack 동시 전송
Slack도 활성화하려면:

```python
briefing_result = briefing_service.send_briefing(
    days=7,
    to_slack=True,   # Slack 활성화
    to_discord=True,
    crawl_stats=results
)
```

`.env`에 Slack Webhook도 추가:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 브리핑 내용 수정
`backend/app/services/briefing_service.py`의 마크다운 생성 메서드 수정:
- `_generate_crawl_summary_markdown()`: 크롤링 통계 포맷
- `_generate_briefing_markdown()`: 변동사항 브리핑 포맷

## 🐛 트러블슈팅

### 브리핑이 전송되지 않는 경우

1. **환경변수 확인**
   ```bash
   # .env 파일 확인
   cat .env | grep DISCORD_WEBHOOK_URL
   ```

2. **Webhook URL 유효성 검사**
   ```bash
   curl -X POST "YOUR_DISCORD_WEBHOOK_URL" \
     -H "Content-Type: application/json" \
     -d '{"content": "테스트 메시지"}'
   ```

3. **Celery Worker 로그 확인**
   ```bash
   # Worker 로그에서 브리핑 전송 확인
   tail -f /tmp/celery_worker.log
   ```

4. **변동사항이 없는 경우**
   - 변동사항이 없으면 브리핑을 건너뜀 (skipped)
   - 로그에 `ℹ️ 브리핑 건너뜀: No changes to report` 표시

### 권한 오류

Discord 채널에 Webhook 권한이 있는지 확인:
- 채널 설정 → 권한 → 웹후크 관리 권한 필요

## 📝 참고 자료

- [Discord Webhook 가이드](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)
- [Celery Beat 스케줄링](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [실거래가 설정 가이드](./TRANSACTION_GUIDE.md)
