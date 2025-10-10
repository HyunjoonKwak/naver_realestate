# Archived Code

이 디렉토리에는 더 이상 사용되지 않지만 참고용으로 보관된 코드가 포함되어 있습니다.

## advanced_crawler.py

**아카이브 날짜**: 2025-10-10
**아카이브 사유**: 백엔드 서비스로 통합됨

### 개요

초기 버전의 독립 실행형 네이버 부동산 크롤러입니다. Playwright를 사용하여 단지 정보, 매물 목록, 실거래가를 크롤링하고 데이터베이스에 저장하는 기능을 제공했습니다.

### 주요 기능

1. **봇 감지 회피 기술**
   - `headless=False` - 실제 브라우저 사용
   - `--disable-blink-features=AutomationControlled`
   - `slow_mo=100` - 자연스러운 동작 연출
   - localStorage 기반 "동일매물묶기" 설정

2. **데이터 수집**
   - 네이버 API 응답 가로채기 (response interception)
   - 스크롤 기반 페이지네이션으로 모든 매물 수집
   - 중복 제거 로직

3. **데이터베이스 저장**
   - Complex, Article, Transaction 테이블에 직접 저장
   - 기존 데이터 업데이트 지원

### 현재 대체 구현

이 파일의 기능은 현재 다음 백엔드 서비스로 완전히 대체되었습니다:

- **크롤러 서비스**: [backend/app/services/crawler_service.py](../../backend/app/services/crawler_service.py)
  - 같은 봇 회피 기술 사용
  - 더 많은 기능 (주소 수집, 변경 추적 등)
  - FastAPI와 통합되어 API 엔드포인트로 호출 가능

- **API 엔드포인트**: [backend/app/api/scraper.py](../../backend/app/api/scraper.py)
  - POST /api/scraper/crawl/{complex_id}
  - POST /api/scraper/refresh/{complex_id} (변경 추적 포함)

- **백그라운드 작업**: [backend/app/tasks/scheduler.py](../../backend/app/tasks/scheduler.py)
  - Celery 기반 스케줄링
  - RedBeat 동적 스케줄 관리

### 코드 비교

| 기능 | advanced_crawler.py | 현재 백엔드 서비스 |
|------|---------------------|-------------------|
| 크롤링 엔진 | Playwright | Playwright |
| 봇 회피 | ✅ | ✅ (동일) |
| 동일매물묶기 | ✅ | ✅ (개선됨) |
| 주소 수집 | ❌ | ✅ (도로명/법정동) |
| 변경 추적 | ❌ | ✅ (Snapshot + Change) |
| API 통합 | ❌ | ✅ (FastAPI) |
| 스케줄링 | ❌ | ✅ (Celery + RedBeat) |
| 실거래가 연동 | ❌ | ✅ (MOLIT API) |
| Discord 알림 | ❌ | ✅ (Weekly briefing) |

### 사용하지 않는 이유

1. **중복 코드**: 백엔드 서비스와 99% 동일한 로직
2. **유지보수 부담**: 두 곳에서 같은 기능을 관리해야 함
3. **기능 부족**: 백엔드 서비스가 더 많은 기능 제공
4. **통합 필요**: API 기반 아키텍처로 프론트엔드와 통합

### 참고 사항

이 파일은 다음 목적으로 보관됩니다:

- 크롤링 로직 히스토리 참고
- 초기 구현 방식 비교
- 봇 회피 기술 레퍼런스

**새로운 크롤링 기능이 필요한 경우**: 이 파일을 수정하지 말고, [backend/app/services/crawler_service.py](../../backend/app/services/crawler_service.py)를 수정하세요.

---

## 관련 문서

- [프로젝트 아키텍처](../PROJECT_STRUCTURE.md)
- [크롤러 서비스 문서](../../CLAUDE.md#crawler-architecture)
- [API 문서](http://localhost:8000/docs)
