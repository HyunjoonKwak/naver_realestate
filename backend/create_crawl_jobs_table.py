"""
crawl_jobs 테이블 생성 스크립트
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine
from app.models.complex import Base, CrawlJob

def create_crawl_jobs_table():
    """crawl_jobs 테이블 생성"""
    print("=" * 60)
    print("📊 crawl_jobs 테이블 생성")
    print("=" * 60)

    try:
        # CrawlJob 테이블만 생성 (다른 테이블은 이미 존재)
        CrawlJob.__table__.create(engine, checkfirst=True)
        print("✅ crawl_jobs 테이블이 생성되었습니다!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    create_crawl_jobs_table()
