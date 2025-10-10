"""
데이터베이스 데이터 확인
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import SessionLocal
from app.models.complex import Complex, Article, Transaction


def check_database():
    """데이터베이스 데이터 확인"""
    db = SessionLocal()

    try:
        print("=" * 80)
        print("📊 데이터베이스 데이터 확인")
        print("=" * 80)

        # 1. 단지 정보
        print("\n🏢 단지 정보")
        print("-" * 80)
        complexes = db.query(Complex).all()
        for c in complexes:
            print(f"\n단지 ID: {c.complex_id}")
            print(f"단지명: {c.complex_name}")
            print(f"유형: {c.complex_type}")
            print(f"세대수: {c.total_households}세대")
            print(f"동수: {c.total_dongs}개동")
            print(f"준공일: {c.completion_date}")
            print(f"면적: {c.min_area}㎡ ~ {c.max_area}㎡")
            print(f"매매가: {c.min_price}만원 ~ {c.max_price}만원")
            print(f"전세가: {c.min_lease_price}만원 ~ {c.max_lease_price}만원")
            print(f"위치: ({c.latitude}, {c.longitude})")

        # 2. 매물 정보 (최근 5건)
        print("\n\n💰 매물 정보 (최근 5건)")
        print("-" * 80)
        articles = db.query(Article).order_by(Article.id.desc()).limit(5).all()
        for a in articles:
            print(f"\n매물번호: {a.article_no}")
            print(f"거래유형: {a.trade_type}")
            print(f"가격: {a.price} (변동: {a.price_change_state})")
            print(f"면적: {a.area_name} ({a.area1}㎡/{a.area2}㎡)")
            print(f"층: {a.floor_info} / 방향: {a.direction}")
            print(f"동: {a.building_name}")
            print(f"특징: {a.feature_desc}")
            print(f"중개사: {a.realtor_name}")
            print(f"확인일: {a.confirm_date}")

        # 3. 실거래가 정보
        print("\n\n📊 실거래가 정보")
        print("-" * 80)
        transactions = db.query(Transaction).all()
        for t in transactions:
            print(f"\n단지 ID: {t.complex_id}")
            print(f"거래유형: {t.trade_type}")
            print(f"거래일: {t.trade_date}")
            print(f"거래가: {t.deal_price}만원 ({t.formatted_price})")
            print(f"층: {t.floor}층")
            print(f"면적: {t.area}㎡ (전용: {t.exclusive_area}㎡)")

        # 4. 통계
        print("\n\n📈 통계")
        print("-" * 80)
        print(f"총 단지: {db.query(Complex).count()}개")
        print(f"총 매물: {db.query(Article).count()}건")
        print(f"총 실거래: {db.query(Transaction).count()}건")

        print("\n✅ 완료!")

    finally:
        db.close()


if __name__ == "__main__":
    check_database()
