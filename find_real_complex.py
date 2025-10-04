"""
실제 존재하는 단지 ID 찾기
네이버 부동산 지도에서 실제 단지 클릭
"""
import asyncio
from playwright.async_api import async_playwright


async def find_complex_ids():
    """지도에서 실제 단지 클릭하여 ID 찾기"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 80)
        print("🗺️  실제 단지 ID 찾기")
        print("=" * 80)

        # 네이버 부동산 메인 (서울 강남 지역)
        url = "https://new.land.naver.com/complexes?ms=37.498095,127.027610,16&a=APT&e=RETAIL"

        print(f"\n📍 URL: {url}")
        await page.goto(url, wait_until="networkidle")

        print("\n⏳ 지도 로딩 대기 중...")
        await asyncio.sleep(10)

        # 페이지에 있는 링크들 찾기
        print("\n" + "=" * 80)
        print("🔗 단지 링크 찾기")
        print("=" * 80)

        # complexes/숫자 패턴의 링크 찾기
        links = await page.evaluate('''
            () => {
                const allLinks = Array.from(document.querySelectorAll('a[href*="/complexes/"]'));
                return allLinks.map(link => ({
                    href: link.href,
                    text: link.textContent.trim()
                })).filter(item => item.href.match(/complexes\\/\\d+/));
            }
        ''')

        if links:
            print(f"✅ {len(links)}개의 단지 링크 발견!")

            # 중복 제거
            unique_links = {}
            for link in links:
                unique_links[link['href']] = link['text']

            print(f"\n📋 실제 단지 목록 (중복 제거):")
            for i, (href, text) in enumerate(list(unique_links.items())[:10], 1):
                # URL에서 단지 ID 추출
                import re
                match = re.search(r'complexes/(\\d+)', href)
                complex_id = match.group(1) if match else "Unknown"

                print(f"\n{i}. 단지 ID: {complex_id}")
                print(f"   이름: {text[:50]}")
                print(f"   URL: {href}")

            # 첫 번째 단지 방문
            if unique_links:
                first_url = list(unique_links.keys())[0]
                print(f"\n" + "=" * 80)
                print(f"🏢 첫 번째 단지 방문: {first_url}")
                print("=" * 80)

                await page.goto(first_url, wait_until="networkidle")
                await asyncio.sleep(5)

                # 페이지 텍스트 확인
                text_content = await page.evaluate('() => document.body.innerText')
                print(f"\n페이지 내용 (처음 500자):")
                print(text_content[:500])

                # 스크린샷
                await page.screenshot(path="real_complex_page.png", full_page=True)
                print(f"\n📸 스크린샷 저장: real_complex_page.png")

        else:
            print("❌ 단지 링크를 찾지 못했습니다.")

            # 페이지의 모든 링크 출력
            all_links = await page.evaluate('() => Array.from(document.querySelectorAll("a")).map(a => a.href)')
            print(f"\n페이지의 모든 링크 ({len(all_links)}개):")
            for link in all_links[:20]:
                print(f"  - {link}")

        print("\n⏸️  브라우저를 60초간 열어둡니다. 직접 단지를 클릭해보세요!")
        print("  클릭한 단지의 URL을 복사하세요!")
        await asyncio.sleep(60)

        await browser.close()

        print("\n✅ 완료!")


if __name__ == "__main__":
    asyncio.run(find_complex_ids())
