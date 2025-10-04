# 네이버 부동산 매물 관리 시스템

## 📌 프로젝트 개요

네이버 부동산 사이트를 활용하여 관심 아파트 단지의 매물 정보를 자동으로 수집하고, 일자별 변동사항과 실거래가를 추적하여 최적의 매매 시기를 분석하는 시스템

### 프로젝트 목표
- 관심 아파트 단지의 매매/전세/월세 매물 자동 모니터링
- 일자별 매물 변동사항 추적 및 알림
- 보유 부동산의 시세 변동 관리
- 실거래가 분석을 통한 최적 매매 시기 제안

---

## 🎯 핵심 기능 요구사항

### 1. 아파트 단지 관리
- [ ] 관심 아파트 단지 검색 및 등록
- [ ] 단지 목록 조회 및 관리
- [ ] 단지별 기본 정보 저장 (위치, 세대수, 건축년도 등)
- [ ] 단지 삭제 및 수정

### 2. 매물 모니터링
- [ ] 매매 매물 정보 수집
- [ ] 전세 매물 정보 수집
- [ ] 월세 매물 정보 수집
- [ ] 일자별 신규 매물 감지
- [ ] 일자별 삭제된 매물 추적
- [ ] 가격 변동 매물 추적
- [ ] 매물 상세 정보 저장 (면적, 층, 방향, 가격 등)

### 3. 보유 부동산 관리
- [ ] 보유 부동산 등록
- [ ] 보유 부동산별 시세 변동 추적
- [ ] 보유 부동산 평가액 계산
- [ ] 매매 시기 분석 및 추천
- [ ] 수익률 계산

### 4. 실거래가 분석
- [ ] 실거래가 데이터 수집
- [ ] 시계열 가격 데이터 저장
- [ ] 시세 트렌드 분석
- [ ] 평균 거래가 계산
- [ ] 가격 예측 모델
- [ ] 최적 매매 시기 제안

### 5. 알림 및 리포트
- [ ] 신규 매물 알림
- [ ] 가격 변동 알림
- [ ] 일일/주간/월간 리포트
- [ ] 관심 가격대 도달 알림

---

## 🎨 UX 워크플로우

```
[메인 대시보드]
├─ 요약 통계 (관심 단지 수, 매물 수, 가격 변동)
├─ 최근 신규 매물
├─ 가격 변동 알림
└─ 보유 부동산 시세 현황

[관심 단지 관리]
├─ 단지 검색
│  ├─ 지역별 검색
│  ├─ 단지명 검색
│  └─ 검색 결과 목록
├─ 단지 추가
├─ 등록된 단지 목록
│  ├─ 단지별 요약 정보
│  ├─ 현재 매물 수
│  └─ 최근 실거래가
└─ 단지 상세 정보
   ├─ 기본 정보
   ├─ 현재 매물 목록
   ├─ 실거래가 내역
   └─ 가격 트렌드 차트

[매물 모니터링]
├─ 전체 매물 현황
│  ├─ 필터링 (매매/전세/월세, 가격대, 면적)
│  ├─ 정렬 (최신순, 가격순, 면적순)
│  └─ 매물 목록
├─ 신규 매물 (오늘/최근 7일/최근 30일)
├─ 가격 변동 매물
├─ 삭제된 매물
└─ 매물 상세 정보
   ├─ 기본 정보 (가격, 면적, 층)
   ├─ 가격 변동 이력
   ├─ 네이버 부동산 링크
   └─ 메모/관심 표시

[보유 부동산]
├─ 부동산 등록
│  ├─ 단지 선택
│  ├─ 호수/면적 입력
│  └─ 취득가/취득일 입력
├─ 보유 목록
│  ├─ 부동산별 카드
│  ├─ 현재 시세
│  ├─ 평가 손익
│  └─ 수익률
└─ 부동산 상세
   ├─ 시세 변동 그래프
   ├─ 유사 매물 비교
   ├─ 매매 시기 분석
   └─ 예상 수익 시뮬레이션

[실거래가 분석]
├─ 단지별 실거래가
│  ├─ 기간별 필터
│  ├─ 면적별 필터
│  └─ 거래 내역 테이블
├─ 시세 트렌드
│  ├─ 시계열 차트
│  ├─ 평균가 추이
│  └─ 거래량 추이
├─ 가격 예측
│  ├─ 향후 3개월/6개월/1년 예측
│  ├─ 신뢰 구간
│  └─ 예측 근거
└─ 매매 시기 분석
   ├─ 시장 상황 판단
   ├─ 매수/매도 추천
   └─ 추천 근거
```

---

## 🏗️ 기술 스택

### Backend
- **언어/프레임워크**: Python 3.11+ / FastAPI
- **데이터베이스**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **스케줄러**: Celery + Redis
- **크롤링**: Playwright (Python)
- **데이터 분석**: Pandas, NumPy, Scikit-learn

### Frontend
- **프레임워크**: Next.js 14+ (React 18+)
- **언어**: TypeScript
- **스타일링**: TailwindCSS
- **차트**: Recharts / Chart.js
- **상태관리**: Zustand or React Query
- **UI 컴포넌트**: shadcn/ui

### 인프라
- **컨테이너**: Docker, Docker Compose
- **배포**: (추후 결정 - Vercel, Railway, AWS 등)
- **모니터링**: (추후 결정)

### 개발 도구
- **버전 관리**: Git, GitHub
- **API 문서**: Swagger/OpenAPI (FastAPI 자동 생성)
- **테스트**: Pytest (Backend), Jest (Frontend)

---

## 🗄️ 데이터베이스 스키마 (초안)

### 테이블 구조

#### 1. complexes (아파트 단지)
```sql
- id: BIGSERIAL PRIMARY KEY
- naver_complex_id: VARCHAR(50) UNIQUE (네이버 단지 ID)
- name: VARCHAR(200) (단지명)
- address: VARCHAR(500) (주소)
- total_households: INTEGER (총 세대수)
- construction_year: INTEGER (건축년도)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### 2. listings (매물)
```sql
- id: BIGSERIAL PRIMARY KEY
- complex_id: BIGINT REFERENCES complexes(id)
- naver_listing_id: VARCHAR(50) UNIQUE (네이버 매물 ID)
- listing_type: VARCHAR(20) (매매/전세/월세)
- price: BIGINT (가격)
- deposit: BIGINT (보증금, 월세의 경우)
- monthly_rent: INTEGER (월세)
- area_exclusive: DECIMAL(10,2) (전용면적)
- area_supply: DECIMAL(10,2) (공급면적)
- floor: INTEGER (층)
- direction: VARCHAR(20) (방향)
- listing_url: TEXT (네이버 링크)
- first_found_at: TIMESTAMP (최초 발견일)
- last_seen_at: TIMESTAMP (마지막 확인일)
- is_active: BOOLEAN (활성 여부)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### 3. listing_history (매물 변동 이력)
```sql
- id: BIGSERIAL PRIMARY KEY
- listing_id: BIGINT REFERENCES listings(id)
- change_type: VARCHAR(20) (신규/가격변경/삭제)
- old_price: BIGINT
- new_price: BIGINT
- changed_at: TIMESTAMP
```

#### 4. transactions (실거래가)
```sql
- id: BIGSERIAL PRIMARY KEY
- complex_id: BIGINT REFERENCES complexes(id)
- transaction_type: VARCHAR(20) (매매/전세)
- price: BIGINT
- area_exclusive: DECIMAL(10,2)
- floor: INTEGER
- transaction_date: DATE (거래일)
- created_at: TIMESTAMP
```

#### 5. owned_properties (보유 부동산)
```sql
- id: BIGSERIAL PRIMARY KEY
- complex_id: BIGINT REFERENCES complexes(id)
- name: VARCHAR(100) (별칭)
- area_exclusive: DECIMAL(10,2)
- floor: INTEGER
- acquisition_price: BIGINT (취득가)
- acquisition_date: DATE (취득일)
- notes: TEXT (메모)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

#### 6. price_evaluations (시세 평가)
```sql
- id: BIGSERIAL PRIMARY KEY
- property_id: BIGINT REFERENCES owned_properties(id)
- evaluated_price: BIGINT (평가액)
- basis: TEXT (평가 근거)
- evaluated_at: DATE
- created_at: TIMESTAMP
```

---

## 🔧 크롤링 전략

### Playwright 활용 방안

#### 네이버 부동산 접근 제약 우회
- **문제**: 직접 API 호출 시 차단 가능
- **해결**: Playwright로 실제 브라우저 시뮬레이션
- **MCP 활용**: Playwright MCP를 통한 안정적인 접근

#### 크롤링 대상
1. **단지 검색 페이지**: `https://new.land.naver.com/complexes`
2. **단지 상세 페이지**: `https://new.land.naver.com/complexes/{complex_id}`
3. **매물 목록**: 단지 상세 내 매물 탭
4. **실거래가**: 단지 상세 내 실거래가 탭

#### 크롤링 주기
- **매물 정보**: 1일 2회 (오전 9시, 오후 6시)
- **실거래가**: 1주 1회 (월요일 오전)
- **신규 단지**: 수동 추가 방식

#### 데이터 수집 항목
```python
# 매물 정보
{
    "listing_id": "네이버 매물 ID",
    "type": "매매|전세|월세",
    "price": "가격",
    "deposit": "보증금",
    "monthly_rent": "월세",
    "area": "면적",
    "floor": "층",
    "direction": "방향",
    "url": "상세 URL"
}

# 실거래가 정보
{
    "transaction_date": "거래일",
    "type": "매매|전세",
    "price": "거래가",
    "area": "면적",
    "floor": "층"
}
```

---

## 📊 분석 알고리즘 (예정)

### 1. 시세 예측
- 이동평균 분석
- 선형 회귀 모델
- 계절성 분석

### 2. 매매 시기 판단
- 현재가 vs 평균가 비교
- 가격 추세 분석 (상승/하락/보합)
- 거래량 분석
- 외부 지표 고려 (금리, 정책 등 - 향후)

### 3. 추천 로직
```
매수 추천:
- 현재가 < 평균가 - 1σ
- 하락세에서 상승 전환 징후
- 거래량 증가

매도 추천:
- 현재가 > 평균가 + 1σ
- 상승세에서 둔화 징후
- 보유 기간 및 수익률 고려
```

---

## 🚀 개발 환경 설정

### 필수 도구
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### 개발 시작
```bash
# 저장소 클론
git clone <repository-url>
cd naver_realestate

# Backend 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend 설정
cd ../frontend
npm install

# Docker 환경 실행
docker-compose up -d
```

---

## 📝 라이선스 및 주의사항

### 크롤링 주의사항
- 네이버 부동산 이용약관 준수
- 과도한 요청으로 서버 부하 방지
- robots.txt 확인 및 준수
- 개인정보 처리 주의

### 면책
- 본 프로젝트는 개인 학습 및 투자 참고용
- 투자 결정은 본인 책임
- 크롤링한 데이터의 정확성 보장 불가

---

## 📚 참고 문서
- [네이버 부동산](https://new.land.naver.com)
- [Playwright Documentation](https://playwright.dev)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Next.js Documentation](https://nextjs.org/docs)
