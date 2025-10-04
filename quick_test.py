"""빠른 테스트"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.crawler.naver_land_crawler import NaverLandCrawler


async def quick_test():
    print("🚀 빠른 테스트 시작")

    async with NaverLandCrawler(headless=True) as crawler:
        result = await crawler.crawl_complex("109208")

        print("\n" + "="*80)
        print("결과:")
        print("="*80)

        if result['complex_detail']:
            print(f"✅ 단지: {result['complex_detail'].get('complexName')}")

        if result['articles']:
            article_count = len(result['articles'].get('articleList', []))
            print(f"✅ 매물: {article_count}건")

        if result['trades']:
            print(f"✅ 실거래: 있음")

        print("\n완료!")


if __name__ == "__main__":
    asyncio.run(quick_test())
