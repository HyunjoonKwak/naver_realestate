"""
관심 단지 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# 관심 단지 추가
class FavoriteCreate(BaseModel):
    complex_id: str = Field(..., description="단지 ID")
    notify_price_change: bool = Field(True, description="가격 변동 알림")
    notify_new_article: bool = Field(True, description="신규 매물 알림")


# 관심 단지 업데이트
class FavoriteUpdate(BaseModel):
    notify_price_change: Optional[bool] = Field(None, description="가격 변동 알림")
    notify_new_article: Optional[bool] = Field(None, description="신규 매물 알림")


# 관심 단지 응답 (단지 정보 포함)
class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    complex_id: str
    notify_price_change: bool
    notify_new_article: bool
    created_at: datetime

    # 단지 정보
    complex_name: Optional[str] = None
    road_address: Optional[str] = None
    total_households: Optional[int] = None

    class Config:
        from_attributes = True
