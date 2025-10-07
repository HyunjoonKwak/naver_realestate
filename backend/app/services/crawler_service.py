"""
네이버 부동산 크롤링 서비스
봇 감지 회피 기술을 포함한 안전한 크롤러
"""
import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models.complex import Complex, Article, Transaction


class NaverRealEstateCrawler:
    """네이버 부동산 크롤러 - 봇 감지 회피 기능 포함"""

    def __init__(self):
        self.api_responses = []
        self.complex_data = None
        self.articles_data = None
        self.transactions_data = []

    async def save_response(self, response):
        """API 응답 저장"""
        try:
            if '/api/' in response.url and response.status == 200:
                data = await response.json()

                # 응답 URL에 따라 데이터 분류
                url = response.url

                # 단지 overview 정보 (주소 포함)
                if 'complexes/overview' in url:
                    # overview 데이터를 complex_data에 병합
                    if self.complex_data is None:
                        self.complex_data = data
                    else:
                        self.complex_data.update(data)
                    print(f"✅ 단지 상세 정보 수집 (overview)")
                    if 'roadAddress' in data or 'jibunAddress' in data:
                        print(f"   🏠 주소: {data.get('roadAddress') or data.get('jibunAddress')}")

                # 단지 기본 정보
                elif 'complexes/' in url and 'complexNo' in str(data) and 'overview' not in url:
                    if self.complex_data is None:
                        self.complex_data = data
                        print(f"✅ 단지 정보 수집: {data.get('complexName', 'N/A')}")
                        print(f"   전체 필드: {list(data.keys())}")

                # 매물 목록
                elif 'articleList' in str(data) and isinstance(data, dict):
                    if 'articleList' in data:
                        # 페이지네이션 정보 출력
                        total_count = data.get('totalCount', 0)
                        current_count = len(data.get('articleList', []))

                        # 기존 데이터에 추가 (여러 페이지 수집)
                        if self.articles_data is None:
                            self.articles_data = data
                            # sameAddressGroup 파라미터 확인
                            same_group = 'sameAddressGroup=true' in url
                            group_status = "✅ ON" if same_group else "❌ OFF"
                            print(f"✅ 매물 정보 수집: {current_count}건 (전체: {total_count}건)")
                            print(f"   동일매물묶기: {group_status}")
                            print(f"   API URL: {url}")
                        else:
                            # 기존 articleList에 새로운 항목 추가 (중복 제거)
                            existing_articles = self.articles_data.get('articleList', [])
                            new_articles = data.get('articleList', [])
                            if len(new_articles) > 0:
                                # 기존 article_id 세트
                                existing_ids = {article.get('articleNo') for article in existing_articles}

                                # 중복되지 않은 새 매물만 추가
                                unique_new_articles = [
                                    article for article in new_articles
                                    if article.get('articleNo') not in existing_ids
                                ]

                                duplicates_count = len(new_articles) - len(unique_new_articles)

                                self.articles_data['articleList'] = existing_articles + unique_new_articles
                                self.articles_data['totalCount'] = data.get('totalCount', 0)
                                total = len(self.articles_data['articleList'])

                                if duplicates_count > 0:
                                    print(f"✅ 추가 매물 수집: +{len(unique_new_articles)}건 (누적: {total}건 / 전체: {total_count}건) [중복 {duplicates_count}건 제거]")
                                else:
                                    print(f"✅ 추가 매물 수집: +{current_count}건 (누적: {total}건 / 전체: {total_count}건)")

                # 실거래가 (realPrice 포함)
                if 'realPrice' in str(data):
                    self.transactions_data.append(data)
                    print(f"✅ 실거래가 정보 수집")

        except Exception as e:
            # JSON 파싱 실패는 무시
            pass

    async def crawl_complex(self, complex_id: str, collect_address: bool = False):
        """
        특정 단지 크롤링

        Args:
            complex_id: 단지 ID
            collect_address: 주소 수집 여부 (기본값: False)

        [중요] 봇 감지 회피 기술:
        - headless=False: 실제 브라우저 사용
        - AutomationControlled 비활성화
        - slow_mo=100: 느린 동작으로 자연스러움 연출
        - localStorage 기반 동일매물묶기 설정
        - 스크롤 속도 제어 (1.5초 대기)
        """
        print(f"\n{'='*80}")
        print(f"🏢 단지 크롤링 시작: {complex_id}")
        print(f"   [봇 회피 모드] headless=False, slow_mo=100")
        print(f"{'='*80}\n")

        # 데이터 초기화
        self.api_responses = []
        self.complex_data = None
        self.articles_data = None
        self.transactions_data = []

        async with async_playwright() as p:
            # ⚠️ 봇 감지 회피: headless=False, AutomationControlled 비활성화
            browser = await p.chromium.launch(
                headless=False,  # 필수: 봇 감지 회피
                args=[
                    '--disable-blink-features=AutomationControlled',  # 필수: automation 감지 차단
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-sandbox'
                ],
                slow_mo=100  # 필수: 느린 동작으로 안정성 향상
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )

            page = await context.new_page()

            # 응답 리스너 등록
            page.on("response", lambda response: asyncio.create_task(self.save_response(response)))

            # ⚠️ 봇 감지 회피: 먼저 메인 페이지에서 localStorage 설정
            print("   🔧 동일매물묶기 설정 준비 중...")
            await page.goto("https://new.land.naver.com", wait_until="domcontentloaded")

            # ⚠️ 필수: localStorage에 동일매물묶기 설정 저장
            await page.evaluate("""
                () => {
                    // 네이버가 사용하는 localStorage 키 설정
                    localStorage.setItem('sameAddrYn', 'true');
                    localStorage.setItem('sameAddressGroup', 'true');
                    console.log('[LocalStorage] 동일매물묶기 설정 완료');
                }
            """)

            print("   ✅ localStorage 설정 완료")

            # 이제 단지 페이지로 이동
            url = f"https://new.land.naver.com/complexes/{complex_id}"
            print(f"🌐 접속: {url}")

            await page.goto(url, wait_until="networkidle")

            # 페이지 로딩 대기
            await asyncio.sleep(2)

            # 주소 수집이 필요한 경우에만 실행
            if collect_address:
                # 단지정보 버튼 클릭
                try:
                    print(f"   🔍 단지정보 버튼 클릭 중...")

                    tab_clicked = await page.evaluate("""
                        () => {
                            // 모든 버튼/탭 탐색
                            const allElements = document.querySelectorAll('button, [role="tab"], a');
                            for (const el of allElements) {
                                const text = el.textContent || '';
                                if (text.includes('단지정보') || text.includes('단지 정보')) {
                                    el.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)

                    if tab_clicked:
                        print(f"   ✅ 단지정보 버튼 클릭 완료")
                        await asyncio.sleep(2)  # 정보 로딩 대기
                    else:
                        print(f"   ⚠️ 단지정보 버튼을 찾지 못했습니다")

                except Exception as e:
                    print(f"   ⚠️ 단지정보 버튼 클릭 실패: {e}")

                # 🛑 주소 필드 확인을 위한 일시정지
                print(f"\n{'='*80}")
                print(f"⏸️  주소 필드 확인 모드")
                print(f"{'='*80}")
                print(f"")
                print(f"브라우저 창에서 주소가 표시된 텍스트를 드래그해주세요.")
                print(f"드래그 후 화면 상단의 '계속 진행' 버튼을 클릭하세요.")
                print(f"")
                print(f"예시: '경기도 화성시 동탄반송길 25' 같은 주소 텍스트를 드래그")
                print(f"      → 화면 상단 '계속 진행' 버튼 클릭")
                print(f"{'='*80}\n")

                # 페이지에 계속 진행 버튼 추가
                await page.evaluate("""
                () => {
                    window.shouldContinue = false;

                    // 오버레이 추가
                    const overlay = document.createElement('div');
                    overlay.id = 'continueOverlay';
                    overlay.style.cssText = `
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        z-index: 999999;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    `;

                    overlay.innerHTML = `
                        <div style="max-width: 1200px; margin: 0 auto;">
                            <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">
                                <h2 style="margin: 0 0 15px 0; color: #333; font-size: 20px; font-weight: 600;">
                                    ⏸️ 주소 필드 확인 모드
                                </h2>
                                <p style="margin: 0 0 15px 0; color: #666; font-size: 14px; line-height: 1.6;">
                                    아래 페이지에서 <strong>주소 텍스트</strong>를 드래그하세요.<br>
                                    예: "경기도 화성시 동탄반송길 25"<br>
                                    드래그 후 이 버튼을 클릭하면 크롤링이 계속 진행됩니다.
                                </p>
                                <button id="continueBtn" style="
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    border: none;
                                    padding: 12px 30px;
                                    font-size: 16px;
                                    font-weight: 600;
                                    border-radius: 8px;
                                    cursor: pointer;
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                                    transition: all 0.3s ease;
                                ">
                                    ✅ 계속 진행
                                </button>
                            </div>
                        </div>
                    `;

                    document.body.appendChild(overlay);

                    // 버튼 클릭 이벤트
                    document.getElementById('continueBtn').addEventListener('click', () => {
                        window.shouldContinue = true;
                        overlay.style.display = 'none';
                    });

                    // 버튼 호버 효과
                    document.getElementById('continueBtn').addEventListener('mouseenter', (e) => {
                        e.target.style.transform = 'translateY(-2px)';
                        e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';
                    });
                    document.getElementById('continueBtn').addEventListener('mouseleave', (e) => {
                        e.target.style.transform = 'translateY(0)';
                        e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                    });
                }
                """)

                # 사용자가 버튼 클릭할 때까지 대기 (최대 5분)
                try:
                    wait_count = 0
                    max_wait = 300  # 5분 (300초)

                    while wait_count < max_wait:
                        should_continue = await page.evaluate("() => window.shouldContinue")
                        if should_continue:
                            print(f"   ✅ 계속 진행 신호 받음!")
                            break
                        await asyncio.sleep(1)
                        wait_count += 1

                        # 10초마다 상태 출력
                        if wait_count % 10 == 0:
                            print(f"   ⏳ 대기 중... ({wait_count}초 경과)")

                    if wait_count >= max_wait:
                        print(f"   ⚠️ 타임아웃 (5분 경과) - 계속 진행합니다")

                except Exception as e:
                    print(f"   ⚠️ 대기 중 오류: {e}")

                # 주소 정보 수집 (도로명 주소와 법정동 주소)
                try:
                    print(f"\n   🔍 주소 정보 수집 중...")

                    # 페이지에서 주소 정보 찾기
                    address_info = await page.evaluate("""
                        () => {
                            // 도로명 주소와 지번 주소 찾기
                            let roadAddress = '';
                            let jibunAddress = '';

                            // 방법 1: dt/dd 태그에서 찾기
                            const dts = document.querySelectorAll('dt');
                            for (const dt of dts) {
                                const text = dt.textContent || '';
                                const dd = dt.nextElementSibling;

                                if (text.includes('도로명주소') && dd) {
                                    roadAddress = dd.textContent.trim();
                                }
                                if ((text.includes('지번주소') || text.includes('법정동주소')) && dd) {
                                    jibunAddress = dd.textContent.trim();
                                }
                            }

                            // 방법 2: 모든 텍스트에서 패턴 매칭
                            if (!roadAddress || !jibunAddress) {
                                const allText = document.body.innerText;
                                const lines = allText.split('\\n');

                                for (const line of lines) {
                                    const trimmed = line.trim();
                                    // 도로명 주소 패턴 (시/도로/길 포함)
                                    if (!roadAddress && (trimmed.includes('로 ') || trimmed.includes('길 ')) &&
                                        /[가-힣]+[시도]/.test(trimmed)) {
                                        roadAddress = trimmed;
                                    }
                                    // 지번 주소 패턴 (동 + 번지)
                                    if (!jibunAddress && /[가-힣]+동\s+\d+/.test(trimmed) &&
                                        /[가-힣]+[시도]/.test(trimmed)) {
                                        jibunAddress = trimmed;
                                    }
                                }
                            }

                            return {
                                roadAddress: roadAddress,
                                jibunAddress: jibunAddress
                            };
                        }
                    """)

                    if address_info:
                        if not self.complex_data:
                            self.complex_data = {}

                        if address_info.get('roadAddress'):
                            self.complex_data['road_address'] = address_info['roadAddress']
                            print(f"   ✅ 도로명 주소: {address_info['roadAddress']}")

                        if address_info.get('jibunAddress'):
                            self.complex_data['jibun_address'] = address_info['jibunAddress']
                            print(f"   ✅ 지번(법정동) 주소: {address_info['jibunAddress']}")

                        # address 필드에는 도로명 주소 우선, 없으면 지번 주소
                        if address_info.get('roadAddress'):
                            self.complex_data['address'] = address_info['roadAddress']
                        elif address_info.get('jibunAddress'):
                            self.complex_data['address'] = address_info['jibunAddress']

                        if not address_info.get('roadAddress') and not address_info.get('jibunAddress'):
                            print(f"   ⚠️ 자동으로 주소를 찾지 못했습니다")
                            print(f"   💡 단지정보 탭에서 주소를 수동으로 드래그해주세요")

                except Exception as e:
                    print(f"   ⚠️ 주소 수집 실패: {e}")

            # localStorage 확인 및 체크박스 상태 검증
            storage_check = await page.evaluate("""
                () => {
                    const sameAddrYn = localStorage.getItem('sameAddrYn');
                    const sameAddressGroup = localStorage.getItem('sameAddressGroup');

                    // 체크박스 상태 확인
                    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                    let checkboxState = null;

                    for (const checkbox of checkboxes) {
                        const label = checkbox.closest('label') || checkbox.nextElementSibling;
                        const text = label ? (label.textContent || label.innerText || '') : '';
                        if (text.includes('동일매물')) {
                            checkboxState = {
                                checked: checkbox.checked,
                                labelText: text
                            };
                            break;
                        }
                    }

                    return {
                        sameAddrYn,
                        sameAddressGroup,
                        checkboxState
                    };
                }
            """)

            print(f"   [DEBUG] localStorage 확인: {storage_check}")

            # 체크박스가 체크되지 않았으면 클릭
            if storage_check.get('checkboxState') and not storage_check['checkboxState'].get('checked'):
                print("   🔘 체크박스 클릭 중...")
                await page.evaluate("""
                    () => {
                        const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                        for (const checkbox of checkboxes) {
                            const label = checkbox.closest('label') || checkbox.nextElementSibling;
                            const text = label ? (label.textContent || label.innerText || '') : '';
                            if (text.includes('동일매물')) {
                                checkbox.click();
                                console.log('[Checkbox] 클릭 완료');
                                return true;
                            }
                        }
                        return false;
                    }
                """)

                # 데이터 초기화 후 재로딩 대기
                print("   [DEBUG] 체크박스 클릭 완료, 데이터 초기화...")
                self.articles_data = None
                self.complex_data = None
                await asyncio.sleep(3)
                print("   ✅ 동일매물묶기 활성화 완료")
            else:
                print("   ✅ 동일매물묶기 이미 활성화됨")

            # 매물 리스트 컨테이너 내부 스크롤로 모든 매물 로딩
            print("   📜 매물 리스트 스크롤 중...")

            previous_api_count = len(self.articles_data.get('articleList', [])) if self.articles_data else 0
            scroll_end_count = 0

            for i in range(100):
                # 컨테이너 스크롤 - .item_list가 실제 스크롤 가능한 컨테이너
                scrolled = await page.evaluate("""
                    () => {
                        const container = document.querySelector('.item_list');
                        if (container) {
                            const before = container.scrollTop;
                            // 스크롤 다운
                            container.scrollTop += 500;
                            const after = container.scrollTop;

                            // 현재 DOM에 있는 매물 개수도 확인
                            const items = document.querySelectorAll('.item_link, .item_inner, [class*="item"]');

                            return {
                                found: true,
                                moved: after > before,
                                scrollTop: after,
                                scrollHeight: container.scrollHeight,
                                clientHeight: container.clientHeight,
                                domItemCount: items.length
                            };
                        }
                        return {found: false};
                    }
                """)

                # 진행상황 출력 (10회마다)
                if i % 10 == 0 and i > 0:
                    print(f"   🔄 스크롤 진행 중... (#{i+1})")

                # ⚠️ 봇 감지 회피: 1.5초 대기로 자연스러운 스크롤 연출
                await asyncio.sleep(1.5)

                # 현재 수집된 매물 수
                current_api_count = len(self.articles_data.get('articleList', [])) if self.articles_data else 0

                if current_api_count > previous_api_count:
                    print(f"   📊 API 응답: {current_api_count}건 수집됨 (+{current_api_count - previous_api_count})")
                    previous_api_count = current_api_count
                    scroll_end_count = 0  # 새 데이터가 들어오면 카운터 리셋

                # 스크롤이 끝에 도달했는지 체크
                if scrolled.get('found') and not scrolled.get('moved'):
                    scroll_end_count += 1
                    # 스크롤 끝에서 5회 연속 데이터 없으면 종료
                    if scroll_end_count >= 5:
                        print(f"   ⏹️  스크롤 끝 도달 - 수집 완료")
                        break
                else:
                    scroll_end_count = 0  # 스크롤이 움직이면 리셋

            print(f"   ✅ 최종 수집: {previous_api_count}건")

            await browser.close()

        return {
            'complex': self.complex_data,
            'articles': self.articles_data,
            'transactions': self.transactions_data
        }

    def save_to_database(self, complex_id: str, db: Session = None):
        """
        데이터베이스에 저장

        Args:
            complex_id: 단지 ID
            db: SQLAlchemy 세션 (없으면 새로 생성)
        """
        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True

        try:
            print(f"\n{'='*80}")
            print(f"💾 데이터베이스 저장")
            print(f"{'='*80}\n")

            # 1. 단지 정보 저장
            if self.complex_data:
                print("🏢 단지 정보 저장 중...")

                existing_complex = db.query(Complex).filter(
                    Complex.complex_id == self.complex_data['complexNo']
                ).first()

                # 주소 정보 수집
                road_address = self.complex_data.get('road_address')
                jibun_address = self.complex_data.get('jibun_address')
                # 하위호환용 address 필드 (도로명 주소 우선)
                address = road_address or jibun_address or self.complex_data.get('address')

                if existing_complex:
                    print(f"   ⚠️  기존 단지 업데이트: {self.complex_data['complexName']}")
                    # 기존 데이터 업데이트
                    update_data = {
                        'complex_name': self.complex_data['complexName'],
                        'complex_type': self.complex_data.get('complexTypeName'),
                        'total_households': self.complex_data.get('totalHouseHoldCount'),
                        'total_dongs': self.complex_data.get('totalDongCount'),
                        'completion_date': self.complex_data.get('useApproveYmd'),
                        'min_area': self.complex_data.get('minArea'),
                        'max_area': self.complex_data.get('maxArea'),
                        'min_price': self.complex_data.get('minPrice'),
                        'max_price': self.complex_data.get('maxPrice'),
                        'min_lease_price': self.complex_data.get('minLeasePrice'),
                        'max_lease_price': self.complex_data.get('maxLeasePrice'),
                        'latitude': self.complex_data.get('latitude'),
                        'longitude': self.complex_data.get('longitude'),
                    }

                    # 주소 정보는 새로 수집된 것이 있을 때만 업데이트 (기존 주소 보존)
                    if road_address:
                        update_data['road_address'] = road_address
                        update_data['address'] = road_address  # 하위호환
                        print(f"   ✅ 도로명 주소 업데이트: {road_address}")
                    else:
                        print(f"   ℹ️  기존 도로명 주소 유지: {existing_complex.road_address}")

                    if jibun_address:
                        update_data['jibun_address'] = jibun_address
                        print(f"   ✅ 법정동 주소 업데이트: {jibun_address}")
                    else:
                        print(f"   ℹ️  기존 법정동 주소 유지: {existing_complex.jibun_address}")

                    if not road_address and not jibun_address and address:
                        update_data['address'] = address
                        print(f"   ✅ 주소 업데이트: {address}")

                    for key, value in update_data.items():
                        setattr(existing_complex, key, value)
                    complex_obj = existing_complex
                else:
                    complex_obj = Complex(
                        complex_id=self.complex_data['complexNo'],
                        complex_name=self.complex_data['complexName'],
                        complex_type=self.complex_data.get('complexTypeName'),
                        address=address,
                        road_address=road_address,
                        jibun_address=jibun_address,
                        total_households=self.complex_data.get('totalHouseHoldCount'),
                        total_dongs=self.complex_data.get('totalDongCount'),
                        completion_date=self.complex_data.get('useApproveYmd'),
                        min_area=self.complex_data.get('minArea'),
                        max_area=self.complex_data.get('maxArea'),
                        min_price=self.complex_data.get('minPrice'),
                        max_price=self.complex_data.get('maxPrice'),
                        min_lease_price=self.complex_data.get('minLeasePrice'),
                        max_lease_price=self.complex_data.get('maxLeasePrice'),
                        latitude=self.complex_data.get('latitude'),
                        longitude=self.complex_data.get('longitude')
                    )
                    db.add(complex_obj)
                    print(f"   ✅ 새 단지 저장: {self.complex_data['complexName']}")
                    if road_address:
                        print(f"   ✅ 도로명 주소: {road_address}")
                    if jibun_address:
                        print(f"   ✅ 법정동 주소: {jibun_address}")

                db.commit()

            # 2. 매물 정보 저장
            if self.articles_data:
                print("\n💰 매물 정보 저장 중...")

                article_list = self.articles_data.get('articleList', [])
                saved_count = 0
                updated_count = 0
                skipped_count = 0

                # 배치 내 중복 제거
                seen_article_nos = set()

                for article in article_list:
                    article_no = article['articleNo']

                    # 배치 내 중복 체크
                    if article_no in seen_article_nos:
                        skipped_count += 1
                        continue
                    seen_article_nos.add(article_no)

                    # DB 중복 확인
                    existing = db.query(Article).filter(
                        Article.article_no == article_no
                    ).first()

                    if existing:
                        # 가격 변동 확인
                        new_price = article.get('dealOrWarrantPrc')
                        if existing.price != new_price:
                            existing.price = new_price
                            existing.price_change_state = article.get('priceChangeState')
                            updated_count += 1
                        else:
                            skipped_count += 1
                        continue

                    article_obj = Article(
                        article_no=article_no,
                        complex_id=complex_id,
                        trade_type=article.get('tradeTypeName'),
                        price=article.get('dealOrWarrantPrc'),
                        area_name=article.get('areaName'),
                        area1=article.get('area1'),
                        area2=article.get('area2'),
                        floor_info=article.get('floorInfo'),
                        direction=article.get('direction'),
                        building_name=article.get('buildingName'),
                        feature_desc=article.get('articleFeatureDesc'),
                        tags=json.dumps(article.get('tagList', []), ensure_ascii=False),
                        realtor_name=article.get('realtorName'),
                        confirm_date=article.get('articleConfirmYmd'),
                        # 동일 매물 정보 추가
                        same_addr_cnt=article.get('sameAddrCnt', 1),
                        same_addr_max_prc=article.get('sameAddrMaxPrc'),
                        same_addr_min_prc=article.get('sameAddrMinPrc')
                    )
                    db.add(article_obj)
                    saved_count += 1

                db.commit()

                print(f"   ✅ 새 매물: {saved_count}건")
                if updated_count > 0:
                    print(f"   🔄 가격변동: {updated_count}건")
                print(f"   ⏭️  변동없음: {skipped_count}건")

            # 3. 실거래가 저장
            if self.transactions_data:
                print("\n📊 실거래가 저장 중...")

                saved_count = 0
                skipped_count = 0

                for trans_data in self.transactions_data:
                    real_price = trans_data.get('realPrice')
                    if not real_price:
                        continue

                    # 거래일자 생성
                    trade_date = None
                    if all(k in real_price for k in ['tradeYear', 'tradeMonth', 'tradeDate']):
                        try:
                            trade_date = f"{real_price['tradeYear']}{str(real_price['tradeMonth']).zfill(2)}{str(real_price['tradeDate']).zfill(2)}"
                        except:
                            pass

                    # 중복 확인
                    existing = db.query(Transaction).filter(
                        Transaction.complex_id == complex_id,
                        Transaction.trade_date == trade_date,
                        Transaction.deal_price == real_price.get('dealPrice'),
                        Transaction.floor == real_price.get('floor')
                    ).first()

                    if existing:
                        skipped_count += 1
                        continue

                    transaction_obj = Transaction(
                        complex_id=complex_id,
                        trade_type=real_price.get('tradeType', 'A1'),
                        trade_date=trade_date,
                        deal_price=real_price.get('dealPrice'),
                        floor=real_price.get('floor'),
                        area=real_price.get('representativeArea'),
                        exclusive_area=real_price.get('exclusiveArea'),
                        formatted_price=real_price.get('formattedPrice')
                    )
                    db.add(transaction_obj)
                    saved_count += 1

                db.commit()

                print(f"   ✅ 새 실거래: {saved_count}건")
                print(f"   ⏭️  기존거래: {skipped_count}건")

            # 4. 최종 통계
            print(f"\n{'='*80}")
            print(f"📊 데이터베이스 현황")
            print(f"{'='*80}")

            total_complexes = db.query(Complex).count()
            total_articles = db.query(Article).count()
            total_transactions = db.query(Transaction).count()

            print(f"\n단지: {total_complexes}개")
            print(f"매물: {total_articles}건")
            print(f"실거래: {total_transactions}건")

            print("\n✅ 저장 완료!\n")

        except Exception as e:
            db.rollback()
            print(f"\n❌ 에러 발생: {e}")
            raise
        finally:
            if close_session:
                db.close()
