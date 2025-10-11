# 프로젝트 구조

네이버 부동산 아파트 단지 크롤링 및 가격 추적 시스템의 전체 디렉토리 구조와 파일 역할을 설명합니다.

## 📋 목차
1. [루트 디렉토리](#루트-디렉토리)
2. [Backend 구조](#backend-구조)
3. [Frontend 구조](#frontend-구조)
4. [문서 구조](#문서-구조)
5. [개발 워크플로우](#개발-워크플로우)
6. [기술 스택 위치](#기술-스택-위치)

---

## 루트 디렉토리

```
naver_realestate/
├── backend/                   # FastAPI 백엔드 서버
├── frontend/                  # Next.js 14 프론트엔드
├── docs/                      # 프로젝트 문서
├── docker-compose.yml         # Docker 컨테이너 설정 (PostgreSQL, Redis)
├── .gitignore                 # Git 제외 파일 설정
├── README.md                  # 프로젝트 메인 문서
├── CLAUDE.md                  # AI 어시스턴트용 기술 가이드
├── PROJECT_STRUCTURE.md       # 이 파일
│
├── migrate_db.py              # DB 마이그레이션 (Foreign Keys 추가)
├── reset_db.py                # DB 초기화 (레거시)
├── advanced_crawler.py        # 독립 실행형 크롤러 (레거시)
├── check_data.py              # DB 데이터 확인 도구
│
├── start_all.sh               # 모든 서비스 시작 스크립트
├── test_api.sh                # API 엔드포인트 테스트
├── test_transaction_api.sh    # 실거래가 API 테스트
├── test_discord_briefing.sh   # Discord 브리핑 테스트
└── check_schedules.sh         # Celery Beat 스케줄 확인
```

### 주요 스크립트 설명

**데이터베이스:**
- `migrate_db.py` - Foreign Keys 포함 테이블 생성 (권장)
- `reset_db.py` - 레거시 DB 초기화

**테스트:**
- `test_api.sh` - 기본 API 엔드포인트 테스트
- `test_transaction_api.sh` - 실거래가 API 기능 테스트
- `test_discord_briefing.sh` - Discord Webhook 브리핑 전송 테스트
- `check_schedules.sh` - Celery Beat 스케줄 상태 확인

**운영:**
- `start_all.sh` - Docker + Backend + Frontend + Celery 모두 시작

---

## Backend 구조

```
backend/
├── app/
│   ├── main.py                      # FastAPI 앱 진입점 (라우터 등록)
│   │
│   ├── api/                         # REST API 라우터 (8개)
│   │   ├── complexes.py             # 단지 CRUD, 통계, 매물/실거래 조회
│   │   ├── articles.py              # 매물 조회, 필터링, 가격 변동 추적
│   │   ├── transactions.py          # 실거래가 조회, 평형별 통계
│   │   ├── scraper.py               # 크롤링 트리거 (crawl, refresh)
│   │   ├── scheduler.py             # 스케줄러 관리 (RedBeat, 동적 스케줄링)
│   │   ├── briefing.py              # Discord 브리핑 트리거
│   │   ├── auth.py                  # 회원가입, 로그인, JWT 인증
│   │   └── favorites.py             # 관심 단지 관리
│   │
│   ├── models/                      # SQLAlchemy ORM 모델
│   │   └── complex.py               # 모든 DB 테이블 정의:
│   │                                  - Complex (단지)
│   │                                  - Article (매물)
│   │                                  - Transaction (실거래)
│   │                                  - ArticleSnapshot (매물 스냅샷)
│   │                                  - ArticleChange (변동사항)
│   │                                  - User (사용자)
│   │                                  - FavoriteComplex (관심 단지)
│   │                                  - CrawlJob (크롤링 작업 이력)
│   │
│   ├── schemas/                     # Pydantic 스키마 (요청/응답 검증)
│   │   ├── complex.py               # 단지, 매물, 실거래 스키마
│   │   ├── user.py                  # 사용자, 로그인 스키마
│   │   └── favorite.py              # 관심 단지 스키마
│   │
│   ├── services/                    # 비즈니스 로직 서비스 (8개)
│   │   ├── crawler_service.py       # Playwright 기반 네이버 크롤러
│   │   ├── article_tracker.py       # 매물 변동사항 추적 (스냅샷 비교)
│   │   ├── molit_service.py         # 국토부 실거래가 API 연동
│   │   ├── transaction_service.py   # 실거래가 저장 및 통계 처리
│   │   ├── location_parser.py       # 법정동 코드 파싱 (20,278개)
│   │   ├── briefing_service.py      # Discord 브리핑 메시지 생성
│   │   └── address_service.py       # 주소 정규화 및 매칭
│   │
│   ├── tasks/                       # Celery 백그라운드 작업
│   │   ├── scheduler.py             # 스케줄 크롤링 (crawl_all_complexes)
│   │   └── briefing_tasks.py        # 브리핑 전송 (weekly_briefing)
│   │
│   ├── core/                        # 핵심 설정 및 유틸리티
│   │   ├── database.py              # SQLAlchemy 엔진/세션
│   │   ├── celery_app.py            # Celery + RedBeat 설정
│   │   ├── security.py              # JWT 토큰, 비밀번호 해싱
│   │   ├── dependencies.py          # FastAPI 의존성 (인증)
│   │   └── schedule_manager.py      # 스케줄 관리 (JSON 파일 동기화)
│   │
│   ├── config/                      # 설정 파일
│   │   └── schedules.json           # RedBeat 스케줄 백업/복원용
│   │
│   ├── data/                        # 정적 데이터
│   │   └── dong_code_active.txt     # 전국 법정동 코드 (20,278개)
│   │
│   └── crawler/                     # 레거시 크롤러 (사용 안 함)
│       ├── naver_crawler.py
│       └── naver_land_crawler.py
│
├── .venv/                           # Python 가상환경 (Python 3.13)
├── requirements.txt                 # Python 의존성
├── run_celery_worker.sh             # Celery Worker 시작 스크립트
└── run_celery_beat.sh               # Celery Beat 시작 스크립트
```

### Backend 주요 모듈 설명

**API 라우터 (`app/api/`):**
- **complexes.py** - 단지 등록/조회/삭제, 통계, 연관 매물/실거래 조회
- **scraper.py** - 크롤링 트리거 (단일/전체), 새로고침 (변동사항 추적)
- **scheduler.py** - 스케줄 CRUD, 작업 이력, Beat 재시작 API
- **transactions.py** - 실거래가 수동 조회, 평형별 통계, 가격 추이

**Services (`app/services/`):**
- **crawler_service.py** - Playwright로 네이버 크롤링 (`headless=False`)
- **article_tracker.py** - 스냅샷 생성 및 변동사항 감지 (NEW/REMOVED/PRICE_UP/DOWN)
- **molit_service.py** - 국토부 실거래가 XML API 호출 및 파싱
- **location_parser.py** - 주소 → 법정동 코드 자동 매칭

**Tasks (`app/tasks/`):**
- **scheduler.py** - Celery Beat에서 실행되는 스케줄 크롤링 작업
- **briefing_tasks.py** - Discord Webhook으로 브리핑 전송

**Core (`app/core/`):**
- **celery_app.py** - Celery + RedBeat 설정 (Redis 기반 동적 스케줄링)
- **security.py** - JWT 생성/검증, bcrypt 비밀번호 해싱
- **schedule_manager.py** - RedBeat 스케줄 ↔ JSON 파일 동기화

---

## Frontend 구조

```
frontend/
├── src/
│   ├── app/                         # Next.js 14 App Router
│   │   ├── layout.tsx               # 루트 레이아웃 + 네비게이션 바
│   │   ├── page.tsx                 # 대시보드 (홈) - 단지 카드 그리드
│   │   │
│   │   ├── complexes/               # 단지 관련 페이지
│   │   │   ├── page.tsx             # 단지 목록 (검색, 정렬)
│   │   │   ├── new/
│   │   │   │   └── page.tsx         # 단지 추가 (네이버 URL 입력)
│   │   │   └── [id]/
│   │   │       └── page.tsx         # 단지 상세:
│   │   │                              - 매물 리스트 (필터링, 정렬)
│   │   │                              - 면적별 가격 카드
│   │   │                              - 실거래가 요약 + 추이 차트
│   │   │                              - 변동사항 요약
│   │   │
│   │   ├── scheduler/               # 스케줄러 관리
│   │   │   └── page.tsx             # 스케줄 CRUD, 작업 이력, Beat 재시작
│   │   │
│   │   ├── transactions/            # 실거래가 페이지 (레거시)
│   │   │   └── page.tsx
│   │   │
│   │   └── articles/                # 매물 페이지 (레거시)
│   │       └── page.tsx
│   │
│   ├── components/                  # 재사용 컴포넌트
│   │   └── PriceTrendChart.tsx      # Chart.js 실거래가 추이 차트
│   │
│   ├── lib/                         # 유틸리티
│   │   └── api.ts                   # Axios API 클라이언트 (백엔드 호출)
│   │
│   └── types/                       # TypeScript 타입 정의
│       └── index.ts                 # Complex, Article, Transaction 등
│
├── public/                          # 정적 파일
├── package.json                     # Node 의존성
├── tsconfig.json                    # TypeScript 설정
├── tailwind.config.ts               # Tailwind CSS 설정
└── next.config.js                   # Next.js 설정
```

### Frontend 주요 페이지 설명

**단지 상세 페이지 (`complexes/[id]/page.tsx`):**
- **매물 탭** - 전용면적별 필터링, 가격 순 정렬, 중개사 정보
- **실거래 탭** - 평형별 통계 카드, 가격 추이 차트 (Chart.js), 최근 거래 내역
- **변동사항** - NEW/REMOVED/PRICE_UP/PRICE_DOWN 요약

**스케줄러 페이지 (`scheduler/page.tsx`):**
- 현재 활성 스케줄 조회/생성/수정/삭제
- 크롤링 작업 이력 (성공/실패, 소요시간, 수집 매물 수)
- Celery Beat 상태 확인 및 재시작 버튼

**컴포넌트 (`components/`):**
- **PriceTrendChart.tsx** - 실거래가 월별 추이 (평균/최고/최저가 라인 차트)

---

## 문서 구조

```
docs/
├── SETUP_GUIDE.md                   # 개발 환경 설정 (맥/맥북 양쪽)
├── API_GUIDE.md                     # REST API 전체 엔드포인트 가이드
├── TRANSACTION_GUIDE.md             # 실거래가 기능 사용법 (MOLIT API)
├── DYNAMIC_SCHEDULING.md            # RedBeat 스케줄러 상세 가이드
├── DISCORD_BRIEFING_GUIDE.md        # Discord 브리핑 설정 및 사용법
├── WEBHOOK_SETUP_GUIDE.md           # Discord Webhook 설정 가이드
├── SCHEDULER_TROUBLESHOOTING.md     # 스케줄러 문제 해결
├── WEEKLY_BRIEFING_FEATURE.md       # 주간 브리핑 기능 설계
├── ARTICLE_CHANGE_TRACKING_UX.md    # 매물 변동 추적 UX 설계
│
└── archive/                         # 아카이브된 문서 (7개)
    ├── README.md                    # 아카이브 사유 설명
    ├── LAPTOP_SETUP.md              # (통합됨 → SETUP_GUIDE.md)
    ├── DEPLOYMENT_GUIDE.md          # (헤드리스 서버 불가)
    ├── PROJECT_OVERVIEW.md          # (초기 기획 문서)
    └── ...
```

### 문서 카테고리

**필수 설정:**
- `SETUP_GUIDE.md` - 처음 시작하는 개발자용 환경 설정
- `WEBHOOK_SETUP_GUIDE.md` - Discord 브리핑 설정

**기능 가이드:**
- `API_GUIDE.md` - 모든 API 엔드포인트 상세 설명
- `TRANSACTION_GUIDE.md` - 실거래가 API Key 발급 및 사용법
- `DYNAMIC_SCHEDULING.md` - 스케줄 생성/관리 상세 가이드
- `DISCORD_BRIEFING_GUIDE.md` - 브리핑 커스터마이징

**트러블슈팅:**
- `SCHEDULER_TROUBLESHOOTING.md` - Beat 재시작, TTL 문제 해결

**설계 문서:**
- `WEEKLY_BRIEFING_FEATURE.md` - 브리핑 기능 설계
- `ARTICLE_CHANGE_TRACKING_UX.md` - 변동사항 추적 UX

---

## 개발 워크플로우

### 1. 초기 환경 설정

```bash
# 1. Docker 컨테이너 시작 (PostgreSQL + Redis)
docker-compose up -d

# 2. Backend 가상환경 및 의존성 설치
cd backend
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium

# 3. Frontend 의존성 설치
cd ../frontend
npm install

# 4. 데이터베이스 마이그레이션
cd ../backend
.venv/bin/python migrate_db.py

# 5. 환경변수 설정 (backend/.env)
# DATABASE_URL, REDIS_URL, MOLIT_API_KEY, DISCORD_WEBHOOK_URL
```

### 2. 개발 서버 실행

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

**터미널 3: Celery Worker (백그라운드 크롤링)**
```bash
cd backend
./run_celery_worker.sh
```

**터미널 4: Celery Beat (자동 스케줄링)**
```bash
cd backend
./run_celery_beat.sh
```

### 3. 데이터 흐름

```
[네이버 부동산]
      ↓ Playwright 크롤링 (headless=False)
[crawler_service.py]
      ↓ SQLAlchemy ORM
[PostgreSQL DB]
      ↓ FastAPI 라우터
[REST API :8000/api/*]
      ↓ Axios
[Next.js Frontend :3000]
      ↓
[사용자 브라우저]
```

**스케줄 크롤링 흐름:**
```
[Celery Beat] → [RedBeat (Redis)] → [Celery Worker] → [crawler_service.py]
                      ↓
            [schedules.json 백업]
```

**브리핑 흐름:**
```
[scheduled crawl] → [article_tracker] → [변동사항 감지] → [Discord Webhook]
```

### 4. 새로운 기능 추가

**API 엔드포인트 추가:**
1. `backend/app/models/complex.py` - DB 모델 수정
2. `backend/app/schemas/complex.py` - Pydantic 스키마 추가
3. `backend/app/api/*.py` - 라우터에 엔드포인트 추가
4. `backend/app/main.py` - 라우터 등록 (필요 시)
5. `frontend/src/lib/api.ts` - API 함수 추가
6. `frontend/src/types/index.ts` - TypeScript 타입 추가

**새 페이지 추가:**
1. `frontend/src/app/*/page.tsx` - 페이지 컴포넌트 생성
2. `frontend/src/app/layout.tsx` - 네비게이션 링크 추가

**새 백그라운드 작업 추가:**
1. `backend/app/tasks/*.py` - Celery 작업 정의
2. `backend/app/core/celery_app.py` - 작업 import
3. `backend/app/api/scheduler.py` - 트리거 API 추가 (선택)

---

## 기술 스택 위치

| 기술 | 위치 | 주요 파일 | 용도 |
|------|------|-----------|------|
| **Python 3.13** | backend/ | requirements.txt | 백엔드 런타임 |
| **FastAPI** | backend/app/ | main.py, api/*.py | REST API 서버 |
| **SQLAlchemy 2.0** | backend/app/ | models/complex.py, core/database.py | ORM |
| **Pydantic** | backend/app/ | schemas/*.py | 데이터 검증 |
| **Celery** | backend/app/ | core/celery_app.py, tasks/*.py | 백그라운드 작업 |
| **RedBeat** | backend/app/ | core/celery_app.py | 동적 스케줄링 |
| **Playwright** | backend/app/ | services/crawler_service.py | 웹 크롤링 |
| **PostgreSQL 15** | Docker | docker-compose.yml | 데이터베이스 (포트 5433) |
| **Redis 7** | Docker | docker-compose.yml | 캐시/메시지 브로커 (포트 6380) |
| **Next.js 14** | frontend/ | app/*/page.tsx | 프론트엔드 프레임워크 |
| **TypeScript** | frontend/src/ | types/index.ts | 타입 안전성 |
| **Tailwind CSS** | frontend/ | tailwind.config.ts | 스타일링 |
| **Chart.js** | frontend/src/ | components/PriceTrendChart.tsx | 차트 시각화 |
| **Axios** | frontend/src/ | lib/api.ts | HTTP 클라이언트 |

---

## 주요 디렉토리 역할 요약

### Backend
- **`api/`** - REST API 엔드포인트 (8개 라우터)
- **`services/`** - 비즈니스 로직 (크롤러, 실거래, 브리핑 등)
- **`tasks/`** - Celery 백그라운드 작업 (스케줄 크롤링, 브리핑 전송)
- **`models/`** - DB 테이블 정의 (8개 테이블)
- **`schemas/`** - API 요청/응답 검증
- **`core/`** - 핵심 설정 (DB, Celery, 인증)

### Frontend
- **`app/`** - Next.js 페이지 (App Router)
- **`components/`** - 재사용 컴포넌트
- **`lib/`** - API 클라이언트 및 유틸리티
- **`types/`** - TypeScript 인터페이스

### Docs
- **활성 문서** - 설정, 가이드, API 문서
- **`archive/`** - 오래된 설계 문서, 배포 가이드

---

## 🔍 파일 찾기 팁

**특정 기능 찾기:**
- **크롤링 로직** → `backend/app/services/crawler_service.py`
- **스케줄러 관리** → `backend/app/api/scheduler.py`
- **실거래가 조회** → `backend/app/services/molit_service.py`
- **Discord 브리핑** → `backend/app/services/briefing_service.py`
- **단지 상세 페이지** → `frontend/src/app/complexes/[id]/page.tsx`
- **스케줄러 페이지** → `frontend/src/app/scheduler/page.tsx`

**설정 파일:**
- **DB 연결** → `backend/app/core/database.py`
- **Celery 설정** → `backend/app/core/celery_app.py`
- **Docker 컨테이너** → `docker-compose.yml`
- **환경변수** → `backend/.env` (Git 제외)

**데이터:**
- **법정동 코드** → `backend/app/data/dong_code_active.txt`
- **스케줄 백업** → `backend/app/config/schedules.json`
- **DB 볼륨** → Docker 볼륨 `postgres_data`, `redis_data`

---

**마지막 업데이트**: 2025-10-10
**프로젝트 버전**: Phase 7 완료 (실거래가 차트, 인증 백엔드, 문서 정리)
