# 개발 환경 설정 가이드

1인 개발자가 맥(Mac mini/iMac)과 맥북(MacBook)을 오가며 작업할 때 필요한 환경 설정 및 운영 가이드입니다.

## 📋 목차
1. [사전 준비사항](#사전-준비사항)
2. [처음 설정하기](#처음-설정하기)
3. [매일 작업 시작/종료](#매일-작업-시작종료)
4. [다른 맥에서 작업하기](#다른-맥에서-작업하기)
5. [문제 해결](#문제-해결)
6. [Docker 사용법](#docker-사용법)

---

## 사전 준비사항

### 필수 도구
- **Git**: 코드 동기화
- **Docker Desktop**: PostgreSQL, Redis 실행
- **Python 3.13**: Backend 실행
- **Node.js 18+**: Frontend 실행
- **Homebrew**: 패키지 관리

### 설치 확인
```bash
# 버전 확인
git --version
docker --version
python3.13 --version
node --version
brew --version
```

### 설치가 필요한 경우
```bash
# Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Docker Desktop 설치
brew install --cask docker
# Applications 폴더에서 Docker 실행 필수

# Python 3.13 설치
brew install python@3.13

# Node.js 설치
brew install node
```

---

## 처음 설정하기

### 1단계: 저장소 클론
```bash
# 저장소 클론
git clone https://github.com/YOUR_USERNAME/naver_realestate.git
cd naver_realestate
```

### 2단계: Backend 환경 설정
```bash
cd backend

# Python 가상환경 생성 (Python 3.13 사용)
python3.13 -m venv .venv

# 가상환경 활성화 및 의존성 설치
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Playwright 브라우저 설치 (크롤링 필수)
.venv/bin/playwright install chromium
```

### 3단계: Frontend 환경 설정
```bash
cd ../frontend
npm install
```

### 4단계: 환경변수 설정
```bash
cd ../backend
touch .env
```

**`.env` 파일 내용:**
```env
# 데이터베이스 (로컬 Docker 사용 시)
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/naver_realestate

# Redis (로컬 Docker 사용 시)
REDIS_URL=redis://localhost:6380/0

# 국토교통부 실거래가 API (선택사항)
# https://www.data.go.kr/data/15058017/openapi.do
MOLIT_API_KEY=your_api_key_here

# Discord Webhook (선택사항 - 브리핑 기능)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

> **⚠️ 주의**: `.env` 파일은 Git에 커밋되지 않습니다. 다른 맥에서 작업 시 수동으로 복사하거나 다시 작성해야 합니다.

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
CONTAINER ID   IMAGE              STATUS         PORTS
xxxxx          postgres:15        Up 10 seconds  0.0.0.0:5433->5432/tcp
xxxxx          redis:7            Up 10 seconds  0.0.0.0:6380->6379/tcp
```

> **포트 정보**:
> - PostgreSQL: **5433** (외부) → 5432 (내부) - NAS 5432 포트 충돌 방지
> - Redis: **6380** (외부) → 6379 (내부) - NAS Redis와 분리

### 6단계: 데이터베이스 초기화
```bash
cd backend

# 데이터베이스 테이블 생성 (Foreign Keys 포함)
.venv/bin/python migrate_db.py
```

**출력:**
```
🔄 데이터베이스 마이그레이션 시작...
✅ 마이그레이션 완료!
   - complexes 테이블
   - articles 테이블
   - transactions 테이블
   - article_snapshots 테이블
   - article_changes 테이블
   - users 테이블
   - favorite_complexes 테이블
   - crawl_jobs 테이블
```

### 7단계: 개발 서버 실행

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

**터미널 3: Celery Worker (선택사항 - 백그라운드 크롤링)**
```bash
cd backend
./run_celery_worker.sh
```

**터미널 4: Celery Beat (선택사항 - 자동 스케줄링)**
```bash
cd backend
./run_celery_beat.sh
```

> **💡 팁**: VS Code 통합 터미널에서 4개 탭을 만들어 각 서버를 실행하면 편리합니다.

### 8단계: 접속 확인
- **Frontend**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs
- **스케줄러 관리**: http://localhost:3000/scheduler

---

## 매일 작업 시작/종료

### 작업 시작 (두 번째부터)

```bash
# 1. 프로젝트 폴더로 이동
cd /Users/specialrisk_mac/code_work/naver_realestate

# 2. 최신 코드 받기 (다른 맥에서 작업했다면)
git pull origin main

# 3. Docker 컨테이너 시작 (이미 실행 중이면 생략)
docker-compose up -d

# 4. 의존성 업데이트 (파일 변경 시만)
cd backend
.venv/bin/pip install -r requirements.txt  # requirements.txt 변경 시

cd ../frontend
npm install  # package.json 변경 시

# 5. 서버 실행
# 터미널 1
cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 터미널 2
cd frontend && npm run dev

# 터미널 3 (크롤링 필요 시)
cd backend && ./run_celery_worker.sh

# 터미널 4 (스케줄러 필요 시)
cd backend && ./run_celery_beat.sh
```

### 작업 종료

```bash
# 1. 변경사항 커밋 (수정한 파일이 있다면)
git add .
git status  # 커밋할 파일 확인
git commit -m "작업 내용 설명"
git push origin main

# 2. 터미널에서 Ctrl+C로 각 서버 종료
# - Backend API
# - Frontend
# - Celery Worker
# - Celery Beat

# 3. Docker 컨테이너 정리 (선택사항)
docker-compose stop    # 컨테이너 중지 (데이터 유지)
# 또는
docker-compose down    # 컨테이너 삭제 (데이터 유지)
# 또는
docker-compose down -v # 컨테이너 + 데이터 삭제 (⚠️ DB 초기화됨)
```

> **🔔 권장사항**:
> - 맥을 끄지 않는다면 Docker는 계속 실행 상태로 두는 것이 편리합니다.
> - 메모리 부족 시에만 `docker-compose stop` 실행
> - `down -v` 옵션은 DB 데이터를 모두 삭제하므로 주의!

---

## 다른 맥에서 작업하기

### 시나리오: 집 맥 → 맥북

#### 집 맥에서 (작업 종료 전)
```bash
# 1. 변경사항 커밋 및 푸시
git add .
git commit -m "집 맥에서 작업한 내용"
git push origin main

# 2. 데이터베이스 백업 (선택사항 - 데이터 공유 필요 시)
docker exec naver_realestate_db pg_dump -U postgres naver_realestate > db_backup.sql

# 3. .env 파일 확인 (맥북에 복사할 내용)
cat backend/.env
```

#### 맥북에서 (작업 시작)
```bash
# 1. 최신 코드 받기
cd naver_realestate
git pull origin main

# 2. .env 파일 확인 (없으면 복사)
cat backend/.env

# 3. Docker 컨테이너 시작
docker-compose up -d

# 4. 데이터베이스 복원 (백업 파일이 있다면)
docker exec -i naver_realestate_db psql -U postgres naver_realestate < db_backup.sql

# 5. 서버 실행
cd backend && .venv/bin/uvicorn app.main:app --reload  # 터미널 1
cd frontend && npm run dev                              # 터미널 2
```

### 시나리오: 맥북 → 집 맥

동일한 방식으로 진행 (위 과정 반복)

### 데이터베이스 동기화 방식

**방법 1: 빈 DB로 시작 (권장)**
```bash
# 각 맥에서 독립적인 데이터베이스 사용
# 장점: 간단함, 충돌 없음
# 단점: 데이터 공유 안 됨
.venv/bin/python migrate_db.py
```

**방법 2: 덤프/복원으로 데이터 공유**
```bash
# 집 맥에서 덤프
docker exec naver_realestate_db pg_dump -U postgres naver_realestate > db_backup.sql

# 맥북으로 파일 복사 (AirDrop, USB, Git LFS 등)

# 맥북에서 복원
docker exec -i naver_realestate_db psql -U postgres naver_realestate < db_backup.sql
```

> **⚠️ 주의사항**:
> - `.env` 파일은 Git에 커밋되지 않으므로 수동 복사 필요
> - Docker 볼륨(DB 데이터)은 각 맥에서 독립적으로 관리됨
> - Redis 스케줄 정보도 독립적 (스케줄러 페이지에서 재설정 필요)

---

## 문제 해결

### 포트 충돌 에러

**증상:**
```
Error: port 5433 is already allocated
```

**원인**: 이미 PostgreSQL 컨테이너가 실행 중이거나 다른 프로세스가 포트 사용

**해결:**
```bash
# 1. 실행 중인 컨테이너 확인
docker ps

# 2. 특정 컨테이너 중지
docker stop naver_realestate_db

# 3. 포트 사용 프로세스 확인
lsof -i :5433  # PostgreSQL
lsof -i :6380  # Redis

# 4. 또는 docker-compose.yml에서 포트 변경
# 예: 5433 -> 5434
```

### Playwright 크롤링 실패

**증상:**
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**원인**: Playwright 브라우저 미설치

**해결:**
```bash
cd backend
.venv/bin/playwright install chromium
```

### Python 버전 문제

**증상:**
```
Python 3.13 required, but 3.11 found
```

**해결:**
```bash
# Python 3.13 설치
brew install python@3.13

# 가상환경 재생성
cd backend
rm -rf .venv
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

### Docker 컨테이너 시작 실패

**확인 사항:**
```bash
# Docker Desktop 실행 확인
docker ps  # 에러 발생 시 Docker Desktop 실행

# 컨테이너 로그 확인
docker logs naver_realestate_db
docker logs naver_realestate_redis

# 컨테이너 재시작
docker-compose restart

# 완전 재시작 (데이터 유지)
docker-compose down
docker-compose up -d

# 완전 초기화 (데이터 삭제 ⚠️)
docker-compose down -v
docker-compose up -d
cd backend && .venv/bin/python migrate_db.py
```

### Celery Beat 스케줄러 작동 안 함

**증상**: 스케줄러 페이지에서 "비활성" 상태

**원인**: Mac 슬립 모드 > 12시간 경과 시 Beat 프로세스 종료

**해결:**
```bash
# 방법 1: 브라우저에서 재활성화 (권장)
# http://localhost:3000/scheduler 접속
# "🔄 재활성화" 버튼 클릭

# 방법 2: 터미널에서 재시작
cd backend
./run_celery_beat.sh
```

### Git 충돌 발생

**증상:**
```
error: Your local changes would be overwritten by merge
```

**해결:**
```bash
# 방법 1: 변경사항 커밋 후 풀
git add .
git commit -m "작업 내용"
git pull origin main

# 방법 2: 변경사항 임시 저장
git stash
git pull origin main
git stash pop

# 방법 3: 충돌 수동 해결
git pull origin main
# 충돌 파일 편집 후
git add .
git commit -m "Merge conflicts resolved"
```

---

## Docker 사용법

### Docker 기본 개념

**Image (이미지)**
- 프로그램 설치 파일 같은 것
- 예: `postgres:15-alpine`, `redis:7-alpine`

**Container (컨테이너)**
- 이미지를 실행한 것
- 독립적인 가상 환경

**Volume (볼륨)**
- 데이터 저장 공간
- 컨테이너 삭제해도 볼륨은 유지

### 자주 쓰는 명령어

```bash
# === 컨테이너 관리 ===

# 컨테이너 시작 (처음 또는 중지 상태에서)
docker-compose up -d

# 컨테이너 중지 (데이터 유지)
docker-compose stop

# 컨테이너 재시작
docker-compose restart

# 컨테이너 삭제 (데이터 유지)
docker-compose down

# 컨테이너 + 볼륨 삭제 (⚠️ 데이터 삭제)
docker-compose down -v


# === 상태 확인 ===

# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인 (중지된 것 포함)
docker ps -a

# 컨테이너 상태 확인 (docker-compose)
docker-compose ps


# === 로그 확인 ===

# 모든 컨테이너 로그
docker-compose logs

# 특정 컨테이너 로그
docker-compose logs postgres
docker-compose logs redis

# 실시간 로그 보기 (Ctrl+C로 종료)
docker-compose logs -f

# 최근 100줄만 보기
docker-compose logs --tail=100


# === 데이터베이스 접속 ===

# PostgreSQL 접속
docker exec -it naver_realestate_db psql -U postgres naver_realestate

# Redis 접속
docker exec -it naver_realestate_redis redis-cli

# 데이터베이스 백업
docker exec naver_realestate_db pg_dump -U postgres naver_realestate > backup.sql

# 데이터베이스 복원
docker exec -i naver_realestate_db psql -U postgres naver_realestate < backup.sql


# === 문제 해결 ===

# 컨테이너 완전 재시작 (데이터 유지)
docker-compose down
docker-compose up -d

# 컨테이너 완전 초기화 (데이터 삭제)
docker-compose down -v
docker-compose up -d

# 사용하지 않는 이미지/컨테이너 삭제 (공간 확보)
docker system prune -a

# 특정 컨테이너 재시작
docker restart naver_realestate_db
docker restart naver_realestate_redis
```

### 프로젝트 Docker 구성

**docker-compose.yml 구조:**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5433:5432"  # 외부:내부 (NAS 5432 충돌 방지)
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"  # 외부:내부 (NAS Redis와 분리)
    volumes:
      - redis_data:/data

volumes:
  postgres_data:  # 데이터 저장 공간
  redis_data:
```

### 로컬 개발 서비스 관리

#### 1. 서비스 시작 (개발 시작 시)

```bash
# 프로젝트 루트에서
cd /Users/specialrisk_mac/code_work/naver_realestate

# Docker 컨테이너만 시작
docker-compose up -d

# 상태 확인
docker ps

# 예상 출력:
# CONTAINER ID   IMAGE              STATUS         PORTS
# xxxxx          postgres:15        Up 5 seconds   0.0.0.0:5433->5432/tcp
# xxxxx          redis:7            Up 5 seconds   0.0.0.0:6380->6379/tcp
```

#### 2. 서비스 정리 (작업 종료 시)

**방법 1: 중지 (데이터 유지, 권장)**
```bash
docker-compose stop

# 장점: 빠른 재시작, 데이터 유지
# 재시작: docker-compose start
```

**방법 2: 컨테이너 삭제 (데이터 유지)**
```bash
docker-compose down

# 장점: 리소스 완전 해제, 데이터 유지
# 재시작: docker-compose up -d
```

**방법 3: 완전 초기화 (데이터 삭제 ⚠️)**
```bash
docker-compose down -v

# ⚠️ 주의: DB 데이터 모두 삭제됨
# 재시작 시 migrate_db.py 다시 실행 필요
# 사용 시기: 개발 환경 완전 초기화 필요 시
```

#### 3. 상황별 권장 방법

| 상황 | 명령어 | 이유 |
|------|--------|------|
| 점심 시간 | 그냥 두기 | 빠른 재작업 |
| 하루 작업 종료 | `stop` 또는 그냥 두기 | 데이터 유지, 다음날 빠른 시작 |
| 주말/휴가 | `down` | 리소스 절약, 데이터 유지 |
| 환경 초기화 | `down -v` | 문제 해결, 테스트 |
| 다른 맥 이동 | `stop` 또는 `down` | 백업 후 이동 |

#### 4. 일반적인 작업 흐름

**아침 작업 시작:**
```bash
# Docker 컨테이너 확인/시작
docker ps  # 실행 중이면 생략
docker-compose up -d  # 중지 상태라면

# 개발 서버 실행
cd backend && .venv/bin/uvicorn app.main:app --reload  # 터미널 1
cd frontend && npm run dev                              # 터미널 2
```

**저녁 작업 종료:**
```bash
# 개발 서버 종료 (Ctrl+C)
# Git 커밋 및 푸시
git add .
git commit -m "작업 내용"
git push origin main

# Docker 정리 (선택)
docker-compose stop  # 또는 그냥 두기
```

#### 5. 맥북 배터리 절약 팁

맥북에서 작업 시 배터리 절약을 위해:

```bash
# 작업 종료 시 반드시 Docker 중지
docker-compose stop

# 또는 Docker Desktop 완전 종료
# Docker Desktop → Quit Docker Desktop
```

> **💡 참고**: Docker Desktop은 실행 중일 때 약 500MB-1GB 메모리 사용

---

## 🎯 체크리스트

### 처음 설정 시
- [ ] Git 저장소 클론
- [ ] Python 3.13 설치 확인
- [ ] Backend 가상환경 생성 (`.venv`)
- [ ] Backend 의존성 설치
- [ ] Playwright 브라우저 설치
- [ ] Frontend 패키지 설치
- [ ] `.env` 파일 생성 (API Key, Webhook URL)
- [ ] Docker Desktop 설치 및 실행
- [ ] Docker 컨테이너 시작 (`docker-compose up -d`)
- [ ] 데이터베이스 마이그레이션 (`migrate_db.py`)
- [ ] API 서버 실행 확인 (http://localhost:8000/docs)
- [ ] Frontend 실행 확인 (http://localhost:3000)

### 매번 작업 시
- [ ] `git pull origin main` (최신 코드 받기)
- [ ] Docker 컨테이너 시작 (`docker-compose up -d`)
- [ ] Backend 서버 실행
- [ ] Frontend 서버 실행
- [ ] 작업 완료 후 `git add . && git commit && git push`

### 다른 맥 이동 시
- [ ] 현재 맥에서 `git push`
- [ ] `.env` 파일 내용 복사 (또는 AirDrop)
- [ ] 새 맥에서 `git pull`
- [ ] `.env` 파일 확인/생성
- [ ] Docker 컨테이너 시작
- [ ] 데이터베이스 복원 (필요 시)

---

## 📚 참고 문서

- [CLAUDE.md](../CLAUDE.md) - 전체 기술 문서
- [README.md](../README.md) - 프로젝트 개요
- [API_GUIDE.md](./API_GUIDE.md) - API 사용법
- [TRANSACTION_GUIDE.md](./TRANSACTION_GUIDE.md) - 실거래가 기능
- [WEBHOOK_SETUP_GUIDE.md](./WEBHOOK_SETUP_GUIDE.md) - Discord 브리핑 설정

---

## ❓ 자주 묻는 질문

### Q: Docker를 계속 실행 상태로 두면 문제가 없나요?
A: 네, 괜찮습니다. PostgreSQL과 Redis는 메모리를 많이 사용하지 않습니다 (약 200-300MB). 메모리가 부족할 때만 `docker-compose stop`으로 중지하세요.

### Q: 맥 슬립 모드에서도 스케줄러가 작동하나요?
A: 아니요. 맥이 슬립 모드에 들어가면 모든 프로세스가 중지됩니다. 슬립 해제 후 스케줄러가 자동으로 재개되지만, 12시간 이상 슬립 시 Beat가 종료될 수 있습니다. 스케줄러 페이지에서 "재활성화" 버튼으로 쉽게 재시작할 수 있습니다.

### Q: 집 맥과 맥북의 데이터베이스를 동기화해야 하나요?
A: 아니요, 필수는 아닙니다. 각 맥에서 독립적으로 단지를 추가하고 크롤링하는 것을 권장합니다. 데이터 공유가 꼭 필요한 경우에만 덤프/복원을 사용하세요.

### Q: .env 파일을 Git에 커밋하면 안 되나요?
A: 절대 안 됩니다. `.env` 파일에는 API Key, Webhook URL 등 민감한 정보가 포함되어 있습니다. `.gitignore`에 이미 추가되어 있으므로 커밋되지 않습니다.

### Q: docker-compose.yml에 api, celery_worker, frontend 서비스가 있는데 사용 안 하나요?
A: 네, 현재는 사용하지 않습니다. 이 서비스들은 프로덕션 배포용이었으나, 크롤러의 `headless=False` 제약으로 로컬 개발만 지원합니다. 로컬에서는 터미널에서 직접 실행하는 방식을 사용합니다.

---

**문제가 생기면:**
1. 에러 메시지를 자세히 읽기
2. `docker logs` 명령어로 로그 확인
3. [문제 해결](#문제-해결) 섹션 참고
4. GitHub Issues에 문제 등록
