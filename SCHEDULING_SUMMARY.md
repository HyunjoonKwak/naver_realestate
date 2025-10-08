# 스케줄 관리 요약

## ❓ 질문: "스케줄을 설정하거나 변경할 때마다 celery beat를 조작해야 하는 거야?"

## ✅ 답변: 아니요! (RedBeat 적용 완료)

**RedBeat**을 적용하여 **재시작 없이** 스케줄을 동적으로 변경할 수 있게 되었습니다.

---

## 🔄 변경 사항

### Before (PersistentScheduler)
```
schedules.json 수정
    ↓
Celery Beat 종료
    ↓
캐시 파일 삭제 (rm -f /tmp/celerybeat-schedule*)
    ↓
Celery Beat 재시작
    ↓
변경사항 반영 ✅
```

### After (RedBeat) ⭐
```
방법 1: schedules.json 수정
    ↓
5초 이내 자동 반영 ✅

방법 2: API 호출
    ↓
즉시 반영 ✅
```

---

## 🚀 사용 방법

### 1. JSON 파일로 스케줄 변경 (기존 방식 - 개선됨)

```bash
# 파일 수정
vim backend/app/config/schedules.json

# 저장 후 - 5초 이내 자동 반영!
# ✨ 재시작 불필요!
```

**장점:**
- 간단함
- 기존 방식과 동일

**단점:**
- Beat 재시작 시 JSON → Redis 재로드 (일회성 변경은 사라짐)

### 2. API로 스케줄 동적 변경 (권장) ⭐

```bash
# 스케줄 생성
curl -X POST "http://localhost:8000/api/scheduler/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "새로운_크롤링",
    "task": "app.tasks.scheduler.crawl_all_complexes",
    "hour": 15,
    "minute": 0,
    "day_of_week": 3,
    "description": "매주 수요일 15시"
  }'

# 스케줄 수정
curl -X PUT "http://localhost:8000/api/scheduler/schedule/새로운_크롤링" \
  -H "Content-Type: application/json" \
  -d '{"hour": 16, "minute": 30}'

# 스케줄 삭제
curl -X DELETE "http://localhost:8000/api/scheduler/schedule/새로운_크롤링"

# ✨ 모두 즉시 반영! 재시작 불필요!
```

**장점:**
- 즉시 반영 (5초 이내)
- 재시작 불필요
- 프로그래밍 가능

**단점:**
- Beat 재시작 시 영구 저장하려면 `schedules.json`도 업데이트 필요

---

## 📋 스케줄 확인

```bash
# 터미널에서 확인
./check_schedules.sh

# API로 확인
curl http://localhost:8000/api/scheduler/schedule

# Redis에서 직접 확인
redis-cli KEYS "redbeat:*"
```

---

## 💡 권장 워크플로우

### 임시 테스트 (일회성)

```bash
# API로 빠르게 추가
curl -X POST http://localhost:8000/api/scheduler/schedule -d {...}

# 테스트 완료 후 삭제
curl -X DELETE http://localhost:8000/api/scheduler/schedule/테스트명
```

### 영구 스케줄 (프로덕션)

```bash
# 1. schedules.json 파일 수정
vim backend/app/config/schedules.json

# 2. 5초 이내 자동 반영 확인
./check_schedules.sh

# 3. Beat 재시작 후에도 유지됨 ✅
```

---

## 🔧 기술 상세

### RedBeat이란?

- **Redis 기반** Celery Beat 스케줄러
- 스케줄을 **Redis**에 저장 (파일 대신)
- **5초마다** Redis를 폴링하여 변경사항 자동 감지
- 여러 Beat 인스턴스 간 **락**으로 중복 실행 방지

### 설정

`backend/app/core/celery_app.py`:
```python
celery_app.conf.beat_scheduler = "redbeat.RedBeatScheduler"
celery_app.conf.redbeat_redis_url = REDIS_URL
```

### 동작 원리

```
JSON 파일 또는 API
        ↓
   Redis 저장
        ↓
RedBeat (5초마다 폴링)
        ↓
   변경 감지
        ↓
   스케줄 적용
```

---

## 📚 관련 문서

- **완전 가이드**: [docs/DYNAMIC_SCHEDULING.md](docs/DYNAMIC_SCHEDULING.md)
- **트러블슈팅**: [docs/SCHEDULER_TROUBLESHOOTING.md](docs/SCHEDULER_TROUBLESHOOTING.md)
- **Discord 브리핑**: [docs/DISCORD_BRIEFING_GUIDE.md](docs/DISCORD_BRIEFING_GUIDE.md)

---

## ⚡ 빠른 참조

```bash
# 스케줄 확인
./check_schedules.sh

# 스케줄 생성 (API)
curl -X POST http://localhost:8000/api/scheduler/schedule -H "Content-Type: application/json" -d '{"name":"...", "task":"...", "hour":..., "minute":..., "day_of_week":...}'

# 스케줄 수정 (API)
curl -X PUT http://localhost:8000/api/scheduler/schedule/{이름} -H "Content-Type: application/json" -d '{"hour":..., "minute":...}'

# 스케줄 삭제 (API)
curl -X DELETE http://localhost:8000/api/scheduler/schedule/{이름}

# Beat 재시작 (필요시 - 보통 불필요)
pkill -f 'celery.*beat' && ./run_celery_beat.sh
```

---

## ✨ 결론

**이제 Celery Beat을 재시작할 필요가 없습니다!**
- JSON 파일 수정 → 자동 반영 (5초)
- API 호출 → 즉시 반영
- Redis에 저장되어 재시작 후에도 유지
