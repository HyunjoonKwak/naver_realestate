"""
네이버 부동산 페이지 구조 상세 분석
실제 HTML과 JavaScript 실행 결과를 확인합니다.
"""
import asyncio
from playwright.async_api import async_playwright


async def analyze_page():
    """페이지 구조 상세 분석"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 브라우저 보이게
        page = await browser.new_page()

        print("=" * 80)
        print("🔍 네이버 부동산 페이지 구조 분석")
        print("=" * 80)

        # 1. 특정 단지 페이지 직접 접속 (래미안 강촌센트럴파크 예시)
        # 실제 존재하는 단지 URL 사용
        test_url = "https://new.land.naver.com/complexes/102199"  # 래미안 강촌센트럴파크

        print(f"\n📍 테스트 URL: {test_url}")
        await page.goto(test_url, wait_until="networkidle")
        await asyncio.sleep(5)  # 충분한 대기

        # 2. 페이지 전체 HTML 길이 확인
        html = await page.content()
        print(f"\n📄 HTML 길이: {len(html)} 문자")

        # 3. 주요 요소들 확인
        print("\n" + "=" * 80)
        print("🔎 주요 요소 탐색")
        print("=" * 80)

        # 다양한 selector 시도
        selectors_to_try = [
            # 단지명
            ("단지명", ["h1", ".complex_title", "[class*='ComplexTitle']", "[class*='complex']", "header h1"]),

            # 주소
            ("주소", [".address", "[class*='Address']", "[class*='location']", "address"]),

            # 가격 정보
            ("가격", [".price", "[class*='Price']", "[class*='price']", "[data-price]"]),

            # 매물 리스트
            ("매물", [".article_list", "[class*='Article']", "[class*='listing']", "[class*='Item']"]),

            # 버튼/탭
            ("탭/버튼", ["button", "[role='tab']", ".tab", "[class*='Tab']"]),
        ]

        for name, selectors in selectors_to_try:
            print(f"\n🎯 {name} 찾기:")
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"  ✅ {selector}: {len(elements)}개 발견")

                        # 첫 번째 요소의 텍스트 출력
                        if len(elements) > 0:
                            text = await elements[0].text_content()
                            if text and text.strip():
                                print(f"     내용: {text.strip()[:100]}")
                    else:
                        print(f"  ❌ {selector}: 없음")
                except Exception as e:
                    print(f"  ⚠️  {selector}: 에러 - {e}")

        # 4. JavaScript로 데이터 추출 시도
        print("\n" + "=" * 80)
        print("🔬 JavaScript로 데이터 추출")
        print("=" * 80)

        # React/Next.js 앱의 경우 __NEXT_DATA__ 확인
        next_data = await page.evaluate('''
            () => {
                const scriptEl = document.getElementById('__NEXT_DATA__');
                if (scriptEl) {
                    try {
                        return JSON.parse(scriptEl.textContent);
                    } catch (e) {
                        return null;
                    }
                }
                return null;
            }
        ''')

        if next_data:
            print("✅ __NEXT_DATA__ 발견!")
            print(f"   키: {list(next_data.keys())}")

            # pageProps 확인
            if 'props' in next_data and 'pageProps' in next_data['props']:
                page_props = next_data['props']['pageProps']
                print(f"   pageProps 키: {list(page_props.keys())}")

                # 파일로 저장
                import json
                with open("next_data.json", "w", encoding="utf-8") as f:
                    json.dump(next_data, f, ensure_ascii=False, indent=2)
                print("\n💾 __NEXT_DATA__를 next_data.json에 저장했습니다.")
        else:
            print("❌ __NEXT_DATA__ 없음")

        # 5. window 객체에 있는 데이터 확인
        window_data = await page.evaluate('''
            () => {
                const keys = Object.keys(window).filter(key =>
                    key.includes('data') ||
                    key.includes('Data') ||
                    key.includes('complex') ||
                    key.includes('listing')
                );
                return keys;
            }
        ''')

        if window_data:
            print(f"\n🪟 window 객체 관련 키: {window_data}")

        # 6. 스크린샷 저장
        await page.screenshot(path="page_structure_analysis.png", full_page=True)
        print("\n📸 전체 페이지 스크린샷: page_structure_analysis.png")

        # 7. 브라우저 열어두기 (수동 확인용)
        print("\n" + "=" * 80)
        print("⏸️  브라우저를 30초간 열어둡니다. 페이지를 직접 확인하세요.")
        print("   개발자 도구(F12)를 열어서 Elements 탭을 확인하세요!")
        print("=" * 80)
        await asyncio.sleep(30)

        await browser.close()

        print("\n✅ 분석 완료!")


if __name__ == "__main__":
    asyncio.run(analyze_page())
