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
    TransactionResponse,
    ComplexCreate
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

    monthly_count = db.query(Article).filter(
        Article.complex_id == complex_id,
        Article.is_active == True,
        Article.trade_type == "월세"
    ).count()

    # 실거래 통계
    total_transactions = db.query(Transaction).filter(
        Transaction.complex_id == complex_id
    ).count()

    # 최근 실거래가
    recent_transaction = db.query(Transaction).filter(
        Transaction.complex_id == complex_id
    ).order_by(Transaction.trade_date.desc()).first()

    # Note: Article prices are stored as strings (e.g. "3억 5,000") so we cannot calculate min/max
    # Price range information comes from Complex table fields

    # 월세 가격 범위 계산 (보증금 및 월세)
    monthly_articles = db.query(Article.price, Article.monthly_rent).filter(
        Article.complex_id == complex_id,
        Article.is_active == True,
        Article.trade_type == "월세",
        Article.price.isnot(None)
    ).all()

    monthly_deposit_min = None
    monthly_deposit_max = None
    monthly_rent_min = None
    monthly_rent_max = None

    if monthly_articles:
        # price 문자열에서 숫자 추출하여 비교
        def extract_price_number(price_str):
            if not price_str:
                return 0
            import re
            # "12억", "5,000" 등에서 숫자 추출
            price_str = price_str.replace(',', '')
            if '억' in price_str:
                parts = price_str.split('억')
                eok = int(re.sub(r'\D', '', parts[0])) if parts[0].strip() else 0
                man = int(re.sub(r'\D', '', parts[1])) if len(parts) > 1 and parts[1].strip() else 0
                return eok * 10000 + man
            else:
                return int(re.sub(r'\D', '', price_str)) if re.sub(r'\D', '', price_str) else 0

        # 보증금 범위
        price_numbers = [(p[0], extract_price_number(p[0])) for p in monthly_articles if p[0]]
        if price_numbers:
            price_numbers.sort(key=lambda x: x[1])
            monthly_deposit_min = price_numbers[0][0]
            monthly_deposit_max = price_numbers[-1][0]

        # 월세 범위
        rent_numbers = [(p[1], extract_price_number(p[1])) for p in monthly_articles if p[1]]
        if rent_numbers:
            rent_numbers.sort(key=lambda x: x[1])
            monthly_rent_min = rent_numbers[0][0]
            monthly_rent_max = rent_numbers[-1][0]

    # 24시간 변경사항 계산
    from datetime import datetime, timezone, timedelta
    from app.models.complex import ArticleChange

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    changes_24h = db.query(ArticleChange).filter(
        ArticleChange.complex_id == complex_id,
        ArticleChange.detected_at >= cutoff
    ).all()

    changes_summary = {
        "new": sum(1 for c in changes_24h if c.change_type == 'NEW'),
        "removed": sum(1 for c in changes_24h if c.change_type == 'REMOVED'),
        "price_up": sum(1 for c in changes_24h if c.change_type == 'PRICE_UP'),
        "price_down": sum(1 for c in changes_24h if c.change_type == 'PRICE_DOWN')
    }

    return {
        "complex_id": complex_id,
        "complex_name": complex_obj.complex_name,
        "total_households": complex_obj.total_households,
        "address": complex_obj.address,
        "articles": {
            "total": total_articles,
            "sale": sale_count,
            "lease": lease_count,
            "monthly": monthly_count,
        },
        "price_range": {
            "sale_min": complex_obj.max_price,  # 비싼가격을 앞에
            "sale_max": complex_obj.min_price,  # 낮은가격을 뒤에
            "lease_min": complex_obj.max_lease_price,  # 비싼가격을 앞에
            "lease_max": complex_obj.min_lease_price,  # 낮은가격을 뒤에
            "monthly_deposit_min": monthly_deposit_max,  # 비싼가격을 앞에
            "monthly_deposit_max": monthly_deposit_min,  # 낮은가격을 뒤에
            "monthly_rent_min": monthly_rent_max,  # 비싼가격을 앞에
            "monthly_rent_max": monthly_rent_min,  # 낮은가격을 뒤에
        },
        "transactions": {
            "total": total_transactions,
            "recent": TransactionResponse.model_validate(recent_transaction) if recent_transaction else None
        },
        "changes_24h": changes_summary
    }


@router.post("/", response_model=ComplexResponse)
def create_complex(
    complex_data: ComplexCreate,
    db: Session = Depends(get_db)
):
    """
    새 단지 추가

    - **complex_id**: 네이버 단지 ID (필수)
    - **complex_name**: 단지명 (필수)
    - 나머지는 선택 사항
    """
    # 중복 체크
    existing = db.query(Complex).filter(Complex.complex_id == complex_data.complex_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 존재하는 단지입니다")

    # 새 단지 생성
    new_complex = Complex(**complex_data.model_dump())
    db.add(new_complex)
    db.commit()
    db.refresh(new_complex)

    return new_complex


@router.post("/{complex_id}/collect-address")
async def collect_complex_address(
    complex_id: str,
    db: Session = Depends(get_db)
):
    """
    단지 주소 수집 (크롤링)

    - **complex_id**: 네이버 단지 ID
    """
    from ..services.crawler_service import NaverRealEstateCrawler
    from fastapi import BackgroundTasks

    # 단지 조회
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()

    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 크롤러로 주소 수집 (collect_address=True)
    crawler = NaverRealEstateCrawler()
    result = await crawler.crawl_complex(complex_id, collect_address=True)

    # 수집된 주소 저장
    if result and result.get('complex') and result['complex'].get('address'):
        new_address = result['complex']['address']
        complex_obj.address = new_address
        db.commit()
        db.refresh(complex_obj)

        return {
            "success": True,
            "message": "주소가 수집되었습니다",
            "complex_id": complex_id,
            "address": new_address
        }
    else:
        return {
            "success": False,
            "message": "주소를 수집하지 못했습니다",
            "complex_id": complex_id
        }


@router.patch("/{complex_id}/address")
def update_complex_address(
    complex_id: str,
    address_data: dict,
    db: Session = Depends(get_db)
):
    """
    단지 주소 업데이트 (수동 입력)

    - **complex_id**: 네이버 단지 ID
    - **address**: 새로운 주소
    """
    # 단지 조회
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()

    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 주소 업데이트
    new_address = address_data.get('address')
    if not new_address:
        raise HTTPException(status_code=400, detail="주소를 입력해주세요")

    complex_obj.address = new_address
    db.commit()
    db.refresh(complex_obj)

    return {
        "message": "주소가 업데이트되었습니다",
        "complex_id": complex_id,
        "address": new_address
    }


@router.delete("/{complex_id}")
def delete_complex(
    complex_id: str,
    db: Session = Depends(get_db)
):
    """
    단지 삭제 (관련된 모든 매물 및 실거래가 함께 삭제)

    - **complex_id**: 네이버 단지 ID
    """
    # 단지 조회
    complex_obj = db.query(Complex).filter(Complex.complex_id == complex_id).first()

    if not complex_obj:
        raise HTTPException(status_code=404, detail="단지를 찾을 수 없습니다")

    # 관련된 매물 삭제
    db.query(Article).filter(Article.complex_id == complex_id).delete()

    # 관련된 실거래가 삭제
    db.query(Transaction).filter(Transaction.complex_id == complex_id).delete()

    # 관련된 스냅샷 삭제
    from app.models.complex import ArticleSnapshot, ArticleChange
    db.query(ArticleSnapshot).filter(ArticleSnapshot.complex_id == complex_id).delete()

    # 관련된 변동사항 삭제
    db.query(ArticleChange).filter(ArticleChange.complex_id == complex_id).delete()

    # 단지 삭제
    db.delete(complex_obj)
    db.commit()

    return {
        "message": "단지가 삭제되었습니다",
        "complex_id": complex_id,
        "complex_name": complex_obj.complex_name
    }
