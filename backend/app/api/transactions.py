"""
실거래가 관련 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.models.complex import Transaction, Complex
from app.schemas.complex import TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/stats/overview")
def get_overview_stats(db: Session = Depends(get_db)):
    """
    전체 실거래가 통계 개요

    모든 단지의 실거래가 통계를 요약합니다.
    """
    # 전체 거래 건수
    total_count = db.query(func.count(Transaction.id)).scalar() or 0

    # 단지별 거래 건수
    complex_stats = db.query(
        Complex.complex_id,
        Complex.complex_name,
        func.count(Transaction.id).label('transaction_count'),
        func.max(Transaction.trade_date).label('latest_date'),
        func.avg(Transaction.deal_price).label('avg_price'),
        func.min(Transaction.deal_price).label('min_price'),
        func.max(Transaction.deal_price).label('max_price')
    ).join(
        Transaction, Complex.complex_id == Transaction.complex_id
    ).group_by(
        Complex.complex_id, Complex.complex_name
    ).all()

    complex_list = [
        {
            "complex_id": stat.complex_id,
            "complex_name": stat.complex_name,
            "transaction_count": stat.transaction_count,
            "latest_date": stat.latest_date,
            "avg_price": int(stat.avg_price) if stat.avg_price else 0,
            "min_price": stat.min_price,
            "max_price": stat.max_price
        }
        for stat in complex_stats
    ]

    # 최근 거래 (최근 7일)
    from datetime import datetime, timedelta
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
    recent_count = db.query(func.count(Transaction.id)).filter(
        Transaction.trade_date >= seven_days_ago
    ).scalar() or 0

    return {
        "total_transactions": total_count,
        "recent_7days": recent_count,
        "complex_count": len(complex_list),
        "complexes": complex_list
    }


@router.get("/", response_model=List[TransactionResponse])
def search_transactions(
    complex_id: Optional[str] = Query(None, description="단지 ID"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYYMMDD)"),
    min_price: Optional[int] = Query(None, description="최소 거래가 (만원)"),
    max_price: Optional[int] = Query(None, description="최대 거래가 (만원)"),
    min_floor: Optional[int] = Query(None, description="최소 층"),
    max_floor: Optional[int] = Query(None, description="최대 층"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    실거래가 검색

    다양한 조건으로 실거래가를 검색합니다.
    """
    query = db.query(Transaction)

    # 필터 적용
    if complex_id:
        query = query.filter(Transaction.complex_id == complex_id)

    if start_date:
        query = query.filter(Transaction.trade_date >= start_date)

    if end_date:
        query = query.filter(Transaction.trade_date <= end_date)

    if min_price:
        query = query.filter(Transaction.deal_price >= min_price)

    if max_price:
        query = query.filter(Transaction.deal_price <= max_price)

    if min_floor:
        query = query.filter(Transaction.floor >= min_floor)

    if max_floor:
        query = query.filter(Transaction.floor <= max_floor)

    # 최신순 정렬
    query = query.order_by(Transaction.trade_date.desc())

    # 페이지네이션
    transactions = query.offset(skip).limit(limit).all()

    return transactions


@router.get("/recent", response_model=List[TransactionResponse])
def get_recent_transactions(
    limit: int = Query(20, ge=1, le=100, description="최대 개수"),
    db: Session = Depends(get_db)
):
    """
    최근 실거래가 목록

    - **limit**: 최대 개수 (최대 100)
    """
    transactions = db.query(Transaction).order_by(
        Transaction.trade_date.desc()
    ).limit(limit).all()

    return transactions


@router.get("/stats/price-trend")
def get_price_trend(
    complex_id: str = Query(..., description="단지 ID"),
    months: int = Query(6, ge=1, le=24, description="조회 기간 (개월)"),
    db: Session = Depends(get_db)
):
    """
    가격 추이 통계

    최근 N개월간의 평균 거래가 추이를 조회합니다.

    - **complex_id**: 단지 ID
    - **months**: 조회 기간 (1~24개월)
    """
    # 단지 확인
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()
    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 월별 평균 거래가
    results = db.query(
        func.substr(Transaction.trade_date, 1, 6).label('month'),
        func.avg(Transaction.deal_price).label('avg_price'),
        func.min(Transaction.deal_price).label('min_price'),
        func.max(Transaction.deal_price).label('max_price'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.complex_id == complex_id
    ).group_by(
        func.substr(Transaction.trade_date, 1, 6)
    ).order_by(
        func.substr(Transaction.trade_date, 1, 6).desc()
    ).limit(months).all()

    trend_data = [
        {
            "month": r.month,
            "avg_price": int(r.avg_price) if r.avg_price else 0,
            "min_price": r.min_price,
            "max_price": r.max_price,
            "count": r.count
        }
        for r in results
    ]

    return {
        "complex_id": complex_id,
        "complex_name": complex_obj.complex_name,
        "period_months": months,
        "trend": trend_data
    }


@router.get("/stats/area-price")
def get_area_price_stats(
    complex_id: str = Query(..., description="단지 ID"),
    db: Session = Depends(get_db)
):
    """
    면적별 가격 통계

    단지의 면적별 평균 거래가를 조회합니다.

    - **complex_id**: 단지 ID
    """
    # 단지 확인
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()
    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 면적별 통계
    results = db.query(
        Transaction.area,
        func.avg(Transaction.deal_price).label('avg_price'),
        func.min(Transaction.deal_price).label('min_price'),
        func.max(Transaction.deal_price).label('max_price'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.complex_id == complex_id
    ).group_by(
        Transaction.area
    ).order_by(
        Transaction.area
    ).all()

    area_stats = [
        {
            "area": r.area,
            "avg_price": int(r.avg_price) if r.avg_price else 0,
            "min_price": r.min_price,
            "max_price": r.max_price,
            "count": r.count
        }
        for r in results
    ]

    return {
        "complex_id": complex_id,
        "complex_name": complex_obj.complex_name,
        "area_stats": area_stats
    }


@router.get("/stats/floor-premium")
def get_floor_premium_stats(
    complex_id: str = Query(..., description="단지 ID"),
    db: Session = Depends(get_db)
):
    """
    층별 프리미엄 분석

    층별 평균 거래가를 분석합니다.

    - **complex_id**: 단지 ID
    """
    # 단지 확인
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()
    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 층 범위별 통계 (저층/중층/고층)
    low_floor = db.query(
        func.avg(Transaction.deal_price)
    ).filter(
        and_(
            Transaction.complex_id == complex_id,
            Transaction.floor <= 10
        )
    ).scalar()

    mid_floor = db.query(
        func.avg(Transaction.deal_price)
    ).filter(
        and_(
            Transaction.complex_id == complex_id,
            Transaction.floor > 10,
            Transaction.floor <= 20
        )
    ).scalar()

    high_floor = db.query(
        func.avg(Transaction.deal_price)
    ).filter(
        and_(
            Transaction.complex_id == complex_id,
            Transaction.floor > 20
        )
    ).scalar()

    return {
        "complex_id": complex_id,
        "complex_name": complex_obj.complex_name,
        "floor_premium": {
            "low_floor": {
                "range": "1~10층",
                "avg_price": int(low_floor) if low_floor else 0
            },
            "mid_floor": {
                "range": "11~20층",
                "avg_price": int(mid_floor) if mid_floor else 0
            },
            "high_floor": {
                "range": "21층 이상",
                "avg_price": int(high_floor) if high_floor else 0
            }
        }
    }


@router.post("/fetch/{complex_id}")
def fetch_transactions_from_molit(
    complex_id: str,
    months: int = Query(6, ge=1, le=24, description="조회 기간 (개월)"),
    db: Session = Depends(get_db)
):
    """
    국토부 API에서 실거래가를 조회하여 DB에 저장

    - **complex_id**: 단지 ID
    - **months**: 조회 기간 (1~24개월)
    """
    service = TransactionService(db)
    result = service.fetch_and_save_transactions(complex_id, months)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/fetch-all")
def fetch_all_transactions_from_molit(
    months: int = Query(6, ge=1, le=24, description="조회 기간 (개월)"),
    db: Session = Depends(get_db)
):
    """
    모든 단지의 실거래가를 국토부 API에서 조회하여 DB에 저장

    - **months**: 조회 기간 (1~24개월)
    """
    # 모든 단지 조회
    complexes = db.query(Complex).all()

    if not complexes:
        return {
            "success": False,
            "message": "등록된 단지가 없습니다"
        }

    service = TransactionService(db)
    results = []
    success_count = 0
    fail_count = 0

    for complex_obj in complexes:
        result = service.fetch_and_save_transactions(complex_obj.complex_id, months)
        results.append({
            "complex_id": complex_obj.complex_id,
            "complex_name": complex_obj.complex_name,
            "success": result["success"],
            "new_count": result.get("new_count", 0),
            "message": result.get("message", "")
        })

        if result["success"]:
            success_count += 1
        else:
            fail_count += 1

    return {
        "success": True,
        "total_complexes": len(complexes),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results
    }


@router.get("/stats/area-summary/{complex_id}")
def get_area_summary_stats(
    complex_id: str,
    months: int = Query(6, ge=1, le=24, description="조회 기간 (개월)"),
    db: Session = Depends(get_db)
):
    """
    평형별 실거래가 요약 통계

    최근 N개월간 평형별 평균/최고/최저가와 거래건수를 조회합니다.

    - **complex_id**: 단지 ID
    - **months**: 조회 기간 (1~24개월)
    """
    # 단지 확인
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()
    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    service = TransactionService(db)
    area_stats = service.get_area_stats(complex_id, months)

    return {
        "complex_id": complex_id,
        "complex_name": complex_obj.complex_name,
        "period_months": months,
        "area_stats": area_stats
    }
