# 🏠 네이버 부동산 매물 추적 시스템

> 네이버 부동산 아파트 매물을 자동으로 수집하고, 가격 변동을 추적하며, 실거래가를 분석하는 풀스택 웹 애플리케이션

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)

---

## 📋 목차

1. [빠른 시작 (5분)](#-빠른-시작-5분)
2. [주요 기능](#-주요-기능)
3. [기술 스택](#-기술-스택)
4. [상세 가이드](#-상세-가이드)
5. [문제 해결](#-문제-해결)

---

## 🚀 빠른 시작 (5분)

### 필수 요구사항

- **macOS/Linux** (GUI 환경 필요)
- **Docker Desktop** ([설치](https://www.docker.com/products/docker-desktop/))
- **Node.js 18+** ([설치](https://nodejs.org/))
- **Python 3.13** (이미 설정됨)

### 1단계: 프로젝트 받기

```bash
git clone <repository-url>
cd naver_realestate
```

### 2단계: 환경 설정

```bash
# Docker 시작 (PostgreSQL + Redis)
docker-compose up -d

# 데이터베이스 초기화
backend/.venv/bin/python scripts/migrate_db.py

# Frontend 의존성 설치 (최초 1회)
cd frontend && npm install && cd ..
```

### 3단계: DevTool로 실행 ⭐

```bash
./devtool
```

DevTool 메뉴에서:
1. `[4]` 서비스 관리 선택
2. `[1]` 전체 시작

**또는 수동 실행:**
```bash
./scripts/start_all.sh  # 모든 서비스 시작
```

### 4단계: 웹 브라우저에서 확인

- **프론트엔드**: http://localhost:3000
- **API 문서**: http://localhost:8000/docs
- **스케줄러**: http://localhost:3000/scheduler

### 5단계: 단지 추가하기

1. http://localhost:3000 접속
2. 우측 상단 "단지 추가" 버튼 클릭
3. 네이버 부동산 URL 입력
   - 예: `https://new.land.naver.com/complexes/109208`
4. 크롤링 자동 시작!

---

## ✨ 주요 기능

### 📊 데이터 수집 & 분석
- ✅ **자동 크롤링**: Playwright 기반 네이버 부동산 매물 수집
- ✅ **가격 추적**: 매매/전세 가격 변동 자동 감지
- ✅ **실거래가 연동**: 국토부 오픈API 실거래가 자동 조회
- ✅ **동일매물묶기**: 네이버 기능 완벽 지원

### 🤖 자동화 & 알림
- ✅ **스케줄 크롤링**: 원하는 시간에 자동 실행
- ✅ **Discord 브리핑**: 주간 변동사항 자동 알림
- ✅ **가격 변동 알림**: 신규/삭제/가격변동 실시간 감지

### 📈 시각화 & 통계
- ✅ **가격 차트**: Chart.js 기반 실거래가 추이 그래프
- ✅ **평형별 통계**: 면적별 최고/최저/평균가 분석
- ✅ **대시보드**: 단지별 매물 현황 한눈에 보기

---

## 🛠️ 기술 스택

### Backend
```
Python 3.13 + FastAPI + PostgreSQL 15 + Redis 7
├─ Playwright      # 웹 크롤링
├─ SQLAlchemy 2.0  # ORM
├─ Celery          # 백그라운드 작업
└─ RedBeat         # 동적 스케줄링
```

### Frontend
```
Next.js 14 + React 18 + TypeScript
├─ Tailwind CSS    # 스타일링
├─ Chart.js        # 데이터 시각화
└─ Axios           # HTTP 클라이언트
```

### Infrastructure
```
Docker + Docker Compose
├─ PostgreSQL (포트 5433)
└─ Redis (포트 6380)
```

---

## 📚 상세 가이드

### 🔧 DevTool 사용법

DevTool은 모든 작업을 쉽게 수행할 수 있는 통합 도구입니다.

```bash
./devtool
```

**주요 기능:**
- 🗄️ **데이터베이스 관리**: 내용 확인, 마이그레이션, 초기화
- 🧪 **테스트 실행**: API, 실거래가, Discord 테스트
- 📊 **모니터링**: 스케줄 상태, 로그 확인, 프로세스 관리
- 🚀 **서비스 관리**: 전체/개별 시작/중지
- 📚 **문서 보기**: 모든 가이드 바로 열기

자세한 내용: [DEVTOOL.md](DEVTOOL.md)

### 🔄 서비스 관리

**방법 1: DevTool (권장)**
```bash
./devtool
# 메뉴: [4] → [1] 전체 시작
```

**방법 2: 스크립트**
```bash
./scripts/start_all.sh  # 시작
./scripts/stop_all.sh   # 중지
./scripts/logs_all.sh   # 로그 보기
```

**방법 3: 수동 (디버깅용)**
```bash
# 터미널 1: Backend API
cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 터미널 2: Celery Worker
cd backend && .venv/bin/celery -A app.core.celery_app worker --loglevel=info

# 터미널 3: Celery Beat
cd backend && .venv/bin/celery -A app.core.celery_app beat --scheduler redbeat.RedBeatScheduler --loglevel=info

# 터미널 4: Frontend
cd frontend && npm run dev
```

### 📅 자동 크롤링 & Discord 알림 설정

1. **Discord Webhook 생성**
   - Discord 서버 → 채널 설정 → 연동 → 웹후크
   - Webhook URL 복사

2. **환경변수 설정**
   ```bash
   # backend/.env 파일에 추가
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
   MOLIT_API_KEY=your-molit-api-key  # 국토부 API (선택)
   ```

3. **스케줄 설정**
   - http://localhost:3000/scheduler 접속
   - "새 스케줄 추가" 버튼 클릭
   - 원하는 시간과 단지 선택

4. **자동 실행 확인**
   - 설정한 시간에 자동 크롤링
   - Discord로 변동사항 브리핑 전송

### 🧪 테스트

```bash
# DevTool에서
./devtool → [2] 테스트 실행 → [4] 전체 테스트

# 또는 직접 실행
./tests/test_api.sh                 # API 테스트
./tests/test_transaction_api.sh     # 실거래가 테스트
./tests/test_discord_briefing.sh    # Discord 테스트
```

---

## 🗂️ 프로젝트 구조

```
naver_realestate/
├── devtool                    # ⭐ 통합 개발 도구
├── backend/                   # FastAPI 백엔드
│   ├── app/
│   │   ├── api/              # REST API 엔드포인트
│   │   ├── models/           # 데이터베이스 모델
│   │   ├── services/         # 비즈니스 로직 (크롤러, 실거래가)
│   │   ├── tasks/            # Celery 백그라운드 작업
│   │   └── main.py           # FastAPI 앱
│   └── .venv/                # Python 가상환경
├── frontend/                  # Next.js 프론트엔드
│   ├── src/app/              # 페이지 (App Router)
│   ├── src/lib/              # API 클라이언트
│   └── src/types/            # TypeScript 타입
├── scripts/                   # 유틸리티 스크립트
│   ├── start_all.sh          # 전체 시작
│   ├── stop_all.sh           # 전체 중지
│   ├── check_schedules.sh    # 스케줄 확인
│   └── *.py                  # DB 관리 스크립트
├── tests/                     # 테스트 스크립트
├── docs/                      # 상세 문서
└── docker-compose.yml         # Docker 설정
```

---

## ❓ 문제 해결

### 서버가 안 켜져요

```bash
# 1. Docker 상태 확인
docker ps

# 2. 포트 충돌 확인
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5433  # PostgreSQL
lsof -i :6380  # Redis

# 3. DevTool로 확인
./devtool → [3] 모니터링 → [4] 프로세스 상태
```

### 크롤링이 안 돼요

**원인**: Playwright 브라우저 미설치
```bash
cd backend
.venv/bin/playwright install chromium
```

### Celery Beat가 죽었어요 (Mac 슬립 후)

```bash
# 방법 1: 웹 UI에서 재시작
# http://localhost:3000/scheduler → 🔄 재활성화 버튼

# 방법 2: DevTool에서
./devtool → [4] 서비스 관리 → [5] 개별 관리 → [7] Beat 중지 → [3] Beat 시작
```

### 로그 확인하고 싶어요

```bash
# 실시간 로그
./scripts/logs_all.sh

# 개별 로그
tail -f logs/backend.log
tail -f logs/worker.log
tail -f logs/beat.log
tail -f logs/frontend.log
```

### 데이터베이스 초기화

```bash
./devtool → [1] 데이터베이스 관리 → [3] 초기화
# 또는
backend/.venv/bin/python scripts/reset_db.py
```

---

## 📖 추가 문서

### 개발자용
- [개발 가이드 (CLAUDE.md)](CLAUDE.md) - 코드 구조, API 설계
- [프로젝트 구조 (docs/PROJECT_STRUCTURE.md)](docs/PROJECT_STRUCTURE.md) - 상세 아키텍처
- [DevTool 가이드 (DEVTOOL.md)](DEVTOOL.md) - 도구 사용법

### 기능별
- [스크립트 가이드 (scripts/README.md)](scripts/README.md) - 유틸리티 스크립트
- [테스트 가이드 (tests/README.md)](tests/README.md) - 테스트 방법
- [Discord 브리핑 (docs/*.md)](docs/) - 각종 기능 문서

---

## 🎯 로드맵

### ✅ 완료
- [x] 네이버 부동산 크롤링 (동일매물묶기 지원)
- [x] FastAPI REST API
- [x] Next.js 프론트엔드
- [x] 실거래가 연동 (국토부 오픈API)
- [x] 자동 스케줄링 (RedBeat)
- [x] Discord 브리핑
- [x] DevTool 통합 관리 도구

### 🚧 진행 중
- [ ] 가격 분석 AI (최적 매매 시기 추천)
- [ ] 사용자 인증 (개인화 기능)

---

## ⚠️ 주의사항

- ✋ **네이버 부동산 이용약관** 준수 필수
- 🔒 **개인 용도**로만 사용하세요
- 🚫 **과도한 크롤링** 시 IP 차단 가능
- 🖥️ **GUI 환경 필요** (headless=False)
- 💾 **정기 백업** 권장

---

## 📝 라이선스

본 프로젝트는 개인 학습 및 포트폴리오 목적으로 제작되었습니다.
- 상업적 사용 불가
- 크롤링 데이터 정확성 보장 안 됨
- 네이버 부동산 이용약관 준수 필수

---

## 🤝 기여

버그 리포트나 기능 제안은 GitHub Issues로 부탁드립니다.

---

<div align="center">

**Made with ❤️ for Real Estate Investors**

[시작하기](#-빠른-시작-5분) • [문서](docs/) • [문제 해결](#-문제-해결)

</div>
