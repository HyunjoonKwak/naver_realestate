# 맥북에서 개발 환경 설정하기

집 맥에서 작업하던 프로젝트를 맥북에서 이어서 작업하기 위한 가이드입니다.

## 📋 사전 준비사항

- **Git**: 코드 동기화용
- **Docker Desktop**: PostgreSQL, Redis 실행용
- **Node.js**: Frontend 실행용
- **Python 3.13**: Backend 실행용

## 🚀 빠른 시작 (처음 설정하는 경우)

### 1단계: 저장소 클론

```bash
# 저장소 클론 (처음인 경우)
git clone https://github.com/YOUR_USERNAME/naver_realestate.git
cd naver_realestate

# 또는 이미 클론했다면 최신 코드 받기
cd naver_realestate
git pull origin main
```

### 2단계: Backend 환경 설정

```bash
cd backend

# Python 가상환경 생성
python3 -m venv .venv

# 의존성 설치
.venv/bin/pip install -r requirements.txt

# Playwright 브라우저 설치 (크롤링용)
.venv/bin/playwright install chromium
```

### 3단계: Frontend 환경 설정

```bash
cd ../frontend

# Node 패키지 설치
npm install
```

### 4단계: 환경변수 설정

집 맥의 `.env` 파일 내용을 맥북으로 복사합니다:

```bash
# backend/.env 파일 생성
cd ../backend
touch .env
```

**`.env` 파일 내용 (집 맥에서 복사):**
```env
# Discord Webhook (선택사항 - 브리핑 기능용)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# 국토부 실거래가 API Key (선택사항)
MOLIT_API_KEY=your_api_key_here
```

> **주의**: `.env` 파일은 Git에 커밋되지 않으므로 직접 복사해야 합니다.

### 5단계: Docker 컨테이너 시작

```bash
# 프로젝트 루트로 이동
cd ..

# PostgreSQL + Redis 컨테이너 시작
docker-compose up -d

# 컨테이너 상태 확인
docker ps
```

**예상 출력:**
```
CONTAINER ID   IMAGE          PORTS
xxxxx          postgres:15    0.0.0.0:5433->5432/tcp
xxxxx          redis:7        0.0.0.0:6380->6379/tcp
```

### 6단계: 데이터베이스 초기화

```bash
cd backend

# 데이터베이스 테이블 생성
.venv/bin/python migrate_db.py
```

**출력:**
```
🔄 데이터베이스 마이그레이션 시작...
✅ 마이그레이션 완료!
   - article_snapshots 테이블
   - article_changes 테이블
   - users 테이블
   - favorite_complexes 테이블
```

### 7단계: 서버 실행

**터미널 1: Backend API**
```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**터미널 2: Frontend**
```bash
cd frontend
npm run dev
```

**터미널 3: Celery Worker (선택사항 - 크롤링용)**
```bash
cd backend
./run_celery_worker.sh
```

**터미널 4: Celery Beat (선택사항 - 스케줄러용)**
```bash
cd backend
./run_celery_beat.sh
```

### 8단계: 접속 확인

- **Frontend**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs
- **스케줄러 페이지**: http://localhost:3000/scheduler

## 🔄 이미 설정한 경우 (두 번째부터)

```bash
# 1. 최신 코드 받기
cd naver_realestate
git pull origin main

# 2. Docker 컨테이너 시작
docker-compose up -d

# 3. Backend 의존성 업데이트 (requirements.txt 변경 시)
cd backend
.venv/bin/pip install -r requirements.txt

# 4. Frontend 의존성 업데이트 (package.json 변경 시)
cd ../frontend
npm install

# 5. 서버 실행
# 터미널 1
cd backend && .venv/bin/uvicorn app.main:app --reload

# 터미널 2
cd frontend && npm run dev
```

## 💾 데이터베이스 동기화

### 방법 1: 집 맥 데이터 가져오기

**집 맥에서 덤프:**
```bash
# 프로젝트 루트에서
docker exec naver_realestate-postgres-1 pg_dump -U postgres realestate > db_backup.sql

# Git에 포함하지 말 것! (.gitignore에 추가됨)
```

**맥북에서 복원:**
```bash
# db_backup.sql 파일을 맥북으로 복사 후
docker exec -i naver_realestate-postgres-1 psql -U postgres realestate < db_backup.sql
```

### 방법 2: 빈 데이터베이스로 시작 (권장)

```bash
cd backend
.venv/bin/python migrate_db.py
```

맥북에서 새로 단지를 추가하면서 작업하는 것을 권장합니다.

## 🔧 문제 해결

### 포트 충돌 에러

**증상:**
```
Error: port 5433 is already allocated
```

**해결:**
```bash
# 충돌하는 컨테이너 확인
docker ps

# 기존 컨테이너 중지
docker stop <container_id>

# 또는 docker-compose.yml에서 포트 변경
# 5433 -> 5434 등으로 변경 후 다시 실행
```

### Playwright 크롤링 안 됨

**증상:**
```
Executable doesn't exist
```

**해결:**
```bash
cd backend
.venv/bin/playwright install chromium
```

### Python 버전 문제

**증상:**
```
Python 3.13 required
```

**해결:**
```bash
# Python 3.13 설치 후
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Docker 컨테이너가 시작 안 됨

**확인:**
```bash
# Docker Desktop이 실행 중인지 확인
docker ps

# 컨테이너 로그 확인
docker logs naver_realestate-postgres-1
docker logs naver_realestate-redis-1
```

## 📝 작업 종료 시

### 맥북에서 작업 종료

```bash
# 1. 변경사항 커밋
git add .
git commit -m "맥북에서 작업한 내용"
git push origin main

# 2. Docker 컨테이너 중지 (선택사항)
docker-compose down

# 또는 실행 상태 유지하려면 그냥 종료
```

### 집 맥에서 이어서 작업

```bash
# 최신 코드 받기
git pull origin main

# 서버 재시작 (실행 중이었다면)
# Backend와 Frontend 터미널에서 자동 리로드됨
```

## ⚠️ 주의사항

### 1. Docker 볼륨은 공유되지 않음
- 집 맥과 맥북의 데이터베이스는 **별도**입니다
- 데이터를 공유하려면 덤프/복원 필요

### 2. Redis 데이터도 별도
- Celery Beat 스케줄도 각각 설정해야 합니다
- 스케줄러 페이지에서 다시 등록 필요

### 3. 크롤링은 GUI 환경 필요
- `headless=False` 설정 때문에 화면 필요
- 원격 SSH로는 크롤링 불가

### 4. .env 파일 주의
- Git에 커밋되지 않으므로 수동 복사 필요
- Discord Webhook, API Key 등 비밀 정보 포함

### 5. 동시 작업 주의
- 집 맥과 맥북에서 동시에 작업하지 말 것
- Git 충돌 발생 가능

## 🎯 체크리스트

### 처음 설정 시
- [ ] Git 저장소 클론
- [ ] Backend 가상환경 생성
- [ ] Backend 의존성 설치
- [ ] Playwright 설치
- [ ] Frontend 패키지 설치
- [ ] .env 파일 생성
- [ ] Docker 컨테이너 시작
- [ ] 데이터베이스 마이그레이션
- [ ] API 서버 실행 확인
- [ ] Frontend 실행 확인

### 매번 작업 시
- [ ] `git pull` 최신 코드 받기
- [ ] Docker 컨테이너 시작
- [ ] Backend 서버 실행
- [ ] Frontend 서버 실행
- [ ] 작업 완료 후 `git push`

## 📚 참고 문서

- [README.md](../README.md) - 프로젝트 전체 개요
- [CLAUDE.md](../CLAUDE.md) - 기술 문서
- [API_GUIDE.md](./API_GUIDE.md) - API 사용법
- [TRANSACTION_GUIDE.md](./TRANSACTION_GUIDE.md) - 실거래가 기능

## 💡 팁

### 터미널 멀티플렉서 사용
```bash
# tmux 사용 예시
tmux new -s naver

# 창 분할
Ctrl+B, %  # 좌우 분할
Ctrl+B, "  # 상하 분할

# 세션 종료 없이 나가기
Ctrl+B, D

# 다시 접속
tmux attach -t naver
```

### VS Code 통합 터미널
- Backend, Frontend, Worker, Beat 각각 터미널 탭 생성
- 한 번에 모든 서버 확인 가능

### Docker Desktop 설정
- Settings → Resources → Memory: 최소 4GB 권장
- PostgreSQL + Redis는 메모리 많이 사용 안 함

---

**문제가 생기면:**
1. GitHub Issues에 문제 등록
2. Claude Code로 문의
3. 로그 파일 확인 (`docker logs`, 터미널 출력)
