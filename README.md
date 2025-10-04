# 네이버 부동산 매물 관리 시스템

네이버 부동산 데이터를 크롤링하여 매물 변동, 가격 추이, 실거래가를 추적하고 분석하는 풀스택 웹 애플리케이션

## 🎯 주요 기능

### ✅ 구현 완료
- 🏢 **단지 정보 수집**: 세대수, 동수, 면적, 준공일 등 상세 정보
- 💰 **매물 추적**: 매매/전세/월세 매물 정보 및 가격 변동 자동 감지
- 📊 **실거래가 수집**: 네이버 부동산 실거래가 데이터
- 🔄 **자동 업데이트**: 중복 체크 및 증분 업데이트
- 🗄️ **데이터베이스**: PostgreSQL에 체계적으로 저장
- 🚀 **REST API**: FastAPI 기반 완전한 API 서버 (15+ 엔드포인트)
- 📈 **통계 분석**: 가격 추이, 면적별 가격, 층별 프리미엄 분석
- 🎨 **웹 프론트엔드**: Next.js 14 + TypeScript + Tailwind CSS
  - 📊 대시보드 (통계 요약, 최근 매물/실거래)
  - 🏘️ 단지 목록 및 상세 페이지 (가격 차트 포함)
  - 🔍 매물 검색 및 필터링 (단지/거래유형/면적/가격대)
  - 💹 실거래가 조회 및 가격 추이 차트 (Recharts)
  - 📱 반응형 디자인 (모바일/태블릿/데스크톱)

### 🚧 개발 예정
- ⏰ Celery 자동 스케줄링 (정기 크롤링)
- 🤖 가격 분석 및 최적 매매 시기 추천
- 🔔 알림 기능 (이메일/Slack/카카오톡)
- 🔐 사용자 인증 및 관심 단지 개인화

## 🚀 빠른 시작

### 1. Docker 컨테이너 시작
```bash
docker-compose up -d
```

### 2. 데이터베이스 초기화
```bash
backend/venv/bin/python reset_db.py
```

### 3. 크롤링 실행
```bash
backend/venv/bin/python advanced_crawler.py
```

### 4. API 서버 시작
```bash
cd backend
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 프론트엔드 시작 (새 터미널)
```bash
cd frontend
npm install  # 최초 1회만
npm run dev
```

### 6. 브라우저에서 접속
- **프론트엔드**: http://localhost:3000 🎨
- **API 문서**: http://localhost:8000/docs 📖
- **데이터 확인**: `backend/venv/bin/python check_data.py`

## 📂 프로젝트 구조

```
naver_realestate/
├── advanced_crawler.py      # ⭐ 통합 크롤러 (단지/매물/실거래)
├── backend/
│   ├── app/
│   │   ├── api/             # ⭐ FastAPI 라우터 (complexes, articles, transactions)
│   │   ├── schemas/         # ⭐ Pydantic 스키마
│   │   ├── core/            # 데이터베이스 설정
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── crawler/         # 크롤러 모듈
│   │   └── main.py          # ⭐ FastAPI 메인 앱
│   └── venv/                # Python 가상환경
├── frontend/                 # ⭐ Next.js 프론트엔드
│   ├── src/
│   │   ├── app/             # ⭐ Next.js 페이지 (App Router)
│   │   ├── lib/             # ⭐ API 클라이언트 (axios)
│   │   └── types/           # TypeScript 타입 정의
│   ├── package.json
│   └── tsconfig.json
├── docs/                    # 프로젝트 문서
│   ├── PROJECT_OVERVIEW.md
│   ├── PROGRESS_SUMMARY.md
│   ├── API_GUIDE.md         # ⭐ API 가이드
│   ├── SETUP_GUIDE.md
│   └── IMPLEMENTATION_CHECKLIST.md
├── test_api.sh              # ⭐ API 테스트 스크립트
├── docker-compose.yml       # Docker 설정
└── README.md
```

## 🔧 기술 스택

### Backend
- **Python 3.13** + Playwright (웹 크롤링)
- **FastAPI** + Uvicorn (REST API)
- **PostgreSQL 15** (데이터베이스)
- **Redis 7** (캐시/메시지 브로커)
- **SQLAlchemy 2.0** (ORM)
- **Pydantic** (데이터 검증)

### Frontend
- **Next.js 14** (App Router)
- **React 18** + TypeScript
- **Tailwind CSS** (스타일링)
- **Recharts** (데이터 시각화)
- **Axios** (HTTP 클라이언트)

### Infrastructure
- **Docker & Docker Compose** (컨테이너화)

## 📖 상세 문서

- [프로젝트 개요](docs/PROJECT_OVERVIEW.md)
- [진행 상황 요약](docs/PROGRESS_SUMMARY.md)
- [API 가이드](docs/API_GUIDE.md) ⭐
- [구현 체크리스트](docs/IMPLEMENTATION_CHECKLIST.md)
- [Docker 가이드](docs/SETUP_GUIDE.md)

## ⚠️ 주의사항

- 네이버 부동산 이용약관 준수
- 개인 용도로만 사용
- 과도한 요청 시 IP 차단 가능
- Bot 탐지 방지를 위해 headless=False 권장

## 📈 현재 상태

**Phase 4 완료** (2025-10-04) 🎉

### 데이터 현황
- 단지: 1개
- 매물: 20건
- 실거래: 1건

### 시스템 구성
- API 엔드포인트: 15+개
- 프론트엔드 페이지: 5개
- 데이터베이스 테이블: 4개

### 완성된 기능

**백엔드 (FastAPI)**
- ✅ 단지 목록/상세/통계 API
- ✅ 매물 검색/필터링 API
- ✅ 실거래가 검색/통계 API
- ✅ 가격 추이 분석 API
- ✅ 면적별/층별 가격 분석 API
- ✅ CORS 설정 (프론트엔드 연동)
- ✅ OpenAPI 문서 자동 생성

**프론트엔드 (Next.js)**
- ✅ 대시보드 (홈페이지)
  - 통계 카드 (단지/매물/실거래 수)
  - 최근 단지 목록
  - 최근 매물 목록
  - 최근 실거래 목록
- ✅ 단지 목록 페이지
  - 그리드 레이아웃
  - 단지 정보 카드
- ✅ 단지 상세 페이지
  - 단지 정보 표시
  - 통계 카드
  - 가격 추이 차트 (Recharts)
  - 매물 목록
  - 실거래가 목록
- ✅ 매물 검색 페이지
  - 다중 필터 (단지/거래유형/면적)
  - 실시간 검색
  - 가격 변동 표시
- ✅ 실거래가 조회 페이지
  - 날짜/가격 범위 필터
  - 테이블 뷰
  - 포맷된 날짜/가격

**크롤링 시스템**
- ✅ Playwright 기반 네이버 부동산 크롤러
- ✅ 네트워크 응답 가로채기 방식
- ✅ 단지/매물/실거래가 통합 수집
- ✅ 중복 체크 및 증분 업데이트
- ✅ 가격 변동 자동 추적

**다음 단계**: Celery 자동화 스케줄링 및 알림 기능

## 💻 개발 환경 설정

### 필수 요구사항
- Docker Desktop
- Python 3.11+
- Node.js 18+

### 설치 방법
```bash
# 1. 저장소 클론
git clone <repository-url>
cd naver_realestate

# 2. Docker 시작
docker-compose up -d

# 3. Python 가상환경 (이미 설정됨)
cd backend
source venv/bin/activate

# 4. Playwright 브라우저 설치
venv/bin/playwright install chromium

# 5. 프론트엔드 의존성 설치
cd ../frontend
npm install
```

## 🧪 테스트

### API 테스트
```bash
./test_api.sh
```

### 프론트엔드 개발 서버
```bash
cd frontend
npm run dev
```

### 크롤러 테스트
```bash
backend/venv/bin/python advanced_crawler.py
```

## 📝 라이선스

본 프로젝트는 개인 학습 및 포트폴리오 목적으로 제작되었습니다.
- 네이버 부동산 이용약관을 준수해야 합니다
- 상업적 용도로 사용 불가
- 크롤링한 데이터의 정확성은 보장되지 않습니다
