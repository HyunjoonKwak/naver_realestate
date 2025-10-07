"""
샘플 브리핑 데이터 생성 스크립트
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models.complex import Complex, Article, ArticleSnapshot, ArticleChange


def create_sample_data():
    """샘플 변동사항 데이터 생성"""
    db = SessionLocal()

    try:
        # 기존 단지 조회
        complexes = db.query(Complex).limit(3).all()

        if not complexes:
            print("❌ 데이터베이스에 단지가 없습니다. 먼저 단지를 추가해주세요.")
            return False

        print(f"✅ {len(complexes)}개 단지 발견")

        # 기존 변동사항 삭제 (is_read=False인 것만)
        deleted = db.query(ArticleChange).filter(ArticleChange.is_read == False).delete()
        db.commit()
        print(f"🗑️  기존 미읽음 변동사항 {deleted}건 삭제")

        total_changes = 0

        for complex_obj in complexes:
            print(f"\n📍 단지: {complex_obj.complex_name}")

            # 각 단지당 5-15개의 샘플 변동사항 생성
            num_changes = random.randint(5, 15)

            for i in range(num_changes):
                change_type = random.choice(['NEW', 'REMOVED', 'PRICE_UP', 'PRICE_DOWN'])

                # 랜덤 시간 (최근 7일 이내)
                days_ago = random.randint(0, 7)
                hours_ago = random.randint(0, 23)
                detected_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)

                # 면적과 가격 설정
                areas = ['59㎡', '84㎡', '114㎡', '135㎡']
                area = random.choice(areas)

                if change_type == 'NEW':
                    trade_type = random.choice(['매매', '전세', '월세'])
                    if trade_type == '매매':
                        price = f"{random.randint(8, 15)}억 {random.randint(0, 9)}천"
                    elif trade_type == '전세':
                        price = f"{random.randint(5, 10)}억"
                    else:
                        price = f"{random.randint(3, 6)}억 / {random.randint(50, 150)}"

                    change = ArticleChange(
                        complex_id=complex_obj.complex_id,
                        change_type=change_type,
                        article_no=f"SAMPLE_{complex_obj.complex_id}_{i}_{int(detected_at.timestamp())}",
                        trade_type=trade_type,
                        area_name=area,
                        new_price=price,
                        old_price=None,
                        price_change_amount=None,
                        price_change_percent=None,
                        detected_at=detected_at,
                        is_read=False
                    )

                elif change_type == 'REMOVED':
                    trade_type = random.choice(['매매', '전세'])
                    if trade_type == '매매':
                        price = f"{random.randint(8, 15)}억"
                    else:
                        price = f"{random.randint(5, 10)}억"

                    change = ArticleChange(
                        complex_id=complex_obj.complex_id,
                        change_type=change_type,
                        article_no=f"SAMPLE_{complex_obj.complex_id}_{i}_{int(detected_at.timestamp())}",
                        trade_type=trade_type,
                        area_name=area,
                        old_price=price,
                        new_price=None,
                        price_change_amount=None,
                        price_change_percent=None,
                        detected_at=detected_at,
                        is_read=False
                    )

                elif change_type in ['PRICE_UP', 'PRICE_DOWN']:
                    trade_type = random.choice(['매매', '전세'])

                    if trade_type == '매매':
                        base_price = random.randint(80000, 150000)  # 만원 단위
                        if change_type == 'PRICE_UP':
                            change_amount = random.randint(2000, 10000)
                            new_price_val = base_price + change_amount
                        else:
                            change_amount = random.randint(2000, 10000)
                            new_price_val = base_price - change_amount

                        old_price = f"{base_price // 10000}억 {(base_price % 10000) // 1000}천"
                        new_price = f"{new_price_val // 10000}억 {(new_price_val % 10000) // 1000}천"
                        percent = (change_amount / base_price) * 100

                    else:  # 전세
                        base_price = random.randint(50000, 100000)
                        if change_type == 'PRICE_UP':
                            change_amount = random.randint(2000, 8000)
                            new_price_val = base_price + change_amount
                        else:
                            change_amount = random.randint(2000, 8000)
                            new_price_val = base_price - change_amount

                        old_price = f"{base_price // 10000}억"
                        new_price = f"{new_price_val // 10000}억"
                        percent = (change_amount / base_price) * 100

                    change = ArticleChange(
                        complex_id=complex_obj.complex_id,
                        change_type=change_type,
                        article_no=f"SAMPLE_{complex_obj.complex_id}_{i}_{int(detected_at.timestamp())}",
                        trade_type=trade_type,
                        area_name=area,
                        old_price=old_price,
                        new_price=new_price,
                        price_change_amount=change_amount * 10000,  # 원 단위로 저장
                        price_change_percent=percent,
                        detected_at=detected_at,
                        is_read=False
                    )

                db.add(change)
                total_changes += 1

            print(f"  ✅ {num_changes}건의 변동사항 생성")

        db.commit()
        print(f"\n🎉 총 {total_changes}건의 샘플 변동사항이 생성되었습니다!")
        return True

    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("📊 샘플 브리핑 데이터 생성")
    print("=" * 60)

    if create_sample_data():
        print("\n✅ 완료! 이제 브리핑을 테스트할 수 있습니다.")
        print("\n다음 명령어로 브리핑을 확인하세요:")
        print("  curl 'http://localhost:8000/api/briefing/preview?days=7'")
        print("\nDiscord로 발송하려면:")
        print("  curl -X POST 'http://localhost:8000/api/briefing/send?days=7'")
