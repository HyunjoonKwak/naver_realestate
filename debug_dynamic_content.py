"""
네이버 부동산 동적 콘텐츠 분석
JavaScript 렌더링 완료 후 실제 데이터 추출
"""
import asyncio
from playwright.async_api import async_playwright


async def wait_for_content():
    """JavaScript 렌더링이 완료될 때까지 대기하며 분석"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 80)
        print("🔍 네이버 부동산 동적 콘텐츠 분석")
        print("=" * 80)

        # 래미안 강촌센트럴파크
        test_url = "https://new.land.naver.com/complexes/102199"

        print(f"\n📍 URL: {test_url}")
        await page.goto(test_url, wait_until="networkidle")

        # JavaScript 실행 대기
        print("\n⏳ JavaScript 렌더링 대기 중...")
        await asyncio.sleep(10)  # 충분한 대기

        # 1. 페이지에 있는 모든 텍스트 추출
        print("\n" + "=" * 80)
        print("📄 페이지 텍스트 내용")
        print("=" * 80)

        all_text = await page.evaluate('() => document.body.innerText')
        print(all_text[:1000])  # 처음 1000자만 출력

        # 2. 모든 div 요소의 class 이름 수집
        print("\n" + "=" * 80)
        print("🏷️  페이지의 주요 class 이름들")
        print("=" * 80)

        classes = await page.evaluate('''
            () => {
                const allElements = document.querySelectorAll('[class]');
                const classSet = new Set();

                allElements.forEach(el => {
                    const classList = el.className;
                    if (typeof classList === 'string') {
                        classList.split(' ').forEach(c => {
                            if (c && c.trim()) classSet.add(c.trim());
                        });
                    }
                });

                return Array.from(classSet).sort();
            }
        ''')

        # 단지/아파트/가격 관련 class만 출력
        relevant_classes = [c for c in classes if any(keyword in c.lower() for keyword in
                            ['complex', 'title', 'name', 'price', 'article', 'item', 'list', 'info'])]

        print("관련 클래스:")
        for cls in relevant_classes[:30]:  # 최대 30개
            print(f"  - {cls}")

        # 3. 특정 텍스트가 포함된 요소 찾기
        print("\n" + "=" * 80)
        print("🎯 '래미안' 텍스트가 포함된 요소 찾기")
        print("=" * 80)

        ramian_elements = await page.query_selector_all('text=/래미안/i')
        print(f"발견된 요소 수: {len(ramian_elements)}")

        for i, element in enumerate(ramian_elements[:5]):  # 최대 5개
            tag = await element.evaluate('el => el.tagName')
            text = await element.text_content()
            classes = await element.evaluate('el => el.className')

            print(f"\n{i+1}. <{tag}> class='{classes}'")
            print(f"   텍스트: {text.strip()[:100]}")

        # 4. 가격 패턴 찾기 ("억" 포함)
        print("\n" + "=" * 80)
        print("💰 가격 패턴 ('억' 포함) 찾기")
        print("=" * 80)

        price_elements = await page.query_selector_all('text=/억/i')
        print(f"발견된 요소 수: {len(price_elements)}")

        for i, element in enumerate(price_elements[:10]):  # 최대 10개
            text = await element.text_content()
            tag = await element.evaluate('el => el.tagName')

            print(f"{i+1}. <{tag}>: {text.strip()}")

        # 5. 네트워크 요청 확인 (API 호출)
        print("\n" + "=" * 80)
        print("🌐 API 호출 내역")
        print("=" * 80)

        api_calls = []

        async def capture_request(request):
            url = request.url
            if '/api/' in url:
                api_calls.append(url)
                print(f"  📡 {request.method} {url}")

        page.on("request", capture_request)

        # 페이지 새로고침하여 API 호출 캡처
        print("  (페이지 새로고침 중...)")
        await page.reload(wait_until="networkidle")
        await asyncio.sleep(5)

        # 6. 최종 스크린샷
        await page.screenshot(path="dynamic_content_analysis.png", full_page=True)
        print("\n📸 스크린샷 저장: dynamic_content_analysis.png")

        # 7. HTML 저장
        html = await page.content()
        with open("page_after_js.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("💾 렌더링 후 HTML 저장: page_after_js.html")

        print("\n⏸️  브라우저를 30초간 열어둡니다.")
        await asyncio.sleep(30)

        await browser.close()

        print("\n✅ 분석 완료!")


if __name__ == "__main__":
    asyncio.run(wait_for_content())
