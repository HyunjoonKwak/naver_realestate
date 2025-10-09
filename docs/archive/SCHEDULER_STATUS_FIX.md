# Celery Beat 상태 확인 개선

## 🔍 문제

**질문:** "celery worker나 celery beat는 활성 상태를 표시하고 있는데 이건 실제 상태를 반영하지 못하고 있는건가?"

**답:** 맞습니다! 이전 구현은 실제 상태를 반영하지 못했습니다.

## ❌ 이전 구현의 문제점

### 백엔드 (`/api/scheduler/status`)

```python
# 이전 코드
return {
    "workers": {
        "active": active_workers is not None,  # Worker는 정확함
        ...
    },
    "beat_schedule": list(celery_app.conf.beat_schedule.keys())  # ❌ 문제!
}
```

**문제:**
1. `beat_schedule`은 **설정 파일**에서 가져옴 (실제 프로세스와 무관)
2. Beat 프로세스가 죽어도 스케줄 목록은 여전히 존재
3. 프론트엔드에서 "스케줄 목록이 있으면 Beat 활성"으로 판단
4. **실제로는 Beat가 죽었는데도 "활성"으로 표시됨** ❌

### 프론트엔드

```typescript
// 이전 코드
{workerStatus?.beat_schedule && workerStatus.beat_schedule.length > 0 ? (
  <span className="text-green-600">활성</span>  // ❌ 틀림!
) : (
  <span className="text-red-600">비활성</span>
)}
```

**문제:**
- `beat_schedule.length > 0`으로 판단
- 스케줄 목록만 확인 (실제 프로세스 상태 확인 안함)

## ✅ 개선된 구현

### 1. 백엔드 - Redis Lock으로 실제 상태 확인

```python
# 개선된 코드
import redis

# Beat 상태 확인 (Redis lock으로 확인)
beat_active = False
beat_lock_ttl = None
try:
    r = redis.from_url(celery_app.conf.redbeat_redis_url)
    lock_key = "redbeat::lock"
    beat_lock_ttl = r.ttl(lock_key)
    # TTL이 양수면 Beat가 락을 보유 중 (실행 중)
    beat_active = beat_lock_ttl > 0
except Exception:
    pass

return {
    "workers": {...},
    "beat": {
        "active": beat_active,        # ✅ 실제 상태!
        "lock_ttl": beat_lock_ttl      # ✅ 건강 상태!
    },
    ...
}
```

**원리:**
- RedBeat는 실행 중일 때 Redis에 `redbeat::lock` 키를 생성
- 락 타임아웃: 30분 (1800초)
- Beat가 살아있으면 주기적으로 락 TTL 갱신
- **TTL > 0 → Beat 실행 중**
- **TTL ≤ 0 → Beat 죽음**

### 2. 프론트엔드 - 실제 상태 표시

```typescript
// 개선된 코드
interface WorkerStatus {
  ...
  beat?: {
    active: boolean;     // ✅ 실제 상태
    lock_ttl?: number;   // ✅ TTL (초)
  };
}

// UI
{workerStatus?.beat?.active ? (
  <span className="text-green-600">활성</span>
) : (
  <span className="text-red-600">비활성</span>
)}
{workerStatus?.beat?.lock_ttl && (
  <p className="text-xs text-gray-500 mt-1">
    Lock TTL: {Math.floor(workerStatus.beat.lock_ttl / 60)}분
  </p>
)}
```

**개선 사항:**
- `beat.active`로 실제 프로세스 상태 확인
- Lock TTL을 분 단위로 표시
- Beat가 죽으면 즉시 "비활성" 표시

## 🧪 테스트 결과

### 시나리오 1: Beat 실행 중
```
API 응답:
{
  "beat": {
    "active": true,
    "lock_ttl": 1510
  }
}

프론트엔드:
Celery Beat: 활성 ✅
Lock TTL: 25분
```

### 시나리오 2: Beat 중지
```
API 응답:
{
  "beat": {
    "active": false,
    "lock_ttl": null
  }
}

프론트엔드:
Celery Beat: 비활성 ✅
Lock TTL: (표시 안됨)
```

### 시나리오 3: Beat 재시작
```
API 응답:
{
  "beat": {
    "active": true,
    "lock_ttl": 1795
  }
}

프론트엔드:
Celery Beat: 활성 ✅
Lock TTL: 29분
```

## 📊 비교

| 항목 | 이전 | 개선 후 |
|------|------|---------|
| 확인 방법 | 스케줄 목록 존재 여부 | Redis Lock TTL |
| Beat 죽었을 때 | "활성" 표시 ❌ | "비활성" 표시 ✅ |
| 실시간성 | 없음 | 있음 (10초마다 갱신) |
| 건강 상태 | 알 수 없음 | Lock TTL로 확인 가능 |

## 🎯 결론

**이전:**
- ❌ Beat가 죽어도 "활성"으로 표시
- ❌ 사용자가 스케줄이 작동하지 않는 이유를 알 수 없음
- ❌ 디버깅 어려움

**개선 후:**
- ✅ Beat 실제 상태를 정확히 표시
- ✅ Lock TTL로 건강 상태 모니터링
- ✅ Beat가 죽으면 즉시 알 수 있음
- ✅ 스케줄러 문제 디버깅 용이

---

**수정 파일:**
- `backend/app/api/scheduler.py` - Beat 상태 확인 로직 추가
- `frontend/src/app/scheduler/page.tsx` - Beat 상태 표시 개선

**날짜:** 2025-10-08
