"""
네이버 부동산 네트워크 탭 기반 크롤링
특정 URL의 API 응답을 캡처하여 데이터 추출
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def crawl_complex_with_network(url: str):
    """네트워크 요청/응답을 캡처하여 부동산 정보 추출"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("=" * 80)
        print("🕵️  네이버 부동산 네트워크 기반 크롤링")
        print("=" * 80)
        print(f"\n📍 URL: {url}")

        # 캡처된 데이터 저장소
        captured_responses = []

        # 네트워크 응답 캡처
        async def handle_response(response):
            """모든 API 응답 캡처"""
            req_url = response.url

            # API 응답만 필터링
            if '/api/' in req_url:
                try:
                    # JSON 응답인지 확인
                    content_type = response.headers.get('content-type', '')

                    if 'application/json' in content_type or response.status == 200:
                        # body를 텍스트로 먼저 가져오기
                        body = await response.body()
                        text = body.decode('utf-8')
                        data = json.loads(text)

                        captured_responses.append({
                            'url': req_url,
                            'status': response.status,
                            'data': data
                        })

                        print(f"\n✅ API 응답 캡처!")
                        print(f"   URL: {req_url}")
                        print(f"   Status: {response.status}")
                        print(f"   크기: {len(str(data))} bytes")

                        # URL 패턴별로 파일 저장
                        filename = None
                        if 'complex' in req_url and req_url.split('/')[-1].isdigit():
                            filename = 'complex_detail.json'
                            print(f"   📦 타입: 단지 상세 정보")
                        elif 'articles' in req_url or 'article' in req_url:
                            filename = 'complex_articles.json'
                            print(f"   📦 타입: 매물 정보")
                        elif 'price' in req_url or 'pyoung' in req_url:
                            filename = 'complex_prices.json'
                            print(f"   📦 타입: 가격 정보")
                        elif 'trade' in req_url or 'real-trade' in req_url:
                            filename = 'complex_transactions.json'
                            print(f"   📦 타입: 실거래가")
                        else:
                            # URL에서 마지막 부분 추출
                            parts = req_url.split('/')
                            filename = f"api_{parts[-1].replace('?', '_')[:30]}.json"
                            print(f"   📦 타입: 기타 API")

                        # 파일 저장
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"   💾 저장: {filename}")

                        # 데이터 미리보기
                        if isinstance(data, dict):
                            print(f"   🔑 키: {list(data.keys())[:10]}")
                        elif isinstance(data, list) and len(data) > 0:
                            print(f"   📊 배열 길이: {len(data)}")
                            if isinstance(data[0], dict):
                                print(f"   🔑 첫 항목 키: {list(data[0].keys())[:10]}")

                except Exception as e:
                    print(f"   ⚠️  JSON 파싱 에러: {e}")

        # 응답 리스너 등록
        page.on("response", handle_response)

        # 페이지 로드
        print("\n⏳ 페이지 로딩 중...")
        await page.goto(url, wait_until="networkidle")

        # 추가 대기 (지연 로딩 API 대비)
        print("\n⏳ 추가 데이터 로딩 대기 중...")
        await asyncio.sleep(5)

        # 페이지 스크롤 (추가 데이터 로드)
        print("\n📜 페이지 스크롤 (추가 데이터 로드)...")
        await page.evaluate('''
            async () => {
                // 천천히 스크롤
                for (let i = 0; i < 3; i++) {
                    window.scrollBy(0, 500);
                    await new Promise(r => setTimeout(r, 1000));
                }
            }
        ''')

        await asyncio.sleep(3)

        # 탭 클릭 시도 (매물, 시세, 실거래가 등)
        print("\n🖱️  페이지 내 탭 클릭 시도...")

        # 모든 버튼/탭 찾기
        buttons = await page.query_selector_all('button, [role="tab"], a[href*="#"]')
        print(f"   발견된 버튼/탭: {len(buttons)}개")

        # 주요 탭들 클릭
        tab_keywords = ['매물', '시세', '실거래가', '거래', '단지정보']

        for button in buttons[:20]:  # 최대 20개만 확인
            try:
                text = await button.text_content()
                if text and any(keyword in text for keyword in tab_keywords):
                    print(f"\n   🖱️  '{text.strip()}' 탭 클릭...")
                    await button.click()
                    await asyncio.sleep(2)  # API 응답 대기
            except:
                pass

        # 스크린샷
        print("\n📸 스크린샷 저장...")
        await page.screenshot(path="complex_page_screenshot.png", full_page=True)

        # 최종 대기
        print("\n⏸️  브라우저를 30초간 열어둡니다. 수동으로 탭을 클릭해보세요!")
        await asyncio.sleep(30)

        await browser.close()

        # 결과 정리
        print("\n" + "=" * 80)
        print("📊 크롤링 결과 요약")
        print("=" * 80)

        if captured_responses:
            print(f"\n✅ 총 {len(captured_responses)}개의 API 응답을 캡처했습니다!")

            # 전체 데이터 저장
            with open("all_api_responses.json", "w", encoding="utf-8") as f:
                json.dump(captured_responses, f, ensure_ascii=False, indent=2)
            print(f"💾 전체 응답: all_api_responses.json")

            # 응답별 요약
            print("\n📋 캡처된 API 목록:")
            for i, resp in enumerate(captured_responses, 1):
                url_short = resp['url'].split('?')[0].split('/')[-1]
                print(f"   {i}. {url_short} (Status: {resp['status']})")

            # 데이터 파싱 및 출력
            print("\n" + "=" * 80)
            print("🏢 추출된 부동산 정보")
            print("=" * 80)

            for resp in captured_responses:
                data = resp['data']

                # 단지 상세 정보
                if isinstance(data, dict):
                    if 'complexName' in data or 'complexDetail' in data:
                        print("\n📍 단지 정보:")
                        print(f"   단지명: {data.get('complexName', 'N/A')}")
                        print(f"   주소: {data.get('address', data.get('roadAddress', 'N/A'))}")
                        print(f"   세대수: {data.get('totalHouseholdCount', 'N/A')}")
                        print(f"   준공년도: {data.get('useApproveYmd', 'N/A')}")

                    # 매물 정보
                    if 'articleList' in data:
                        articles = data['articleList']
                        print(f"\n💰 매물 정보: {len(articles)}건")
                        for article in articles[:5]:  # 최대 5개
                            print(f"   - {article.get('dealOrWarrantPrc', 'N/A')} / "
                                  f"{article.get('area1', 'N/A')}㎡ / "
                                  f"{article.get('floor', 'N/A')}층")

                    # 실거래가
                    if 'realTradePriceList' in data or 'tradeList' in data:
                        trades = data.get('realTradePriceList', data.get('tradeList', []))
                        print(f"\n📊 실거래가: {len(trades)}건")
                        for trade in trades[:5]:
                            print(f"   - {trade.get('dealPrice', trade.get('price', 'N/A'))} / "
                                  f"{trade.get('dealDate', trade.get('date', 'N/A'))}")

        else:
            print("\n❌ API 응답을 캡처하지 못했습니다.")

        print("\n✅ 크롤링 완료!")


if __name__ == "__main__":
    # 제공받은 URL
    target_url = "https://new.land.naver.com/complexes/678?ms=37.5279559,126.895385,19&a=APT:PRE:ABYG:JGC&e=RETAIL"

    asyncio.run(crawl_complex_with_network(target_url))
