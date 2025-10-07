"""
단지 관련 데이터베이스 모델
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, BigInteger, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Complex(Base):
    """아파트 단지 모델"""
    __tablename__ = "complexes"

    id = Column(BigInteger, primary_key=True, index=True)
    complex_id = Column(String(50), unique=True, index=True, nullable=False, comment="네이버 단지 ID")
    complex_name = Column(String(200), nullable=False, comment="단지명")
    complex_type = Column(String(50), comment="단지 유형")
    address = Column(String(500), comment="주소")

    # 단지 기본 정보
    total_households = Column(Integer, comment="총 세대수")
    total_dongs = Column(Integer, comment="총 동수")
    completion_date = Column(String(20), comment="준공일 (YYYYMMDD)")

    # 면적 정보
    min_area = Column(Float, comment="최소 면적(㎡)")
    max_area = Column(Float, comment="최대 면적(㎡)")

    # 가격 정보 (만원 단위)
    min_price = Column(BigInteger, comment="최저 매매가")
    max_price = Column(BigInteger, comment="최고 매매가")
    min_lease_price = Column(BigInteger, comment="최저 전세가")
    max_lease_price = Column(BigInteger, comment="최고 전세가")

    # 위치 정보
    latitude = Column(Float, comment="위도")
    longitude = Column(Float, comment="경도")

    # 메타 데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Complex(id={self.complex_id}, name={self.complex_name})>"


class Article(Base):
    """매물 모델"""
    __tablename__ = "articles"

    id = Column(BigInteger, primary_key=True, index=True)
    article_no = Column(String(50), unique=True, index=True, nullable=False, comment="매물 번호")
    complex_id = Column(String(50), ForeignKey('complexes.complex_id', ondelete='CASCADE'), index=True, nullable=False, comment="단지 ID")

    # 거래 정보
    trade_type = Column(String(20), comment="거래 유형 (매매/전세/월세)")
    price = Column(String(100), comment="가격 (문자열)")
    price_change_state = Column(String(20), comment="가격 변동 상태 (SAME/UP/DOWN)")

    # 면적 정보
    area_name = Column(String(50), comment="면적 타입명")
    area1 = Column(Float, comment="공급면적(㎡)")
    area2 = Column(Float, comment="전용면적(㎡)")

    # 위치 정보
    floor_info = Column(String(50), comment="층 정보")
    direction = Column(String(50), comment="방향")
    building_name = Column(String(100), comment="동 정보")

    # 매물 상세
    feature_desc = Column(Text, comment="매물 특징")
    tags = Column(Text, comment="태그 (JSON 배열)")
    realtor_name = Column(String(200), comment="공인중개사")

    # 동일 매물 정보
    same_addr_cnt = Column(Integer, default=1, comment="동일 매물 수 (중개사 수)")
    same_addr_max_prc = Column(String(100), comment="동일 매물 최고가")
    same_addr_min_prc = Column(String(100), comment="동일 매물 최저가")

    # 날짜 정보
    confirm_date = Column(String(20), comment="확인일 (YYYYMMDD)")

    # 상태
    is_active = Column(Boolean, default=True, comment="활성 여부")
    first_found_at = Column(DateTime(timezone=True), server_default=func.now(), comment="최초 발견일")
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="마지막 확인일")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Article(no={self.article_no}, price={self.price})>"


class Transaction(Base):
    """실거래가 모델"""
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, index=True)
    complex_id = Column(String(50), ForeignKey('complexes.complex_id', ondelete='CASCADE'), index=True, nullable=False, comment="단지 ID")

    # 거래 정보
    trade_type = Column(String(20), comment="거래 유형")
    trade_date = Column(String(20), index=True, comment="거래일 (YYYYMMDD)")
    deal_price = Column(BigInteger, comment="거래가 (만원)")
    formatted_price = Column(String(100), comment="포맷된 가격 (예: 10억 4,000)")

    # 물건 정보
    floor = Column(Integer, comment="층")
    area = Column(Float, comment="대표 면적(㎡)")
    exclusive_area = Column(Float, comment="전용 면적(㎡)")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Transaction(complex={self.complex_id}, price={self.deal_price}, date={self.trade_date})>"


class ArticleHistory(Base):
    """매물 변동 이력"""
    __tablename__ = "article_history"

    id = Column(BigInteger, primary_key=True, index=True)
    article_no = Column(String(50), index=True, nullable=False)

    change_type = Column(String(20), comment="변동 유형 (신규/가격변경/삭제)")
    old_price = Column(String(100), comment="이전 가격")
    new_price = Column(String(100), comment="변경 가격")

    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ArticleHistory(article={self.article_no}, type={self.change_type})>"


class ArticleSnapshot(Base):
    """매물 스냅샷 - 특정 시점의 매물 상태 저장"""
    __tablename__ = "article_snapshots"

    id = Column(BigInteger, primary_key=True, index=True)
    complex_id = Column(String(50), ForeignKey('complexes.complex_id', ondelete='CASCADE'), index=True, nullable=False, comment="단지 ID")
    article_no = Column(String(50), index=True, nullable=False, comment="매물 번호")

    # 매물 정보 (스냅샷 시점)
    trade_type = Column(String(20), comment="거래 유형")
    price = Column(String(100), comment="가격")
    area_name = Column(String(50), comment="면적 타입명")
    area1 = Column(Float, comment="공급면적(㎡)")
    floor_info = Column(String(50), comment="층 정보")
    direction = Column(String(50), comment="방향")
    building_name = Column(String(100), comment="동 정보")
    realtor_name = Column(String(200), comment="공인중개사")
    same_addr_cnt = Column(Integer, comment="동일 매물 수")

    # 스냅샷 메타데이터
    snapshot_date = Column(DateTime(timezone=True), index=True, nullable=False, comment="스냅샷 일시")
    crawl_session_id = Column(String(100), comment="크롤링 세션 ID")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ArticleSnapshot(article={self.article_no}, date={self.snapshot_date})>"


class ArticleChange(Base):
    """매물 변동 감지 결과"""
    __tablename__ = "article_changes"

    id = Column(BigInteger, primary_key=True, index=True)
    complex_id = Column(String(50), ForeignKey('complexes.complex_id', ondelete='CASCADE'), index=True, nullable=False, comment="단지 ID")
    article_no = Column(String(50), index=True, comment="매물 번호 (신규/삭제는 null 가능)")

    # 변동 유형: NEW, REMOVED, PRICE_UP, PRICE_DOWN
    change_type = Column(String(20), index=True, nullable=False, comment="변동 유형")

    # 변동 상세 정보
    old_price = Column(String(100), comment="이전 가격")
    new_price = Column(String(100), comment="변경 가격")
    price_change_amount = Column(BigInteger, comment="가격 변동액 (만원)")
    price_change_percent = Column(Float, comment="가격 변동률 (%)")

    # 매물 기본 정보 (빠른 조회용)
    trade_type = Column(String(20), comment="거래 유형")
    area_name = Column(String(50), comment="면적")
    building_name = Column(String(100), comment="동")
    floor_info = Column(String(50), comment="층")

    # 스냅샷 참조
    from_snapshot_id = Column(BigInteger, comment="이전 스냅샷 ID")
    to_snapshot_id = Column(BigInteger, comment="현재 스냅샷 ID")

    # 감지 시각
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 읽음 여부 (주간 브리핑에서 사용)
    is_read = Column(Boolean, default=False, comment="확인 여부")

    def __repr__(self):
        return f"<ArticleChange(type={self.change_type}, article={self.article_no})>"
