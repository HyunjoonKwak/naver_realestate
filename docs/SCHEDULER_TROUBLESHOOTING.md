# Celery 스케줄러 트러블슈팅 가이드

## 📋 목차
1. [스케줄러가 동작하지 않는 경우](#스케줄러가-동작하지-않는-경우)
2. [day_of_week 설정 방법](#day_of_week-설정-방법)
3. [스케줄 확인 방법](#스케줄-확인-방법)
4. [디버깅 팁](#디버깅-팁)

---

## 스케줄러가 동작하지 않는 경우

### 1. Celery Worker & Beat 실행 확인

```bash
# 실행 중인 프로세스 확인
ps aux | grep -E "celery.*(worker|beat)" | grep -v grep

# 예상 출력:
# - worker: celery -A app.core.celery_app worker
# - beat: celery -A app.core.celery_app beat
```

**둘 다 실행 중이어야 합니다:**
- **Worker**: 태스크를 실제로 실행하는 프로세스
- **Beat**: 스케줄에 따라 태스크를 큐에 추가하는 프로세스

### 2. Celery Beat 재시작

`schedules.json` 파일을 수정한 후 **반드시** Celery Beat을 재시작해야 합니다:

```bash
cd backend

# 1. 실행 중인 Beat 종료
pkill -f 'celery.*beat'

# 2. 스케줄 캐시 삭제 (중요!)
rm -f /tmp/celerybeat-schedule*

# 3. Beat 재시작
./run_celery_beat.sh
```

**주의**: 스케줄 캐시를 삭제하지 않으면 이전 스케줄이 계속 사용될 수 있습니다!

### 3. Redis 연결 확인

```bash
# Redis 컨테이너 실행 확인
docker ps | grep redis

# Redis ping 테스트
redis-cli ping
# 예상 출력: PONG
```

---

## day_of_week 설정 방법

### ⚠️ 중요: Celery의 요일 규칙

Celery의 `crontab`은 **0=일요일**부터 시작합니다!

```python
# Celery crontab day_of_week 매핑
0 = 일요일
1 = 월요일
2 = 화요일
3 = 수요일
4 = 목요일
5 = 금요일
6 = 토요일
```

### schedules.json 설정 예시

```json
{
  "매주_월요일_크롤링": {
    "task": "app.tasks.scheduler.crawl_all_complexes",
    "schedule": {
      "hour": 6,
      "minute": 0,
      "day_of_week": 1,
      "comment": "1=월요일"
    },
    "enabled": true,
    "description": "매주 월요일 오전 6시"
  },
  "매주_수요일_테스트": {
    "task": "app.tasks.scheduler.crawl_all_complexes",
    "schedule": {
      "hour": 14,
      "minute": 30,
      "day_of_week": 3,
      "comment": "3=수요일"
    },
    "enabled": true,
    "description": "매주 수요일 오후 2시 30분"
  }
}
```

### 특수 스케줄

```json
{
  "매일_실행": {
    "schedule": {
      "hour": 9,
      "minute": 0,
      "day_of_week": "*"
    }
  },
  "매월_1일": {
    "schedule": {
      "hour": 6,
      "minute": 0,
      "day_of_week": "MONTHLY_1"
    }
  },
  "분기별_1일": {
    "schedule": {
      "hour": 6,
      "minute": 0,
      "day_of_week": "QUARTERLY_1"
    }
  }
}
```

---

## 스케줄 확인 방법

### 1. 스케줄 확인 스크립트 사용

```bash
./check_schedules.sh
```

**출력 예시:**
```
📋 등록된 스케줄 목록:

🔹 주간업데이트
   태스크: app.tasks.scheduler.crawl_all_complexes
   스케줄: 월요일 06:00
   다음 실행: 2025-10-13 06:00:00 Monday
   남은 시간: 4일 17시간 51분
```

### 2. Python으로 직접 확인

```bash
cd backend
.venv/bin/python << 'EOF'
from datetime import datetime
from app.core.celery_app import celery_app

print("📋 등록된 스케줄:")
for name, config in celery_app.conf.beat_schedule.items():
    schedule = config['schedule']
    now = datetime.now()
    remaining = schedule.remaining_estimate(now)
    next_run = now + remaining

    print(f"\n{name}:")
    print(f"  스케줄: {schedule}")
    print(f"  다음 실행: {next_run.strftime('%Y-%m-%d %H:%M:%S %A')}")
    print(f"  남은 시간: {remaining}")
EOF
```

### 3. Celery Beat 로그 확인

```bash
# Beat 로그 실시간 확인
tail -f /tmp/celery_beat.log

# Worker 로그 확인
tail -f /tmp/celery_worker.log
```

**정상 동작 시 로그 예시:**
```
[2025-10-08 06:00:00,000: INFO/MainProcess] Scheduler: Sending due task 주간업데이트
[2025-10-08 06:00:01,234: INFO/MainProcess] Task app.tasks.scheduler.crawl_all_complexes[abc-123] received
```

---

## 디버깅 팁

### 1. 즉시 실행 테스트 (분 단위 조정)

스케줄이 올바르게 설정되었는지 확인하려면 현재 시각으로부터 2-3분 후로 설정:

```json
{
  "테스트_스케줄": {
    "task": "app.tasks.scheduler.crawl_all_complexes",
    "schedule": {
      "hour": 14,
      "minute": 32,
      "day_of_week": 3,
      "comment": "현재: 14:30, 테스트: 14:32 (2분 후)"
    },
    "enabled": true
  }
}
```

**순서:**
1. `schedules.json` 수정
2. Celery Beat 재시작 (캐시 삭제 필수!)
3. `./check_schedules.sh`로 다음 실행 시간 확인
4. Worker 로그에서 태스크 실행 확인

### 2. Celery Inspect로 활성 태스크 확인

```bash
cd backend

# 현재 실행 중인 태스크 확인
.venv/bin/celery -A app.core.celery_app inspect active

# 예약된 태스크 확인
.venv/bin/celery -A app.core.celery_app inspect scheduled
```

### 3. 수동 태스크 실행

스케줄러 없이 직접 태스크를 실행하여 태스크 자체의 문제를 분리:

```bash
cd backend
.venv/bin/python << 'EOF'
from app.tasks.scheduler import crawl_all_complexes

# 동기 실행 (테스트용)
result = crawl_all_complexes(job_type='manual')
print(result)
EOF
```

### 4. 타임존 문제

Celery는 `Asia/Seoul` 타임존을 사용하도록 설정되어 있습니다:

```python
# backend/app/core/celery_app.py
celery_app.conf.update(
    timezone="Asia/Seoul",
    enable_utc=False
)
```

**시간대 확인:**
```bash
.venv/bin/python -c "
from datetime import datetime
print('현재 시간:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
"
```

### 5. 흔한 실수

#### ❌ 잘못된 요일 설정
```json
{
  "schedule": {
    "day_of_week": "1",  // 문자열도 작동하지만 정수 권장
  }
}
```

#### ✅ 올바른 설정
```json
{
  "schedule": {
    "day_of_week": 1,  // 정수 (1=월요일)
  }
}
```

#### ❌ Beat 재시작 없이 스케줄 변경
- 스케줄 변경 후 Beat을 재시작하지 않으면 변경사항이 반영되지 않음

#### ❌ 캐시 파일 미삭제
- `/tmp/celerybeat-schedule*` 파일이 남아있으면 이전 스케줄 사용

---

## 자주 하는 질문 (FAQ)

### Q1: 스케줄을 추가했는데 실행되지 않아요
**A:** Celery Beat을 재시작하고 캐시를 삭제하세요:
```bash
pkill -f 'celery.*beat'
rm -f /tmp/celerybeat-schedule*
./run_celery_beat.sh
```

### Q2: 월요일 오전 6시에 실행하고 싶은데 어떻게 설정하나요?
**A:**
```json
{
  "schedule": {
    "hour": 6,
    "minute": 0,
    "day_of_week": 1
  }
}
```

### Q3: 스케줄이 UTC 시간으로 실행돼요
**A:** `celery_app.py`에서 타임존이 `Asia/Seoul`로 설정되어 있는지 확인하세요.

### Q4: 태스크가 중복 실행돼요
**A:** Celery Beat이 여러 개 실행 중일 수 있습니다:
```bash
# 모든 Beat 종료
pkill -f 'celery.*beat'

# 단 하나만 재시작
./run_celery_beat.sh
```

### Q5: 스케줄 변경 없이 즉시 크롤링하고 싶어요
**A:** API 엔드포인트 사용:
```bash
curl -X POST "http://localhost:8000/api/scheduler/crawl-all?job_type=manual"
```

---

## 참고 자료

- [Celery Beat 공식 문서](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [Celery crontab 문서](https://docs.celeryproject.org/en/stable/reference/celery.schedules.html#celery.schedules.crontab)
- [Discord 브리핑 가이드](./DISCORD_BRIEFING_GUIDE.md)
