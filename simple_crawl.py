"""
간단한 네이버 부동산 크롤링
단지 ID: 109208
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def simple_crawl():
    """간단하고 직접적인 크롤링"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = await context.new_page()

        print("=" * 80)
        print("🏢 네이버 부동산 크롤링")
        print("=" * 80)

        url = "https://new.land.naver.com/complexes/109208"
        print(f"\n📍 URL: {url}")

        # API 응답 저장
        api_responses = []

        # 응답 리스너
        page.on("response", lambda response: asyncio.create_task(save_response(response, api_responses)))

        async def save_response(response, storage):
            """응답 저장"""
            if '/api/' in response.url and response.status == 200:
                try:
                    data = await response.json()
                    storage.append({
                        'url': response.url,
                        'data': data
                    })
                    print(f"✅ API: {response.url.split('/')[-1][:50]}")

                    # 즉시 파일 저장
                    filename = f"captured_{len(storage)}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                except:
                    pass

        # 페이지 로드
        print("\n⏳ 로딩...")
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)

        # 페이지 확인
        title = await page.title()
        print(f"\n📄 타이틀: {title}")

        text = await page.text_content("body")
        if "찾을 수 없습니다" in text:
            print("❌ 404 페이지")
        else:
            print("✅ 페이지 로드 성공")

            # 스크롤
            print("\n📜 스크롤...")
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, 400)")
                await asyncio.sleep(1)

            # 버튼 클릭
            print("\n🖱️  버튼 클릭...")
            buttons = await page.query_selector_all("button")
            for btn in buttons[:20]:
                try:
                    text = await btn.text_content()
                    if text and any(k in text for k in ["매물", "시세", "실거래"]):
                        print(f"   클릭: {text.strip()}")
                        await btn.click()
                        await asyncio.sleep(2)
                except:
                    pass

        # 스크린샷
        await page.screenshot(path="result.png", full_page=True)
        print("\n📸 스크린샷: result.png")

        # 대기
        print("\n⏸️  30초 대기...")
        await asyncio.sleep(30)

        await browser.close()

        # 결과
        print("\n" + "=" * 80)
        print(f"📊 결과: {len(api_responses)}개 API 응답")
        print("=" * 80)

        if api_responses:
            with open("all_api.json", "w", encoding='utf-8') as f:
                json.dump(api_responses, f, ensure_ascii=False, indent=2)

            for i, resp in enumerate(api_responses, 1):
                print(f"\n{i}. {resp['url'].split('/')[-1][:60]}")
                data = resp['data']
                if isinstance(data, dict):
                    # 단지 정보
                    if 'complexName' in data:
                        print(f"   🏢 {data['complexName']}")
                    if 'address' in data:
                        print(f"   📍 {data['address']}")
                    # 매물
                    if 'articleList' in data:
                        print(f"   💰 매물 {len(data['articleList'])}건")
                    # 실거래
                    if 'list' in data and isinstance(data['list'], list):
                        print(f"   📊 거래 {len(data['list'])}건")

        print("\n✅ 완료!")


if __name__ == "__main__":
    asyncio.run(simple_crawl())
