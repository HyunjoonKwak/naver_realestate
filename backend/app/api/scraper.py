"""
네이버 부동산 스크래핑 API
"""
import re
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from pydantic import BaseModel
from playwright.async_api import async_playwright
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..models.complex import Complex, Article, Transaction
from ..services.article_tracker import ArticleTracker

router = APIRouter(prefix="/scraper", tags=["scraper"])


class CrawlRequest(BaseModel):
    complex_id: str
    collect_address: bool = False


@router.get("/complex")
async def scrape_complex_info(url: str = Query(..., description="네이버 부동산 URL")):
    """
    네이버 부동산 URL에서 단지 정보 추출

    - **url**: 네이버 부동산 단지 URL (예: https://new.land.naver.com/complexes/1482)
    """
    # URL에서 단지 ID 추출
    match = re.search(r'/complexes/(\d+)', url)
    if not match:
        raise HTTPException(status_code=400, detail="유효하지 않은 네이버 부동산 URL입니다")

    complex_id = match.group(1)

    complex_data = None
    articles_data = None
    api_responses = []

    try:
        async def save_response(response):
            """API 응답 저장"""
            nonlocal complex_data, articles_data
            try:
                # 모든 API 응답 기록
                if '/api/' in response.url:
                    api_responses.append(f"{response.status} - {response.url}")

                # 단지 정보 API 응답 확인
                if '/api/complexes/overview/' in response.url and response.status == 200:
                    data = await response.json()
                    if data.get('complexNo') or data.get('complexName'):
                        complex_data = data
                        print(f"✅ 단지 정보 수집: {data.get('complexName', 'N/A')}")

                # 매물 정보 API 응답 확인
                if '/api/articles/complex/' in response.url and response.status == 200:
                    data = await response.json()
                    if isinstance(data, dict) and 'articleList' in data:
                        articles_data = data
                        count = len(data.get('articleList', []))
                        print(f"✅ 매물 정보 수집: {count}건")
            except Exception as e:
                print(f"❌ 응답 파싱 오류: {e}")

        # Playwright로 페이지 방문하여 API 응답 가로채기
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='ko-KR',
                timezone_id='Asia/Seoul'
            )

            # JavaScript로 webdriver 감지 차단
            await context.add_init_script('''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
            ''')

            page = await context.new_page()

            # 응답 리스너 등록
            page.on("response", lambda response: asyncio.create_task(save_response(response)))

            # 네이버 페이지 방문
            print(f"🌐 페이지 접속 중: {url}")
            await page.goto(url, timeout=30000)
            await asyncio.sleep(5)  # API 응답 대기

            await browser.close()

        print(f"📊 캡처된 API 응답 수: {len(api_responses)}")
        for resp in api_responses[:5]:  # 최대 5개만 로그
            print(f"  - {resp}")

        if not complex_data:
            raise HTTPException(
                status_code=404,
                detail=f"단지 정보를 가져올 수 없습니다. 캡처된 API: {len(api_responses)}개"
            )

        # 응답 데이터 매핑 (네이버 API 필드명에 맞춤)
        result = {
            'complex_id': str(complex_id),
            'complex_name': complex_data.get('complexName', ''),
            'complex_type': complex_data.get('complexTypeName', '아파트'),
            'total_households': complex_data.get('totalHouseHoldCount'),  # 대문자 H
            'total_dongs': complex_data.get('totalDongCount'),
            'latitude': complex_data.get('latitude'),
            'longitude': complex_data.get('longitude'),
        }

        # 준공일 포맷: YYYYMMDD -> YYYY-MM
        use_approve_ymd = complex_data.get('useApproveYmd')
        if use_approve_ymd and len(use_approve_ymd) >= 6:
            result['completion_date'] = f"{use_approve_ymd[:4]}-{use_approve_ymd[4:6]}"

        # 면적 정보 (API에서 직접 제공)
        result['min_area'] = complex_data.get('minArea')
        result['max_area'] = complex_data.get('maxArea')

        # 가격 정보 (만원 단위)
        result['min_price'] = complex_data.get('minPrice')
        result['max_price'] = complex_data.get('maxPrice')
        result['min_lease_price'] = complex_data.get('minLeasePrice')
        result['max_lease_price'] = complex_data.get('maxLeasePrice')

        # 매물 정보 추가
        result['articles'] = []
        if articles_data and 'articleList' in articles_data:
            result['articles'] = articles_data.get('articleList', [])
            result['article_count'] = len(result['articles'])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"크롤링 오류: {str(e)}")


@router.post("/crawl")
async def crawl_complex(request: CrawlRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    단지의 매물 정보 크롤링 (백그라운드 작업)

    - **complex_id**: 크롤링할 단지 ID
    - **collect_address**: 주소 수집 여부 (기본값: False)
    """
    # 단지가 존재하는지 확인
    complex = db.query(Complex).filter(Complex.complex_id == request.complex_id).first()
    if not complex:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 크롤링 상태 초기화
    crawling_status[request.complex_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat()
    }

    # 백그라운드에서 크롤링 실행 (변동 추적 활성화)
    background_tasks.add_task(run_crawler_with_status, request.complex_id, True, request.collect_address)

    return {
        "message": "크롤링이 시작되었습니다",
        "complex_id": request.complex_id,
        "complex_name": complex.complex_name,
        "collect_address": request.collect_address
    }


@router.post("/crawl/{complex_id}")
async def crawl_complex_by_id(complex_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    단지의 매물 정보 크롤링 (RESTful 경로 파라미터 버전)

    - **complex_id**: 크롤링할 단지 ID
    """
    # 단지가 존재하는지 확인
    complex = db.query(Complex).filter(Complex.complex_id == complex_id).first()
    if not complex:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 백그라운드에서 크롤링 실행 (변동 추적 활성화)
    background_tasks.add_task(run_crawler, complex_id, True)

    return {
        "message": "크롤링이 시작되었습니다",
        "complex_id": complex_id,
        "complex_name": complex.complex_name
    }


async def run_crawler(complex_id: str, create_snapshot: bool = True, collect_address: bool = False):
    """
    실제 크롤링 실행 (crawler_service 사용)

    Args:
        complex_id: 단지 ID
        create_snapshot: 스냅샷 생성 및 변동 감지 여부 (기본값 True)
        collect_address: 주소 수집 여부 (기본값 False)
    """
    import traceback
    from ..core.database import SessionLocal
    from ..services.crawler_service import NaverRealEstateCrawler

    print(f"   [SCRAPER] Starting run_crawler for complex {complex_id}")
    print(f"   [SCRAPER] Snapshot tracking: {'Enabled' if create_snapshot else 'Disabled'}")
    print(f"   [SCRAPER] Address collection: {'Enabled' if collect_address else 'Disabled'}")

    try:
        print(f"   [SCRAPER] Creating crawler instance...")
        crawler = NaverRealEstateCrawler()

        print(f"   [SCRAPER] Starting crawl_complex...")
        await crawler.crawl_complex(complex_id, collect_address=collect_address)

        print(f"   [SCRAPER] Saving to database...")
        crawler.save_to_database(complex_id)

        # 스냅샷 생성 및 변동사항 감지
        if create_snapshot:
            print(f"   [SCRAPER] Creating snapshot and detecting changes...")
            db = SessionLocal()
            try:
                tracker = ArticleTracker(db)

                # 현재 매물 조회
                articles = db.query(Article).filter(
                    Article.complex_id == complex_id,
                    Article.is_active == True
                ).all()

                # 스냅샷 생성
                tracker.create_snapshot(complex_id, articles)

                # 변동사항 감지
                tracker.detect_changes(complex_id)

            finally:
                db.close()

        print(f"✅ 크롤링 완료: {complex_id}")
    except Exception as e:
        print(f"❌ 크롤링 실패: {complex_id} - {e}")
        print(f"   [SCRAPER] Full traceback:")
        traceback.print_exc()


# 크롤링 상태 저장용 딕셔너리
crawling_status = {}


async def run_crawler_with_status(complex_id: str, create_snapshot: bool = True, collect_address: bool = False):
    """
    상태 업데이트를 포함한 크롤링 실행

    Args:
        complex_id: 단지 ID
        create_snapshot: 스냅샷 생성 및 변동 감지 여부 (기본값 True)
        collect_address: 주소 수집 여부 (기본값 False)
    """
    try:
        await run_crawler(complex_id, create_snapshot, collect_address)
        crawling_status[complex_id] = {
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }
    except Exception as e:
        crawling_status[complex_id] = {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }


@router.get("/crawl/{complex_id}/status")
def get_crawl_status(complex_id: str):
    """
    크롤링 상태 조회

    Args:
        complex_id: 단지 ID

    Returns:
        상태 정보 (running, completed, failed)
    """
    status = crawling_status.get(complex_id, {"status": "not_found"})
    return {
        "complex_id": complex_id,
        **status
    }


@router.post("/refresh/{complex_id}")
async def refresh_and_track(
    complex_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    매물 목록 새로고침 및 변동사항 추적

    - 크롤링 실행
    - 스냅샷 생성
    - 변동사항 자동 감지

    Args:
        complex_id: 단지 ID
    """
    # 단지가 존재하는지 확인
    complex = db.query(Complex).filter(Complex.complex_id == complex_id).first()
    if not complex:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 크롤링 상태 초기화
    crawling_status[complex_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat()
    }

    # 백그라운드에서 크롤링 + 스냅샷 생성 + 변동 감지 + 실거래가 조회 실행
    async def crawl_with_status_update():
        try:
            await run_crawler(complex_id, True)

            # 실거래가 조회 및 저장
            from ..core.database import SessionLocal
            from ..services.transaction_service import TransactionService

            db_local = SessionLocal()
            try:
                transaction_service = TransactionService(db_local)
                result = transaction_service.fetch_and_save_transactions(complex_id, months=6)
                print(f"✅ 실거래가 저장: {result.get('saved_count', 0)}건")
            except Exception as tx_error:
                print(f"⚠️ 실거래가 조회 실패 (무시): {tx_error}")
            finally:
                db_local.close()

            crawling_status[complex_id] = {
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            }
        except Exception as e:
            crawling_status[complex_id] = {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }

    background_tasks.add_task(crawl_with_status_update)

    return {
        "message": "매물 새로고침이 시작되었습니다. 완료 후 변동사항이 자동으로 감지됩니다.",
        "complex_id": complex_id,
        "complex_name": complex.complex_name
    }


@router.get("/refresh/{complex_id}/status")
def get_refresh_status(complex_id: str):
    """
    크롤링 상태 조회

    Args:
        complex_id: 단지 ID

    Returns:
        상태 정보 (running, completed, failed)
    """
    status = crawling_status.get(complex_id, {"status": "not_found"})
    return {
        "complex_id": complex_id,
        **status
    }


@router.get("/search-address")
async def search_address(complex_name: str = Query(..., description="단지명")):
    """
    네이버 검색으로 단지 주소 크롤링

    - **complex_name**: 검색할 단지명
    """
    try:
        from ..services.address_service import AddressService

        address_service = AddressService()
        address = await address_service._get_complex_address_async(complex_name)

        if address:
            return {
                "success": True,
                "complex_name": complex_name,
                "address": address
            }
        else:
            return {
                "success": False,
                "complex_name": complex_name,
                "address": None,
                "message": "주소를 찾을 수 없습니다"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주소 검색 오류: {str(e)}")
