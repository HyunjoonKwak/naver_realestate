"""
네이버 부동산 API 분석 스크립트
실제 네트워크 요청을 캡처하여 API 구조를 파악합니다.
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def analyze_naver_land_api():
    """네이버 부동산 API 요청 분석"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 브라우저 보이게
        context = await browser.new_context()
        page = await context.new_page()

        # 모든 네트워크 요청을 캡처
        api_requests = []

        async def handle_request(route, request):
            """네트워크 요청 핸들러"""
            url = request.url

            # API 요청만 필터링
            if 'api' in url or 'land.naver.com' in url:
                api_requests.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                })
                print(f"📡 API 요청: {request.method} {url}")

            await route.continue_()

        # 모든 요청을 가로채기
        await page.route('**/*', handle_request)

        print("=" * 80)
        print("🔍 네이버 부동산 API 분석 시작")
        print("=" * 80)

        # 1. 메인 페이지 접속
        print("\n1️⃣  메인 페이지 접속...")
        await page.goto("https://new.land.naver.com/complexes", wait_until="networkidle")
        await asyncio.sleep(3)

        # 2. 검색 테스트
        print("\n2️⃣  단지 검색 테스트 (래미안)...")

        # 검색창 찾기
        search_selectors = [
            'input[placeholder*="검색"]',
            'input[type="text"]',
            '.search_input',
            '#search-input',
        ]

        search_input = None
        for selector in search_selectors:
            search_input = await page.query_selector(selector)
            if search_input:
                print(f"✅ 검색창 발견: {selector}")
                break

        if search_input:
            await search_input.click()
            await search_input.fill("래미안")
            await asyncio.sleep(2)

            # Enter 키 누르기
            await search_input.press("Enter")
            await asyncio.sleep(3)
        else:
            print("⚠️  검색창을 찾을 수 없습니다.")
            # 페이지 HTML 일부 출력
            html = await page.content()
            print(f"페이지 길이: {len(html)} 문자")

        # 3. 특정 단지 페이지 직접 접속 (예시)
        print("\n3️⃣  특정 단지 페이지 접속...")

        # 래미안 강촌센트럴파크 예시 (단지 ID는 임의)
        # 실제 단지 ID를 찾으려면 검색 결과에서 클릭해야 함
        # await page.goto("https://new.land.naver.com/complexes/12345", wait_until="networkidle")
        # await asyncio.sleep(3)

        # 4. 수집된 API 요청 분석
        print("\n" + "=" * 80)
        print("📊 수집된 API 요청 분석")
        print("=" * 80)

        if api_requests:
            # API 요청을 파일로 저장
            with open("api_requests.json", "w", encoding="utf-8") as f:
                json.dump(api_requests, f, ensure_ascii=False, indent=2)

            print(f"\n✅ 총 {len(api_requests)}개의 API 요청 발견")
            print("\n주요 API 엔드포인트:")

            unique_urls = set()
            for req in api_requests:
                # Query string 제거하고 기본 URL만 추출
                base_url = req['url'].split('?')[0]
                unique_urls.add(base_url)

            for url in sorted(unique_urls):
                print(f"  - {url}")

            print(f"\n📄 상세 내용은 api_requests.json 파일에 저장되었습니다.")
        else:
            print("⚠️  API 요청이 캡처되지 않았습니다.")

        # 5. 페이지 구조 분석
        print("\n" + "=" * 80)
        print("🏗️  페이지 구조 분석")
        print("=" * 80)

        # 주요 요소들 찾기
        elements_to_check = [
            ('검색 결과 아이템', '.complex_item, .item, [class*="complex"], [class*="item"]'),
            ('매물 리스트', '.article_list, [class*="article"], [class*="listing"]'),
            ('가격 정보', '[class*="price"], .price'),
            ('단지명', '.complex_title, [class*="title"]'),
        ]

        for name, selector in elements_to_check:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"✅ {name} 발견: {len(elements)}개 ({selector})")
            else:
                print(f"❌ {name} 없음 ({selector})")

        # 브라우저 종료 전 대기 (수동으로 페이지 확인 가능)
        print("\n" + "=" * 80)
        print("⏸️  브라우저를 10초간 열어둡니다. 페이지를 확인하세요.")
        print("=" * 80)
        await asyncio.sleep(10)

        await browser.close()

        print("\n✅ 분석 완료!")


if __name__ == "__main__":
    asyncio.run(analyze_naver_land_api())
