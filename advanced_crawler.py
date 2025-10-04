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

                # 단지 상세 정보
                if 'complexes/' in url and 'complexNo' in str(data):
                    self.complex_data = data
                    print(f"✅ 단지 정보 수집: {data.get('complexName', 'N/A')}")

                # 매물 목록
                elif 'articleList' in str(data) and isinstance(data, dict):
                    if 'articleList' in data:
                        self.articles_data = data
                        count = len(data.get('articleList', []))
                        print(f"✅ 매물 정보 수집: {count}건")

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
        print(f"{'='*80}\n")

        # 데이터 초기화
        self.api_responses = []
        self.complex_data = None
        self.articles_data = None
        self.transactions_data = []

        async with async_playwright() as p:
            # 브라우저 실행
            browser = await p.chromium.launch(
                headless=False,  # Bot 탐지 방지
                args=['--disable-blink-features=AutomationControlled']
            )

            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )

            page = await context.new_page()

            # 응답 리스너 등록
            page.on("response", lambda response: asyncio.create_task(self.save_response(response)))

            # 페이지 이동
            url = f"https://new.land.naver.com/complexes/{complex_id}"
            print(f"🌐 접속: {url}")

            await page.goto(url, wait_until="networkidle")

            # 페이지 로딩 대기
            await asyncio.sleep(3)

            # 스크롤하여 추가 데이터 로드
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(2)

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

                for article in article_list:
                    existing = db.query(Article).filter(
                        Article.article_no == article['articleNo']
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
                        article_no=article['articleNo'],
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
                        confirm_date=article.get('articleConfirmYmd')
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
        "109208",  # 시범반도유보라아이비파크4.0
        # 여기에 추가 단지 ID 추가 가능
        # "105416",  # 동탄역KCC스위첸
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
