"""
네트워크 응답 가로채기
네이버 부동산 API 응답 데이터를 직접 캡처
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def intercept_and_extract():
    """네트워크 응답을 가로채서 실제 데이터 추출"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("=" * 80)
        print("🕵️  네이버 부동산 API 응답 가로채기")
        print("=" * 80)

        captured_data = {
            'complexes': [],
            'complex_detail': None,
            'listings': [],
            'transactions': []
        }

        # 응답 가로채기
        async def handle_response(response):
            """API 응답 캡처"""
            url = response.url

            # 단지 목록 API
            if '/api/complexes' in url or '/api/search' in url:
                try:
                    if response.status == 200:
                        data = await response.json()
                        print(f"\n✅ API 응답 캡처: {url}")
                        print(f"   응답 크기: {len(str(data))} bytes")

                        # 파일로 저장
                        filename = None
                        if 'single-markers' in url:
                            filename = 'api_complexes_markers.json'
                            captured_data['complexes'] = data
                        elif 'complexes/' in url and url.split('/')[-1].isdigit():
                            filename = 'api_complex_detail.json'
                            captured_data['complex_detail'] = data
                        elif 'articles' in url or 'listings' in url:
                            filename = 'api_listings.json'
                            captured_data['listings'] = data
                        elif 'trade' in url or 'transaction' in url:
                            filename = 'api_transactions.json'
                            captured_data['transactions'] = data
                        else:
                            filename = f'api_response_{len(captured_data["complexes"])}.json'

                        if filename:
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            print(f"   💾 저장됨: {filename}")

                            # 데이터 미리보기
                            preview = json.dumps(data, ensure_ascii=False, indent=2)[:500]
                            print(f"   📄 미리보기:\n{preview}...")

                except Exception as e:
                    print(f"⚠️  응답 파싱 에러 ({url}): {e}")

        page.on("response", handle_response)

        # 1. 메인 페이지 접속 (서울 강남 지역)
        print("\n1️⃣  메인 페이지 접속...")
        url = "https://new.land.naver.com/complexes?ms=37.498095,127.027610,16&a=APT&e=RETAIL"
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)

        # 2. 지도 이동해서 더 많은 단지 로드
        print("\n2️⃣  지도 이동 (더 많은 단지 로드)...")
        await page.evaluate('''
            () => {
                // 페이지를 조금씩 스크롤하여 더 많은 데이터 로드
                window.scrollBy(0, 300);
            }
        ''')
        await asyncio.sleep(3)

        # 3. 검색 시도
        print("\n3️⃣  검색 시도...")
        search_url = "https://new.land.naver.com/search?sk=래미안"
        await page.goto(search_url, wait_until="networkidle")
        await asyncio.sleep(5)

        # 4. 캡처된 데이터 확인
        print("\n" + "=" * 80)
        print("📊 캡처된 데이터 요약")
        print("=" * 80)

        if captured_data['complexes']:
            print(f"✅ 단지 목록: {len(captured_data['complexes'])}개 항목")

            # complexes 데이터 구조 확인
            if isinstance(captured_data['complexes'], dict):
                print(f"   키: {list(captured_data['complexes'].keys())}")

                # complexList가 있는지 확인
                if 'complexList' in captured_data['complexes']:
                    complex_list = captured_data['complexes']['complexList']
                    print(f"   단지 수: {len(complex_list)}")

                    if complex_list:
                        print(f"\n   📋 첫 번째 단지 정보:")
                        first = complex_list[0]
                        for key, value in list(first.items())[:10]:
                            print(f"      {key}: {value}")
        else:
            print("❌ 단지 목록 데이터 없음")

        if captured_data['complex_detail']:
            print(f"✅ 단지 상세: 캡처됨")
        else:
            print("❌ 단지 상세 데이터 없음")

        # 5. 최종 대기
        print("\n⏸️  브라우저를 60초간 열어둡니다.")
        print("   직접 단지를 클릭하거나 검색해보세요!")
        await asyncio.sleep(60)

        await browser.close()

        # 전체 캡처 데이터 저장
        with open("all_captured_data.json", "w", encoding="utf-8") as f:
            json.dump(captured_data, f, ensure_ascii=False, indent=2)
        print("\n💾 모든 캡처 데이터: all_captured_data.json")

        print("\n✅ 완료!")

        # 결과 요약
        print("\n" + "=" * 80)
        print("📋 최종 요약")
        print("=" * 80)

        if any(captured_data.values()):
            print("✅ 성공! API 응답 데이터를 캡처했습니다.")
            print("   이제 이 데이터 구조를 바탕으로 크롤러를 개선할 수 있습니다.")
        else:
            print("❌ API 응답을 캡처하지 못했습니다.")
            print("   네이버 부동산의 보안이 매우 강력합니다.")
            print("   공공 데이터 포털 API 사용을 권장합니다.")


if __name__ == "__main__":
    asyncio.run(intercept_and_extract())
