"""
쿠키 및 헤더 설정 후 크롤링
Bot 탐지를 우회하기 위한 설정 추가
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def crawl_with_proper_setup():
    """제대로 설정된 브라우저로 크롤링"""

    async with async_playwright() as p:
        # 실제 브라우저처럼 보이도록 설정
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        # Context 생성 (User-Agent 등 설정)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )

        # WebDriver 탐지 우회
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()

        print("=" * 80)
        print("🏢 네이버 부동산 크롤링 (Bot 탐지 우회)")
        print("=" * 80)

        target_url = "https://new.land.naver.com/complexes/109208"

        print(f"\n📍 URL: {target_url}")

        captured_data = []

        # Route 설정
        async def handle_route(route):
            request = route.request
            req_url = request.url

            response = await route.fetch()

            if '/api/' in req_url:
                try:
                    body_bytes = await response.body()
                    body_text = body_bytes.decode('utf-8')
                    data = json.loads(body_text)

                    print(f"\n✅ API 캡처: {req_url.split('/')[-1][:50]}")

                    captured_data.append({
                        'url': req_url,
                        'data': data
                    })

                    # 저장
                    filename = f"api_{len(captured_data)}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    # 데이터 타입 확인
                    if isinstance(data, dict):
                        if 'complexName' in data:
                            print(f"   🏢 단지: {data['complexName']}")
                        if 'articleList' in data:
                            print(f"   💰 매물: {len(data['articleList'])}건")
                        print(f"   🔑 키: {list(data.keys())[:5]}")

                except:
                    pass

            await route.fulfill(response=response)

        await page.route("**/*", handle_route)

        # 먼저 메인 페이지 방문 (쿠키 획득)
        print("\n1️⃣  메인 페이지 방문 (쿠키 획득)...")
        await page.goto("https://new.land.naver.com/", wait_until="networkidle")
        await asyncio.sleep(3)

        # 쿠키 확인
        cookies = await context.cookies()
        print(f"   ✅ 쿠키 획득: {len(cookies)}개")

        # 이제 실제 단지 페이지 방문
        print(f"\n2️⃣  단지 페이지 방문...")
        await page.goto(target_url, wait_until="networkidle")
        await asyncio.sleep(5)

        # 페이지 내용 확인
        text = await page.evaluate('() => document.body.innerText')
        print(f"\n📄 페이지 내용 (처음 300자):")
        print(text[:300])

        # 404인지 확인
        if "찾을 수 없습니다" in text or "404" in text:
            print("\n⚠️  404 페이지입니다!")
            print("   URL을 다시 확인해주세요.")
            print("\n💡 해결 방법:")
            print("   1. 브라우저에서 직접 네이버 부동산 접속")
            print("   2. 단지를 검색하여 찾기")
            print("   3. 단지 페이지 URL 복사")
            print("   4. 복사한 URL 제공")
        else:
            print("\n✅ 페이지 로드 성공!")

            # 스크롤 및 탭 클릭
            print("\n3️⃣  추가 데이터 로드...")

            # 스크롤
            for i in range(5):
                await page.evaluate('window.scrollBy(0, 300)')
                await asyncio.sleep(1)

            # 탭 클릭
            buttons = await page.query_selector_all('button, [role="tab"], a')
            for btn in buttons[:30]:
                try:
                    text = await btn.inner_text()
                    if text and any(kw in text for kw in ['매물', '시세', '실거래', '거래', '정보']):
                        print(f"   🖱️  '{text.strip()}' 클릭...")
                        await btn.click()
                        await asyncio.sleep(3)
                except:
                    pass

        # 스크린샷
        await page.screenshot(path="final_page.png", full_page=True)
        print("\n📸 스크린샷: final_page.png")

        # 대기
        print("\n⏸️  60초 대기 (수동 조작 가능)...")
        await asyncio.sleep(60)

        await browser.close()

        # 결과
        print("\n" + "=" * 80)
        print("📊 결과")
        print("=" * 80)

        if captured_data:
            print(f"\n✅ {len(captured_data)}개 API 응답 캡처!")

            with open("all_captured.json", "w", encoding='utf-8') as f:
                json.dump(captured_data, f, ensure_ascii=False, indent=2)

            for i, item in enumerate(captured_data, 1):
                print(f"\n{i}. {item['url'].split('/')[-1][:50]}")
                data = item['data']
                if isinstance(data, dict):
                    print(f"   키: {list(data.keys())[:10]}")
        else:
            print("\n❌ 캡처 실패")

        print("\n✅ 완료!")


if __name__ == "__main__":
    asyncio.run(crawl_with_proper_setup())
