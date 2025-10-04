"""
네이버 부동산 크롤러 - 완전판
단지 정보, 매물, 실거래가 모두 수집
"""
import asyncio
import json
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page


class NaverLandCrawler:
    """네이버 부동산 크롤러"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """브라우저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()

    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()

    async def crawl_complex(self, complex_id: str) -> Dict:
        """
        단지 전체 정보 크롤링

        Args:
            complex_id: 단지 ID

        Returns:
            {
                'complex': 단지 상세 정보,
                'articles': 매물 목록,
                'trades': 실거래가 목록
            }
        """
        print(f"\n{'='*80}")
        print(f"🏢 단지 크롤링: ID {complex_id}")
        print(f"{'='*80}")

        url = f"https://new.land.naver.com/complexes/{complex_id}"

        # API 응답 저장소
        captured = {
            'complex': None,
            'articles': None,
            'trades': None,
            'all_responses': []
        }

        # 응답 리스너
        async def save_response(response):
            if '/api/' in response.url and response.status == 200:
                try:
                    data = await response.json()
                    captured['all_responses'].append({
                        'url': response.url,
                        'data': data
                    })

                    # 단지 상세 정보
                    if f'complexes/{complex_id}?' in response.url and 'complexNo=' in response.url:
                        captured['complex'] = data
                        print(f"✅ 단지 정보: {data.get('complexName', 'Unknown')}")

                    # 매물 정보
                    elif f'{complex_id}?' in response.url and 'realEstateType=' in response.url:
                        captured['articles'] = data
                        article_count = len(data.get('articleList', []))
                        print(f"✅ 매물 정보: {article_count}건")

                    # 실거래가
                    elif 'real-trades' in response.url or 'trade' in response.url.lower():
                        captured['trades'] = data
                        print(f"✅ 실거래가 정보")

                except:
                    pass

        self.page.on("response", save_response)

        # 페이지 로드
        print(f"\n⏳ 페이지 로딩...")
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # 스크롤
        print(f"\n📜 스크롤...")
        for _ in range(2):
            await self.page.evaluate("window.scrollBy(0, 400)")
            await asyncio.sleep(0.5)

        # 탭 클릭 (실거래가 탭 등)
        print(f"\n🖱️  탭 클릭...")
        buttons = await self.page.query_selector_all("button, a, [role='tab']")

        clicked = 0
        for btn in buttons:
            if clicked >= 3:  # 최대 3개만
                break
            try:
                text = await btn.inner_text()
                # 실거래, 시세 등의 탭 클릭
                if text and any(kw in text for kw in ["실거래", "거래", "시세"]):
                    print(f"   클릭: {text.strip()}")
                    await btn.click()
                    await asyncio.sleep(2)
                    clicked += 1
            except:
                pass

        # 추가 대기
        await asyncio.sleep(1)

        print(f"\n{'='*80}")
        print(f"📊 수집 완료")
        print(f"{'='*80}")

        return {
            'complex_id': complex_id,
            'complex_detail': captured['complex'],
            'articles': captured['articles'],
            'trades': captured['trades'],
            'raw_responses': captured['all_responses']
        }

    def parse_complex_detail(self, data: Dict) -> Dict:
        """단지 상세 정보 파싱"""
        if not data:
            return None

        return {
            'complex_id': data.get('complexNo'),
            'name': data.get('complexName'),
            'type': data.get('complexTypeName'),
            'address': data.get('address'),
            'total_households': data.get('totalHouseHoldCount'),
            'total_dongs': data.get('totalDongCount'),
            'completion_date': data.get('useApproveYmd'),
            'min_area': data.get('minArea'),
            'max_area': data.get('maxArea'),
            'min_price': data.get('minPrice'),
            'max_price': data.get('maxPrice'),
            'min_lease_price': data.get('minLeasePrice'),
            'max_lease_price': data.get('maxLeasePrice'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'pyeongs': data.get('pyeongs', []),
            'dongs': data.get('dongs', [])
        }

    def parse_articles(self, data: Dict) -> List[Dict]:
        """매물 정보 파싱"""
        if not data or 'articleList' not in data:
            return []

        articles = []
        for article in data['articleList']:
            articles.append({
                'article_no': article.get('articleNo'),
                'trade_type': article.get('tradeTypeName'),
                'price': article.get('dealOrWarrantPrc'),
                'area_name': article.get('areaName'),
                'area1': article.get('area1'),
                'area2': article.get('area2'),
                'floor_info': article.get('floorInfo'),
                'direction': article.get('direction'),
                'confirm_date': article.get('articleConfirmYmd'),
                'building_name': article.get('buildingName'),
                'feature_desc': article.get('articleFeatureDesc'),
                'tags': article.get('tagList', []),
                'realtor_name': article.get('realtorName'),
                'latitude': article.get('latitude'),
                'longitude': article.get('longitude')
            })

        return articles

    def parse_trades(self, data: Dict) -> List[Dict]:
        """실거래가 정보 파싱"""
        if not data:
            return []

        trades = []
        trade_list = data.get('list', [])

        for trade in trade_list:
            trades.append({
                'deal_date': trade.get('dealDate'),
                'deal_price': trade.get('dealAmount'),
                'area': trade.get('area'),
                'floor': trade.get('floor'),
                'trade_type': trade.get('tradeTypeName')
            })

        return trades


async def test_crawler():
    """크롤러 테스트"""

    async with NaverLandCrawler(headless=False) as crawler:
        # 단지 크롤링
        result = await crawler.crawl_complex("109208")

        # 파싱
        complex_detail = crawler.parse_complex_detail(result['complex_detail'])
        articles = crawler.parse_articles(result['articles'])
        trades = crawler.parse_trades(result['trades'])

        # 결과 출력
        print(f"\n{'='*80}")
        print("📋 파싱 결과")
        print(f"{'='*80}")

        if complex_detail:
            print(f"\n🏢 단지 정보:")
            print(f"   이름: {complex_detail['name']}")
            print(f"   주소: {complex_detail.get('address', 'N/A')}")
            print(f"   세대수: {complex_detail['total_households']}")
            print(f"   준공: {complex_detail['completion_date']}")
            print(f"   가격대: {complex_detail['min_price']}만원 ~ {complex_detail['max_price']}만원")

        print(f"\n💰 매물: {len(articles)}건")
        for i, art in enumerate(articles[:5], 1):
            print(f"   {i}. {art['price']} / {art['area_name']} / {art['floor_info']} / {art['direction']}")

        print(f"\n📊 실거래: {len(trades)}건")
        for i, trade in enumerate(trades[:5], 1):
            print(f"   {i}. {trade.get('deal_date', 'N/A')} / {trade.get('deal_price', 'N/A')}만원")

        # 파일 저장
        output = {
            'complex': complex_detail,
            'articles': articles,
            'trades': trades
        }

        with open('crawled_data.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n💾 저장: crawled_data.json")
        print(f"\n✅ 완료!")


if __name__ == "__main__":
    asyncio.run(test_crawler())
