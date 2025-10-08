# 스케줄러 자동 시작 가이드

## 🎯 목적
컴퓨터 재시작 후에도 Celery Beat(스케줄러)가 자동으로 시작되도록 설정

## ✅ 현재 상황
- 스케줄 설정: Redis + JSON 파일에 정상 저장됨
- **문제**: Celery Beat가 실행되지 않으면 스케줄이 작동하지 않음

## 🔧 해결 방법

### 방법 1: macOS launchd 사용 (추천)

컴퓨터가 켜질 때마다 자동으로 Celery 서비스 시작

```bash
# 1. launchd 설정 로드
launchctl load ~/Library/LaunchAgents/com.naver.realestate.celery.plist

# 2. 시작 확인
launchctl list | grep naver.realestate

# 3. 수동 시작/중지
launchctl start com.naver.realestate.celery
launchctl stop com.naver.realestate.celery

# 4. 자동 시작 해제
launchctl unload ~/Library/LaunchAgents/com.naver.realestate.celery.plist
```

### 방법 2: 수동 실행 (현재 사용 중)

```bash
cd backend
./start_celery_services.sh
```

**단점**: 컴퓨터 재시작 시 다시 실행해야 함

### 방법 3: Docker Compose (프로덕션)

```bash
docker-compose up -d celery_worker celery_beat
```

**장점**: 
- 재시작 시 자동 실행 (`restart: unless-stopped`)
- 로그 관리 편함

**단점**: 
- 크롤러가 headless=False 필요 (Docker에서는 어려움)

## 📊 상태 확인

```bash
# Celery Beat 실행 확인
ps aux | grep "celery.*beat" | grep -v grep

# 로그 확인
tail -f backend/logs/celery_beat.log

# 스케줄 확인
curl http://localhost:8000/api/scheduler/schedule | python3 -m json.tool

# 작업 이력 확인
curl http://localhost:8000/api/scheduler/jobs | python3 -m json.tool
```

## ⚠️ 주의사항

1. **Celery Beat는 하나만 실행**: 여러 개 실행하면 중복 작업 발생
2. **로그 파일 용량**: 주기적으로 정리 필요
3. **Redis 연결**: Redis가 실행 중이어야 함 (`docker-compose up -d redis`)

## 🐛 트러블슈팅

### 스케줄이 실행되지 않을 때

1. Celery Beat 실행 확인
   ```bash
   ps aux | grep "celery.*beat"
   ```

2. 로그 확인
   ```bash
   tail -50 backend/logs/celery_beat.log
   ```

3. Redis 연결 확인
   ```bash
   docker ps | grep redis
   ```

4. 스케줄 확인
   ```bash
   curl http://localhost:8000/api/scheduler/schedule
   ```

### Beat가 자꾸 종료될 때

- launchd 사용 (방법 1) → KeepAlive=true로 자동 재시작
- 로그에서 에러 확인: `backend/logs/celery_beat.log`

## 📝 요약

**스케줄러 = 스케줄 설정(Redis) + Celery Beat(프로세스)**

둘 다 있어야 작동합니다!
