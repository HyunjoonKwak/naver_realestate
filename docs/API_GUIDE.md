# API 가이드

네이버 부동산 API 사용 가이드

## 🚀 서버 시작

```bash
cd backend
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 URL에 접속 가능합니다:
- **API 문서 (Swagger)**: http://localhost:8000/docs
- **API 문서 (ReDoc)**: http://localhost:8000/redoc
- **루트**: http://localhost:8000/

---

## 📚 API 엔드포인트 목록

### 단지 API (6개)
- `GET /complexes/` - 단지 목록 조회
- `GET /complexes/{complex_id}` - 단지 상세 정보
- `GET /complexes/{complex_id}/articles` - 단지 매물 목록
- `GET /complexes/{complex_id}/transactions` - 단지 실거래가 목록
- `GET /complexes/{complex_id}/stats` - 단지 통계

### 매물 API (5개)
- `GET /articles/` - 매물 검색
- `GET /articles/{article_no}` - 매물 상세 정보
- `GET /articles/recent/all` - 최근 매물
- `GET /articles/price-changed/all` - 가격 변동 매물

### 실거래가 API (5개)
- `GET /transactions/` - 실거래가 검색
- `GET /transactions/recent` - 최근 실거래가
- `GET /transactions/stats/price-trend` - 가격 추이 통계
- `GET /transactions/stats/area-price` - 면적별 가격 통계
- `GET /transactions/stats/floor-premium` - 층별 프리미엄 분석

---

## 📖 상세 API 문서

### 1. 단지 (Complexes)

#### 1.1 단지 목록 조회
```bash
GET /complexes/
```

**Query Parameters:**
- `skip`: 건너뛸 개수 (기본값: 0)
- `limit`: 최대 개수 (기본값: 100, 최대: 100)

**예시:**
```bash
curl "http://localhost:8000/complexes/?skip=0&limit=10"
```

**응답:**
```json
[
  {
    "id": 1,
    "complex_id": "109208",
    "complex_name": "시범반도유보라아이비파크4.0",
    "total_households": 740,
    "total_buildings": 6,
    "completion_date": "2018-01-29",
    "min_supply_area": 114.58,
    "max_supply_area": 130.55
  }
]
```

#### 1.2 단지 상세 정보
```bash
GET /complexes/{complex_id}
```

**Query Parameters:**
- `include_articles`: 매물 정보 포함 (기본값: true)
- `include_transactions`: 실거래가 정보 포함 (기본값: true)

**예시:**
```bash
curl "http://localhost:8000/complexes/109208"
```

**응답:**
```json
{
  "complex": {
    "complex_id": "109208",
    "complex_name": "시범반도유보라아이비파크4.0",
    "address": "대전광역시 서구 둔산동",
    "total_households": 740,
    "total_buildings": 6
  },
  "articles": [...],
  "transactions": [...]
}
```

#### 1.3 단지 매물 목록
```bash
GET /complexes/{complex_id}/articles
```

**Query Parameters:**
- `trade_type`: 거래 유형 (매매/전세/월세)
- `is_active`: 활성 매물만 (기본값: true)

**예시:**
```bash
curl "http://localhost:8000/complexes/109208/articles?trade_type=매매"
```

#### 1.4 단지 통계
```bash
GET /complexes/{complex_id}/stats
```

**응답 예시:**
```json
{
  "complex_id": "109208",
  "complex_name": "시범반도유보라아이비파크4.0",
  "articles": {
    "total": 20,
    "sale": 20,
    "lease": 0
  },
  "transactions": {
    "total": 1,
    "avg_price": 104000,
    "recent": {...}
  }
}
```

---

### 2. 매물 (Articles)

#### 2.1 매물 검색
```bash
GET /articles/
```

**Query Parameters:**
- `complex_id`: 단지 ID
- `trade_type`: 거래 유형 (매매/전세/월세)
- `area_name`: 면적 타입
- `building_name`: 동 정보
- `min_area`: 최소 면적(㎡)
- `max_area`: 최대 면적(㎡)
- `is_active`: 활성 매물만 (기본값: true)
- `skip`: 건너뛸 개수 (기본값: 0)
- `limit`: 최대 개수 (기본값: 50, 최대: 100)

**예시:**
```bash
# 특정 단지의 매매 매물
curl "http://localhost:8000/articles/?complex_id=109208&trade_type=매매"

# 면적 필터
curl "http://localhost:8000/articles/?min_area=100&max_area=130"
```

#### 2.2 최근 매물
```bash
GET /articles/recent/all
```

**Query Parameters:**
- `limit`: 최대 개수 (기본값: 20, 최대: 100)

**예시:**
```bash
curl "http://localhost:8000/articles/recent/all?limit=10"
```

#### 2.3 가격 변동 매물
```bash
GET /articles/price-changed/all
```

가격이 변동된 매물만 조회합니다.

---

### 3. 실거래가 (Transactions)

#### 3.1 실거래가 검색
```bash
GET /transactions/
```

**Query Parameters:**
- `complex_id`: 단지 ID
- `start_date`: 시작일 (YYYYMMDD)
- `end_date`: 종료일 (YYYYMMDD)
- `min_price`: 최소 거래가 (만원)
- `max_price`: 최대 거래가 (만원)
- `min_floor`: 최소 층
- `max_floor`: 최대 층
- `skip`: 건너뛸 개수
- `limit`: 최대 개수

**예시:**
```bash
# 특정 단지
curl "http://localhost:8000/transactions/?complex_id=109208"

# 기간 필터
curl "http://localhost:8000/transactions/?start_date=20250101&end_date=20251231"
```

#### 3.2 가격 추이 통계
```bash
GET /transactions/stats/price-trend
```

**Query Parameters:**
- `complex_id`: 단지 ID (필수)
- `months`: 조회 기간 (개월, 기본값: 6, 1~24)

월별 평균/최소/최대 거래가 추이를 조회합니다.

**예시:**
```bash
curl "http://localhost:8000/transactions/stats/price-trend?complex_id=109208&months=12"
```

**응답:**
```json
{
  "complex_id": "109208",
  "complex_name": "시범반도유보라아이비파크4.0",
  "period_months": 12,
  "trend": [
    {
      "month": "202509",
      "avg_price": 104000,
      "min_price": 104000,
      "max_price": 104000,
      "count": 1
    }
  ]
}
```

#### 3.3 면적별 가격 통계
```bash
GET /transactions/stats/area-price
```

**Query Parameters:**
- `complex_id`: 단지 ID (필수)

#### 3.4 층별 프리미엄 분석
```bash
GET /transactions/stats/floor-premium
```

**Query Parameters:**
- `complex_id`: 단지 ID (필수)

저층/중층/고층별 평균 거래가를 분석합니다.

---

## 🧪 테스트

### 자동 테스트 스크립트
```bash
./test_api.sh
```

### Python 예시
```python
import requests

# 단지 목록
response = requests.get("http://localhost:8000/complexes/")
complexes = response.json()

# 단지 상세
response = requests.get("http://localhost:8000/complexes/109208")
complex_detail = response.json()

# 매물 검색
response = requests.get("http://localhost:8000/articles/", params={
    "complex_id": "109208",
    "trade_type": "매매",
    "limit": 10
})
articles = response.json()
```

---

## 📊 응답 형식

### 성공 응답
```json
{
  "complex_id": "109208",
  "complex_name": "시범반도유보라아이비파크4.0",
  ...
}
```

### 에러 응답
```json
{
  "detail": "단지를 찾을 수 없습니다"
}
```

**HTTP 상태 코드:**
- `200`: 성공
- `404`: 리소스를 찾을 수 없음
- `422`: 유효성 검사 실패
- `500`: 서버 에러

---

## 🔧 개발 팁

### CORS 설정
프론트엔드 개발 시 CORS가 허용되어 있습니다. (`app/main.py`)

### API 문서 자동 생성
FastAPI는 자동으로 OpenAPI 스펙을 생성합니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 프론트엔드 연동
프론트엔드는 [http://localhost:3000](http://localhost:3000)에서 실행되며, axios를 통해 API와 통신합니다.

```typescript
// frontend/src/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const complexAPI = {
  getList: async () => {
    const { data } = await api.get('/complexes/');
    return data;
  },
};
```

---

## 📝 다음 단계

1. ✅ 프론트엔드 통합 완료
2. ⬜ 캐싱 (Redis)
3. ⬜ Rate Limiting
4. ⬜ 인증/인가 (JWT)
5. ⬜ 로깅 및 모니터링
