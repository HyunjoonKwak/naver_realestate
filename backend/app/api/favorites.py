"""
관심 단지 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.complex import User, FavoriteComplex, Complex
from app.schemas.favorite import FavoriteCreate, FavoriteUpdate, FavoriteResponse

router = APIRouter()


@router.get("", response_model=List[FavoriteResponse])
def get_my_favorites(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """내 관심 단지 목록 조회"""
    favorites = db.query(FavoriteComplex).filter(
        FavoriteComplex.user_id == current_user.id
    ).all()

    # 단지 정보 포함하여 응답
    result = []
    for fav in favorites:
        complex_info = db.query(Complex).filter(
            Complex.complex_id == fav.complex_id
        ).first()

        fav_dict = {
            "id": fav.id,
            "user_id": fav.user_id,
            "complex_id": fav.complex_id,
            "notify_price_change": fav.notify_price_change,
            "notify_new_article": fav.notify_new_article,
            "created_at": fav.created_at,
            "complex_name": complex_info.complex_name if complex_info else None,
            "road_address": complex_info.road_address if complex_info else None,
            "total_households": complex_info.total_households if complex_info else None,
        }
        result.append(FavoriteResponse(**fav_dict))

    return result


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """관심 단지 추가"""
    # 단지 존재 여부 확인
    complex_exists = db.query(Complex).filter(
        Complex.complex_id == favorite_data.complex_id
    ).first()

    if not complex_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 단지입니다."
        )

    # 이미 추가된 관심 단지인지 확인
    existing = db.query(FavoriteComplex).filter(
        FavoriteComplex.user_id == current_user.id,
        FavoriteComplex.complex_id == favorite_data.complex_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 관심 단지로 등록되어 있습니다."
        )

    # 관심 단지 추가
    new_favorite = FavoriteComplex(
        user_id=current_user.id,
        complex_id=favorite_data.complex_id,
        notify_price_change=favorite_data.notify_price_change,
        notify_new_article=favorite_data.notify_new_article
    )

    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)

    # 단지 정보 포함하여 응답
    fav_dict = {
        "id": new_favorite.id,
        "user_id": new_favorite.user_id,
        "complex_id": new_favorite.complex_id,
        "notify_price_change": new_favorite.notify_price_change,
        "notify_new_article": new_favorite.notify_new_article,
        "created_at": new_favorite.created_at,
        "complex_name": complex_exists.complex_name,
        "road_address": complex_exists.road_address,
        "total_households": complex_exists.total_households,
    }

    return FavoriteResponse(**fav_dict)


@router.delete("/{complex_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    complex_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """관심 단지 제거"""
    favorite = db.query(FavoriteComplex).filter(
        FavoriteComplex.user_id == current_user.id,
        FavoriteComplex.complex_id == complex_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관심 단지를 찾을 수 없습니다."
        )

    db.delete(favorite)
    db.commit()

    return None


@router.put("/{complex_id}", response_model=FavoriteResponse)
def update_favorite(
    complex_id: str,
    favorite_data: FavoriteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """관심 단지 알림 설정 업데이트"""
    favorite = db.query(FavoriteComplex).filter(
        FavoriteComplex.user_id == current_user.id,
        FavoriteComplex.complex_id == complex_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관심 단지를 찾을 수 없습니다."
        )

    if favorite_data.notify_price_change is not None:
        favorite.notify_price_change = favorite_data.notify_price_change

    if favorite_data.notify_new_article is not None:
        favorite.notify_new_article = favorite_data.notify_new_article

    db.commit()
    db.refresh(favorite)

    # 단지 정보 포함하여 응답
    complex_info = db.query(Complex).filter(
        Complex.complex_id == favorite.complex_id
    ).first()

    fav_dict = {
        "id": favorite.id,
        "user_id": favorite.user_id,
        "complex_id": favorite.complex_id,
        "notify_price_change": favorite.notify_price_change,
        "notify_new_article": favorite.notify_new_article,
        "created_at": favorite.created_at,
        "complex_name": complex_info.complex_name if complex_info else None,
        "road_address": complex_info.road_address if complex_info else None,
        "total_households": complex_info.total_households if complex_info else None,
    }

    return FavoriteResponse(**fav_dict)


@router.get("/check/{complex_id}", response_model=dict)
def check_favorite(
    complex_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """특정 단지가 관심 단지인지 확인"""
    favorite = db.query(FavoriteComplex).filter(
        FavoriteComplex.user_id == current_user.id,
        FavoriteComplex.complex_id == complex_id
    ).first()

    return {
        "is_favorite": favorite is not None,
        "favorite_id": favorite.id if favorite else None
    }
