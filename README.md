# 네이버 부동산 매물 관리 시스템

네이버 부동산 데이터를 크롤링하여 매물 변동, 가격 추이, 실거래가를 추적하고 분석하는 시스템

## 🎯 주요 기능

### ✅ 구현 완료
- 🏢 **단지 정보 수집**: 세대수, 동수, 면적, 준공일 등
- 💰 **매물 추적**: 매매/전세/월세 매물 정보 및 가격 변동 감지
- 📊 **실거래가 수집**: 네이버 부동산 실거래가 데이터
- 🔄 **자동 업데이트**: 중복 체크 및 증분 업데이트
- 🗄️ **데이터베이스 저장**: PostgreSQL에 체계적으로 저장
- 🚀 **REST API**: FastAPI 기반 완전한 API 서버
- 📈 **통계 분석**: 가격 추이, 면적별 가격, 층별 프리미엄

### 🚧 개발 예정
- Celery 자동 스케줄링
- 가격 분석 및 최적 매매 시기 추천
- Next.js 프론트엔드

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

브라우저에서 http://localhost:8000/docs 접속하여 API 문서 확인

### 5. 데이터 확인
```bash
backend/venv/bin/python check_data.py
# 또는 API로 확인
curl http://localhost:8000/complexes/
```

## 📂 프로젝트 구조

```
naver_realestate/
├── advanced_crawler.py      # ⭐ 통합 크롤러 (단지/매물/실거래)
├── backend/
│   ├── app/
│   │   ├── api/             # ⭐ FastAPI 라우터
│   │   ├── schemas/         # ⭐ Pydantic 스키마
│   │   ├── core/            # 데이터베이스 설정
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── crawler/         # 크롤러 모듈
│   │   └── main.py          # ⭐ FastAPI 메인 앱
│   └── venv/                # Python 가상환경
├── docs/                    # 프로젝트 문서
│   └── API_GUIDE.md         # ⭐ API 가이드
├── test_api.sh              # ⭐ API 테스트 스크립트
├── docker-compose.yml       # Docker 설정
└── README.md
```

## 🔧 기술 스택

- **Python 3.13** + Playwright (웹 크롤링)
- **FastAPI** + Uvicorn (REST API)
- **PostgreSQL 15** (데이터베이스)
- **Redis 7** (캐시/메시지 브로커)
- **SQLAlchemy 2.0** (ORM)
- **Pydantic** (데이터 검증)
- **Docker** (컨테이너화)

## 📖 상세 문서

- [프로젝트 개요](docs/PROJECT_OVERVIEW.md)
- [진행 상황 요약](docs/PROGRESS_SUMMARY.md)
- [API 가이드](docs/API_GUIDE.md) ⭐ NEW
- [구현 체크리스트](docs/IMPLEMENTATION_CHECKLIST.md)
- [Docker 가이드](docs/SETUP_GUIDE.md)

## ⚠️ 주의사항

- 네이버 부동산 이용약관 준수
- 개인 용도로만 사용
- 과도한 요청 시 IP 차단 가능
- Bot 탐지 방지를 위해 headless=False 권장

## 📈 현재 상태

**Phase 3 완료** (2025-10-04)
- 단지: 1개
- 매물: 20건
- 실거래: 1건
- API 엔드포인트: 15+개

### API 엔드포인트
- ✅ 단지 목록/상세/통계
- ✅ 매물 검색/필터링
- ✅ 실거래가 검색/통계
- ✅ 가격 추이 분석
- ✅ 면적별/층별 가격 분석

다음 단계: Celery 자동화 스케줄링
