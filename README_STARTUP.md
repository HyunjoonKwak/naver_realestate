# 네이버 부동산 로컬 개발 환경 시작 가이드

## ✅ 환경 설정 정리 완료

NAS 관련 설정이 모두 제거되고, **로컬 개발 전용**으로 통일되었습니다.

### 포트 설정 (확정)
- **PostgreSQL**: localhost:**5433** (Docker 컨테이너)
- **Redis**: localhost:**6380** (Docker 컨테이너)
- **FastAPI**: localhost:**8000**
- **Next.js**: localhost:**3000**

### 환경 파일
- **루트 `.env`**: 프로젝트 루트 환경변수 (로컬 개발용)
- **`backend/.env`**: Backend 환경변수 (로컬 개발용)
- **중복 제거**: `backend/backend/.env` 삭제됨

## 🚀 서비스 시작 방법

### 방법 1: 통합 스크립트 (권장) ⭐

**한 터미널에서 모든 서비스 시작:**
```bash
./start_all.sh
```

모든 서비스가 백그라운드로 실행되며, 로그는 `logs/` 디렉토리에 저장됩니다.

**로그 확인:**
```bash
# 모든 로그 실시간 모니터링
./logs_all.sh

# 개별 로그 확인
tail -f logs/backend.log
tail -f logs/worker.log
tail -f logs/beat.log
tail -f logs/frontend.log
```

**종료:**
```bash
./stop_all.sh
```

---

### 방법 2: 터미널 4개로 수동 실행

각 터미널에서 개별 실행 (디버깅 시 유용):

**터미널 1: Backend**
```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**터미널 2: Celery Worker**
```bash
cd backend
.venv/bin/celery -A app.core.celery_app worker --loglevel=info
```

**터미널 3: Celery Beat**
```bash
cd backend
.venv/bin/celery -A app.core.celery_app beat --scheduler redbeat.RedBeatScheduler --loglevel=info
```

**터미널 4: Frontend**
```bash
cd frontend
npm run dev
```

## 🔗 접속 주소

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **스케줄러 관리**: http://localhost:3000/scheduler

## 🛠️ 주요 개선사항

### 1. 환경변수 자동 로딩
- `python-dotenv` 패키지 추가
- `database.py`와 `celery_app.py`에서 자동으로 `.env` 로드
- 더 이상 환경변수 수동 설정 불필요

### 2. NAS 관련 설정 제거
- Docker Compose 주석에서 NAS 참조 제거
- 루트 `.env` 포트를 로컬용(5433, 6380)으로 변경
- 중복 환경 파일 삭제

### 3. 스케줄러 기능 추가
- **특정 단지 크롤링** 스케줄 지원
- **요일 다중 선택** 기능 (예: 월,수,금)
- 체크박스 방식 UI로 개선

## 📝 의존성 추가

`backend/requirements.txt`에 추가됨:
```
python-dotenv==1.1.1
```

설치:
```bash
cd backend
.venv/bin/pip install -r requirements.txt
```

## ⚠️ 주의사항

1. **Celery는 자동 리로드 미지원**
   - 코드 수정 시 Worker와 Beat를 수동으로 재시작해야 함

2. **환경변수 우선순위**
   - 시스템 환경변수 > `.env` 파일
   - `load_dotenv(override=True)`로 `.env` 우선 적용

3. **Docker 포트 충돌**
   - 기본 5432, 6379 포트를 사용 중이면 충돌 가능
   - 현재는 5433, 6380으로 회피

## 🐛 문제 해결

### Celery가 Redis 6379에 연결하려고 함
→ `backend/.env` 파일의 `REDIS_URL=redis://localhost:6380/0` 확인

### Backend API가 5432 포트에 연결하려고 함
→ `backend/.env` 파일의 `DATABASE_URL=postgresql://postgres:postgres@localhost:5433/naver_realestate` 확인

### python-dotenv 모듈 에러
→ `cd backend && .venv/bin/pip install python-dotenv`

## 🧪 테스트

테스트 스크립트들이 `tests/` 디렉토리에 정리되어 있습니다:

```bash
# 기본 API 테스트
./tests/test_api.sh

# 실거래가 API 테스트
./tests/test_transaction_api.sh

# Discord 브리핑 테스트
./tests/test_discord_briefing.sh
```

자세한 내용은 [tests/README.md](tests/README.md)를 참고하세요.

## 📚 추가 문서

- [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) - 프로젝트 구조
- [CLAUDE.md](CLAUDE.md) - AI 개발 가이드
- [tests/README.md](tests/README.md) - 테스트 가이드
