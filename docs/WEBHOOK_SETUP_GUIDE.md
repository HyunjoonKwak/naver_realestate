# 📧 주간 브리핑 Webhook 설정 가이드

주간 브리핑 기능을 사용하려면 Slack 또는 Discord의 Webhook URL이 필요합니다.

## 📋 목차
- [Slack Webhook 설정](#slack-webhook-설정)
- [Discord Webhook 설정](#discord-webhook-설정)
- [환경변수 설정](#환경변수-설정)
- [브리핑 테스트](#브리핑-테스트)
- [API 사용법](#api-사용법)

---

## 🟦 Slack Webhook 설정

### 1. Slack App 생성

1. [Slack API 페이지](https://api.slack.com/apps)에 접속
2. **"Create New App"** 클릭
3. **"From scratch"** 선택
4. App 이름 입력 (예: "부동산 브리핑 봇")
5. Workspace 선택 후 **"Create App"** 클릭

### 2. Incoming Webhook 활성화

1. 왼쪽 메뉴에서 **"Incoming Webhooks"** 클릭
2. **"Activate Incoming Webhooks"** 토글을 ON으로 변경
3. 페이지 하단의 **"Add New Webhook to Workspace"** 클릭
4. 메시지를 받을 채널 선택 (예: #부동산-알림)
5. **"Allow"** 클릭

### 3. Webhook URL 복사

생성된 Webhook URL을 복사합니다.

```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

---

## 🟪 Discord Webhook 설정

### 1. Discord 서버 설정

1. Discord 서버 선택
2. 채널 옆 톱니바퀴 아이콘 클릭 (채널 편집)
3. 왼쪽 메뉴에서 **"연동"** 클릭

### 2. Webhook 생성

1. **"웹후크"** 탭 클릭
2. **"새 웹후크"** 버튼 클릭
3. 웹후크 이름 입력 (예: "부동산 브리핑 봇")
4. 아바타 이미지 설정 (선택사항)
5. **"웹후크 URL 복사"** 클릭

복사한 URL 형식:
```
https://discord.com/api/webhooks/1234567890/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## ⚙️ 환경변수 설정

### 1. .env 파일 생성

프로젝트 루트에 `.env` 파일을 생성합니다:

```bash
cd /path/to/naver_realestate
cp .env.example .env
```

### 2. Webhook URL 설정

`.env` 파일을 에디터로 열어 Webhook URL을 설정합니다:

```bash
# Slack Webhook URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Discord Webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL

# 브리핑 설정
BRIEFING_ENABLED=true
BRIEFING_DAYS=7
```

**참고:**
- Slack만 사용하는 경우 `DISCORD_WEBHOOK_URL`은 비워두면 됩니다
- Discord만 사용하는 경우 `SLACK_WEBHOOK_URL`은 비워두면 됩니다
- 둘 다 설정하면 양쪽 모두에 브리핑이 발송됩니다

### 3. 환경변수 로드 확인

FastAPI 서버와 Celery Worker를 재시작하여 환경변수를 로드합니다:

```bash
# API 서버 재시작
cd backend
pkill -f "uvicorn app.main"
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Celery Worker 재시작 (새 터미널)
pkill -f "celery.*worker"
cd backend
./run_celery_worker.sh

# Celery Beat 재시작 (새 터미널)
pkill -f "celery.*beat"
cd backend
./run_celery_beat.sh
```

---

## 🧪 브리핑 테스트

### 1. 설정 확인

API를 통해 Webhook URL이 올바르게 설정되었는지 확인:

```bash
curl http://localhost:8000/api/briefing/config | python3 -m json.tool
```

출력 예시:
```json
{
  "slack": {
    "configured": true,
    "webhook_preview": "https://hooks.slack.com/services/T00000000/B00..."
  },
  "discord": {
    "configured": true,
    "webhook_preview": "https://discord.com/api/webhooks/1234567890/XXX..."
  },
  "schedule": {
    "enabled": true,
    "cron": "매주 월요일 09:00 (KST)",
    "task_name": "send-weekly-briefing"
  }
}
```

### 2. 테스트 메시지 발송

간단한 테스트 메시지를 발송하여 연결을 확인:

```bash
curl -X POST "http://localhost:8000/api/briefing/test?message=테스트%20메시지" | python3 -m json.tool
```

성공 시 Slack 또는 Discord 채널에 "테스트 메시지"가 표시됩니다.

### 3. 브리핑 미리보기

발송하지 않고 브리핑 내용만 확인:

```bash
curl "http://localhost:8000/api/briefing/preview?days=7" | python3 -m json.tool
```

### 4. 브리핑 즉시 발송

수동으로 브리핑 발송:

```bash
curl -X POST "http://localhost:8000/api/briefing/send?days=7" | python3 -m json.tool
```

---

## 📡 API 사용법

### 엔드포인트 목록

브리핑 관련 API는 모두 `/api/briefing` 아래에 있습니다:

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/briefing/config` | 브리핑 설정 확인 |
| GET | `/api/briefing/stats` | 변동사항 통계 조회 |
| GET | `/api/briefing/preview` | 브리핑 미리보기 (발송 안 함) |
| POST | `/api/briefing/send` | 브리핑 즉시 발송 |
| POST | `/api/briefing/test` | 알림 시스템 테스트 |

### 브리핑 미리보기

```bash
# 최근 7일 브리핑 미리보기
curl "http://localhost:8000/api/briefing/preview?days=7"

# 최근 30일 브리핑 미리보기
curl "http://localhost:8000/api/briefing/preview?days=30"
```

### 브리핑 발송

```bash
# 기본 발송 (Slack + Discord 모두, 지난 7일)
curl -X POST "http://localhost:8000/api/briefing/send"

# Slack만 발송
curl -X POST "http://localhost:8000/api/briefing/send?to_slack=true&to_discord=false"

# Discord만 발송
curl -X POST "http://localhost:8000/api/briefing/send?to_slack=false&to_discord=true"

# 커스텀 기간 (최근 14일)
curl -X POST "http://localhost:8000/api/briefing/send?days=14"

# 비동기 모드 (백그라운드 실행)
curl -X POST "http://localhost:8000/api/briefing/send?async_mode=true"
```

### 통계 조회

```bash
# 최근 30일 변동사항 통계
curl "http://localhost:8000/api/briefing/stats?days=30"
```

응답 예시:
```json
{
  "period_days": 30,
  "total_changes": 156,
  "unread_changes": 23,
  "type_breakdown": {
    "NEW": 45,
    "REMOVED": 38,
    "PRICE_UP": 42,
    "PRICE_DOWN": 31
  },
  "next_scheduled_briefing": "매주 월요일 09:00"
}
```

---

## 🔄 자동 브리핑 스케줄

Celery Beat이 실행 중이면 매주 월요일 오전 9시에 자동으로 브리핑이 발송됩니다.

### 스케줄 확인

`backend/app/core/celery_app.py`에서 스케줄 설정 확인:

```python
"send-weekly-briefing": {
    "task": "app.tasks.briefing_tasks.send_weekly_briefing",
    "schedule": crontab(hour=9, minute=0, day_of_week=1),  # 매주 월요일 09:00
    "options": {"expires": 3600},
}
```

### 스케줄 변경

스케줄을 변경하려면 `celery_app.py`의 `crontab` 설정을 수정:

```python
# 매일 오전 10시
crontab(hour=10, minute=0)

# 매주 수요일 오후 2시
crontab(hour=14, minute=0, day_of_week=3)

# 매주 월/수/금 오전 9시
crontab(hour=9, minute=0, day_of_week='1,3,5')
```

변경 후 Celery Beat 재시작:
```bash
pkill -f "celery.*beat"
cd backend && ./run_celery_beat.sh
```

---

## 📝 브리핑 메시지 예시

### Slack 메시지

```
🏠 주간 부동산 브리핑

📅 기간: 2025-10-01 ~ 2025-10-07

📊 전체 요약
• 총 단지 수: 3개
• 신규 매물: 12건 🆕
• 삭제 매물: 8건 ❌
• 가격 변동: 15건 (↑9건, ↓6건)

---

🏢 단지별 상세 정보

● 래미안 강남
  - 신규 매물: 5건
  - 가격 상승: 3건
  - 가격 하락: 2건
  🔥 주목: 84㎡ 매매가 10억 → 10억5천 (+5.0%)

● 자이 서초
  - 신규 매물: 4건
  - 삭제 매물: 3건
  🔥 주목: 59㎡ 전세 6억 → 5억5천 (-8.3%)

---

⏰ 다음 브리핑: 2025-10-14 (Mon)

이 브리핑은 자동으로 생성되었습니다.
```

### Discord Embed

Discord에서는 더 보기 좋은 Embed 형식으로 표시됩니다:
- 제목: 🏠 주간 부동산 브리핑
- 색상: 파란색 사이드바
- 필드별 구분된 정보
- 타임스탬프 자동 추가

---

## ❓ 문제 해결

### Webhook URL이 인식되지 않음

**증상:** `/api/briefing/config`에서 `configured: false`로 표시

**해결방법:**
1. `.env` 파일이 프로젝트 루트에 있는지 확인
2. `.env` 파일 내용에 공백이나 따옴표가 없는지 확인
3. API 서버와 Celery Worker 재시작

### 테스트 메시지가 발송되지 않음

**Slack 오류:**
- Webhook URL이 유효한지 확인
- App이 채널에 초대되었는지 확인
- Webhook이 삭제되지 않았는지 Slack API 페이지에서 확인

**Discord 오류:**
- Webhook URL이 유효한지 확인
- 채널이 삭제되지 않았는지 확인
- Bot 권한이 충분한지 확인 (메시지 전송 권한)

### 자동 브리핑이 발송되지 않음

**확인사항:**
1. Celery Beat이 실행 중인지 확인
   ```bash
   ps aux | grep "celery.*beat"
   ```

2. Celery Worker가 실행 중인지 확인
   ```bash
   ps aux | grep "celery.*worker"
   ```

3. Redis가 실행 중인지 확인
   ```bash
   docker ps | grep redis
   ```

4. 로그 확인
   ```bash
   # Worker 로그
   tail -f backend/logs/celery_worker.log

   # Beat 로그
   tail -f backend/logs/celery_beat.log
   ```

---

## 📚 관련 문서

- [Slack Incoming Webhooks 공식 문서](https://api.slack.com/messaging/webhooks)
- [Discord Webhooks 공식 문서](https://discord.com/developers/docs/resources/webhook)
- [Celery Beat 공식 문서](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)

---

**작성일**: 2025-10-07
**버전**: 1.0.0
