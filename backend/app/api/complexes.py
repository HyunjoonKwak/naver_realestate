"""
단지 관련 API 엔드포인트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.complex import Complex, Article, Transaction
from app.schemas.complex import (
    ComplexResponse,
    ComplexDetailResponse,
    ArticleResponse,
    TransactionResponse
)

router = APIRouter(prefix="/complexes", tags=["complexes"])


@router.get("/", response_model=List[ComplexResponse])
def get_complexes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    단지 목록 조회

    - **skip**: 건너뛸 개수 (페이지네이션)
    - **limit**: 가져올 최대 개수 (최대 100)
    """
    complexes = db.query(Complex).offset(skip).limit(limit).all()
    return complexes


@router.get("/{complex_id}", response_model=ComplexDetailResponse)
def get_complex_detail(
    complex_id: str,
    include_articles: bool = Query(True, description="매물 정보 포함 여부"),
    include_transactions: bool = Query(True, description="실거래가 정보 포함 여부"),
    db: Session = Depends(get_db)
):
    """
    단지 상세 정보 조회

    - **complex_id**: 네이버 단지 ID
    - **include_articles**: 매물 정보 포함 여부
    - **include_transactions**: 실거래가 정보 포함 여부
    """
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()

    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # Pydantic 모델로 변환
    result = ComplexDetailResponse.model_validate(complex_obj)

    # 매물 정보 추가
    if include_articles:
        articles = db.query(Article).filter(
            Article.complex_id == complex_id,
            Article.is_active == True
        ).all()
        result.articles = [ArticleResponse.model_validate(a) for a in articles]

    # 실거래가 정보 추가
    if include_transactions:
        transactions = db.query(Transaction).filter(
            Transaction.complex_id == complex_id
        ).order_by(Transaction.trade_date.desc()).all()
        result.transactions = [TransactionResponse.model_validate(t) for t in transactions]

    return result


@router.get("/{complex_id}/articles", response_model=List[ArticleResponse])
def get_complex_articles(
    complex_id: str,
    trade_type: Optional[str] = Query(None, description="거래 유형 (매매/전세/월세)"),
    is_active: bool = Query(True, description="활성 매물만 조회"),
    db: Session = Depends(get_db)
):
    """
    단지의 매물 목록 조회

    - **complex_id**: 네이버 단지 ID
    - **trade_type**: 거래 유형 필터 (매매/전세/월세)
    - **is_active**: 활성 매물만 조회
    """
    query = db.query(Article).filter(Article.complex_id == complex_id)

    if trade_type:
        query = query.filter(Article.trade_type == trade_type)

    if is_active:
        query = query.filter(Article.is_active == True)

    articles = query.all()
    return articles


@router.get("/{complex_id}/transactions", response_model=List[TransactionResponse])
def get_complex_transactions(
    complex_id: str,
    limit: int = Query(50, ge=1, le=100, description="최대 개수"),
    db: Session = Depends(get_db)
):
    """
    단지의 실거래가 목록 조회

    - **complex_id**: 네이버 단지 ID
    - **limit**: 최대 개수 (최대 100)
    """
    transactions = db.query(Transaction).filter(
        Transaction.complex_id == complex_id
    ).order_by(Transaction.trade_date.desc()).limit(limit).all()

    return transactions


@router.get("/{complex_id}/stats")
def get_complex_stats(
    complex_id: str,
    db: Session = Depends(get_db)
):
    """
    단지 통계 정보

    - **complex_id**: 네이버 단지 ID
    """
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()

    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 매물 통계
    total_articles = db.query(Article).filter(
        Article.complex_id == complex_id,
        Article.is_active == True
    ).count()

    sale_count = db.query(Article).filter(
        Article.complex_id == complex_id,
        Article.is_active == True,
        Article.trade_type == "매매"
    ).count()

    lease_count = db.query(Article).filter(
        Article.complex_id == complex_id,
        Article.is_active == True,
        Article.trade_type == "전세"
    ).count()

    # 실거래 통계
    total_transactions = db.query(Transaction).filter(
        Transaction.complex_id == complex_id
    ).count()

    # 최근 실거래가
    recent_transaction = db.query(Transaction).filter(
        Transaction.complex_id == complex_id
    ).order_by(Transaction.trade_date.desc()).first()

    return {
        "complex_id": complex_id,
        "complex_name": complex_obj.complex_name,
        "articles": {
            "total": total_articles,
            "sale": sale_count,
            "lease": lease_count,
        },
        "transactions": {
            "total": total_transactions,
            "recent": TransactionResponse.model_validate(recent_transaction) if recent_transaction else None
        }
    }
