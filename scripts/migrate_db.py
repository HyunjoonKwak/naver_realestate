"""
데이터베이스 마이그레이션: 외래키 제약조건 추가

[Phase 1 개선사항]
- Article.complex_id에 FK 추가
- Transaction.complex_id에 FK 추가
- ArticleSnapshot.complex_id에 FK 추가
- ArticleChange.complex_id에 FK 추가
- 모든 FK에 CASCADE 삭제 규칙 적용
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import engine
from app.models.complex import Base

if __name__ == "__main__":
    print("=" * 80)
    print("🔄 데이터베이스 마이그레이션: 외래키 제약조건 추가")
    print("=" * 80)

    print(f"\n📍 데이터베이스: {engine.url}")

    # 커맨드라인 인자로 확인 스킵 가능
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("\n⚠️  --force 옵션: 확인 없이 진행합니다.")
    else:
        try:
            response = input("\n⚠️  모든 기존 테이블을 삭제하고 재생성합니다. 계속하시겠습니까? (yes/no): ")
            if response.lower() != 'yes':
                print("\n❌ 취소되었습니다.")
                sys.exit(0)
        except EOFError:
            print("\n⚠️  비대화형 모드에서는 --force 옵션을 사용하세요.")
            print("   예: backend/.venv/bin/python migrate_db.py --force")
            sys.exit(1)

    # 모든 테이블 삭제
    print("\n⏳ 기존 테이블 삭제 중...")
    Base.metadata.drop_all(bind=engine)
    print("   ✅ 삭제 완료")

    # 외래키 제약조건이 추가된 테이블 재생성
    print("\n⏳ 새 테이블 생성 중 (외래키 포함)...")
    Base.metadata.create_all(bind=engine)

    # 생성된 테이블 확인
    print("\n✅ 생성된 테이블 (외래키 CASCADE 적용):")
    for table in Base.metadata.sorted_tables:
        print(f"   - {table.name}")
        # 외래키 정보 출력
        for fk in table.foreign_keys:
            print(f"     └─ FK: {fk.parent.name} -> {fk.column} (ondelete={fk.ondelete})")

    print("\n" + "=" * 80)
    print("✅ 마이그레이션 완료!")
    print("=" * 80)
    print("\n📌 변경사항:")
    print("   - Article.complex_id → complexes.complex_id (CASCADE)")
    print("   - Transaction.complex_id → complexes.complex_id (CASCADE)")
    print("   - ArticleSnapshot.complex_id → complexes.complex_id (CASCADE)")
    print("   - ArticleChange.complex_id → complexes.complex_id (CASCADE)")
    print("\n💡 이제 단지 삭제 시 관련 데이터가 자동으로 삭제됩니다.\n")
