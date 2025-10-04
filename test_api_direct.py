"""
네이버 부동산 API 직접 호출 테스트
"""
import asyncio
import json
from playwright.async_api import async_playwright
import httpx


async def get_auth_token():
    """Playwright로 Authorization 토큰 획득"""
    print("🔑 Authorization 토큰 획득 중...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        token = None
        cookies = {}

        async def capture_token(route, request):
            nonlocal token
            auth = request.headers.get("authorization")
            if auth and auth.startswith("Bearer "):
                token = auth
            await route.continue_()

        await page.route("**/*", capture_token)
        await page.goto("https://new.land.naver.com/complexes", wait_until="networkidle")
        await asyncio.sleep(5)  # 대기 시간 증가

        # 쿠키 수집
        cookie_list = await context.cookies()
        for cookie in cookie_list:
            cookies[cookie['name']] = cookie['value']

        await browser.close()

        return token, cookies


async def test_search_api(keyword: str):
    """단지 검색 API 테스트"""
    print(f"\n🔍 '{keyword}' 검색 API 호출 테스트...")

    # 토큰 획득
    token, cookies = await get_auth_token()

    if not token:
        print("❌ 토큰 획득 실패")
        return

    print(f"✅ 토큰: {token[:50]}...")
    print(f"✅ 쿠키: {list(cookies.keys())}")

    # API 호출
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://new.land.naver.com/complexes",
    }

    # 검색 API URL (추정)
    search_url = f"https://new.land.naver.com/api/search?keyword={keyword}"

    async with httpx.AsyncClient() as client:
        try:
            print(f"\n📡 API 호출: {search_url}")
            response = await client.get(search_url, headers=headers, timeout=10.0)

            print(f"✅ Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 응답 데이터:")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])

                # 파일로 저장
                with open("search_api_response.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print("\n💾 전체 응답을 search_api_response.json에 저장했습니다.")

            else:
                print(f"⚠️  응답 내용: {response.text[:500]}")

        except Exception as e:
            print(f"❌ 에러: {e}")


async def test_complex_markers_api():
    """단지 마커 API 테스트 (지도에 표시되는 단지들)"""
    print(f"\n🗺️  단지 마커 API 호출 테스트...")

    # 토큰 획득
    token, cookies = await get_auth_token()

    if not token:
        print("❌ 토큰 획득 실패")
        return

    headers = {
        "Accept": "*/*",
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://new.land.naver.com/complexes",
    }

    # 서울 강남 지역 좌표 예시
    params = {
        "cortarNo": "1168000000",  # 강남구 코드
        "zoom": 16,
        "priceType": "RETAIL",
        "realEstateType": "APT:ABYG:JGC:PRE",
        "tradeType": "",
        "leftLon": "127.0",
        "rightLon": "127.1",
        "topLat": "37.5",
        "bottomLat": "37.4",
        "showArticle": "false",
    }

    # 발견한 API 사용
    api_url = "https://new.land.naver.com/api/complexes/single-markers/2.0"

    async with httpx.AsyncClient() as client:
        try:
            print(f"\n📡 API 호출: {api_url}")
            response = await client.get(api_url, headers=headers, params=params, timeout=10.0)

            print(f"✅ Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 응답 데이터:")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])

                # 파일로 저장
                with open("markers_api_response.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print("\n💾 전체 응답을 markers_api_response.json에 저장했습니다.")

                # 단지 개수 확인
                if isinstance(data, dict) and 'complexList' in data:
                    complexes = data['complexList']
                    print(f"\n📊 발견된 단지 수: {len(complexes)}")

                    # 첫 3개 단지 출력
                    for i, complex_data in enumerate(complexes[:3], 1):
                        print(f"\n{i}. {complex_data.get('complexName', 'Unknown')}")
                        print(f"   ID: {complex_data.get('complexNo')}")
                        print(f"   주소: {complex_data.get('cortarName', '')}")

            else:
                print(f"⚠️  응답 내용: {response.text[:500]}")

        except Exception as e:
            print(f"❌ 에러: {e}")


async def test_complex_detail_api(complex_id: str):
    """단지 상세 정보 API 테스트"""
    print(f"\n🏢 단지 상세 정보 API 테스트 (ID: {complex_id})...")

    token, cookies = await get_auth_token()

    if not token:
        print("❌ 토큰 획득 실패")
        return

    headers = {
        "Accept": "*/*",
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": f"https://new.land.naver.com/complexes/{complex_id}",
    }

    api_url = f"https://new.land.naver.com/api/complexes/{complex_id}"

    async with httpx.AsyncClient() as client:
        try:
            print(f"\n📡 API 호출: {api_url}")
            response = await client.get(api_url, headers=headers, timeout=10.0)

            print(f"✅ Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 응답 데이터:")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:1000])

                with open(f"complex_{complex_id}_response.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 전체 응답을 complex_{complex_id}_response.json에 저장했습니다.")

            else:
                print(f"⚠️  응답 내용: {response.text[:500]}")

        except Exception as e:
            print(f"❌ 에러: {e}")


async def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("🧪 네이버 부동산 API 직접 호출 테스트")
    print("=" * 80)

    # 1. 검색 API 테스트
    # await test_search_api("래미안")

    # 2. 단지 마커 API 테스트 (가장 유력)
    await test_complex_markers_api()

    # 3. 단지 상세 정보 API 테스트 (단지 ID를 알면)
    # await test_complex_detail_api("12345")

    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
