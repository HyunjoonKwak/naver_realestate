# 📚 네이버 부동산 추적 시스템 - 문서 인덱스

프로젝트의 모든 문서를 카테고리별로 정리한 인덱스입니다.

---

## 🚀 시작하기

새로운 개발자가 프로젝트를 시작할 때 읽어야 할 문서:

1. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - 개발 환경 설정 (맥북/맥 양쪽 지원)
   - Docker, PostgreSQL, Redis 설정
   - Python 가상환경 및 의존성 설치
   - Frontend 설정
   - 환경변수 구성

2. **[README_STARTUP.md](README_STARTUP.md)** - 서비스 실행 방법
   - DevTool 사용법 (권장)
   - 통합 스크립트로 실행
   - 수동 실행 (디버깅용)
   - 포트 설정 확인

3. **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - 프로젝트 구조 및 아키텍처
   - 디렉토리 구조 상세 설명
   - Backend/Frontend 모듈 역할
   - 데이터 흐름
   - 파일 찾기 팁

---

## 📖 기능별 가이드

### 크롤링 & 데이터 수집

- **[../CLAUDE.md](../CLAUDE.md)** - AI 개발 가이드 (크롤러 상세 설명 포함)
  - 봇 회피 기법 (headless=False, localStorage 설정)
  - 동일매물묶기 구현
  - 네트워크 인터셉션
  - 스크롤 기반 수집

### 실거래가 기능

- **[TRANSACTION_GUIDE.md](TRANSACTION_GUIDE.md)** - 국토부 실거래가 API 연동
  - MOLIT API Key 발급 방법
  - 법정동 코드 매칭 (20,000개 자동)
  - 평형별 통계 조회
  - 테스트 방법

### 스케줄러

- **[DYNAMIC_SCHEDULING.md](DYNAMIC_SCHEDULING.md)** - RedBeat 동적 스케줄링 상세 가이드
  - 스케줄 생성/수정/삭제
  - Weekly/Daily/Monthly/Quarterly 스케줄
  - 특정 단지 크롤링
  - 요일 다중 선택

- **[SCHEDULER_TROUBLESHOOTING.md](SCHEDULER_TROUBLESHOOTING.md)** - 스케줄러 문제 해결
  - Celery Beat 재시작 방법
  - Mac 슬립 후 복구
  - LockNotOwnedError 해결
  - 웹 UI에서 재활성화

### Discord 브리핑

- **[DISCORD_BRIEFING_GUIDE.md](DISCORD_BRIEFING_GUIDE.md)** - Discord 브리핑 설정 및 사용법
  - 브리핑 메시지 구조
  - 수동 트리거 방법
  - 커스터마이징

- **[WEBHOOK_SETUP_GUIDE.md](WEBHOOK_SETUP_GUIDE.md)** - Discord Webhook 설정
  - Webhook 생성 방법
  - 환경변수 설정
  - 테스트 방법

### API

- **[API_GUIDE.md](API_GUIDE.md)** - REST API 전체 엔드포인트 가이드
  - 단지 관리 API
  - 매물 조회 API
  - 실거래가 API
  - 스케줄러 API
  - 브리핑 API

---

## 🎯 설계 문서

프로젝트 기능 설계 및 UX 문서:

- **[WEEKLY_BRIEFING_FEATURE.md](WEEKLY_BRIEFING_FEATURE.md)** - 주간 브리핑 기능 설계
  - 변동사항 추적 로직
  - ArticleSnapshot 및 ArticleChange 모델
  - 브리핑 메시지 포맷

- **[ARTICLE_CHANGE_TRACKING_UX.md](ARTICLE_CHANGE_TRACKING_UX.md)** - 매물 변동 추적 UX 설계
  - NEW/REMOVED/PRICE_UP/PRICE_DOWN 표시
  - 스냅샷 비교 알고리즘
  - 프론트엔드 UI 설계

---

## 🗂️ 아카이브

더 이상 사용되지 않거나 통합된 문서:

- **[archive/README.md](archive/README.md)** - 아카이브 사유 설명
- **[archive/LAPTOP_SETUP.md](archive/LAPTOP_SETUP.md)** - (통합됨 → SETUP_GUIDE.md)
- **[archive/DEPLOYMENT_GUIDE.md](archive/DEPLOYMENT_GUIDE.md)** - (헤드리스 서버 배포 불가로 보류)
- **[archive/PROJECT_OVERVIEW.md](archive/PROJECT_OVERVIEW.md)** - (초기 기획 문서)

---

## 🛠️ 개발 도구

- **[../DEVTOOL.md](../DEVTOOL.md)** - DevTool 통합 관리 도구 가이드
  - 데이터베이스 관리
  - 테스트 실행
  - 모니터링
  - 서비스 관리
  - 문서 빠른 접근

- **[../scripts/README.md](../scripts/README.md)** - 유틸리티 스크립트 가이드
  - start_all.sh, stop_all.sh, logs_all.sh
  - migrate_db.py, reset_db.py, check_data.py
  - check_schedules.sh

- **[../tests/README.md](../tests/README.md)** - 테스트 가이드
  - test_api.sh
  - test_transaction_api.sh
  - test_discord_briefing.sh

---

## 📋 문서 읽는 순서 추천

### 초보자 (처음 시작)
1. [SETUP_GUIDE.md](SETUP_GUIDE.md) - 환경 설정
2. [README_STARTUP.md](README_STARTUP.md) - 서비스 실행
3. [../DEVTOOL.md](../DEVTOOL.md) - DevTool 사용법
4. [API_GUIDE.md](API_GUIDE.md) - API 이해

### 중급자 (기능 추가/수정)
1. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 프로젝트 구조 이해
2. [../CLAUDE.md](../CLAUDE.md) - 코드 상세 설명
3. [TRANSACTION_GUIDE.md](TRANSACTION_GUIDE.md) - 실거래가 기능
4. [DYNAMIC_SCHEDULING.md](DYNAMIC_SCHEDULING.md) - 스케줄러 확장

### 고급 (문제 해결/최적화)
1. [SCHEDULER_TROUBLESHOOTING.md](SCHEDULER_TROUBLESHOOTING.md) - 트러블슈팅
2. [WEEKLY_BRIEFING_FEATURE.md](WEEKLY_BRIEFING_FEATURE.md) - 변동 추적 로직
3. [ARTICLE_CHANGE_TRACKING_UX.md](ARTICLE_CHANGE_TRACKING_UX.md) - UX 설계

---

## 🔗 외부 참고 링크

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Next.js 14 문서](https://nextjs.org/docs)
- [Celery 문서](https://docs.celeryq.dev/)
- [RedBeat 문서](https://github.com/sibson/redbeat)
- [Playwright 문서](https://playwright.dev/)
- [국토부 실거래가 API](https://www.data.go.kr/data/15058017/openapi.do)

---

**최종 업데이트**: 2025-10-10  
**문서 관리자**: README 통합 및 구조 정리 완료
