"""
매물 변동 추적 서비스
"""
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uuid
import re

from app.models.complex import Article, ArticleSnapshot, ArticleChange


class ArticleTracker:
    """매물 변동 추적 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def create_snapshot(self, complex_id: str, articles: List[Article]) -> str:
        """
        현재 매물 상태의 스냅샷 생성

        Args:
            complex_id: 단지 ID
            articles: 현재 매물 리스트

        Returns:
            crawl_session_id: 크롤링 세션 ID
        """
        crawl_session_id = str(uuid.uuid4())
        snapshot_date = datetime.now()

        for article in articles:
            snapshot = ArticleSnapshot(
                complex_id=complex_id,
                article_no=article.article_no,
                trade_type=article.trade_type,
                price=article.price,
                area_name=article.area_name,
                area1=article.area1,
                floor_info=article.floor_info,
                direction=article.direction,
                building_name=article.building_name,
                realtor_name=article.realtor_name,
                same_addr_cnt=article.same_addr_cnt,
                snapshot_date=snapshot_date,
                crawl_session_id=crawl_session_id
            )
            self.db.add(snapshot)

        self.db.commit()
        print(f"✅ 스냅샷 생성 완료: {len(articles)}건 (세션: {crawl_session_id[:8]}...)")
        return crawl_session_id

    def detect_changes(self, complex_id: str) -> List[ArticleChange]:
        """
        최근 2개 스냅샷을 비교하여 변동사항 감지

        Args:
            complex_id: 단지 ID

        Returns:
            감지된 변동사항 리스트
        """
        # 최근 2개의 스냅샷 세션 가져오기
        from sqlalchemy import func as sqlfunc
        recent_sessions = (
            self.db.query(
                ArticleSnapshot.crawl_session_id,
                sqlfunc.max(ArticleSnapshot.snapshot_date).label('snapshot_date')
            )
            .filter(ArticleSnapshot.complex_id == complex_id)
            .group_by(ArticleSnapshot.crawl_session_id)
            .order_by(desc('snapshot_date'))
            .limit(2)
            .all()
        )

        if len(recent_sessions) < 2:
            print("ℹ️  이전 스냅샷이 없어 변동사항을 감지할 수 없습니다.")
            return []

        prev_session_id = recent_sessions[1][0]
        curr_session_id = recent_sessions[0][0]

        # 이전 스냅샷
        prev_snapshots = (
            self.db.query(ArticleSnapshot)
            .filter(
                ArticleSnapshot.complex_id == complex_id,
                ArticleSnapshot.crawl_session_id == prev_session_id
            )
            .all()
        )

        # 현재 스냅샷
        curr_snapshots = (
            self.db.query(ArticleSnapshot)
            .filter(
                ArticleSnapshot.complex_id == complex_id,
                ArticleSnapshot.crawl_session_id == curr_session_id
            )
            .all()
        )

        # 매물 번호별로 매핑
        prev_map = {s.article_no: s for s in prev_snapshots}
        curr_map = {s.article_no: s for s in curr_snapshots}

        changes = []

        # 1. 신규 매물 감지
        new_articles = set(curr_map.keys()) - set(prev_map.keys())
        for article_no in new_articles:
            snapshot = curr_map[article_no]
            change = ArticleChange(
                complex_id=complex_id,
                article_no=article_no,
                change_type='NEW',
                new_price=snapshot.price,
                trade_type=snapshot.trade_type,
                area_name=snapshot.area_name,
                building_name=snapshot.building_name,
                floor_info=snapshot.floor_info,
                to_snapshot_id=snapshot.id
            )
            changes.append(change)
            self.db.add(change)

        # 2. 삭제된 매물 감지
        removed_articles = set(prev_map.keys()) - set(curr_map.keys())
        for article_no in removed_articles:
            snapshot = prev_map[article_no]
            change = ArticleChange(
                complex_id=complex_id,
                article_no=article_no,
                change_type='REMOVED',
                old_price=snapshot.price,
                trade_type=snapshot.trade_type,
                area_name=snapshot.area_name,
                building_name=snapshot.building_name,
                floor_info=snapshot.floor_info,
                from_snapshot_id=snapshot.id
            )
            changes.append(change)
            self.db.add(change)

        # 3. 가격 변동 감지
        common_articles = set(prev_map.keys()) & set(curr_map.keys())
        for article_no in common_articles:
            prev_snap = prev_map[article_no]
            curr_snap = curr_map[article_no]

            if prev_snap.price != curr_snap.price:
                # 가격에서 숫자만 추출
                prev_price_num = self._extract_price_number(prev_snap.price)
                curr_price_num = self._extract_price_number(curr_snap.price)

                if prev_price_num and curr_price_num:
                    price_diff = curr_price_num - prev_price_num

                    # 실제 가격 차이가 없으면 스킵 (문자열만 다른 경우)
                    if price_diff == 0:
                        continue

                    price_change_percent = (price_diff / prev_price_num) * 100

                    change_type = 'PRICE_UP' if price_diff > 0 else 'PRICE_DOWN'

                    change = ArticleChange(
                        complex_id=complex_id,
                        article_no=article_no,
                        change_type=change_type,
                        old_price=prev_snap.price,
                        new_price=curr_snap.price,
                        price_change_amount=price_diff,
                        price_change_percent=round(price_change_percent, 2),
                        trade_type=curr_snap.trade_type,
                        area_name=curr_snap.area_name,
                        building_name=curr_snap.building_name,
                        floor_info=curr_snap.floor_info,
                        from_snapshot_id=prev_snap.id,
                        to_snapshot_id=curr_snap.id
                    )
                    changes.append(change)
                    self.db.add(change)

        self.db.commit()

        print(f"""
📊 변동사항 감지 완료:
   - 신규: {len(new_articles)}건
   - 삭제: {len(removed_articles)}건
   - 가격변동: {len([c for c in changes if c.change_type in ['PRICE_UP', 'PRICE_DOWN']])}건
        """)

        return changes

    def get_recent_changes(
        self,
        complex_id: str,
        hours: int = 24,
        limit: Optional[int] = None
    ) -> List[ArticleChange]:
        """
        최근 N시간 이내 변동사항 조회

        Args:
            complex_id: 단지 ID
            hours: 조회할 시간 범위 (기본: 24시간)
            limit: 최대 조회 건수

        Returns:
            변동사항 리스트
        """
        from datetime import timedelta

        since = datetime.now() - timedelta(hours=hours)

        query = (
            self.db.query(ArticleChange)
            .filter(
                ArticleChange.complex_id == complex_id,
                ArticleChange.detected_at >= since
            )
            .order_by(desc(ArticleChange.detected_at))
        )

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_change_summary(self, complex_id: str, hours: int = 24) -> Dict:
        """
        변동사항 요약 정보

        Args:
            complex_id: 단지 ID
            hours: 조회할 시간 범위

        Returns:
            요약 정보 딕셔너리
        """
        changes = self.get_recent_changes(complex_id, hours=hours)

        new_count = len([c for c in changes if c.change_type == 'NEW'])
        removed_count = len([c for c in changes if c.change_type == 'REMOVED'])
        price_up_count = len([c for c in changes if c.change_type == 'PRICE_UP'])
        price_down_count = len([c for c in changes if c.change_type == 'PRICE_DOWN'])

        # 가장 큰 가격 변동 찾기
        price_changes = [c for c in changes if c.change_type in ['PRICE_UP', 'PRICE_DOWN']]
        most_significant_change = None
        if price_changes:
            most_significant_change = max(
                price_changes,
                key=lambda c: abs(c.price_change_percent) if c.price_change_percent else 0
            )

        return {
            'new': new_count,
            'removed': removed_count,
            'price_up': price_up_count,
            'price_down': price_down_count,
            'total': len(changes),
            'most_significant_change': most_significant_change
        }

    @staticmethod
    def _extract_price_number(price_str: str) -> Optional[int]:
        """가격 문자열에서 숫자 추출 (만원 단위)"""
        if not price_str:
            return None

        # 모든 숫자와 쉼표만 추출
        numbers = re.sub(r'[^0-9,]', '', price_str)
        numbers = numbers.replace(',', '')

        if numbers:
            return int(numbers)

        return None
