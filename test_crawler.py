"""
네이버 부동산 크롤러 테스트
"""
import asyncio
import sys
import json
from pathlib import Path

# backend/app를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.crawler.naver_crawler import NaverRealEstateCrawler


async def test_crawler():
    """크롤러 기능 테스트"""

    print("=" * 80)
    print("🧪 네이버 부동산 크롤러 테스트")
    print("=" * 80)

    # 크롤러 초기화 (headless=False로 하면 브라우저가 보임)
    async with NaverRealEstateCrawler(headless=False) as crawler:

        # 1. 단지 검색 테스트
        print("\n" + "=" * 80)
        print("TEST 1: 단지 검색")
        print("=" * 80)

        complexes = await crawler.search_complexes("래미안", limit=5)

        if complexes:
            print(f"\n✅ 검색 결과 {len(complexes)}개:")
            for i, complex_info in enumerate(complexes, 1):
                print(f"\n{i}. {complex_info.get('name', 'Unknown')}")
                print(f"   ID: {complex_info.get('id')}")
                print(f"   주소: {complex_info.get('address')}")
                print(f"   URL: {complex_info.get('url')}")

            # 첫 번째 단지로 상세 정보 테스트
            first_complex = complexes[0]
            complex_id = first_complex.get('id')

            if complex_id:
                # 2. 단지 상세 정보 조회 테스트
                print("\n" + "=" * 80)
                print("TEST 2: 단지 상세 정보 조회")
                print("=" * 80)

                detail = await crawler.get_complex_detail(complex_id)

                print(f"\n단지명: {detail.get('name')}")
                print(f"주소: {detail.get('address')}")
                print(f"준공년도: {detail.get('completion_year')}")
                print(f"총 세대수: {detail.get('total_households')}")

                # 3. 매물 정보 조회 테스트
                print("\n" + "=" * 80)
                print("TEST 3: 매물 정보 조회")
                print("=" * 80)

                listings = await crawler.get_listings(complex_id, "매매")

                if listings:
                    print(f"\n✅ 매물 {len(listings)}개 발견:")
                    for i, listing in enumerate(listings[:5], 1):  # 최대 5개만 출력
                        print(f"\n{i}. 가격: {listing.get('price')}")
                        print(f"   면적: {listing.get('area')}")
                        print(f"   층: {listing.get('floor')}")
                else:
                    print("⚠️  매물 정보를 찾지 못했습니다.")

                # 4. 실거래가 조회 테스트
                print("\n" + "=" * 80)
                print("TEST 4: 실거래가 조회")
                print("=" * 80)

                transactions = await crawler.get_transactions(complex_id)

                if transactions:
                    print(f"\n✅ 실거래 {len(transactions)}개 발견:")
                    for i, trans in enumerate(transactions[:5], 1):  # 최대 5개만 출력
                        print(f"\n{i}. 거래일: {trans.get('date')}")
                        print(f"   가격: {trans.get('price')}")
                        print(f"   면적: {trans.get('area')}")
                        print(f"   층: {trans.get('floor')}")
                else:
                    print("⚠️  실거래 정보를 찾지 못했습니다.")

                # 스크린샷 저장
                await crawler.take_screenshot("test_final_page.png")

            else:
                print("❌ 단지 ID를 찾을 수 없습니다.")

        else:
            print("❌ 검색 결과가 없습니다.")

    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)


async def test_specific_complex():
    """특정 단지 ID로 직접 테스트 (단지 ID를 알고 있을 때)"""

    print("=" * 80)
    print("🧪 특정 단지 직접 조회 테스트")
    print("=" * 80)

    # 예시 단지 ID (실제로는 검색을 통해 얻어야 함)
    # complex_id = "12345"  # 실제 단지 ID로 변경

    # async with NaverRealEstateCrawler(headless=False) as crawler:
    #     detail = await crawler.get_complex_detail(complex_id)
    #     print(json.dumps(detail, ensure_ascii=False, indent=2))

    print("⚠️  이 테스트를 실행하려면 실제 단지 ID가 필요합니다.")
    print("먼저 test_crawler()를 실행하여 단지 ID를 찾으세요.")


if __name__ == "__main__":
    print("\n어떤 테스트를 실행하시겠습니까?")
    print("1. 전체 테스트 (단지 검색 → 상세 정보 → 매물 → 실거래가)")
    print("2. 특정 단지 직접 조회")
    print()

    choice = input("선택 (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(test_crawler())
    elif choice == "2":
        asyncio.run(test_specific_complex())
    else:
        print("1 또는 2를 입력하세요.")
