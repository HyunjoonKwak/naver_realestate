"""
네이버 부동산 크롤링 테스트 스크립트
"""
import asyncio
from playwright.async_api import async_playwright


async def test_naver_real_estate():
    """네이버 부동산 접근 및 기본 정보 추출 테스트"""

    async with async_playwright() as p:
        # 브라우저 실행 (headless=False로 하면 브라우저가 화면에 보임)
        browser = await p.chromium.launch(headless=True)

        # 새 페이지 열기
        page = await browser.new_page()

        print("🚀 네이버 부동산 접속 중...")

        # 네이버 부동산 메인 페이지 접속
        await page.goto("https://new.land.naver.com/", wait_until="networkidle")

        # 페이지 타이틀 확인
        title = await page.title()
        print(f"✅ 페이지 타이틀: {title}")

        # 스크린샷 저장 (확인용)
        await page.screenshot(path="naver_land_homepage.png")
        print("✅ 스크린샷 저장: naver_land_homepage.png")

        # 특정 단지 페이지 접속 테스트 (예: 아크로리버파크)
        print("\n🏢 특정 단지 페이지 접속 테스트...")

        # 단지 검색 페이지로 이동
        await page.goto("https://new.land.naver.com/complexes", wait_until="networkidle")
        await asyncio.sleep(2)

        # 검색창이 있는지 확인
        search_input = await page.query_selector('input[placeholder*="검색"]')
        if search_input:
            print("✅ 검색창 발견!")

            # 검색어 입력 테스트
            await search_input.fill("래미안")
            await asyncio.sleep(1)

            # 스크린샷
            await page.screenshot(path="search_result.png")
            print("✅ 검색 결과 스크린샷 저장: search_result.png")
        else:
            print("⚠️  검색창을 찾을 수 없습니다. (페이지 구조 변경 가능)")

        # 브라우저 종료
        await browser.close()

        print("\n✅ 테스트 완료!")
        print("=" * 60)
        print("Playwright가 정상적으로 작동합니다!")
        print("네이버 부동산 접근이 가능합니다.")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_naver_real_estate())
