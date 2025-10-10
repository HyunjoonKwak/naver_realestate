"""
고급 네이버 부동산 크롤러
여러 단지의 매물, 단지정보, 실거래가를 수집
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import SessionLocal
from app.models.complex import Complex, Article, Transaction


class NaverRealEstateCrawler:
    """네이버 부동산 크롤러"""

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

                # 단지 상세 정보 (최초 1회만 저장)
                if 'complexes/' in url and 'complexNo' in str(data):
                    if self.complex_data is None:
                        self.complex_data = data
                        print(f"✅ 단지 정보 수집: {data.get('complexName', 'N/A')}")

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

    async def crawl_complex(self, complex_id: str):
        """특정 단지 크롤링"""
        print(f"\n{'='*80}")
        print(f"🏢 단지 크롤링 시작: {complex_id}")
        print(f"   [CRITICAL-DEBUG] This is UPDATED code with button clicking - Version 2.0")
        print(f"{'='*80}\n")

        # 데이터 초기화
        self.api_responses = []
        self.complex_data = None
        self.articles_data = None
        self.transactions_data = []

        async with async_playwright() as p:
            # 브라우저 실행
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-sandbox'
                ],
                slow_mo=100  # 느린 동작으로 안정성 향상
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )

            page = await context.new_page()

            # 응답 리스너 등록
            page.on("response", lambda response: asyncio.create_task(self.save_response(response)))

            # 먼저 메인 페이지에 접속해서 localStorage 설정
            print("   🔧 동일매물묶기 설정 준비 중...")
            await page.goto("https://new.land.naver.com", wait_until="domcontentloaded")

            # localStorage에 동일매물묶기 설정 저장
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

                await asyncio.sleep(1.5)  # API 응답 대기

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

    def save_to_database(self, complex_id: str):
        """데이터베이스에 저장"""
        db = SessionLocal()

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

                if existing_complex:
                    print(f"   ⚠️  기존 단지 업데이트: {self.complex_data['complexName']}")
                    # 기존 데이터 업데이트
                    for key, value in {
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
                    }.items():
                        setattr(existing_complex, key, value)
                    complex_obj = existing_complex
                else:
                    complex_obj = Complex(
                        complex_id=self.complex_data['complexNo'],
                        complex_name=self.complex_data['complexName'],
                        complex_type=self.complex_data.get('complexTypeName'),
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
            db.close()


async def main():
    """메인 함수"""
    # 크롤링할 단지 ID 목록
    complex_ids = [
        "1482",    # 향촌현대5차 (테스트)
    ]

    crawler = NaverRealEstateCrawler()

    for complex_id in complex_ids:
        # 크롤링
        result = await crawler.crawl_complex(complex_id)

        # 데이터베이스 저장
        crawler.save_to_database(complex_id)

        # 다음 단지 크롤링 전 대기
        if len(complex_ids) > 1:
            print("\n⏳ 다음 단지 크롤링까지 5초 대기...\n")
            await asyncio.sleep(5)

    print("\n🎉 모든 작업 완료!")


if __name__ == "__main__":
    asyncio.run(main())
