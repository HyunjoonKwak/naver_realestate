# 개발 환경 설정 가이드

## 📋 목차
1. [옵션 A: Docker 사용 (추천)](#옵션-a-docker-사용-추천)
2. [옵션 B: 로컬 환경 직접 설정](#옵션-b-로컬-환경-직접-설정)
3. [Docker 기본 사용법](#docker-기본-사용법)

---

## 🤔 어떤 방법을 선택해야 할까요?

### Docker 사용 (옵션 A) - 추천 ✅
**장점:**
- ✅ PostgreSQL, Redis를 클릭 한 번으로 설치
- ✅ 모든 팀원이 동일한 환경 사용
- ✅ Mac을 포맷해도 프로젝트만 다시 받으면 즉시 실행
- ✅ 다른 프로젝트와 충돌 없음
- ✅ 제가 모든 설정을 자동화해드립니다

**단점:**
- ❌ Docker Desktop 설치 필요 (약 500MB)
- ❌ 처음에 개념 이해 필요 (하지만 어렵지 않습니다!)

### 로컬 직접 설정 (옵션 B)
**장점:**
- ✅ Docker 없이 바로 시작
- ✅ 각 도구를 직접 제어

**단점:**
- ❌ PostgreSQL, Redis 직접 설치 필요
- ❌ 설정이 복잡함
- ❌ Mac 환경에 따라 문제 발생 가능
- ❌ 다른 프로젝트와 충돌 가능

---

## 옵션 A: Docker 사용 (추천)

> **Docker를 처음 사용하시나요?** 걱정 마세요! 제가 단계별로 안내해드리겠습니다.

### 1단계: Docker Desktop 설치

#### Docker란?
- 가상의 컴퓨터를 만들어서 그 안에 PostgreSQL, Redis 등을 설치하는 도구
- 실제 컴퓨터에는 아무것도 설치하지 않아도 됨
- 필요 없으면 클릭 한 번으로 삭제 가능

#### 설치 방법
```bash
# 1. Docker Desktop 다운로드 (Mac용)
# 브라우저에서 방문: https://www.docker.com/products/docker-desktop

# 2. 또는 Homebrew로 설치 (추천)
brew install --cask docker

# 3. Docker Desktop 앱 실행
# Applications 폴더에서 Docker 아이콘 클릭

# 4. 설치 확인
docker --version
# 출력 예: Docker version 24.0.0

docker-compose --version
# 출력 예: Docker Compose version v2.20.0
```

### 2단계: 프로젝트에서 Docker 사용하기

#### docker-compose.yml 파일이란?
- "이런 프로그램들을 설치해줘"라고 적어놓은 설정 파일
- 우리 프로젝트에 필요한 것들을 미리 정의

#### 사용 방법 (정말 간단합니다!)

```bash
# 프로젝트 폴더로 이동
cd /Users/specialrisk_mac/code_work/naver_realestate

# 명령어 1: 모든 것 시작하기
docker-compose up -d

# 무슨 일이 일어나나요?
# - PostgreSQL 데이터베이스가 자동으로 설치되고 시작됨
# - Redis가 자동으로 설치되고 시작됨
# - 백그라운드에서 조용히 실행됨 (-d 옵션)

# 명령어 2: 잘 실행되고 있는지 확인
docker-compose ps

# 출력 예:
# NAME                STATUS
# postgres            Up 2 minutes
# redis               Up 2 minutes

# 명령어 3: 중지하기 (컴퓨터 끌 때)
docker-compose stop

# 명령어 4: 다시 시작하기
docker-compose start

# 명령어 5: 완전히 삭제하기 (데이터도 모두 삭제)
docker-compose down -v
```

### 3단계: Docker 기본 명령어 치트시트

```bash
# === 자주 쓰는 명령어 ===

# 1. 시작 (처음 또는 오랜만에 개발할 때)
docker-compose up -d

# 2. 로그 보기 (에러 확인할 때)
docker-compose logs

# 3. 특정 서비스 로그만 보기
docker-compose logs postgres
docker-compose logs redis

# 4. 실시간 로그 보기 (Ctrl+C로 종료)
docker-compose logs -f

# 5. 중지 (컴퓨터 끌 때)
docker-compose stop

# 6. 재시작 (뭔가 이상할 때)
docker-compose restart

# 7. 상태 확인
docker-compose ps

# 8. 데이터베이스 접속 (확인용)
docker-compose exec postgres psql -U postgres -d naver_realestate

# 9. 완전 삭제 후 재시작 (문제 발생 시)
docker-compose down -v
docker-compose up -d
```

### 4단계: 문제 해결

#### Q1. "docker: command not found" 에러가 나요
```bash
# Docker Desktop이 실행 중인지 확인
# 화면 상단 메뉴바에 Docker 고래 아이콘이 있어야 함

# Docker Desktop 재시작
# Applications > Docker 더블클릭
```

#### Q2. "port already in use" 에러가 나요
```bash
# 이미 PostgreSQL이나 Redis가 실행 중일 수 있음
# 1. 실행 중인 프로세스 확인
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# 2. 기존 프로세스 종료 또는
# 3. docker-compose.yml에서 포트 변경
```

#### Q3. 데이터가 사라졌어요
```bash
# docker-compose down -v 명령어는 데이터를 삭제합니다
# 데이터를 유지하려면:
docker-compose down      # -v 옵션 없이 사용
docker-compose stop      # 또는 stop 사용
```

### 5단계: 우리 프로젝트의 docker-compose.yml 설명

```yaml
# 파일 위치: /Users/specialrisk_mac/code_work/naver_realestate/docker-compose.yml

services:
  # PostgreSQL 데이터베이스
  postgres:
    image: postgres:15-alpine          # PostgreSQL 15 버전 사용
    container_name: naver_realestate_db
    environment:
      POSTGRES_USER: postgres          # 사용자명
      POSTGRES_PASSWORD: postgres      # 비밀번호 (개발용)
      POSTGRES_DB: naver_realestate    # 데이터베이스 이름
    ports:
      - "5432:5432"                    # 외부:내부 포트
    volumes:
      - postgres_data:/var/lib/postgresql/data  # 데이터 저장 위치

  # Redis (캐시 및 Celery용)
  redis:
    image: redis:7-alpine              # Redis 7 버전 사용
    container_name: naver_realestate_redis
    ports:
      - "6379:6379"                    # 외부:내부 포트
    volumes:
      - redis_data:/data               # 데이터 저장 위치

volumes:
  postgres_data:    # PostgreSQL 데이터가 저장되는 볼륨
  redis_data:       # Redis 데이터가 저장되는 볼륨
```

### 6단계: Python 애플리케이션 연결

```python
# backend/.env 파일
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/naver_realestate
REDIS_URL=redis://localhost:6379/0

# Python 코드에서 사용
from sqlalchemy import create_engine
import os

engine = create_engine(os.getenv("DATABASE_URL"))
```

---

## 옵션 B: 로컬 환경 직접 설정

> Docker 없이 직접 설치하는 방법입니다.

### 1단계: PostgreSQL 설치

```bash
# Homebrew로 PostgreSQL 설치
brew install postgresql@15

# PostgreSQL 시작
brew services start postgresql@15

# 데이터베이스 생성
createdb naver_realestate

# 접속 테스트
psql naver_realestate
```

### 2단계: Redis 설치

```bash
# Homebrew로 Redis 설치
brew install redis

# Redis 시작
brew services start redis

# 접속 테스트
redis-cli ping
# 출력: PONG
```

### 3단계: Python 가상환경 설정

```bash
# 프로젝트 폴더로 이동
cd /Users/specialrisk_mac/code_work/naver_realestate

# 가상환경 생성
python3.11 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 패키지 설치 (requirements.txt 생성 후)
pip install -r backend/requirements.txt
```

### 4단계: 환경변수 설정

```bash
# backend/.env 파일 생성
DATABASE_URL=postgresql://localhost:5432/naver_realestate
REDIS_URL=redis://localhost:6379/0
```

### 로컬 설정의 단점
- PostgreSQL과 Redis가 항상 백그라운드에서 실행됨 (메모리 사용)
- 다른 프로젝트에서도 같은 PostgreSQL을 사용하면 충돌 가능
- 삭제하려면 각각 수동으로 제거해야 함

---

## Docker 기본 사용법

### Docker의 핵심 개념 3가지

#### 1. Image (이미지)
- 프로그램의 설치 파일 같은 것
- 예: `postgres:15-alpine`은 PostgreSQL 15 설치 파일

#### 2. Container (컨테이너)
- Image를 실행한 것
- 예: postgres 이미지를 실행하면 postgres 컨테이너가 생성됨
- 컴퓨터 안의 작은 가상 컴퓨터

#### 3. Volume (볼륨)
- 데이터를 저장하는 공간
- 컨테이너를 삭제해도 볼륨은 남아있음

### 시각화

```
[당신의 Mac]
  ├─ Docker Desktop (실행 중)
  │
  ├─ [postgres 컨테이너] ← postgres:15 이미지로 생성
  │   └─ PostgreSQL 실행 중
  │   └─ 포트 5432로 접속 가능
  │   └─ 데이터는 postgres_data 볼륨에 저장
  │
  └─ [redis 컨테이너] ← redis:7 이미지로 생성
      └─ Redis 실행 중
      └─ 포트 6379로 접속 가능
      └─ 데이터는 redis_data 볼륨에 저장
```

---

## 💡 추천 방법

### 초보자에게 추천: Docker 사용

**이유:**
1. 한 번만 설정하면 계속 사용 가능
2. 문제 발생 시 `docker-compose down -v && docker-compose up -d` 한 줄로 해결
3. 나중에 팀 프로젝트나 배포할 때도 똑같이 사용
4. 제가 모든 설정 파일을 만들어드립니다

**필요한 것:**
- Docker Desktop 설치 (10분)
- 기본 명령어 4개만 외우기
  - `docker-compose up -d` (시작)
  - `docker-compose ps` (확인)
  - `docker-compose logs` (로그 보기)
  - `docker-compose stop` (중지)

---

## 🚀 다음 단계

### Docker 사용 시
1. Docker Desktop 설치
2. 제가 `docker-compose.yml` 파일 생성
3. `docker-compose up -d` 실행
4. 개발 시작!

### 로컬 직접 설정 시
1. PostgreSQL 설치
2. Redis 설치
3. Python 가상환경 설정
4. 개발 시작!

---

## ❓ 자주 묻는 질문

### Q: Docker가 어려워 보이는데요?
A: 처음에만 낯설 뿐, 실제로는 4개 명령어만 사용합니다. 제가 모든 설정을 해드리기 때문에 걱정하지 않으셔도 됩니다!

### Q: Docker 없이 개발해도 되나요?
A: 네, 가능합니다. 하지만 PostgreSQL과 Redis를 직접 설치하고 관리해야 합니다.

### Q: Docker를 배워두면 다른 곳에서도 쓸 수 있나요?
A: 네! 거의 모든 현대적인 개발 프로젝트에서 Docker를 사용합니다. 한 번 배워두면 평생 사용합니다.

### Q: Docker Desktop이 무거운가요?
A: 실행 중일 때 메모리를 약 500MB-1GB 사용합니다. 개발하지 않을 때는 종료하면 됩니다.

### Q: 문제가 생기면 어떻게 하나요?
A: 대부분의 문제는 `docker-compose restart` 또는 `docker-compose down -v && docker-compose up -d`로 해결됩니다. 제가 도와드리겠습니다!

---

## 📚 더 배우고 싶다면

### Docker 공식 튜토리얼 (한글)
- https://docs.docker.com/get-started/

### Docker Compose 문서
- https://docs.docker.com/compose/

### 유용한 Docker 명령어 모음
```bash
# 모든 컨테이너 확인
docker ps -a

# 모든 이미지 확인
docker images

# 컨테이너 로그 보기
docker logs <container_name>

# 컨테이너 안으로 들어가기
docker exec -it <container_name> bash

# 사용하지 않는 이미지/컨테이너 삭제 (공간 확보)
docker system prune -a
```
