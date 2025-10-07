"""
Pydantic 스키마 - API 요청/응답 모델
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ComplexBase(BaseModel):
    """단지 기본 정보"""
    complex_id: str
    complex_name: str
    complex_type: Optional[str] = None
    address: Optional[str] = None  # 하위호환용 (도로명 주소 우선)
    road_address: Optional[str] = None  # 도로명 주소
    jibun_address: Optional[str] = None  # 지번(법정동) 주소
    total_households: Optional[int] = None
    total_dongs: Optional[int] = None
    completion_date: Optional[str] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_lease_price: Optional[int] = None
    max_lease_price: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ComplexResponse(ComplexBase):
    """단지 응답 (DB 포함)"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArticleBase(BaseModel):
    """매물 기본 정보"""
    article_no: str
    complex_id: str
    trade_type: Optional[str] = None
    price: Optional[str] = None
    price_change_state: Optional[str] = None
    area_name: Optional[str] = None
    area1: Optional[float] = None
    area2: Optional[float] = None
    floor_info: Optional[str] = None
    direction: Optional[str] = None
    building_name: Optional[str] = None
    feature_desc: Optional[str] = None
    tags: Optional[str] = None
    realtor_name: Optional[str] = None
    confirm_date: Optional[str] = None
    same_addr_cnt: Optional[int] = 1
    same_addr_max_prc: Optional[str] = None
    same_addr_min_prc: Optional[str] = None


class ArticleResponse(ArticleBase):
    """매물 응답"""
    id: int
    is_active: Optional[bool] = True
    first_found_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    """실거래가 기본 정보"""
    complex_id: str
    trade_type: Optional[str] = None
    trade_date: Optional[str] = None
    deal_price: Optional[int] = None
    formatted_price: Optional[str] = None
    floor: Optional[int] = None
    area: Optional[float] = None
    exclusive_area: Optional[float] = None


class TransactionResponse(TransactionBase):
    """실거래가 응답"""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplexDetailResponse(ComplexResponse):
    """단지 상세 정보 (매물 포함)"""
    articles: List[ArticleResponse] = []
    transactions: List[TransactionResponse] = []


class ArticleSearchParams(BaseModel):
    """매물 검색 파라미터"""
    complex_id: Optional[str] = None
    trade_type: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    area_name: Optional[str] = None
    building_name: Optional[str] = None
    is_active: Optional[bool] = True
    limit: int = 50
    offset: int = 0


class ComplexCreate(BaseModel):
    """단지 생성 요청"""
    complex_id: str
    complex_name: str
    complex_type: Optional[str] = None
    total_households: Optional[int] = None
    total_dongs: Optional[int] = None
    completion_date: Optional[str] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_lease_price: Optional[int] = None
    max_lease_price: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
