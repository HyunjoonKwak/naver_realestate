"""
크롤링한 데이터를 데이터베이스에 저장
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.core.database import SessionLocal
from app.models.complex import Complex, Article


def save_complex_data():
    """단지 및 매물 데이터 저장"""

    print("=" * 80)
    print("💾 데이터 저장")
    print("=" * 80)

    # 크롤링된 데이터 로드
    print("\n📖 데이터 파일 읽기...")

    # 단지 정보
    with open("captured_9.json", "r", encoding="utf-8") as f:
        complex_data = json.load(f)

    # 매물 정보
    with open("captured_11.json", "r", encoding="utf-8") as f:
        articles_data = json.load(f)

    db = SessionLocal()

    try:
        # 1. 단지 정보 저장
        print("\n🏢 단지 정보 저장...")

        # 기존 단지 확인
        existing_complex = db.query(Complex).filter(
            Complex.complex_id == complex_data['complexNo']
        ).first()

        if existing_complex:
            print(f"   ⚠️  이미 존재하는 단지: {complex_data['complexName']}")
            complex_obj = existing_complex
        else:
            complex_obj = Complex(
                complex_id=complex_data['complexNo'],
                complex_name=complex_data['complexName'],
                complex_type=complex_data.get('complexTypeName'),
                total_households=complex_data.get('totalHouseHoldCount'),
                total_dongs=complex_data.get('totalDongCount'),
                completion_date=complex_data.get('useApproveYmd'),
                min_area=complex_data.get('minArea'),
                max_area=complex_data.get('maxArea'),
                min_price=complex_data.get('minPrice'),
                max_price=complex_data.get('maxPrice'),
                min_lease_price=complex_data.get('minLeasePrice'),
                max_lease_price=complex_data.get('maxLeasePrice'),
                latitude=complex_data.get('latitude'),
                longitude=complex_data.get('longitude')
            )
            db.add(complex_obj)
            db.commit()
            print(f"   ✅ 저장 완료: {complex_data['complexName']}")

        # 2. 매물 정보 저장
        print("\n💰 매물 정보 저장...")

        article_list = articles_data.get('articleList', [])
        saved_count = 0
        skipped_count = 0

        for article in article_list:
            # 기존 매물 확인
            existing = db.query(Article).filter(
                Article.article_no == article['articleNo']
            ).first()

            if existing:
                skipped_count += 1
                continue

            article_obj = Article(
                article_no=article['articleNo'],
                complex_id=complex_data['complexNo'],
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

        print(f"   ✅ 저장: {saved_count}건")
        print(f"   ⚠️  건너뜀 (기존): {skipped_count}건")

        # 3. 결과 확인
        print("\n" + "=" * 80)
        print("📊 데이터베이스 현황")
        print("=" * 80)

        total_complexes = db.query(Complex).count()
        total_articles = db.query(Article).count()

        print(f"\n단지: {total_complexes}개")
        print(f"매물: {total_articles}건")

        print("\n✅ 완료!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 에러: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    save_complex_data()
