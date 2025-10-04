"""
실제 단지 크롤링
단지 ID: 109208
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def crawl_complex():
    """실제 단지 크롤링"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 80)
        print("🏢 네이버 부동산 크롤링 - 실제 단지")
        print("=" * 80)

        target_url = "https://new.land.naver.com/complexes/109208?ms=37.19921,127.1134283,19&a=APT:PRE:ABYG:JGC&e=RETAIL"

        print(f"\n📍 단지 ID: 109208")
        print(f"📍 URL: {target_url}")

        captured_data = []

        # Route로 API 응답 캡처
        async def handle_route(route):
            request = route.request
            req_url = request.url

            # 요청 진행
            response = await route.fetch()

            # API 응답 캡처
            if '/api/' in req_url:
                try:
                    body_bytes = await response.body()
                    body_text = body_bytes.decode('utf-8')

                    # JSON 파싱
                    data = json.loads(body_text)

                    print(f"\n✅ API 캡처!")
                    print(f"   URL: {req_url}")
                    print(f"   Status: {response.status}")

                    captured_data.append({
                        'url': req_url,
                        'status': response.status,
                        'data': data
                    })

                    # 파일 저장
                    if 'complexes/109208' in req_url:
                        filename = 'complex_109208_detail.json'
                        print(f"   📦 타입: 단지 상세 정보")
                    elif 'article' in req_url.lower():
                        filename = 'complex_109208_articles.json'
                        print(f"   📦 타입: 매물 정보")
                    elif 'price' in req_url.lower() or 'pyoung' in req_url.lower():
                        filename = 'complex_109208_prices.json'
                        print(f"   📦 타입: 가격 정보")
                    elif 'trade' in req_url.lower() or 'real' in req_url.lower():
                        filename = 'complex_109208_trades.json'
                        print(f"   📦 타입: 실거래가")
                    else:
                        filename = f"complex_109208_{len(captured_data)}.json"
                        print(f"   📦 타입: 기타")

                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"   💾 저장: {filename}")

                    # 데이터 미리보기
                    if isinstance(data, dict):
                        print(f"   🔑 키: {list(data.keys())[:10]}")
                    elif isinstance(data, list):
                        print(f"   📊 배열 길이: {len(data)}")

                except:
                    pass

            # 응답 전달
            await route.fulfill(response=response)

        await page.route("**/*", handle_route)

        # 페이지 로드
        print("\n⏳ 페이지 로딩...")
        await page.goto(target_url, wait_until="networkidle")
        await asyncio.sleep(5)

        # 페이지 텍스트 확인
        text = await page.evaluate('() => document.body.innerText')
        print(f"\n📄 페이지 텍스트 (처음 200자):")
        print(text[:200])

        # 스크롤
        print("\n📜 스크롤로 추가 데이터 로드...")
        for i in range(3):
            await page.evaluate('window.scrollBy(0, 500)')
            await asyncio.sleep(1)

        # 클릭 가능한 요소 찾기
        print("\n🖱️  탭/버튼 찾기...")
        clickables = await page.query_selector_all('a, button, [role="tab"]')
        print(f"   발견: {len(clickables)}개")

        # 주요 탭 클릭
        keywords = ['매물', '시세', '실거래', '거래', '단지정보', '정보']
        for elem in clickables:
            try:
                text = await elem.inner_text()
                if text and any(kw in text for kw in keywords):
                    print(f"\n   🖱️  '{text.strip()}' 클릭...")
                    await elem.click()
                    await asyncio.sleep(3)  # API 응답 대기
            except:
                pass

        # 스크린샷
        await page.screenshot(path="complex_109208_screenshot.png", full_page=True)
        print("\n📸 스크린샷: complex_109208_screenshot.png")

        # 추가 대기
        print("\n⏸️  브라우저를 60초간 열어둡니다.")
        print("   수동으로 탭을 클릭하고 데이터를 확인해보세요!")
        await asyncio.sleep(60)

        await browser.close()

        # 결과 출력
        print("\n" + "=" * 80)
        print("📊 크롤링 결과")
        print("=" * 80)

        if captured_data:
            print(f"\n✅ 성공! {len(captured_data)}개의 API 응답을 캡처했습니다!")

            # 전체 저장
            with open("complex_109208_all_data.json", "w", encoding='utf-8') as f:
                json.dump(captured_data, f, ensure_ascii=False, indent=2)
            print("💾 전체 데이터: complex_109208_all_data.json")

            # 각 데이터 분석
            print("\n📋 캡처된 데이터 분석:")
            for i, item in enumerate(captured_data, 1):
                print(f"\n{i}. {item['url'].split('/')[-1].split('?')[0]}")
                data = item['data']

                if isinstance(data, dict):
                    # 단지 정보
                    if 'complexName' in data:
                        print(f"   ✅ 단지명: {data['complexName']}")
                        print(f"   ✅ 주소: {data.get('address', 'N/A')}")
                        print(f"   ✅ 세대수: {data.get('totalHouseholdCount', 'N/A')}")
                        print(f"   ✅ 준공: {data.get('useApproveYmd', 'N/A')}")

                    # 매물
                    if 'articleList' in data:
                        articles = data['articleList']
                        print(f"   ✅ 매물: {len(articles)}건")
                        for j, art in enumerate(articles[:3], 1):
                            print(f"      {j}. {art.get('dealOrWarrantPrc', 'N/A')} / "
                                  f"{art.get('area1', 'N/A')}㎡ / {art.get('floorInfo', 'N/A')}")

                    # 실거래가
                    if 'list' in data and isinstance(data['list'], list):
                        trades = data['list']
                        print(f"   ✅ 실거래: {len(trades)}건")
                        for j, t in enumerate(trades[:3], 1):
                            print(f"      {j}. {t.get('dealAmount', t.get('price', 'N/A'))} / "
                                  f"{t.get('dealDate', 'N/A')}")

        else:
            print("\n❌ API 응답을 캡처하지 못했습니다.")
            print("   페이지가 404인지 확인하세요.")

        print("\n✅ 크롤링 완료!")


if __name__ == "__main__":
    asyncio.run(crawl_complex())
