# 실거래가 기능 사용 가이드

국토교통부 실거래가 API를 활용한 아파트 실거래가 조회 및 분석 기능입니다.

## 📋 목차

- [기능 개요](#기능-개요)
- [설정 방법](#설정-방법)
- [사용 방법](#사용-방법)
- [API 엔드포인트](#api-엔드포인트)
- [데이터 구조](#데이터-구조)
- [문제 해결](#문제-해결)

---

## 🎯 기능 개요

### 주요 기능

1. **자동 실거래가 조회**
   - 단지 새로고침 시 자동으로 국토부 실거래가 조회
   - 최근 6개월 매매 실거래가 자동 수집

2. **평형별 통계**
   - 평형별 평균/최고/최저 실거래가
   - 거래 건수 표시
   - 시세 대비 실거래가 비교

3. **전국 지원**
   - 20,000개 이상 법정동 코드 데이터
   - 주소 자동 파싱 및 시군구 코드 추출
   - 전국 모든 아파트 단지 지원

---

## ⚙️ 설정 방법

### 1. API 키 발급

국토교통부 공공데이터포털에서 API 키를 발급받습니다.

1. **공공데이터포털 접속**
   - URL: https://www.data.go.kr/data/15058017/openapi.do

2. **회원가입 및 로그인**

3. **활용신청 클릭**
   - 일반 인증키(Encoding) 선택
   - 활용목적 입력

4. **API 키 발급**
   - 마이페이지 → 오픈API → 인증키 확인

### 2. 환경변수 설정

프로젝트 루트의 `.env` 파일에 API 키를 추가합니다.

```bash
# .env
MOLIT_API_KEY=발급받은_API_키_입력
```

**위치**: `/Users/specialrisk_mac/code_work/naver_realestate/.env`

### 3. 서버 재시작

환경변수 변경 후 백엔드 서버를 재시작합니다.

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload
```

---

## 🚀 사용 방법

### 1. 단지 추가

1. **프론트엔드 접속**
   ```
   http://localhost:3000
   ```

2. **새 단지 추가**
   - "새 단지 추가" 버튼 클릭
   - 네이버 부동산 단지 URL 입력
   - 예: `https://new.land.naver.com/complexes/1482`

3. **자동 크롤링**
   - 네이버 매물 정보 크롤링
   - 단지 정보 저장

### 2. 실거래가 조회

1. **단지 상세 페이지 접속**
   - 단지 목록에서 단지 클릭

2. **새로고침 버튼 클릭**
   - 우측 상단 "새로고침" 버튼 클릭
   - 자동으로 다음 작업 수행:
     - ✅ 네이버 매물 크롤링
     - ✅ 매물 변동 감지
     - ✅ **실거래가 조회** (국토부 API)
     - ✅ 평형별 통계 계산

3. **실거래가 요약 확인**
   - 상단 탭에서 "실거래" 탭 클릭
   - 평형별 통계 카드 확인:
     - 평균 거래가
     - 최고가
     - 최저가
     - 거래 건수
   - 가격 추이 차트 확인:
     - Chart.js 기반 시계열 그래프
     - 평균가, 최고가, 최저가 추이
     - 월별 거래건수 표시
     - 최근 6개월 데이터 시각화
   - 최근 실거래 내역 테이블:
     - 거래일, 평형, 거래가, 층 정보

### 3. 수동 조회 (선택사항)

API를 직접 호출하여 실거래가를 조회할 수 있습니다.

```bash
# 실거래가 수동 조회 (6개월)
curl -X POST "http://localhost:8000/api/transactions/fetch/{complex_id}?months=6"

# 평형별 통계 조회
curl "http://localhost:8000/api/transactions/stats/area-summary/{complex_id}?months=6"
```

---

## 📡 API 엔드포인트

### 1. 실거래가 조회 및 저장

**POST** `/api/transactions/fetch/{complex_id}`

국토부 API에서 실거래가를 조회하여 DB에 저장합니다.

**Parameters:**
- `complex_id` (path): 단지 ID
- `months` (query, optional): 조회 기간 (기본 6개월)

**Response:**
```json
{
  "success": true,
  "message": "실거래가 저장 완료",
  "saved_count": 15,
  "skipped_count": 3,
  "total_count": 18
}
```

### 2. 평형별 실거래가 통계

**GET** `/api/transactions/stats/area-summary/{complex_id}`

평형별 실거래가 요약 통계를 조회합니다.

**Parameters:**
- `complex_id` (path): 단지 ID
- `months` (query, optional): 조회 기간 (기본 6개월)

**Response:**
```json
{
  "complex_id": "1482",
  "complex_name": "판교원마을6단지",
  "period_months": 6,
  "area_stats": [
    {
      "exclusive_area": 59.9,
      "area_name": "18.1평형",
      "avg_price": 125000,
      "min_price": 118000,
      "max_price": 132000,
      "count": 12,
      "formatted_avg_price": "12억 5,000만"
    }
  ]
}
```

### 3. 기존 Transaction API

**GET** `/api/transactions/`
- 실거래가 검색 (복잡한 필터링)

**GET** `/api/transactions/stats/price-trend`
- 월별 가격 추이

**GET** `/api/transactions/stats/area-price`
- 면적별 가격 통계

---

## 📊 데이터 구조

### Transaction 모델

```python
class Transaction:
    id: int                    # Primary Key
    complex_id: str           # 단지 ID (Foreign Key)
    trade_type: str           # 거래 유형 (매매/전세)
    trade_date: str           # 거래일 (YYYYMMDD)
    deal_price: int           # 거래가 (만원 단위)
    formatted_price: str      # 포맷된 가격 (예: "12억 5,000만")
    floor: int                # 층
    area: float               # 대표 면적
    exclusive_area: float     # 전용 면적
    created_at: datetime      # 생성일시
```

### 법정동 코드 데이터

- **파일**: `backend/app/data/dong_code_active.txt`
- **레코드 수**: 20,278개
- **형식**: `법정동코드\t법정동명`

```
4113500000	경기도 성남시 분당구
4113510300	경기도 성남시 분당구 정자동
1168000000	서울특별시 강남구
```

---

## 🔧 문제 해결

### 1. API 키 오류

**증상:**
```
⚠️ MOLIT_API_KEY가 설정되지 않았습니다.
```

**해결:**
1. `.env` 파일에 API 키 추가 확인
2. 서버 재시작
3. 환경변수 로드 확인:
   ```bash
   cd backend
   .venv/bin/python -c "import os; print(os.getenv('MOLIT_API_KEY'))"
   ```

### 2. 시군구 코드 추출 실패

**증상:**
```
시군구 코드를 찾을 수 없습니다: {주소}
```

**해결:**
- 주소 형식 확인 (예: "경기도 성남시 분당구")
- 법정동 코드 파일 존재 확인:
  ```bash
  ls backend/app/data/dong_code_active.txt
  ```

### 3. API 호출 실패

**증상:**
```
실거래가 API 호출 실패: Connection timeout
```

**원인:**
- 국가정보자원 시스템 점검 중
- API 키 만료 또는 잘못된 키

**해결:**
1. 국가정보자원 시스템 운영 시간 확인
2. API 키 재발급
3. 네트워크 연결 확인

### 4. 데이터 없음

**증상:**
```json
{
  "area_stats": []
}
```

**원인:**
- 조회 기간 내 실거래 없음
- 단지명 매칭 실패

**해결:**
- 조회 기간 늘리기 (`months` 파라미터 증가)
- 단지명 확인 (DB의 `complex_name`과 국토부 데이터 일치 필요)

---

## 🧪 테스트

### 테스트 스크립트 실행

```bash
./test_transaction_api.sh
```

### 수동 테스트

1. **LocationParser 테스트**
   ```bash
   cd backend
   .venv/bin/python
   ```
   ```python
   from app.services.location_parser import LocationParser
   parser = LocationParser()
   parser.extract_sigungu_code("경기도 성남시 분당구 정자동")
   # 출력: '41135'
   ```

2. **MOLIT API 테스트**
   ```bash
   cd backend
   .venv/bin/python
   ```
   ```python
   from app.services.molit_service import MOLITService
   service = MOLITService()
   trades = service.get_apt_trade_data("41135", "202501", "판교원마을")
   print(f"조회된 거래: {len(trades)}건")
   ```

---

## 📚 참고 자료

### 공공데이터 포털
- **아파트 매매 실거래가**: https://www.data.go.kr/data/15058017/openapi.do
- **아파트 전월세 실거래가**: https://www.data.go.kr/data/15058016/openapi.do

### API 명세
- **Endpoint**: `http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev`
- **Response**: XML 형식
- **Rate Limit**: 1일 1,000회 (일반 인증키 기준)

### 법정동 코드
- **출처**: 행정표준관리시스템
- **갱신**: 주기적으로 갱신 필요

---

## 💡 Tips

1. **API 호출 최적화**
   - 중복 조회 방지 (DB에 이미 있는 데이터는 재조회 안함)
   - 조회 기간은 6개월 권장 (너무 길면 API 호출 증가)

2. **데이터 정확도**
   - 단지명이 정확해야 매칭 성공
   - 주소가 상세할수록 시군구 코드 추출 정확도 향상

3. **성능**
   - 실거래가 조회는 비동기로 처리됨
   - 새로고침 후 잠시 대기 필요

---

## 📞 문의

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해 주세요.
