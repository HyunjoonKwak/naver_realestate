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

### Development
```bash
# Start API server (from project root)
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend dev server (from project root)
cd frontend
npm run dev

# API documentation
open http://localhost:8000/docs
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

**Schemas:** [backend/app/schemas/](backend/app/schemas/) - Pydantic models for request/response validation

**Services:** [backend/app/services/](backend/app/services/)
- `crawler_service.py` - NaverRealEstateCrawler class (moved from root)
- `article_tracker.py` - Article change detection and snapshot management

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
3. **Change Detection:** Crawler compares new snapshot with latest ArticleSnapshot → Creates ArticleChange records → Used for weekly briefing feature

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

## Known Limitations

- No user authentication system yet (planned)
- No scheduled crawling (Celery integration planned)
- Real transaction (실거래가) feature was removed, needs re-implementation via MOLIT API
- Weekly briefing feature designed but not fully implemented
- Crawling requires headless=False to avoid bot detection
