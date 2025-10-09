"""
사용자 관련 Pydantic 스키마
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# 사용자 등록
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="이메일 (로그인 ID)")
    username: str = Field(..., min_length=2, max_length=100, description="사용자명")
    password: str = Field(..., min_length=6, description="비밀번호")


# 사용자 로그인
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="이메일")
    password: str = Field(..., description="비밀번호")


# 사용자 응답
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 토큰 응답
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# 사용자 업데이트
class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
