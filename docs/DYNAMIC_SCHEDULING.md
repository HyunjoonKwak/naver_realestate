# 동적 스케줄 관리 가이드 (RedBeat)

## ✨ 개요

**RedBeat**을 사용하면 Celery Beat을 **재시작하지 않고** 스케줄을 동적으로 변경할 수 있습니다!

### 🆚 비교

| 기능 | PersistentScheduler (이전) | RedBeat (현재) |
|------|---------------------------|----------------|
| 스케줄 저장 | 파일 (`/tmp/celerybeat-schedule`) | Redis |
| 스케줄 변경 후 | **Beat 재시작 필수** | **재시작 불필요** ✅ |
| 캐시 삭제 | 필요 | 불필요 ✅ |
| 변경 반영 시간 | 재시작 시 | 5초 이내 (기본 polling) ✅ |
| 동시 수정 | 불가 | 가능 ✅ |

---

## 🚀 사용 방법

### 방법 1: JSON 파일 수정 (기존 방식)

```bash
# 1. schedules.json 수정
vim backend/app/config/schedules.json

# 2. 변경사항 저장 후 - 자동 반영됨! (재시작 불필요)
# RedBeat이 5초마다 Redis의 스케줄을 확인하여 자동 적용
```

**주의**: JSON 파일 변경 시 **일회성**입니다. Beat을 재시작하면 JSON에서 다시 로드되므로, JSON과 Redis를 모두 업데이트해야 영구적입니다.

### 방법 2: API로 동적 변경 (권장)

스케줄을 API로 생성/수정하면 **즉시 반영**되고 Redis에 저장됩니다!

#### 스케줄 조회

```bash
curl http://localhost:8000/api/scheduler/schedule
```

**응답 예시:**
```json
{
  "schedule": {
    "주간업데이트": {
      "task": "app.tasks.scheduler.crawl_all_complexes",
      "schedule": "<crontab: 0 6 * * 1 (m/h/dM/MY/d)>",
      "options": {"expires": 3600}
    }
  },
  "timezone": "Asia/Seoul"
}
```

#### 스케줄 생성

```bash
curl -X POST "http://localhost:8000/api/scheduler/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "테스트_크롤링",
    "task": "app.tasks.scheduler.crawl_all_complexes",
    "hour": 14,
    "minute": 30,
    "day_of_week": "3",
    "description": "매주 수요일 오후 2시 30분"
  }'
```

**응답:**
```json
{
  "message": "스케줄 '테스트_크롤링'이 생성되었습니다.",
  "schedule": {
    "name": "테스트_크롤링",
    "task": "app.tasks.scheduler.crawl_all_complexes",
    "hour": 14,
    "minute": 30,
    "day_of_week": "3"
  },
  "note": "RedBeat이 자동으로 감지하여 5초 이내 적용됩니다."
}
```

#### 스케줄 수정

```bash
curl -X PUT "http://localhost:8000/api/scheduler/schedule/테스트_크롤링" \
  -H "Content-Type: application/json" \
  -d '{
    "hour": 15,
    "minute": 0
  }'
```

#### 스케줄 삭제

```bash
curl -X DELETE "http://localhost:8000/api/scheduler/schedule/테스트_크롤링"
```

### 방법 3: Python 코드로 직접 변경

```python
from redbeat import RedBeatSchedulerEntry
from celery.schedules import crontab
from app.core.celery_app import celery_app

# 새 스케줄 생성
entry = RedBeatSchedulerEntry(
    name='임시_테스트',
    task='app.tasks.scheduler.crawl_all_complexes',
    schedule=crontab(hour=16, minute=0, day_of_week=3),
    app=celery_app
)

# Redis에 저장 (즉시 반영!)
entry.save()

print(f"✅ 스케줄 '{entry.name}' 저장 완료!")

# 스케줄 삭제
entry.delete()
```

---

## 🔧 동작 원리

### RedBeat 스케줄 저장 위치

```
Redis Key: redbeat:주간업데이트
Value: {
  "name": "주간업데이트",
  "task": "app.tasks.scheduler.crawl_all_complexes",
  "schedule": {...},
  "enabled": true
}
```

### Redis에서 스케줄 확인

```bash
# Redis CLI 접속
redis-cli

# 모든 RedBeat 키 확인
KEYS redbeat:*

# 특정 스케줄 내용 확인
GET "redbeat:주간업데이트"

# 모든 스케줄 삭제 (주의!)
DEL redbeat:*
```

### 스케줄 동기화 주기

RedBeat은 **5초마다** Redis를 확인하여 변경사항을 자동 적용합니다:

```python
# backend/app/core/celery_app.py
celery_app.conf.redbeat_lock_timeout = 30  # Redis 락 타임아웃
```

---

## ❓ FAQ

### Q1: 스케줄을 변경했는데 언제 반영되나요?

**A:** RedBeat은 최대 **5초** 이내에 변경사항을 자동 감지합니다. 재시작 불필요!

```bash
# 변경 후 로그 확인
tail -f /tmp/celery_beat.log

# 예상 로그:
# [INFO] RedBeatScheduler: Scheduler entry changed: 테스트_크롤링
```

### Q2: Beat을 재시작하면 스케줄이 사라지나요?

**A:** 아니요! Redis에 저장되어 있으므로 재시작 후에도 유지됩니다.

단, `schedules.json` 파일과 Redis 스케줄이 **다를 경우**:
- Beat 시작 시 JSON 파일의 스케줄이 Redis에 **덮어씌워집니다**
- **권장**: JSON 파일도 함께 업데이트하거나, API만 사용

### Q3: schedules.json과 Redis 중 어느 것이 우선인가요?

**A:**
1. **Beat 시작 시**: `schedules.json` → Redis 로드
2. **실행 중**: Redis가 우선 (JSON 무시)
3. **영구 저장**: JSON 파일도 업데이트 권장

### Q4: 스케줄이 중복 실행되나요?

**A:** RedBeat은 Redis 락을 사용하여 중복 실행을 방지합니다. 여러 Beat 인스턴스가 실행 중이어도 안전합니다.

### Q5: 기존 PersistentScheduler 캐시 파일은 삭제해야 하나요?

**A:** 선택사항입니다. RedBeat은 Redis만 사용하므로 파일 캐시는 무시됩니다.

```bash
# 기존 캐시 삭제 (선택)
rm -f /tmp/celerybeat-schedule*
```

---

## 🧪 테스트

### 1. 스케줄 생성 테스트

```bash
# 현재 시각 기준 2분 후 실행되도록 설정
CURRENT_HOUR=$(date +%H)
CURRENT_MIN=$(date +%M)
TARGET_MIN=$((CURRENT_MIN + 2))
TARGET_HOUR=$CURRENT_HOUR

if [ $TARGET_MIN -ge 60 ]; then
    TARGET_MIN=$((TARGET_MIN - 60))
    TARGET_HOUR=$((CURRENT_HOUR + 1))
fi

# API로 스케줄 생성
curl -X POST "http://localhost:8000/api/scheduler/schedule" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"즉시_테스트\",
    \"task\": \"app.tasks.scheduler.crawl_all_complexes\",
    \"hour\": $TARGET_HOUR,
    \"minute\": $TARGET_MIN,
    \"day_of_week\": \"*\",
    \"description\": \"즉시 테스트 (2분 후 실행)\"
  }"

echo ""
echo "✅ 스케줄 생성 완료! ${TARGET_HOUR}:${TARGET_MIN}에 실행됩니다."
echo "📋 로그 확인: tail -f /tmp/celery_beat.log"
```

### 2. 스케줄 확인

```bash
# 등록된 스케줄 목록
./check_schedules.sh

# 또는 API 사용
curl http://localhost:8000/api/scheduler/schedule | jq
```

### 3. 실행 중 스케줄 변경

```bash
# 시간 변경
curl -X PUT "http://localhost:8000/api/scheduler/schedule/즉시_테스트" \
  -H "Content-Type: application/json" \
  -d '{"minute": 45}'

# 5초 이내 자동 반영!
```

### 4. 정리

```bash
# 테스트 스케줄 삭제
curl -X DELETE "http://localhost:8000/api/scheduler/schedule/즉시_테스트"
```

---

## 💡 권장 사항

### ✅ DO

1. **API 사용**: 동적 스케줄 관리는 API를 사용하세요
2. **JSON 동기화**: API로 변경 후 `schedules.json`도 수동 업데이트 (영구 저장)
3. **스케줄 확인**: `./check_schedules.sh`로 주기적으로 확인
4. **로그 모니터링**: Beat 로그를 확인하여 변경 반영 확인

```bash
# 권장 워크플로우
# 1. API로 스케줄 생성/수정
curl -X POST http://localhost:8000/api/scheduler/schedule ...

# 2. 변경 확인
./check_schedules.sh

# 3. 정상 작동 확인 후 JSON 파일 수동 업데이트 (영구 보존)
vim backend/app/config/schedules.json
```

### ❌ DON'T

1. **Beat 여러 개 실행 금지**: 중복 실행 방지
2. **Redis 수동 변경 금지**: API나 Python 코드 사용
3. **JSON과 Redis 불일치**: Beat 재시작 시 JSON이 우선됨

---

## 🔄 마이그레이션 (PersistentScheduler → RedBeat)

기존 PersistentScheduler에서 RedBeat으로 전환하는 방법:

### 1. 패키지 설치 (완료)

```bash
pip install celery-redbeat
```

### 2. 설정 변경 (완료)

`backend/app/core/celery_app.py`:
```python
# Before
celery_app.conf.beat_scheduler = "celery.beat:PersistentScheduler"

# After
celery_app.conf.beat_scheduler = "redbeat.RedBeatScheduler"
celery_app.conf.redbeat_redis_url = REDIS_URL
```

### 3. Celery Beat 재시작

```bash
# 기존 Beat 종료
pkill -f 'celery.*beat'

# 캐시 파일 삭제 (선택)
rm -f /tmp/celerybeat-schedule*

# Beat 재시작
cd backend
./run_celery_beat.sh
```

### 4. 스케줄 확인

```bash
./check_schedules.sh

# schedules.json의 스케줄이 Redis로 자동 로드됨
```

### 5. 테스트

```bash
# API로 스케줄 생성
curl -X POST http://localhost:8000/api/scheduler/schedule \
  -H "Content-Type: application/json" \
  -d '{"name": "테스트", "task": "app.tasks.scheduler.crawl_all_complexes", "hour": 15, "minute": 0, "day_of_week": "*"}'

# 5초 후 로그 확인
tail -f /tmp/celery_beat.log
# 예상: [INFO] RedBeatScheduler: Scheduler entry changed: 테스트
```

---

## 📚 참고 자료

- [RedBeat GitHub](https://github.com/sibson/redbeat)
- [Celery Beat 문서](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [스케줄러 API 문서](http://localhost:8000/docs#/scheduler)
