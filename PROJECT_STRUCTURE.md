# 프로젝트 구조

## 📁 루트 디렉토리

```
naver_realestate/
├── advanced_crawler.py      # ⭐ 프로덕션 크롤러 (단지/매물/실거래 통합 수집)
├── check_data.py            # 데이터베이스 데이터 확인 도구
├── reset_db.py              # 데이터베이스 초기화 도구
├── test_api.sh              # API 테스트 스크립트
├── docker-compose.yml       # Docker 컨테이너 설정
├── .gitignore               # Git 제외 파일 설정
├── README.md                # 프로젝트 메인 문서
└── PROJECT_STRUCTURE.md     # 이 파일
```

## 📂 주요 디렉토리

### backend/ - 백엔드 API 서버
```
backend/
├── app/
│   ├── api/                 # FastAPI 라우터
│   │   ├── complexes.py     # 단지 API (6개 엔드포인트)
│   │   ├── articles.py      # 매물 API (5개 엔드포인트)
│   │   └── transactions.py  # 실거래가 API (5개 엔드포인트)
│   ├── schemas/             # Pydantic 스키마
│   │   └── complex.py       # API 요청/응답 스키마
│   ├── models/              # SQLAlchemy ORM 모델
│   │   └── complex.py       # DB 테이블 정의
│   ├── core/                # 핵심 설정
│   │   └── database.py      # DB 연결 설정
│   ├── crawler/             # 크롤러 모듈
│   │   └── naver_land_crawler.py
│   └── main.py              # FastAPI 앱 진입점
└── venv/                    # Python 가상환경
```

### frontend/ - Next.js 프론트엔드
```
frontend/
├── src/
│   ├── app/                 # Next.js 14 App Router
│   │   ├── layout.tsx       # 루트 레이아웃 + 네비게이션
│   │   ├── page.tsx         # 대시보드 (홈)
│   │   ├── complexes/
│   │   │   ├── page.tsx     # 단지 목록
│   │   │   └── [id]/page.tsx # 단지 상세 (차트)
│   │   ├── articles/
│   │   │   └── page.tsx     # 매물 검색
│   │   └── transactions/
│   │       └── page.tsx     # 실거래가 조회
│   ├── lib/
│   │   └── api.ts           # Axios API 클라이언트
│   └── types/
│       └── index.ts         # TypeScript 타입 정의
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

### docs/ - 프로젝트 문서
```
docs/
├── PROJECT_OVERVIEW.md      # 프로젝트 개요
├── PROGRESS_SUMMARY.md      # 진행 상황 요약
├── API_GUIDE.md             # API 사용 가이드
├── SETUP_GUIDE.md           # Docker 설정 가이드
└── IMPLEMENTATION_CHECKLIST.md  # 구현 체크리스트
```

### archive/ - 개발 중 생성된 테스트 파일 보관 🗄️
```
archive/
├── test_scripts/            # 실험/테스트용 Python 스크립트
│   ├── crawl_with_cookies.py
│   ├── debug_dynamic_content.py
│   ├── simple_crawl.py
│   └── ... (15개 파일)
├── screenshots/             # 크롤링 테스트 스크린샷
│   ├── complex_page_screenshot.png
│   ├── result.png
│   └── ... (8개 파일)
├── test_data/               # API 응답 테스트 데이터
│   ├── api_1.json ~ api_23.json
│   ├── captured_1.json ~ captured_25.json
│   └── all_api.json
└── README.md                # Archive 폴더 설명
```

## 🎯 파일 역할

### 프로덕션 파일 (Git 추적)
- ✅ **advanced_crawler.py** - 네이버 부동산 크롤러 (실제 사용)
- ✅ **check_data.py** - DB 데이터 확인
- ✅ **reset_db.py** - DB 초기화
- ✅ **test_api.sh** - API 테스트
- ✅ **backend/app/** - FastAPI 애플리케이션
- ✅ **frontend/src/** - Next.js 애플리케이션
- ✅ **docs/** - 문서

### 개발/테스트 파일 (Git 제외, archive에 보관)
- 🗄️ **archive/test_scripts/** - 개발 중 실험 스크립트
- 🗄️ **archive/screenshots/** - 테스트 스크린샷
- 🗄️ **archive/test_data/** - API 테스트 데이터

## 🚀 실행 흐름

### 1. 개발 환경 시작
```bash
# Docker 컨테이너 시작 (PostgreSQL + Redis)
docker-compose up -d

# DB 초기화 (최초 1회)
backend/venv/bin/python reset_db.py
```

### 2. 데이터 수집
```bash
# 크롤링 실행
backend/venv/bin/python advanced_crawler.py
```

### 3. 백엔드 API 시작
```bash
cd backend
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 프론트엔드 시작
```bash
cd frontend
npm run dev  # http://localhost:3000
```

## 📊 데이터 흐름

```
[네이버 부동산]
     ↓ (Playwright 크롤링)
[advanced_crawler.py]
     ↓ (SQLAlchemy ORM)
[PostgreSQL DB]
     ↓ (FastAPI)
[REST API :8000]
     ↓ (Axios)
[Next.js Frontend :3000]
     ↓
[사용자 브라우저]
```

## 🔧 기술 스택별 위치

| 기술 | 위치 | 설명 |
|------|------|------|
| **Playwright** | advanced_crawler.py | 웹 크롤링 |
| **SQLAlchemy** | backend/app/models/ | ORM |
| **FastAPI** | backend/app/main.py, api/ | REST API |
| **Pydantic** | backend/app/schemas/ | 데이터 검증 |
| **Next.js** | frontend/src/app/ | 프론트엔드 |
| **TypeScript** | frontend/src/ | 타입 안전성 |
| **Tailwind CSS** | frontend/src/app/ | 스타일링 |
| **Recharts** | frontend/src/app/complexes/[id]/ | 차트 |
| **PostgreSQL** | Docker 컨테이너 | 데이터베이스 |
| **Redis** | Docker 컨테이너 | 캐시 |

## 📝 개발 가이드

### 새로운 API 엔드포인트 추가
1. `backend/app/models/complex.py` - DB 모델 수정
2. `backend/app/schemas/complex.py` - Pydantic 스키마 추가
3. `backend/app/api/` - 라우터에 엔드포인트 추가
4. `frontend/src/lib/api.ts` - API 클라이언트 함수 추가
5. `frontend/src/types/index.ts` - TypeScript 타입 추가

### 새로운 페이지 추가
1. `frontend/src/app/` - 페이지 컴포넌트 생성
2. `frontend/src/app/layout.tsx` - 네비게이션 링크 추가

### 크롤러 수정
1. `advanced_crawler.py` - 크롤링 로직 수정
2. `backend/app/models/complex.py` - 필요시 DB 모델 수정
3. `reset_db.py` 실행으로 DB 재생성

## ⚠️ 주의사항

- **archive/** 폴더는 Git에 포함되지 않음
- 테스트 파일은 **archive/test_scripts/**에 보관
- 실제 사용되는 크롤러는 **advanced_crawler.py**만 사용
- 모든 API는 **http://localhost:8000/docs**에서 확인 가능
