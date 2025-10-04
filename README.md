# 네이버 부동산 매물 관리 시스템

네이버 부동산 데이터를 크롤링하여 매물 변동, 가격 추이를 추적하고 분석하는 풀스택 웹 애플리케이션

## 🎯 주요 기능

### ✅ 구현 완료
- 🏢 **단지 정보 수집**: 세대수, 동수, 면적, 준공일 등 상세 정보
- 💰 **매물 추적**: 매매/전세 매물 정보 및 가격 변동 자동 감지
- 🔗 **동일매물묶기**: localStorage 기반 네이버 동일매물묶기 기능 완벽 지원
- 🔄 **자동 업데이트**: 중복 체크 및 증분 업데이트
- 🗄️ **데이터베이스**: PostgreSQL에 체계적으로 저장
- 🚀 **REST API**: FastAPI 기반 완전한 API 서버
- 📈 **통계 분석**: 면적별 최고가/최저가 분석
- 🎨 **웹 프론트엔드**: Next.js 14 + TypeScript + Tailwind CSS
  - 📊 대시보드 (통계 요약, 단지 목록)
  - 🏘️ 단지 목록 및 상세 페이지
  - 🔍 매물 필터링 (거래유형/면적/동)
  - 📋 엑셀 스타일 매물 테이블 뷰
  - 💹 면적별 가격 정보 카드
  - 📱 반응형 디자인 (모바일/태블릿/데스크톱)

### 🚧 개발 예정
- 🏛️ **실거래가 기능**: 국토부 실거래가 공개시스템 연동
  - 국토교통부 오픈API 활용
  - 아파트 실거래가 조회 및 DB 저장
  - 가격 추이 차트 및 분석
- 📈 **주간 브리핑**: 단지별 변동사항 요약 (매물 증감, 가격 변동, 특이사항)
- ⏰ **자동 스케줄링**: Celery 기반 정기 크롤링
- 🤖 **가격 분석**: 최적 매매 시기 추천
- 🔔 **알림 기능**: 가격 변동 알림
- 🔐 **사용자 인증**: 개인화 및 관심 단지 관리

## 🚀 빠른 시작

### 1. Docker 컨테이너 시작
```bash
docker-compose up -d
```

### 2. 데이터베이스 초기화
```bash
backend/.venv/bin/python reset_db.py
```

### 3. API 서버 시작
```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 프론트엔드 시작 (새 터미널)
```bash
cd frontend
npm install  # 최초 1회만
npm run dev
```

### 5. 브라우저에서 단지 추가
- **프론트엔드**: http://localhost:3000
- 우측 상단 "단지 추가" 버튼 클릭
- 네이버 부동산 URL 입력 (예: `https://new.land.naver.com/complexes/1482`)
- 크롤링이 백그라운드에서 자동 실행됩니다

### 6. 참고
- **API 문서**: http://localhost:8000/docs 📖
- **크롤링 직접 실행**: `backend/.venv/bin/python advanced_crawler.py`

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
- [국토부 실거래가 API 연동](docs/MOLIT_API_INTEGRATION.md) 🆕
- [주간 브리핑 기능 설계](docs/WEEKLY_BRIEFING_FEATURE.md) 🆕
- [구현 체크리스트](docs/IMPLEMENTATION_CHECKLIST.md)
- [Docker 가이드](docs/SETUP_GUIDE.md)

## ⚠️ 주의사항

- 네이버 부동산 이용약관 준수
- 개인 용도로만 사용
- 과도한 요청 시 IP 차단 가능
- Bot 탐지 방지를 위해 headless=False 권장

## 📈 현재 상태

**Phase 5 완료** (2025-10-04) 🎉

### 최근 업데이트 (2025-10-04)
- ✅ **동일매물묶기 완벽 구현**: localStorage 기반 네이버 API 정확한 데이터 수집
- ✅ **엑셀 스타일 테이블**: 매물 리스트를 한눈에 보기 쉬운 테이블로 전환
- ✅ **고급 필터링**: 거래유형/면적/동 3가지 필터 + 필터 초기화 기능
- ✅ **면적별 가격 정보**: 매매/전세별 최고가/최저가 카드 뷰
- ✅ **수집일시 표시**: 매물별 크롤링 시간 추적
- ✅ **실거래가 기능 제거**: 코드 정리 (향후 재추가 예정)

### 시스템 구성
- API 엔드포인트: 10+개
- 프론트엔드 페이지: 4개 (대시보드, 단지목록, 단지상세, 단지추가)
- 데이터베이스 테이블: 3개 (Complex, Article, Transaction)

### 완성된 기능

**크롤링 시스템 (Playwright)**
- ✅ localStorage 기반 동일매물묶기 설정
- ✅ 페이지 로드 전 설정 주입
- ✅ 체크박스 자동 활성화 검증
- ✅ 네트워크 응답 가로채기
- ✅ 스크롤 기반 전체 매물 수집
- ✅ articleNo 기반 중복 제거
- ✅ 증분 업데이트 및 가격 변동 추적

**백엔드 (FastAPI)**
- ✅ 단지 CRUD API (생성/조회/수정/삭제)
- ✅ 단지 통계 API (매매/전세 집계)
- ✅ 매물 조회 API (단지별)
- ✅ 백그라운드 크롤링 API
- ✅ CORS 설정 (프론트엔드 연동)
- ✅ OpenAPI 문서 자동 생성

**프론트엔드 (Next.js)**
- ✅ **대시보드**
  - 단지/매물 통계 카드
  - 단지 목록 그리드
  - 단지 추가 버튼
  - 실제 API 연동

- ✅ **단지 상세 페이지**
  - 단지 정보 헤더
  - 매매/전세 통계
  - **면적별 가격 정보** (매매/전세 최고가/최저가)
  - **고급 필터** (거래유형/면적/동)
  - **엑셀 스타일 매물 테이블**
  - 수집일시 표시
  - 단지 삭제 기능

- ✅ **단지 추가 페이지**
  - URL 기반 단지 추가
  - 백그라운드 크롤링
  - 실시간 진행 상태

**다음 단계**: 실거래가 기능 재구현, Celery 자동화 스케줄링

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
source .venv/bin/activate

# 4. Playwright 브라우저 설치
.venv/bin/playwright install chromium

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
backend/.venv/bin/python advanced_crawler.py
```

## 🔑 핵심 기술

### 동일매물묶기 구현
네이버 부동산의 "동일매물묶기" 기능을 완벽하게 재현:
1. **localStorage 설정**: 페이지 로드 전 `sameAddrYn=true` 설정
2. **체크박스 자동 활성화**: JavaScript로 체크박스 상태 확인 및 클릭
3. **API 파라미터 검증**: `sameAddressGroup=true` 확인
4. **정확한 데이터 수집**: 네이버와 동일한 묶음 기준 적용

### 크롤링 최적화
- **스크롤 기반 수집**: `.item_list` 컨테이너 내부 스크롤
- **중복 제거**: `articleNo` 기반 unique 체크
- **증분 업데이트**: 기존 매물과 비교하여 변경사항만 저장

## 📝 라이선스

본 프로젝트는 개인 학습 및 포트폴리오 목적으로 제작되었습니다.
- 네이버 부동산 이용약관을 준수해야 합니다
- 상업적 용도로 사용 불가
- 크롤링한 데이터의 정확성은 보장되지 않습니다
