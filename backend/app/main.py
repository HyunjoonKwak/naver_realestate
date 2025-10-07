"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import complexes, articles, scraper, transactions, scheduler

# FastAPI 앱 생성
app = FastAPI(
    title="네이버 부동산 API",
    description="네이버 부동산 매물 및 실거래가 관리 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(complexes.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(scraper.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(scheduler.router)


@app.get("/")
def root():
    """API 루트"""
    return {
        "message": "네이버 부동산 API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """헬스 체크"""
    return {"status": "healthy"}
