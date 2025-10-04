"""
데이터베이스 테이블 삭제 및 재생성
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import engine
from app.models.complex import Base

if __name__ == "__main__":
    print("=" * 80)
    print("🗑️  데이터베이스 테이블 삭제 및 재생성")
    print("=" * 80)

    print(f"\n📍 데이터베이스: {engine.url}")

    # 모든 테이블 삭제
    print("\n⏳ 기존 테이블 삭제 중...")
    Base.metadata.drop_all(bind=engine)
    print("   ✅ 삭제 완료")

    # 테이블 재생성
    print("\n⏳ 새 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)

    # 생성된 테이블 확인
    print("\n✅ 생성된 테이블:")
    for table in Base.metadata.sorted_tables:
        print(f"   - {table.name}")

    print("\n✅ 완료!")
