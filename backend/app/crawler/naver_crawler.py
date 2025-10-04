"""
네이버 부동산 크롤러
Playwright를 사용하여 네이버 부동산 데이터를 수집합니다.
"""
import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, BrowserContext
from datetime import datetime


class NaverRealEstateCrawler:
    """네이버 부동산 크롤러 클래스"""

    def __init__(self, headless: bool = True):
        """
        Args:
            headless: 브라우저를 백그라운드에서 실행할지 여부
        """
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.authorization_token = None
        self.cookies = {}

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()

    async def initialize(self):
        """브라우저 초기화 및 토큰 획득"""
        print("🚀 브라우저 초기화 중...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()

        # Authorization 토큰 캡처
        await self._capture_auth_token()

    async def _capture_auth_token(self):
        """네이버 부동산 페이지에서 Authorization 토큰 캡처"""
        print("🔑 Authorization 토큰 획득 중...")

        token_captured = asyncio.Event()

        async def handle_request(route, request):
            """네트워크 요청에서 토큰 캡처"""
            auth = request.headers.get("authorization")
            if auth and auth.startswith("Bearer "):
                self.authorization_token = auth
                print(f"✅ 토큰 획득 성공: {auth[:50]}...")
                token_captured.set()

            await route.continue_()

        await self.page.route("**/*", handle_request)

        # 페이지 로드하여 토큰 획득
        await self.page.goto("https://new.land.naver.com/complexes", wait_until="networkidle")
        await asyncio.sleep(2)

        # 토큰 획득 대기 (최대 5초)
        try:
            await asyncio.wait_for(token_captured.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            print("⚠️  토큰 획득 실패. 일부 API 요청이 작동하지 않을 수 있습니다.")

        # 쿠키 저장
        cookies = await self.context.cookies()
        for cookie in cookies:
            self.cookies[cookie['name']] = cookie['value']

        print(f"✅ 쿠키 {len(self.cookies)}개 수집 완료")

    async def search_complexes(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        단지 검색

        Args:
            keyword: 검색 키워드 (예: "래미안", "아크로")
            limit: 최대 검색 결과 수

        Returns:
            단지 정보 리스트
        """
        print(f"\n🔍 '{keyword}' 검색 중...")

        # 검색 페이지로 이동
        search_url = f"https://new.land.naver.com/search?sk={keyword}"
        await self.page.goto(search_url, wait_until="networkidle")
        await asyncio.sleep(2)

        # JavaScript로 검색 결과 추출
        complexes = await self.page.evaluate('''
            () => {
                const results = [];
                // 검색 결과 아이템 찾기 (실제 selector는 페이지 구조에 따라 다를 수 있음)
                const items = document.querySelectorAll('[class*="item"], [class*="complex"]');

                items.forEach((item, index) => {
                    if (index >= 10) return; // 최대 10개

                    const titleEl = item.querySelector('[class*="title"], [class*="name"]');
                    const addressEl = item.querySelector('[class*="address"], [class*="location"]');
                    const linkEl = item.querySelector('a[href*="/complexes/"]');

                    if (titleEl && linkEl) {
                        const href = linkEl.getAttribute('href');
                        const match = href.match(/complexes\\/(\\d+)/);

                        results.push({
                            id: match ? match[1] : null,
                            name: titleEl.textContent.trim(),
                            address: addressEl ? addressEl.textContent.trim() : '',
                            url: 'https://new.land.naver.com' + href
                        });
                    }
                });

                return results;
            }
        ''')

        if not complexes:
            print(f"⚠️  '{keyword}' 검색 결과가 없습니다.")
            print("🔄 대체 방법: API 직접 호출을 시도합니다...")
            # TODO: API 직접 호출 구현

        print(f"✅ {len(complexes)}개의 단지를 찾았습니다.")
        return complexes[:limit]

    async def get_complex_detail(self, complex_id: str) -> Dict:
        """
        단지 상세 정보 조회

        Args:
            complex_id: 단지 ID

        Returns:
            단지 상세 정보
        """
        print(f"\n🏢 단지 ID {complex_id} 상세 정보 조회 중...")

        url = f"https://new.land.naver.com/complexes/{complex_id}"
        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)

        # 단지 정보 추출
        detail = await self.page.evaluate('''
            () => {
                return {
                    name: document.querySelector('[class*="complex_title"], h1')?.textContent?.trim() || '',
                    address: document.querySelector('[class*="address"]')?.textContent?.trim() || '',
                    completion_year: document.querySelector('[class*="year"]')?.textContent?.trim() || '',
                    total_households: document.querySelector('[class*="household"]')?.textContent?.trim() || '',
                };
            }
        ''')

        detail['id'] = complex_id
        detail['url'] = url

        print(f"✅ 단지 정보: {detail.get('name', 'Unknown')}")
        return detail

    async def get_listings(self, complex_id: str, trade_type: str = "매매") -> List[Dict]:
        """
        매물 정보 조회

        Args:
            complex_id: 단지 ID
            trade_type: 거래 유형 (매매, 전세, 월세)

        Returns:
            매물 정보 리스트
        """
        print(f"\n💰 단지 ID {complex_id}의 {trade_type} 매물 조회 중...")

        url = f"https://new.land.naver.com/complexes/{complex_id}"
        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)

        # 매물 탭 클릭 (trade_type에 따라)
        # TODO: 실제 탭 selector 찾아서 클릭

        # 매물 목록 추출
        listings = await self.page.evaluate('''
            () => {
                const results = [];
                const items = document.querySelectorAll('[class*="article"], [class*="listing"]');

                items.forEach(item => {
                    const priceEl = item.querySelector('[class*="price"]');
                    const areaEl = item.querySelector('[class*="area"]');
                    const floorEl = item.querySelector('[class*="floor"]');

                    if (priceEl) {
                        results.push({
                            price: priceEl.textContent.trim(),
                            area: areaEl ? areaEl.textContent.trim() : '',
                            floor: floorEl ? floorEl.textContent.trim() : '',
                        });
                    }
                });

                return results;
            }
        ''')

        print(f"✅ {len(listings)}개의 매물을 찾았습니다.")
        return listings

    async def get_transactions(self, complex_id: str) -> List[Dict]:
        """
        실거래가 정보 조회

        Args:
            complex_id: 단지 ID

        Returns:
            실거래가 정보 리스트
        """
        print(f"\n📊 단지 ID {complex_id}의 실거래가 조회 중...")

        url = f"https://new.land.naver.com/complexes/{complex_id}?tab=transaction"
        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)

        # 실거래가 데이터 추출
        transactions = await self.page.evaluate('''
            () => {
                const results = [];
                const items = document.querySelectorAll('[class*="transaction"], [class*="deal"]');

                items.forEach(item => {
                    const dateEl = item.querySelector('[class*="date"]');
                    const priceEl = item.querySelector('[class*="price"]');
                    const areaEl = item.querySelector('[class*="area"]');
                    const floorEl = item.querySelector('[class*="floor"]');

                    if (dateEl && priceEl) {
                        results.push({
                            date: dateEl.textContent.trim(),
                            price: priceEl.textContent.trim(),
                            area: areaEl ? areaEl.textContent.trim() : '',
                            floor: floorEl ? floorEl.textContent.trim() : '',
                        });
                    }
                });

                return results;
            }
        ''')

        print(f"✅ {len(transactions)}개의 실거래 내역을 찾았습니다.")
        return transactions

    async def take_screenshot(self, filename: str = "screenshot.png"):
        """스크린샷 저장 (디버깅용)"""
        if self.page:
            await self.page.screenshot(path=filename)
            print(f"📸 스크린샷 저장: {filename}")

    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("\n✅ 브라우저 종료")


# ========== 유틸리티 함수 ==========

def parse_price(price_str: str) -> Optional[int]:
    """
    가격 문자열을 숫자로 변환
    예: "3억 2,000" -> 320000000
    """
    if not price_str:
        return None

    # "억" 단위 처리
    price_str = price_str.replace(",", "").replace(" ", "")

    match = re.search(r'(\\d+)억', price_str)
    if match:
        eok = int(match.group(1)) * 100000000
        # 만 단위 추가
        match_man = re.search(r'억(\\d+)', price_str)
        if match_man:
            man = int(match_man.group(1)) * 10000
            return eok + man
        return eok

    # 순수 숫자만
    match = re.search(r'(\\d+)', price_str)
    if match:
        return int(match.group(1))

    return None


def parse_area(area_str: str) -> Optional[float]:
    """
    면적 문자열을 숫자로 변환
    예: "84.52㎡" -> 84.52
    """
    if not area_str:
        return None

    match = re.search(r'([0-9.]+)', area_str)
    if match:
        return float(match.group(1))

    return None
