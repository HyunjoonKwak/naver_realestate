"""
수동 네트워크 확인
브라우저를 열어서 직접 네트워크 탭을 확인하는 방식
"""
import asyncio
from playwright.async_api import async_playwright


async def manual_check(url: str):
    """브라우저를 열고 수동으로 확인"""

    async with async_playwright() as p:
        # CDP (Chrome DevTools Protocol) 활성화
        browser = await p.chromium.launch(
            headless=False,
            args=['--auto-open-devtools-for-tabs']  # 개발자 도구 자동 열기
        )

        context = await browser.new_context()

        # CDP 세션 생성
        cdp = await context.new_cdp_session(await context.new_page())

        # Network 활성화
        await cdp.send('Network.enable')

        page = await context.new_page()

        print("=" * 80)
        print("🔍 수동 네트워크 확인")
        print("=" * 80)
        print(f"\n📍 URL: {url}")
        print("\n✅ 브라우저가 열렸습니다!")
        print("   F12를 눌러 개발자 도구를 여세요.")
        print("   Network 탭을 클릭하세요.")
        print("   아래 작업을 수행하세요:")
        print("   1. 페이지가 로드되는 동안 API 호출을 확인")
        print("   2. /api/ 가 포함된 요청을 찾으세요")
        print("   3. 응답(Response)을 복사하세요")
        print("\n⏳ 페이지 로딩...")

        # 네트워크 이벤트 리스너
        network_requests = []

        async def on_request(params):
            url = params['request']['url']
            if '/api/' in url:
                network_requests.append({
                    'requestId': params['requestId'],
                    'url': url,
                    'method': params['request']['method']
                })
                print(f"\n📡 API 요청: {params['request']['method']} {url}")

        async def on_response(params):
            request_id = params['requestId']
            # 캡처한 요청 찾기
            for req in network_requests:
                if req['requestId'] == request_id:
                    print(f"   ✅ 응답 도착: Status {params['response']['status']}")

                    # 응답 본문 가져오기 시도
                    try:
                        response_body = await cdp.send('Network.getResponseBody', {
                            'requestId': request_id
                        })

                        if 'body' in response_body:
                            import json
                            try:
                                data = json.loads(response_body['body'])
                                print(f"   📦 JSON 데이터 캡처 성공!")

                                # 파일명
                                filename = f"captured_{request_id[:8]}.json"

                                with open(filename, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)

                                print(f"   💾 저장: {filename}")

                                # 데이터 미리보기
                                if isinstance(data, dict):
                                    print(f"   🔑 키: {list(data.keys())[:10]}")
                            except:
                                pass
                    except Exception as e:
                        print(f"   ⚠️  응답 가져오기 실패: {e}")

        cdp.on('Network.requestWillBeSent', lambda params: asyncio.create_task(on_request(params)))
        cdp.on('Network.responseReceived', lambda params: asyncio.create_task(on_response(params)))

        await page.goto(url, wait_until='networkidle')

        print("\n" + "=" * 80)
        print("⏸️  브라우저를 120초간 열어둡니다.")
        print("   직접 페이지를 탐색하고 탭을 클릭해보세요!")
        print("   Network 탭에서 API 응답을 확인하세요!")
        print("=" * 80)

        await asyncio.sleep(120)

        await browser.close()

        print("\n" + "=" * 80)
        print("📊 발견된 API 요청")
        print("=" * 80)

        if network_requests:
            print(f"\n총 {len(network_requests)}개:")
            for req in network_requests:
                print(f"   - {req['method']} {req['url']}")
        else:
            print("\n❌ API 요청을 발견하지 못했습니다.")
            print("   페이지가 404인지 확인하세요!")

        print("\n✅ 완료!")


if __name__ == "__main__":
    target_url = "https://new.land.naver.com/complexes/678?ms=37.5279559,126.895385,19&a=APT:PRE:ABYG:JGC&e=RETAIL"
    asyncio.run(manual_check(target_url))
