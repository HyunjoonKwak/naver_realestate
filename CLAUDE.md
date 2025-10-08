# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Korean real estate tracking system that crawls Naver Real Estate for apartment complex listings, monitors price changes, and provides analytics. Full-stack application with FastAPI backend, Next.js 14 frontend, PostgreSQL database, and Playwright-based crawler.

**Tech Stack:** Python 3.13, FastAPI, PostgreSQL 15, Redis 7, SQLAlchemy 2.0, Next.js 14 (App Router), TypeScript, Tailwind CSS

## Essential Commands

### Initial Setup
```bash
# Start Docker containers (PostgreSQL + Redis)
docker-compose up -d

# Migrate database with foreign keys (recommended - Phase 1 improvement)
backend/.venv/bin/python migrate_db.py

# Legacy: Initialize/reset database tables (no foreign keys)
backend/.venv/bin/python reset_db.py

# Install Playwright browsers (first time only)
backend/.venv/bin/playwright install chromium

# Install frontend dependencies (first time only)
cd frontend && npm install
```

### Development (로컬)
```bash
# Start API server (from project root)
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start Celery Worker (백그라운드 작업 처리)
cd backend
./run_celery_worker.sh

# Start Celery Beat (스케줄러 - 자동 크롤링)
cd backend
./run_celery_beat.sh

# Start frontend dev server (from project root)
cd frontend
npm run dev

# API documentation
open http://localhost:8000/docs
```

### Production (NAS 운영)
```bash
# .env 파일 설정 (필수!)
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/naver_realestate
REDIS_HOST=redis
REDIS_PORT=6379
MOLIT_API_KEY=your_api_key
DISCORD_WEBHOOK_URL=your_webhook_url
EOF

# 모든 서비스 시작 (Docker Compose)
docker-compose up -d --build

# 데이터베이스 마이그레이션
docker-compose exec api python migrate_db.py

# 상태 확인
docker-compose ps
docker-compose logs -f celery_beat

# Beat Lock 확인 (양수면 정상 작동 중)
docker-compose exec redis redis-cli TTL "redbeat::lock"

# 서비스 재시작
docker-compose restart celery_beat

# 자세한 내용은 NAS_DEPLOYMENT.md 참고
```

### Testing
```bash
# Test API endpoints
./test_api.sh
```

## Architecture

### Backend Structure (FastAPI)

**Core Application:** [backend/app/main.py](backend/app/main.py) - Main FastAPI app with CORS middleware and router registration

**Database Layer:**
- [backend/app/core/database.py](backend/app/core/database.py) - SQLAlchemy engine/session management, `get_db()` dependency
- [backend/app/models/complex.py](backend/app/models/complex.py) - All database models using declarative base:
  - `Complex` - Apartment complex master data
  - `Article` - Current listings (unique by `article_no`)
  - `Transaction` - Real transaction history
  - `ArticleSnapshot` - Point-in-time article states for change tracking
  - `ArticleChange` - Detected changes (NEW/REMOVED/PRICE_UP/PRICE_DOWN)
  - `ArticleHistory` - Legacy change tracking

**API Routes:** [backend/app/api/](backend/app/api/)
- `complexes.py` - Complex CRUD, stats, associated articles/transactions
- `articles.py` - Article listing, filtering, price change queries
- `scraper.py` - Background crawling endpoints:
  - POST /api/scraper/crawl (body: {complex_id})
  - POST /api/scraper/crawl/{complex_id} (RESTful path param)
  - POST /api/scraper/refresh/{complex_id} (with change tracking)
- `transactions.py` - Transaction queries and analytics
- `scheduler.py` - Dynamic scheduling API (RedBeat-based, no restart needed):
  - POST /api/scheduler/trigger/all - Manual crawl all complexes
  - POST /api/scheduler/trigger/{complex_id} - Manual crawl single complex
  - GET /api/scheduler/schedule - View current schedules
  - POST /api/scheduler/schedule - Create new schedule (instant effect)
  - PUT /api/scheduler/schedule/{name} - Update schedule (instant effect)
  - DELETE /api/scheduler/schedule/{name} - Delete schedule
  - GET /api/scheduler/jobs - View crawl job history
  - GET /api/scheduler/stats - View crawling statistics

**Schemas:** [backend/app/schemas/](backend/app/schemas/) - Pydantic models for request/response validation

**Services:** [backend/app/services/](backend/app/services/)
- `crawler_service.py` - NaverRealEstateCrawler class (moved from root)
- `article_tracker.py` - Article change detection and snapshot management
- `molit_service.py` - 국토교통부 실거래가 API 연동 (XML 파싱, 페이지네이션)
- `transaction_service.py` - 실거래가 데이터 저장 및 통계 처리
- `location_parser.py` - 법정동 코드 파싱 및 시군구 코드 추출 (20,000개 법정동)
- `discord_service.py` - Discord webhook 알림 (크롤링 브리핑, 에러 알림)

**Background Tasks:** [backend/app/tasks/](backend/app/tasks/)
- `scheduler.py` - Celery tasks for scheduled crawling (crawl_all_complexes, cleanup_old_snapshots)
- `briefing_tasks.py` - Discord briefing tasks (send_weekly_briefing, send_custom_briefing)

### Crawler Architecture

**Main Crawler:** [backend/app/services/crawler_service.py](backend/app/services/crawler_service.py) - Playwright-based scraper with critical bot evasion features:

1. **동일매물묶기 (Same Address Grouping):** Sets `localStorage.sameAddrYn=true` BEFORE page load, clicks checkbox, validates `sameAddressGroup=true` in API calls. This groups duplicate listings by same address.

2. **Network Response Interception:** Captures Naver API responses for complex data, article lists, and transactions during page interaction.

3. **Scroll-based Collection:** Scrolls `.item_list` container to trigger lazy loading and collect all listings.

4. **Incremental Updates:** Compares with existing DB records by `article_no`, detects NEW/REMOVED/PRICE_CHANGED items, stores snapshots.

5. **Background Execution:** Triggered via `/api/scrape/{complex_id}` endpoint for async processing.

### Frontend Structure (Next.js App Router)

**Pages:** [frontend/src/app/](frontend/src/app/)
- `page.tsx` - Dashboard with complex grid and stats
- `complexes/page.tsx` - Complex list page
- `complexes/[id]/page.tsx` - Complex detail with articles table, filters, price cards
- `complexes/new/page.tsx` - Add new complex by Naver URL
- `scheduler/page.tsx` - Scheduler management (view/create/edit/delete schedules, job history)

**API Client:** [frontend/src/lib/api.ts](frontend/src/lib/api.ts) - Axios-based client for backend API calls

**Types:** [frontend/src/types/](frontend/src/types/) - TypeScript interfaces matching backend schemas

### Database Design

**Key Relationships (Phase 1: Foreign Keys Added):**
- `Complex.complex_id` → `Article.complex_id` (1:N, CASCADE delete)
- `Complex.complex_id` → `Transaction.complex_id` (1:N, CASCADE delete)
- `Complex.complex_id` → `ArticleSnapshot.complex_id` (1:N, CASCADE delete)
- `Complex.complex_id` → `ArticleChange.complex_id` (1:N, CASCADE delete)
- `Article.article_no` → `ArticleSnapshot.article_no` (1:N for history)
- `ArticleChange` references snapshots via `from_snapshot_id` / `to_snapshot_id`

**Important Fields:**
- `Article.same_addr_cnt` - Number of realtors with same listing (from 동일매물묶기)
- `Article.price_change_state` - "SAME", "UP", "DOWN" from Naver API
- `Article.is_active` - False when listing removed from site
- `ArticleChange.change_type` - "NEW", "REMOVED", "PRICE_UP", "PRICE_DOWN"

### Data Flow

1. **Adding Complex:** Frontend sends Naver URL → POST /api/scrape/{complex_id} → Crawler runs in background → Stores Complex + Articles in DB
2. **Viewing Articles:** Frontend calls GET /api/complexes/{complex_id}/articles → Returns filtered articles with stats
3. **Change Detection:** Crawler compares new snapshot with latest ArticleSnapshot → Creates ArticleChange records → Used for weekly briefing
4. **Scheduled Crawling:** Celery Beat triggers crawl_all_complexes task → Crawls all complexes → Sends Discord briefing with summary
5. **Dynamic Scheduling:** Frontend/API updates schedule → RedBeat saves to Redis → Celery Beat auto-reloads within 5 seconds (no restart needed)

## Critical Implementation Details

**Bot Evasion (DO NOT MODIFY):** Crawler uses these techniques to avoid Naver bot detection:
- `headless=False` - Required for bypassing bot detection
- `--disable-blink-features=AutomationControlled` - Hides automation signals
- `slow_mo=100` - Natural-looking browser actions
- `await asyncio.sleep(1.5)` - Scroll speed throttling
- localStorage setup BEFORE page navigation

**Crawler localStorage Setup:** Must inject `localStorage.setItem('sameAddrYn', 'true')` via `page.add_init_script()` BEFORE navigating to Naver page. Checkbox clicking alone is insufficient.

**Article Deduplication:** Use `article_no` as unique identifier, not realtor name or price combinations. Multiple realtors can list same article.

**Database Sessions:** Always use `get_db()` dependency in FastAPI routes. Crawler service accepts optional `db` parameter or creates `SessionLocal()`.

**Change Tracking (Phase 1):** All crawling endpoints now enable snapshot creation and change detection by default (`create_snapshot=True`).

**Foreign Keys (Phase 1):** Deleting a Complex now CASCADE deletes all Articles, Transactions, Snapshots, and Changes. Use `migrate_db.py` to apply.

**CORS Configuration:** Backend allows all origins (`*`) - restrict in production.

**Complex ID Extraction:** From Naver URL `https://new.land.naver.com/complexes/{complex_id}`, extract numeric ID.

**Real Transaction Integration:** Refresh endpoint automatically fetches MOLIT data after crawling. See Real Transaction section below.

**Scheduled Crawling & Discord Briefing:** Uses Celery + RedBeat for dynamic scheduling. Schedules stored in Redis (editable via API without restart) and JSON file ([backend/app/config/schedules.json](backend/app/config/schedules.json)) for persistence. Weekly briefing automatically sent to Discord after scheduled crawls.

## Real Transaction (실거래가) Feature

### Setup
1. **Get API Key**: https://www.data.go.kr/data/15058017/openapi.do
2. **Add to .env**: `MOLIT_API_KEY=your_key_here`
3. **Restart server**: `.venv/bin/uvicorn app.main:app --reload`

### Architecture
- **Data Source**: 국토교통부 공공데이터 (XML format)
- **Coverage**: 전국 20,278개 법정동 코드 자동 매칭
- **Auto-fetch**: 단지 새로고침 시 자동으로 최근 6개월 실거래가 조회
- **Deduplication**: 같은 날짜/면적/층/가격 거래는 중복 제거

### Services
1. **MOLITService** ([molit_service.py](backend/app/services/molit_service.py))
   - XML 응답 파싱 (`_parse_xml_response()`)
   - 페이지네이션 처리 (`_fetch_all_pages()`) - 1000건 이상 자동 수집
   - 매매/전월세 API 지원
   - LocationParser 통합으로 전국 주소 자동 매칭

2. **TransactionService** ([transaction_service.py](backend/app/services/transaction_service.py))
   - `fetch_and_save_transactions()` - API 조회 및 DB 저장
   - `get_area_stats()` - 평형별 통계 계산 (평균/최고/최저/거래건수)
   - 가격 포맷팅 (억/만원)

3. **LocationParser** ([location_parser.py](backend/app/services/location_parser.py))
   - 법정동 코드 파일 로드 (`dong_code_active.txt`, 20,278개)
   - 주소 → 시군구 코드(5자리) 자동 추출
   - 정확한 매칭 + 부분 매칭 + fallback 전략

### API Endpoints
- `POST /api/transactions/fetch/{complex_id}` - 실거래가 수동 조회
- `GET /api/transactions/stats/area-summary/{complex_id}` - 평형별 통계
- `POST /api/scraper/refresh/{complex_id}` - 크롤링 + 실거래가 자동 조회

### Frontend Integration
- **위치**: 단지 상세 페이지 ([complexes/[id]/page.tsx](frontend/src/app/complexes/[id]/page.tsx))
- **UI**: 변동사항 요약 아래 "💰 실거래가 요약" 섹션
- **표시 정보**: 평형별 카드 (평균/최고/최저가, 거래건수)
- **자동 업데이트**: 새로고침 버튼 클릭 시 자동 조회

### Testing
```bash
# 테스트 스크립트 실행
./test_transaction_api.sh

# LocationParser 테스트
cd backend && .venv/bin/python
>>> from app.services.location_parser import LocationParser
>>> parser = LocationParser()
>>> parser.extract_sigungu_code("경기도 성남시 분당구")
'41135'
```

### Data Files
- **법정동 코드**: `backend/app/data/dong_code_active.txt` (20,278 records)
- **Format**: `법정동코드\t법정동명` (TSV)

## Scheduled Crawling & Discord Briefing

### Setup
1. **Discord Webhook**: Create webhook in Discord channel settings
2. **Add to .env**: `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...`
3. **Start Celery**: See Essential Commands above

### Architecture
- **Scheduler**: Celery Beat with RedBeat (Redis-based dynamic scheduler)
- **Worker**: Celery Worker processes background crawling tasks
- **Storage**: Schedules stored in Redis (runtime) + JSON file (persistence)
- **Config File**: [backend/app/config/schedules.json](backend/app/config/schedules.json)

### Features
1. **Dynamic Scheduling** (RedBeat)
   - Create/Update/Delete schedules via API
   - Changes reflected within 5 seconds (no Celery restart needed)
   - Survives restarts (loaded from JSON file on startup)

2. **Crawl Job Tracking**
   - Every crawl creates CrawlJob record in DB
   - Tracks: status, duration, articles collected/new/updated, errors
   - Accessible via `/api/scheduler/jobs` endpoint

3. **Discord Briefing**
   - Automatically sent after scheduled `crawl_all_complexes` task
   - Includes: crawl stats, success/failure counts, complex-level changes
   - Change summary: NEW/REMOVED/PRICE_UP/PRICE_DOWN articles
   - Manual trigger: `send_weekly_briefing.delay()` or `/api/briefing/send`

### Schedule Types
- **Weekly**: `day_of_week: 0-6` (0=Monday, 6=Sunday)
- **Daily**: `day_of_week: "*"`
- **Monthly**: `day_of_week: "MONTHLY_1"` or `"MONTHLY_15"`
- **Quarterly**: `day_of_week: "QUARTERLY_1"` or `"QUARTERLY_15"`

### Frontend Management
- **Scheduler Page**: [frontend/src/app/scheduler/page.tsx](frontend/src/app/scheduler/page.tsx)
- View active schedules, job history, crawl statistics
- Create/edit/delete schedules through UI
- Trigger manual crawls (all complexes or single complex)

### Testing
```bash
# Test manual crawl all complexes
curl -X POST http://localhost:8000/api/scheduler/trigger/all

# View job history
curl http://localhost:8000/api/scheduler/jobs

# View current schedules
curl http://localhost:8000/api/scheduler/schedule
```

## Known Limitations

- No user authentication system yet (planned)
- Crawling requires headless=False to avoid bot detection
  - **Solution**: Use official Playwright Docker image (`mcr.microsoft.com/playwright/python`) - already configured in Dockerfile
- MOLIT API has rate limits (1,000 calls/day for general key)
- Discord briefing only supports webhook (no bidirectional interaction)
- RedBeat scheduler requires Redis
  - Schedules are stored in Redis (`redbeat:*` keys) and backed up to `backend/app/config/schedules.json`
  - If Redis data is lost, schedules are restored from JSON on next Beat startup

## Deployment & Operations

### Development vs Production

| Component | Development (로컬) | Production (NAS) |
|-----------|-------------------|------------------|
| **FastAPI** | `.venv/bin/uvicorn` (manual) | Docker container (auto-restart) |
| **Celery Worker** | `./run_celery_worker.sh` | Docker container (auto-restart) |
| **Celery Beat** | `./run_celery_beat.sh` | Docker container (auto-restart) |
| **PostgreSQL** | Docker (port 5433) | Docker (port 5433) |
| **Redis** | Docker (port 6379) | Docker (port 6379) |
| **Frontend** | `npm run dev` (port 3000) | Docker container (port 3000) |
| **Auto-restart** | ❌ Manual management | ✅ Docker `restart: unless-stopped` |
| **Environment** | `.env` + `.venv` | `.env` + Docker images |

### NAS Deployment

The project is production-ready with Docker Compose:
- All services containerized with health checks
- `restart: unless-stopped` for automatic recovery
- Celery Beat auto-restarts if crashed (Docker manages it)
- RedBeat Lock (TTL 1800s) prevents duplicate Beat instances
- See **[NAS_DEPLOYMENT.md](NAS_DEPLOYMENT.md)** for detailed guide

### Celery Beat Auto-Recovery

**Q: How does Celery Beat restart automatically?**

A: In production (NAS), Docker's `restart: unless-stopped` policy automatically restarts the Beat container if it crashes. The RedBeat Lock (Redis key with 30-min TTL) is used to:
1. Prevent multiple Beat instances from running simultaneously
2. Allow other Beat instances to take over if one dies (in distributed setup)
3. Verify Beat is alive (check `docker-compose exec redis redis-cli TTL "redbeat::lock"`)

If Lock TTL is `-2`, Beat is dead and needs restart:
```bash
docker-compose restart celery_beat
```

### Environment Variables

Beat and Worker read `.env` file through celery_app.py startup code:
```python
# backend/app/core/celery_app.py lines 9-17
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            # Parse and set environment variables
```

This ensures `DISCORD_WEBHOOK_URL` and `MOLIT_API_KEY` are available in background tasks.
