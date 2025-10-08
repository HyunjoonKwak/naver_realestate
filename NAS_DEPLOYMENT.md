# NAS 배포 가이드

## 개요

이 프로젝트는 Docker Compose를 사용하여 NAS에서 운영할 수 있도록 설계되었습니다.
모든 서비스(FastAPI, Celery Worker, Celery Beat, Frontend)가 컨테이너화되어 있으며,
`restart: unless-stopped` 정책으로 자동 복구됩니다.

## 1. 사전 준비

```bash
# NAS에 Docker 및 Docker Compose 설치 확인
docker --version
docker-compose --version
```

## 2. 코드 배포

### 방법 1: Git으로 배포 (추천)
```bash
cd /volume1/docker
git clone <your-repo-url> naver_realestate
cd naver_realestate
```

### 방법 2: rsync로 로컬에서 전송
```bash
rsync -avz --exclude 'node_modules' --exclude '.venv' \
  /Users/specialrisk_mac/code_work/naver_realestate/ \
  nas-user@nas-ip:/volume1/docker/naver_realestate/
```

## 3. 환경 변수 설정

```bash
# backend/.env 파일 생성
cat > backend/.env << 'ENVEOF'
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/naver_realestate
REDIS_HOST=redis
REDIS_PORT=6379
MOLIT_API_KEY=your_molit_api_key_here
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_here
ENVEOF
```

## 4. 서비스 시작

```bash
# 빌드 및 시작
docker-compose up -d --build

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f celery_beat
docker-compose logs -f celery_worker
```

## 5. 데이터베이스 초기화

```bash
# DB 마이그레이션 (외래키 포함 - 권장)
docker-compose exec api python migrate_db.py

# 또는 리셋 (주의! 모든 데이터 삭제)
docker-compose exec api python reset_db.py
```

## 6. 상태 확인

```bash
# 모든 컨테이너 상태
docker-compose ps

# Beat가 Lock 획득했는지 확인
docker-compose exec redis redis-cli TTL "redbeat::lock"
# 양수(1800 근처)가 나오면 정상

# API 헬스체크
curl http://localhost:8000/health

# 스케줄 확인
curl http://localhost:8000/api/scheduler/schedules

# Beat 스케줄 상태
docker-compose exec celery_beat celery -A app.core.celery_app inspect scheduled
```

## 7. NAS 재부팅 시 자동 시작 설정

### Synology NAS
1. **제어판** > **작업 스케줄러** > **생성** > **트리거된 작업** > **사용자 정의 스크립트**
2. **부팅** 이벤트 선택
3. 스크립트 입력:
```bash
#!/bin/bash
sleep 30  # Docker Daemon 시작 대기
cd /volume1/docker/naver_realestate
docker-compose up -d
```

### QNAP NAS
1. **Container Station** > **Preferences** > **Auto-start**
2. 또는 crontab 사용:
```bash
@reboot cd /share/Container/naver_realestate && docker-compose up -d
```

## 8. 업데이트

```bash
# 코드 업데이트
git pull

# 컨테이너 재빌드 및 재시작
docker-compose up -d --build

# 또는 특정 서비스만
docker-compose up -d --build celery_beat

# 다운타임 없이 업데이트 (rolling update)
docker-compose up -d --no-deps --build celery_beat
```

## 9. 모니터링

```bash
# 실시간 로그 보기
docker-compose logs -f --tail=100

# 특정 서비스 로그
docker-compose logs -f celery_beat celery_worker

# Celery Beat 작동 확인
docker-compose exec celery_beat celery -A app.core.celery_app inspect active

# Redis 상태
docker-compose exec redis redis-cli INFO stats

# PostgreSQL 연결 확인
docker-compose exec postgres psql -U postgres -d naver_realestate -c "\dt"
```

## 10. 문제 해결

### Celery Beat가 작동하지 않을 때
```bash
# Beat 로그 확인
docker-compose logs celery_beat

# Redis Lock 확인
docker-compose exec redis redis-cli GET "redbeat::lock"
docker-compose exec redis redis-cli TTL "redbeat::lock"

# Lock 수동 삭제 후 재시작
docker-compose exec redis redis-cli DEL "redbeat::lock"
docker-compose restart celery_beat

# Lock 획득 로그 확인
docker-compose logs celery_beat | grep -i "acquired lock"
```

### 크롤링이 실행되지 않을 때
```bash
# Worker 상태 확인
docker-compose exec celery_worker celery -A app.core.celery_app inspect active
docker-compose exec celery_worker celery -A app.core.celery_app inspect registered

# Redis 큐 확인
docker-compose exec redis redis-cli LLEN "celery"

# Worker 재시작
docker-compose restart celery_worker
```

### Discord 브리핑이 전송되지 않을 때
```bash
# 환경변수 확인
docker-compose exec celery_worker env | grep DISCORD

# 브리핑 서비스 테스트
docker-compose exec api python -c "
from app.services.briefing_service import BriefingService
from app.core.database import SessionLocal
db = SessionLocal()
service = BriefingService(db)
print(service.notification_manager.discord.webhook_url)
"

# Webhook URL 테스트
docker-compose exec api curl -X POST $DISCORD_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"content": "테스트 메시지"}'
```

### 컨테이너가 계속 재시작될 때
```bash
# 재시작 원인 확인
docker-compose ps
docker-compose logs <서비스명>

# 모든 컨테이너 재시작
docker-compose restart

# 전체 재구축
docker-compose down
docker-compose up -d --build
```

## 11. 백업

### PostgreSQL 백업
```bash
# 덤프 생성
docker-compose exec postgres pg_dump -U postgres naver_realestate > backup_$(date +%Y%m%d).sql

# 복원
docker-compose exec -T postgres psql -U postgres naver_realestate < backup_20251008.sql
```

### Redis 백업
```bash
# Redis 데이터 저장
docker-compose exec redis redis-cli SAVE

# dump.rdb 파일 복사
docker cp naver_realestate_redis:/data/dump.rdb ./backup/redis_dump_$(date +%Y%m%d).rdb
```

### 전체 볼륨 백업
```bash
# 서비스 중지
docker-compose down

# 볼륨 백업
tar czf naver_realestate_backup_$(date +%Y%m%d).tar.gz \
  postgres_data/ redis_data/ backend/.env backend/app/config/

# 서비스 재시작
docker-compose up -d
```

### 복원
```bash
# 볼륨 압축 해제
tar xzf naver_realestate_backup_20251008.tar.gz

# 서비스 시작
docker-compose up -d
```

## 12. 성능 최적화

### 리소스 제한 설정
docker-compose.yml에 추가:
```yaml
services:
  celery_worker:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Playwright 크롤링 최적화
```yaml
celery_worker:
  environment:
    - PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    - PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
  shm_size: 2gb  # Chromium 메모리 증가
```

## 13. 보안

### 프로덕션 환경 권장사항
1. **환경변수 파일 권한 설정**
```bash
chmod 600 backend/.env
```

2. **PostgreSQL 비밀번호 변경**
```yaml
environment:
  POSTGRES_PASSWORD: <strong-password>
```

3. **네트워크 격리**
```yaml
services:
  postgres:
    ports: []  # 외부 포트 노출 제거
  redis:
    ports: []
```

4. **Reverse Proxy 사용 (nginx)**
```bash
# API와 Frontend만 노출
nginx -> api:8000
nginx -> frontend:3000
```

## 14. 로그 관리

### 로그 크기 제한
docker-compose.yml에 추가:
```yaml
services:
  celery_worker:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 로그 수집
```bash
# 로그 파일로 저장
docker-compose logs > logs_$(date +%Y%m%d_%H%M%S).txt

# 에러만 추출
docker-compose logs | grep -i error > errors.txt
```

## 15. 유지보수 체크리스트

### 일일 점검
- [ ] 모든 컨테이너 상태 확인 (`docker-compose ps`)
- [ ] Celery Beat Lock TTL 확인
- [ ] 크롤링 작업 실행 여부 확인

### 주간 점검
- [ ] 로그 확인 및 에러 분석
- [ ] 디스크 용량 확인
- [ ] 데이터베이스 백업

### 월간 점검
- [ ] Docker 이미지 업데이트
- [ ] 보안 패치 적용
- [ ] 성능 모니터링 및 최적화

## 문의 및 이슈

- 문제 발생 시 로그 확인: `docker-compose logs`
- GitHub Issues: [프로젝트 저장소 URL]
