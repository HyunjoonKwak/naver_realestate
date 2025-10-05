"""
데이터베이스 마이그레이션 스크립트
- ArticleSnapshot, ArticleChange 테이블 추가
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine, init_db
from app.models.complex import Base

def migrate():
    """데이터베이스 마이그레이션 실행"""
    print("🔄 데이터베이스 마이그레이션 시작...")

    # 모든 테이블 생성 (이미 존재하는 테이블은 스킵)
    Base.metadata.create_all(bind=engine)

    print("✅ 마이그레이션 완료!")
    print("   - article_snapshots 테이블")
    print("   - article_changes 테이블")

if __name__ == "__main__":
    migrate()
