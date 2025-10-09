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

### 단지 API
- `GET /api/complexes/` - 단지 목록 조회
- `POST /api/complexes/` - 단지 추가
- `GET /api/complexes/{complex_id}` - 단지 상세 정보
- `DELETE /api/complexes/{complex_id}` - 단지 삭제
- `GET /api/complexes/{complex_id}/stats` - 단지 통계

### 매물 API
- `GET /api/articles/` - 매물 검색
- `GET /api/articles/{article_no}` - 매물 상세 정보
- `GET /api/articles/changes/{complex_id}/summary` - 변동사항 요약
- `GET /api/articles/changes/{complex_id}/list` - 변동사항 목록
- `GET /api/articles/changes/weekly-summary` - 주간 변동사항 요약

### 실거래가 API
- `GET /api/transactions/` - 실거래가 검색
- `GET /api/transactions/stats/overview` - 전체 통계 개요
- `GET /api/transactions/stats/price-trend` - 가격 추이 통계
- `GET /api/transactions/stats/area-summary/{complex_id}` - 평형별 실거래가 요약
- `POST /api/transactions/fetch/{complex_id}` - 실거래가 수동 조회

### 크롤링 API
- `POST /api/scraper/crawl` - 단지 크롤링 (body)
- `POST /api/scraper/crawl/{complex_id}` - 단지 크롤링 (path)
- `POST /api/scraper/refresh/{complex_id}` - 크롤링 + 실거래가 자동 조회

### 스케줄러 API
- `GET /api/scheduler/schedule` - 스케줄 목록
- `POST /api/scheduler/schedule` - 스케줄 생성
- `PUT /api/scheduler/schedule/{schedule_key}` - 스케줄 수정
- `DELETE /api/scheduler/schedule/{schedule_key}` - 스케줄 삭제
- `GET /api/scheduler/status` - Worker & Beat 상태
- `GET /api/scheduler/jobs` - 작업 이력
- `GET /api/scheduler/stats` - 통계
- `POST /api/scheduler/beat/restart` - Celery Beat 재시작

### 브리핑 API
- `POST /api/briefing/send-manual` - 수동 브리핑 전송
- `GET /api/briefing/preview` - 브리핑 미리보기

### 인증 API (NEW - 2025-10-10)
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /api/auth/me` - 현재 사용자 정보
- `PUT /api/auth/me` - 사용자 정보 수정

### 관심단지 API (NEW - 2025-10-10)
- `GET /api/favorites` - 내 관심 단지 목록
- `POST /api/favorites` - 관심 단지 추가
- `DELETE /api/favorites/{complex_id}` - 관심 단지 제거
- `PUT /api/favorites/{complex_id}` - 알림 설정 변경
- `GET /api/favorites/check/{complex_id}` - 관심 단지 여부 확인

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
2. ✅ 인증/인가 (JWT) - 백엔드 완료
3. ⬜ 프론트엔드 인증 UI
4. ⬜ 캐싱 (Redis)
5. ⬜ Rate Limiting
6. ⬜ 로깅 및 모니터링

---

## 🔐 인증 API 사용 예시

### 회원가입
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "홍길동",
    "password": "password123"
  }'
```

### 로그인
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**응답:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "홍길동",
    "is_active": true,
    "is_admin": false
  }
}
```

### 인증이 필요한 API 호출
```bash
curl "http://localhost:8000/api/favorites" \
  -H "Authorization: Bearer eyJhbGc..."
```

---

## 📊 주요 API 상세

### 스케줄러 관리

**스케줄 생성:**
```bash
curl -X POST "http://localhost:8000/api/scheduler/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_key": "daily_crawl",
    "task_name": "crawl_all_complexes",
    "cron_expression": "0 9 * * *",
    "description": "매일 오전 9시 전체 크롤링"
  }'
```

**Beat 재시작 (Mac 슬립 복구):**
```bash
curl -X POST "http://localhost:8000/api/scheduler/beat/restart"
```

### 실거래가 수집

**특정 단지 실거래가 조회:**
```bash
curl -X POST "http://localhost:8000/api/transactions/fetch/109208"
```

**평형별 요약:**
```bash
curl "http://localhost:8000/api/transactions/stats/area-summary/109208?months=6"
```

### 주간 브리핑

**Discord로 브리핑 전송:**
```bash
curl -X POST "http://localhost:8000/api/briefing/send-manual"
```
