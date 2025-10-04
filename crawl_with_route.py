"""
네이버 부동산 크롤링 - Route 방식
Request/Response를 가로채서 데이터 추출
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def crawl_with_route(url: str):
    """Route를 사용한 API 응답 캡처"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 80)
        print("🕵️  네이버 부동산 크롤링 (Route 방식)")
        print("=" * 80)
        print(f"\n📍 URL: {url}")

        captured_data = []

        # Route로 요청/응답 가로채기
        async def handle_route(route):
            """모든 요청을 가로채서 응답 캡처"""
            request = route.request
            req_url = request.url

            # 요청 계속 진행
            response = await route.fetch()

            # API 응답 확인
            if '/api/' in req_url and response.status == 200:
                try:
                    body_bytes = await response.body()
                    body_text = body_bytes.decode('utf-8')

                    # JSON 파싱 시도
                    try:
                        data = json.loads(body_text)

                        print(f"\n✅ API 캡처!")
                        print(f"   URL: {req_url.split('?')[0]}")
                        print(f"   Method: {request.method}")

                        captured_data.append({
                            'url': req_url,
                            'method': request.method,
                            'status': response.status,
                            'data': data
                        })

                        # 파일명 결정
                        if 'complexes/' in req_url and req_url.split('/')[-1].split('?')[0].isdigit():
                            filename = 'api_complex_detail.json'
                            print(f"   📦 타입: 단지 상세")
                        elif 'article' in req_url.lower():
                            filename = 'api_articles.json'
                            print(f"   📦 타입: 매물")
                        elif 'price' in req_url.lower() or 'pyoung' in req_url.lower():
                            filename = 'api_prices.json'
                            print(f"   📦 타입: 가격")
                        elif 'trade' in req_url.lower():
                            filename = 'api_trades.json'
                            print(f"   📦 타입: 실거래")
                        else:
                            parts = req_url.split('/')
                            filename = f"api_{parts[-1][:30].replace('?', '_')}.json"
                            print(f"   📦 타입: 기타")

                        # 저장
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"   💾 저장: {filename}")

                        # 키 출력
                        if isinstance(data, dict):
                            keys = list(data.keys())[:10]
                            print(f"   🔑 키: {keys}")
                        elif isinstance(data, list):
                            print(f"   📊 배열 길이: {len(data)}")

                    except json.JSONDecodeError:
                        # JSON이 아닌 응답
                        pass

                except Exception as e:
                    print(f"   ⚠️  에러: {e}")

            # 응답 전달
            await route.fulfill(response=response)

        # 모든 요청에 대해 route 설정
        await page.route("**/*", handle_route)

        # 페이지 로드
        print("\n⏳ 페이지 로딩...")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)

        # 스크롤
        print("\n📜 스크롤...")
        for i in range(3):
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(1)

        # 모든 클릭 가능한 요소 찾기
        print("\n🖱️  클릭 가능한 요소 찾기...")
        clickables = await page.query_selector_all('a, button, [role="tab"], [role="button"]')
        print(f"   발견: {len(clickables)}개")

        # 텍스트 기반으로 탭 클릭
        keywords = ['매물', '시세', '실거래', '거래', '정보', '단지']

        for elem in clickables[:30]:
            try:
                text = await elem.inner_text()
                if text and any(kw in text for kw in keywords):
                    print(f"\n   🖱️  '{text.strip()[:20]}' 클릭...")
                    await elem.click()
                    await asyncio.sleep(2)
            except:
                pass

        # 스크린샷
        await page.screenshot(path="crawled_page.png", full_page=True)
        print("\n📸 스크린샷: crawled_page.png")

        # 대기
        print("\n⏸️  30초 대기... (수동으로 탭을 클릭해보세요!)")
        await asyncio.sleep(30)

        await browser.close()

        # 결과
        print("\n" + "=" * 80)
        print("📊 결과")
        print("=" * 80)

        if captured_data:
            print(f"\n✅ {len(captured_data)}개의 API 응답 캡처!")

            # 전체 저장
            with open("all_captured.json", "w", encoding='utf-8') as f:
                json.dump(captured_data, f, ensure_ascii=False, indent=2)
            print("💾 전체: all_captured.json")

            # 데이터 분석
            print("\n📋 캡처된 데이터:")
            for item in captured_data:
                url_short = item['url'].split('/')[-1].split('?')[0]
                print(f"   - {item['method']} {url_short}")

                data = item['data']

                # 단지 정보
                if isinstance(data, dict):
                    if 'complexName' in data:
                        print(f"      단지: {data['complexName']}")
                    if 'address' in data:
                        print(f"      주소: {data['address']}")
                    if 'articleList' in data:
                        print(f"      매물: {len(data['articleList'])}건")
                    if 'priceList' in data or 'pyoungList' in data:
                        print(f"      가격정보 있음")

        else:
            print("\n❌ 캡처 실패")

        print("\n✅ 완료!")


if __name__ == "__main__":
    target_url = "https://new.land.naver.com/complexes/678?ms=37.5279559,126.895385,19&a=APT:PRE:ABYG:JGC&e=RETAIL"
    asyncio.run(crawl_with_route(target_url))
