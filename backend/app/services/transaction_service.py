"""
실거래가 데이터 저장 및 처리 서비스
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.complex import Complex, Transaction
from app.services.molit_service import MOLITService

logger = logging.getLogger(__name__)


class TransactionService:
    """실거래가 데이터 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.molit_service = MOLITService()

    def fetch_and_save_transactions(
        self,
        complex_id: str,
        months: int = 6
    ) -> Dict:
        """
        국토부 API에서 실거래가를 조회하여 DB에 저장

        Args:
            complex_id: 단지 ID
            months: 조회할 개월 수

        Returns:
            처리 결과 딕셔너리
        """
        # 단지 정보 조회
        complex_obj = self.db.query(Complex).filter(
            Complex.complex_id == complex_id
        ).first()

        if not complex_obj:
            logger.error(f"단지를 찾을 수 없습니다: {complex_id}")
            return {"success": False, "message": "단지를 찾을 수 없습니다"}

        # 주소에서 시군구 코드 추출
        sigungu_code = self.molit_service.extract_sigungu_code(complex_obj.address or "")

        if not sigungu_code:
            logger.warning(f"시군구 코드 추출 실패: {complex_obj.address}")
            return {"success": False, "message": "시군구 코드를 추출할 수 없습니다"}

        # 실거래가 조회
        trades = self.molit_service.get_recent_trades(
            sigungu_code=sigungu_code,
            complex_name=complex_obj.complex_name,
            months=months
        )

        if not trades:
            logger.info(f"조회된 실거래가가 없습니다: {complex_obj.complex_name}")
            return {
                "success": True,
                "message": "조회된 실거래가가 없습니다",
                "saved_count": 0,
                "skipped_count": 0
            }

        # DB에 저장
        saved_count = 0
        skipped_count = 0

        for trade_raw in trades:
            trade_data = self.molit_service.parse_trade_to_dict(trade_raw)

            if not trade_data:
                skipped_count += 1
                continue

            # 중복 확인 (같은 날짜, 같은 면적, 같은 층, 같은 가격)
            existing = self.db.query(Transaction).filter(
                Transaction.complex_id == complex_id,
                Transaction.trade_date == trade_data["trade_date"],
                Transaction.exclusive_area == trade_data["exclusive_area"],
                Transaction.floor == trade_data["floor"],
                Transaction.deal_price == trade_data["deal_price"]
            ).first()

            if existing:
                skipped_count += 1
                continue

            # 새로운 거래 저장
            transaction = Transaction(
                complex_id=complex_id,
                trade_type="매매",
                trade_date=trade_data["trade_date"],
                deal_price=trade_data["deal_price"],
                formatted_price=self._format_price(trade_data["deal_price"]),
                floor=trade_data["floor"],
                area=trade_data["exclusive_area"],
                exclusive_area=trade_data["exclusive_area"]
            )

            self.db.add(transaction)
            saved_count += 1

        self.db.commit()

        logger.info(
            f"실거래가 저장 완료 - {complex_obj.complex_name}: "
            f"저장 {saved_count}건, 중복 {skipped_count}건"
        )

        return {
            "success": True,
            "message": "실거래가 저장 완료",
            "saved_count": saved_count,
            "skipped_count": skipped_count,
            "total_count": saved_count + skipped_count
        }

    def get_area_stats(
        self,
        complex_id: str,
        months: int = 6
    ) -> List[Dict]:
        """
        평형별 실거래가 통계 조회

        Args:
            complex_id: 단지 ID
            months: 조회 기간 (개월)

        Returns:
            평형별 통계 리스트
        """
        # N개월 전 날짜 계산
        start_date = datetime.now()
        start_date = start_date.replace(
            month=start_date.month - months if start_date.month > months else 12 - (months - start_date.month),
            year=start_date.year - 1 if start_date.month <= months else start_date.year
        )
        start_date_str = start_date.strftime("%Y%m%d")

        # 전용면적별 그룹핑하여 통계 조회
        results = self.db.query(
            Transaction.exclusive_area,
            func.avg(Transaction.deal_price).label('avg_price'),
            func.min(Transaction.deal_price).label('min_price'),
            func.max(Transaction.deal_price).label('max_price'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.complex_id == complex_id,
            Transaction.trade_date >= start_date_str
        ).group_by(
            Transaction.exclusive_area
        ).order_by(
            Transaction.exclusive_area
        ).all()

        area_stats = []
        for r in results:
            # 평형 계산 (㎡ → 평)
            pyeong = round(r.exclusive_area / 3.3058, 1)

            area_stats.append({
                "exclusive_area": r.exclusive_area,
                "area_name": f"{pyeong}평형",
                "avg_price": int(r.avg_price) if r.avg_price else 0,
                "min_price": r.min_price,
                "max_price": r.max_price,
                "count": r.count,
                "formatted_avg_price": self._format_price(int(r.avg_price)) if r.avg_price else "0"
            })

        return area_stats

    def _format_price(self, price: int) -> str:
        """
        가격 포맷팅 (만원 → 억/만원)

        Args:
            price: 가격 (만원)

        Returns:
            포맷된 가격 문자열
        """
        if price >= 10000:
            eok = price // 10000
            man = price % 10000
            if man > 0:
                return f"{eok}억 {man:,}만"
            else:
                return f"{eok}억"
        else:
            return f"{price:,}만"
