# 멀티 디바이스 개발 환경 설정 가이드

## 📱 개발 환경

- **외부**: MacBook (이동 중 개발)
- **집**: Mac Mini (메인 개발)
- **운영**: Synology NAS (24/7 운영)

---

## 🔄 작업 흐름

```
MacBook (외부)
    ↓ git push
GitHub (중앙 저장소)
    ↓ git pull
Mac Mini (집)
    ↓ 개발 완료
GitHub
    ↓ 배포
Synology NAS (운영)
```

---

## 🚀 초기 설정 (Mac Mini)

### 1. Git 저장소 클론

```bash
# 1. 프로젝트 폴더로 이동
cd ~/code_work  # 또는 원하는 경로

# 2. 저장소 클론
git clone https://github.com/HyunjoonKwak/naver_realestate.git
cd naver_realestate

# 3. 브랜치 확인
git branch -a
```

### 2. Docker 설치 (Mac Mini)

```bash
# Homebrew로 Docker Desktop 설치
brew install --cask docker

# Docker Desktop 실행
open /Applications/Docker.app

# 컨테이너 시작
docker-compose up -d

# 상태 확인
docker-compose ps
```

### 3. Python 환경 설정

```bash
# Python 3.11+ 설치 (없다면)
brew install python@3.11

# 가상환경 생성
cd backend
python3.11 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# Playwright 설치
playwright install chromium
playwright install-deps
```

### 4. Node.js 환경 설정

```bash
# Node.js 18+ 설치 (없다면)
brew install node@18

# 프론트엔드 의존성 설치
cd ../frontend
npm install
```

### 5. 데이터베이스 초기화

```bash
# 프로젝트 루트로
cd ..

# DB 초기화
backend/venv/bin/python reset_db.py

# (선택) 초기 데이터 크롤링
backend/venv/bin/python advanced_crawler.py
```

---

## 💻 일일 작업 흐름

### 🏠 집에서 작업 시작 (Mac Mini)

```bash
# 1. 프로젝트 폴더로 이동
cd ~/code_work/naver_realestate

# 2. 최신 코드 받기
git pull origin main

# 3. 의존성 업데이트 (필요시)
cd backend
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install

# 4. Docker 컨테이너 시작
cd ..
docker-compose up -d

# 5. 개발 서버 실행
# 터미널 1: API
cd backend
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 터미널 2: Frontend
cd frontend
npm run dev
```

### 📤 작업 완료 후 (Mac Mini → GitHub)

```bash
# 1. 변경사항 확인
git status
git diff

# 2. 스테이징
git add .

# 3. 커밋
git commit -m "feat: 작업 내용 설명

- 추가한 기능
- 수정한 내용
- 버그 수정 등

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 4. 푸시
git push origin main

# 5. 서버 종료 (선택)
# Ctrl+C로 API, Frontend 종료
docker-compose stop  # Docker 컨테이너 중지
```

### 🚗 외부에서 작업 시작 (MacBook)

```bash
# 1. 프로젝트 폴더로 이동
cd ~/code_work/naver_realestate

# 2. 최신 코드 받기
git pull origin main

# 3. 의존성 확인 (이미 설치되어 있음)
# 새로운 패키지 추가되었다면:
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 4. Docker 시작
docker-compose up -d

# 5. 개발 서버 실행
# (Mac Mini와 동일)
```

### 📤 작업 완료 후 (MacBook → GitHub)

```bash
# Mac Mini와 동일한 프로세스
git add .
git commit -m "작업 내용"
git push origin main
```

---

## ⚠️ 주의사항

### 1. 항상 Pull 먼저!

```bash
# ❌ 잘못된 방법
git add .
git commit -m "작업"
git push  # 충돌 발생 가능!

# ✅ 올바른 방법
git pull origin main  # 먼저 최신 코드 받기
git add .
git commit -m "작업"
git push origin main
```

### 2. 충돌 해결

```bash
# Pull 시 충돌 발생한 경우
git pull origin main
# CONFLICT 메시지 확인

# 충돌 파일 수정
code conflicted_file.py  # 또는 다른 에디터

# 충돌 표시 제거 후
git add conflicted_file.py
git commit -m "fix: resolve merge conflict"
git push origin main
```

### 3. .gitignore 확인

**절대 커밋하면 안 되는 것들:**
- ✅ `.env` (환경변수)
- ✅ `venv/` (Python 가상환경)
- ✅ `node_modules/` (Node 의존성)
- ✅ `.next/` (Next.js 빌드)
- ✅ `*.pyc` (컴파일된 Python)
- ✅ `archive/` (테스트 파일)
- ✅ `.claude/` (AI 도구 설정)

현재 `.gitignore`에 모두 포함되어 있음 ✅

---

## 🔧 환경 차이 관리

### 1. 환경변수 (.env)

**각 컴퓨터마다 다를 수 있는 설정:**

```bash
# MacBook .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/naver_realestate
REDIS_URL=redis://localhost:6379/0
NEXT_PUBLIC_API_URL=http://localhost:8000

# Mac Mini .env (동일하게 유지)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/naver_realestate
REDIS_URL=redis://localhost:6379/0
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**`.env`는 Git에 포함되지 않으므로 각 컴퓨터에서 직접 생성**

### 2. .env.example 사용

```bash
# 프로젝트에 .env.example 파일 추가 (템플릿)
cat > .env.example << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/naver_realestate

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Git에 커밋
git add .env.example
git commit -m "docs: add .env.example template"
git push

# 새 컴퓨터에서 사용
cp .env.example .env
```

---

## 🗂️ 데이터베이스 동기화

### 문제: 각 컴퓨터마다 다른 DB 데이터

#### 옵션 1: 매번 초기화 (개발 중 권장)

```bash
# 새 컴퓨터에서 작업 시작 시
backend/venv/bin/python reset_db.py
backend/venv/bin/python advanced_crawler.py
```

#### 옵션 2: DB 백업/복원 (데이터 유지)

**Mac Mini에서 백업:**
```bash
# PostgreSQL 데이터 백업
docker exec naver_realestate_db pg_dump -U postgres naver_realestate > db_backup.sql

# Git에 커밋 (작은 데이터만)
git add db_backup.sql
git commit -m "chore: backup database"
git push
```

**MacBook에서 복원:**
```bash
# 최신 코드 받기
git pull origin main

# DB 복원
docker exec -i naver_realestate_db psql -U postgres naver_realestate < db_backup.sql
```

#### 옵션 3: 외부 DB 사용 (동기화 자동)

```bash
# 둘 다 같은 외부 DB 사용
# .env
DATABASE_URL=postgres://user:pass@elephantsql.com/db

# MacBook, Mac Mini 모두 같은 DB 접속 → 자동 동기화!
```

---

## 🌿 브랜치 전략 (고급)

### 혼자 개발 시 (현재)

```bash
# main 브랜치만 사용
git checkout main
git pull
# 작업
git add .
git commit -m "작업 내용"
git push
```

### 기능별 브랜치 (권장)

```bash
# 새 기능 개발 시
git checkout -b feature/new-dashboard
# 작업
git add .
git commit -m "feat: add new dashboard"
git push origin feature/new-dashboard

# GitHub에서 Pull Request 생성
# main에 병합

# 다른 컴퓨터에서
git checkout main
git pull  # 최신 main 받기
```

---

## 🔍 유용한 Git 명령어

### 상태 확인

```bash
# 현재 변경사항 확인
git status

# 변경 내용 확인
git diff

# 커밋 히스토리
git log --oneline -10

# 원격 저장소 확인
git remote -v
```

### 변경사항 취소

```bash
# 스테이징 취소
git restore --staged <file>

# 변경사항 취소 (주의!)
git restore <file>

# 최근 커밋 취소 (주의!)
git reset --soft HEAD~1  # 커밋만 취소, 변경사항 유지
git reset --hard HEAD~1  # 커밋 + 변경사항 모두 취소
```

### 임시 저장 (stash)

```bash
# 현재 작업 임시 저장
git stash

# 다른 작업...
git pull origin main

# 임시 저장한 작업 복구
git stash pop
```

---

## 📋 체크리스트

### 🆕 새 컴퓨터 초기 설정

- [ ] Git 설치 및 설정
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your@email.com"
  ```
- [ ] Docker Desktop 설치
- [ ] Python 3.11+ 설치
- [ ] Node.js 18+ 설치
- [ ] 저장소 클론
- [ ] Python 가상환경 생성 및 패키지 설치
- [ ] Node.js 의존성 설치
- [ ] .env 파일 생성
- [ ] Docker 컨테이너 시작
- [ ] DB 초기화

### 📅 매일 작업 시작

- [ ] `git pull origin main`
- [ ] 의존성 업데이트 확인 (requirements.txt, package.json)
- [ ] Docker 컨테이너 시작
- [ ] 개발 서버 실행

### 📅 매일 작업 종료

- [ ] `git status` (변경사항 확인)
- [ ] `git add .`
- [ ] `git commit -m "작업 내용"`
- [ ] `git push origin main`
- [ ] 서버 종료 (선택)

---

## 🚨 문제 해결

### 문제 1: "Your branch is behind" 에러

```bash
# 원격 저장소가 더 최신일 때
git pull origin main

# 충돌 없으면 자동 병합
# 충돌 있으면 수동 해결 후
git add .
git commit -m "fix: resolve conflicts"
git push
```

### 문제 2: "Please commit or stash" 에러

```bash
# 현재 작업 임시 저장
git stash

# 최신 코드 받기
git pull origin main

# 작업 복구
git stash pop
```

### 문제 3: 의존성 문제

```bash
# requirements.txt 업데이트됨
cd backend
source venv/bin/activate
pip install -r requirements.txt

# package.json 업데이트됨
cd frontend
npm install
```

### 문제 4: Docker 포트 충돌

```bash
# 기존 컨테이너 종료
docker-compose down

# 다시 시작
docker-compose up -d
```

---

## 💡 추천 워크플로우

### 시나리오 1: 집 → 외부

```bash
# 집 (Mac Mini)에서 작업 완료
git add .
git commit -m "feat: add new feature"
git push origin main

# 외부 (MacBook)에서 이어서 작업
cd ~/code_work/naver_realestate
git pull origin main
docker-compose up -d
# 개발 계속...
```

### 시나리오 2: 외부 → 집

```bash
# 외부 (MacBook)에서 작업 완료
git add .
git commit -m "fix: bug fix"
git push origin main

# 집 (Mac Mini)에서 이어서 작업
cd ~/code_work/naver_realestate
git pull origin main
docker-compose up -d
# 개발 계속...
```

### 시나리오 3: 긴급 수정

```bash
# MacBook에서 긴급 수정
git pull origin main
# 수정...
git add .
git commit -m "hotfix: critical bug"
git push origin main

# Mac Mini에서 자동으로 pull 받기 (다음 작업 시)
git pull origin main
```

---

## 🔐 보안 팁

### SSH 키 사용 (추천)

```bash
# SSH 키 생성 (각 컴퓨터에서)
ssh-keygen -t ed25519 -C "your@email.com"

# 공개키 복사
cat ~/.ssh/id_ed25519.pub

# GitHub → Settings → SSH Keys → Add
# 붙여넣기

# Git 리모트 변경
git remote set-url origin git@github.com:username/naver_realestate.git

# 이후 push/pull 시 비밀번호 입력 불필요!
```

---

## 📚 추가 리소스

- [Git 공식 문서](https://git-scm.com/doc)
- [Pro Git 책 (무료)](https://git-scm.com/book/ko/v2)
- [GitHub Desktop](https://desktop.github.com/) - GUI 도구

---

## ✅ 요약

**핵심 원칙:**
1. 항상 `git pull` 먼저
2. 작업 완료 후 `git push`
3. `.env`는 각 컴퓨터에서 직접 생성
4. `venv/`, `node_modules/`는 각 컴퓨터에서 직접 설치

**일일 루틴:**
```bash
# 시작
git pull origin main
docker-compose up -d

# 작업...

# 종료
git add .
git commit -m "작업 내용"
git push origin main
```

이제 MacBook과 Mac Mini를 오가며 자유롭게 개발하세요! 🚀
