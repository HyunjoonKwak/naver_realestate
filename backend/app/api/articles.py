"""
매물 관련 API 엔드포인트
"""
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.models.complex import Article, ArticleChange
from app.schemas.complex import ArticleResponse
from app.services.article_tracker import ArticleTracker

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_model=List[ArticleResponse])
def search_articles(
    complex_id: Optional[str] = Query(None, description="단지 ID"),
    trade_type: Optional[str] = Query(None, description="거래 유형 (매매/전세/월세)"),
    area_name: Optional[str] = Query(None, description="면적 타입"),
    building_name: Optional[str] = Query(None, description="동 정보"),
    min_area: Optional[float] = Query(None, description="최소 면적(㎡)"),
    max_area: Optional[float] = Query(None, description="최대 면적(㎡)"),
    is_active: bool = Query(True, description="활성 매물만"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    매물 검색

    다양한 조건으로 매물을 검색합니다.
    """
    query = db.query(Article)

    # 필터 적용
    if complex_id:
        query = query.filter(Article.complex_id == complex_id)

    if trade_type:
        query = query.filter(Article.trade_type == trade_type)

    if area_name:
        query = query.filter(Article.area_name == area_name)

    if building_name:
        query = query.filter(Article.building_name.like(f"%{building_name}%"))

    if min_area:
        query = query.filter(Article.area1 >= min_area)

    if max_area:
        query = query.filter(Article.area1 <= max_area)

    if is_active:
        query = query.filter(Article.is_active == True)

    # 최신순 정렬
    query = query.order_by(Article.last_seen_at.desc())

    # 페이지네이션
    articles = query.offset(skip).limit(limit).all()

    return articles


@router.get("/{article_no}", response_model=ArticleResponse)
def get_article(
    article_no: str,
    db: Session = Depends(get_db)
):
    """
    매물 상세 정보 조회

    - **article_no**: 매물 번호
    """
    article = db.query(Article).filter(Article.article_no == article_no).first()

    if not article:
        raise HTTPException(status_code=404, detail="매물을 찾을 수 없습니다")

    return article


@router.get("/recent/all", response_model=List[ArticleResponse])
def get_recent_articles(
    limit: int = Query(20, ge=1, le=100, description="최대 개수"),
    db: Session = Depends(get_db)
):
    """
    최근 매물 목록

    - **limit**: 최대 개수 (최대 100)
    """
    articles = db.query(Article).filter(
        Article.is_active == True
    ).order_by(Article.last_seen_at.desc()).limit(limit).all()

    return articles


@router.get("/price-changed/all", response_model=List[ArticleResponse])
def get_price_changed_articles(
    limit: int = Query(20, ge=1, le=100, description="최대 개수"),
    db: Session = Depends(get_db)
):
    """
    가격 변동 매물 목록

    가격이 변동된 매물만 조회합니다.

    - **limit**: 최대 개수 (최대 100)
    """
    articles = db.query(Article).filter(
        and_(
            Article.is_active == True,
            or_(
                Article.price_change_state == "UP",
                Article.price_change_state == "DOWN"
            )
        )
    ).order_by(Article.updated_at.desc()).limit(limit).all()

    return articles


@router.get("/changes/{complex_id}/summary")
def get_change_summary(
    complex_id: str,
    hours: int = Query(24, ge=1, le=168, description="조회할 시간 범위 (시간)"),
    db: Session = Depends(get_db)
) -> Dict:
    """
    매물 변동사항 요약 정보

    지정된 시간 범위 내의 매물 변동사항을 요약하여 반환합니다.

    - **complex_id**: 단지 ID
    - **hours**: 조회할 시간 범위 (기본: 24시간, 최대: 1주일)
    """
    tracker = ArticleTracker(db)
    summary = tracker.get_change_summary(complex_id, hours=hours)

    return {
        "complex_id": complex_id,
        "hours": hours,
        "summary": summary
    }


@router.get("/changes/{complex_id}/list")
def get_change_list(
    complex_id: str,
    hours: int = Query(24, ge=1, le=168, description="조회할 시간 범위 (시간)"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="최대 개수"),
    db: Session = Depends(get_db)
):
    """
    매물 변동사항 상세 목록

    지정된 시간 범위 내의 모든 변동사항을 반환합니다.

    - **complex_id**: 단지 ID
    - **hours**: 조회할 시간 범위
    - **limit**: 최대 개수 (선택)
    """
    tracker = ArticleTracker(db)
    changes = tracker.get_recent_changes(complex_id, hours=hours, limit=limit)

    return {
        "complex_id": complex_id,
        "hours": hours,
        "total": len(changes),
        "changes": [
            {
                "id": change.id,
                "change_type": change.change_type,
                "article_no": change.article_no,
                "trade_type": change.trade_type,
                "area_name": change.area_name,
                "building_name": change.building_name,
                "floor_info": change.floor_info,
                "old_price": change.old_price,
                "new_price": change.new_price,
                "price_change_amount": change.price_change_amount,
                "price_change_percent": change.price_change_percent,
                "detected_at": change.detected_at.isoformat() if change.detected_at else None
            }
            for change in changes
        ]
    }
