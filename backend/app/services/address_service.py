"""
주소 수집 서비스
네이버 검색을 통해 단지 주소를 수집
"""
import asyncio
import re
from typing import Optional
from playwright.async_api import async_playwright


class AddressService:
    """네이버 검색을 통한 주소 수집"""

    def get_complex_address(self, complex_name: str) -> Optional[str]:
        """
        단지명으로 주소 검색 (동기 래퍼)

        Args:
            complex_name: 단지명

        Returns:
            주소 문자열 또는 None
        """
        return asyncio.run(self._get_complex_address_async(complex_name))

    async def _get_complex_address_async(self, complex_name: str) -> Optional[str]:
        """
        단지명으로 주소 검색 (비동기 버전)

        Args:
            complex_name: 단지명

        Returns:
            주소 문자열 또는 None
        """
        try:
            print(f"   🔍 네이버 검색으로 주소 찾는 중: {complex_name}")

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=False,  # 디버깅용 headless=False
                    args=['--disable-blink-features=AutomationControlled'],
                    slow_mo=100
                )

                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                page = await context.new_page()

                # 네이버 통합검색
                search_url = f"https://search.naver.com/search.naver?where=nexearch&query={complex_name}"
                print(f"   📍 검색 URL: {search_url}")
                await page.goto(search_url, timeout=30000, wait_until='networkidle')
                await asyncio.sleep(3)

                # 디버깅: 페이지 스크린샷 저장
                # await page.screenshot(path=f'/tmp/address_search_{complex_name}.png')

                # 주소 추출 - 더 구체적인 선택자와 디버깅 정보 추가
                result = await page.evaluate("""
                    () => {
                        console.log('=== 주소 검색 시작 ===');

                        // 1. 부동산 정보 영역에서 찾기
                        const estateInfo = document.querySelector('.estate_info');
                        if (estateInfo) {
                            console.log('부동산 정보 영역 발견');
                            const addressEl = estateInfo.querySelector('.addr');
                            if (addressEl) {
                                const addr = addressEl.textContent.trim();
                                console.log('주소 발견 (estate_info):', addr);
                                return { address: addr, method: 'estate_info' };
                            }
                        }

                        // 2. 로컬 정보 영역에서 찾기
                        const localInfo = document.querySelector('.place_section');
                        if (localInfo) {
                            console.log('지역 정보 영역 발견');
                            const addressEl = localInfo.querySelector('.addr');
                            if (addressEl) {
                                const addr = addressEl.textContent.trim();
                                console.log('주소 발견 (place_section):', addr);
                                return { address: addr, method: 'place_section' };
                            }
                        }

                        // 3. 일반 검색 결과에서 찾기
                        const totalArea = document.querySelector('.total_area');
                        if (totalArea) {
                            console.log('통합 검색 영역 발견');
                            const allText = totalArea.innerText;
                            const addressMatch = allText.match(/(경기도|서울특별시|부산광역시|인천광역시|대전광역시|대구광역시|광주광역시|울산광역시|세종특별자치시)[^\n]{10,80}/);
                            if (addressMatch) {
                                const addr = addressMatch[0].trim();
                                console.log('주소 발견 (total_area):', addr);
                                return { address: addr, method: 'total_area' };
                            }
                        }

                        // 4. API 검색 영역
                        const apiWrap = document.querySelector('.api_cs_wrap');
                        if (apiWrap) {
                            console.log('API 검색 영역 발견');
                            const addressEl = apiWrap.querySelector('.addr');
                            if (addressEl) {
                                const addr = addressEl.textContent.trim();
                                console.log('주소 발견 (api_cs_wrap):', addr);
                                return { address: addr, method: 'api_cs_wrap' };
                            }
                        }

                        // 5. 전체 페이지에서 정규식으로 찾기
                        console.log('정규식 패턴 매칭 시도');
                        const bodyText = document.body.innerText;
                        const patterns = [
                            /(경기도\s+[^\n]{10,80})/,
                            /(서울특별시\s+[^\n]{10,80})/,
                            /(부산광역시\s+[^\n]{10,80})/,
                            /(인천광역시\s+[^\n]{10,80})/,
                            /(대전광역시\s+[^\n]{10,80})/,
                            /(대구광역시\s+[^\n]{10,80})/,
                            /(광주광역시\s+[^\n]{10,80})/,
                            /(울산광역시\s+[^\n]{10,80})/,
                            /(세종특별자치시\s+[^\n]{10,80})/
                        ];

                        for (const pattern of patterns) {
                            const match = bodyText.match(pattern);
                            if (match) {
                                const addr = match[0].trim();
                                console.log('주소 발견 (regex):', addr);
                                return { address: addr, method: 'regex' };
                            }
                        }

                        console.log('주소를 찾지 못함');
                        return null;
                    }
                """)

                await browser.close()

                if result and result.get('address'):
                    address = result['address']
                    method = result.get('method', 'unknown')
                    print(f"   ✅ 주소 검색 성공 ({method}): {address}")

                    # 주소 정제
                    address = re.sub(r'\(우\)\d+', '', address)  # 우편번호 제거
                    address = re.sub(r'지번.*', '', address)  # "지번..." 이후 제거
                    address = re.sub(r'지도보기.*', '', address)  # "지도보기" 제거
                    address = re.sub(r'\s+', ' ', address)  # 공백 정리
                    address = address.strip()

                    return address
                else:
                    print(f"   ⚠️ 주소를 찾을 수 없음: {complex_name}")
                    return None

        except Exception as e:
            print(f"   ❌ 주소 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
