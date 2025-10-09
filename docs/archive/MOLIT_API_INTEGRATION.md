# 국토부 실거래가 API 연동 설계

## 📋 개요

국토교통부 실거래가 공개시스템 오픈API를 활용하여 아파트 실거래가 데이터를 수집하고 분석하는 기능

## 🎯 목표

- 네이버 부동산 매물과 실거래가를 함께 제공
- 실거래가 기반 시세 분석
- 가격 추이 및 트렌드 파악

## 🔑 국토부 오픈API

### API 정보
- **제공기관**: 국토교통부
- **API 명**: 아파트매매 실거래 상세 자료
- **인증방식**: 일반 인증키 (Encoding)
- **요청방식**: GET (REST)
- **응답형식**: XML / JSON

### API 신청
1. 공공데이터포털 회원가입: https://www.data.go.kr
2. API 신청: "아파트매매 실거래 상세 자료" 검색
3. 활용신청 후 인증키 발급 (즉시)
4. 일일 트래픽: 1,000건 (무료)

### 엔드포인트
```
Base URL: http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/

- getRTMSDataSvcAptTradeDev: 아파트 매매 실거래 상세
```

## 📊 API 요청/응답 구조

### 요청 파라미터
```python
params = {
    'serviceKey': 'YOUR_API_KEY',          # 인증키
    'LAWD_CD': '41135',                     # 법정동코드 (5자리)
    'DEAL_YMD': '202410',                   # 계약월 (YYYYMM)
    'numOfRows': '100',                     # 결과 수
    'pageNo': '1',                          # 페이지 번호
    'type': 'json'                          # 응답 형식
}
```

### 법정동코드 찾기
```python
# 예시: 경기도 성남시 분당구 = 41135
# 서울시 강남구 = 11680
# 부산시 해운대구 = 26350

# 법정동코드 전체 목록: 행정안전부 제공
# https://www.code.go.kr/stdcode/regCodeL.do
```

### 응답 예시 (JSON)
```json
{
  "response": {
    "header": {
      "resultCode": "00",
      "resultMsg": "NORMAL SERVICE."
    },
    "body": {
      "items": {
        "item": [
          {
            "거래금액": "1,250,000,000",
            "건축년도": "2020",
            "년": "2024",
            "월": "10",
            "일": "15",
            "도로명": "판교역로 ",
            "도로명건물본번호코드": "235",
            "도로명건물부번호코드": "0",
            "도로명시군구코드": "41135",
            "도로명일련번호코드": "03",
            "도로명지상지하코드": "0",
            "도로명코드": "4113510600",
            "법정동": "백현동",
            "법정동본번코드": "532",
            "법정동부번코드": "0",
            "법정동시군구코드": "41135",
            "법정동읍면동코드": "10600",
            "법정동지번코드": "1",
            "아파트": "향촌현대5차",
            "전용면적": "59.97",
            "지번": "532",
            "지역코드": "41135",
            "층": "12",
            "해제사유발생일": null,
            "해제여부": null,
            "거래유형": "직거래",
            "중개사소재지": null
          }
        ]
      },
      "numOfRows": 100,
      "pageNo": 1,
      "totalCount": 1
    }
  }
}
```

## 🗄️ 데이터 모델 확장

### Transaction 테이블 수정
```python
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    complex_id = Column(String(50), ForeignKey("complexes.complex_id"))

    # 기본 정보
    trade_type = Column(String(10))  # A1(매매), B1(전세), B2(월세)

    # 거래 정보
    deal_amount = Column(BigInteger)           # 거래금액 (원)
    deal_year = Column(Integer)                # 거래년도
    deal_month = Column(Integer)               # 거래월
    deal_day = Column(Integer)                 # 거래일

    # 물건 정보
    building_name = Column(String(200))        # 아파트명
    exclusive_area = Column(Float)             # 전용면적(㎡)
    floor = Column(Integer)                    # 층
    construction_year = Column(Integer)        # 건축년도

    # 위치 정보
    region_code = Column(String(10))           # 지역코드
    legal_dong = Column(String(100))           # 법정동
    jibun = Column(String(20))                 # 지번
    road_name = Column(String(200))            # 도로명

    # 거래 상세
    transaction_type = Column(String(20))      # 거래유형 (직거래/중개거래)
    broker_location = Column(String(200))      # 중개사 소재지
    cancel_deal_date = Column(Date)            # 해제사유발생일
    cancel_deal_type = Column(String(10))      # 해제여부 (O/X)

    # 메타 정보
    source = Column(String(20), default='MOLIT')  # 데이터 출처 (MOLIT/NAVER)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

## 🔄 데이터 수집 플로우

### 1. 단지 정보 기반 법정동코드 추출
```python
async def get_lawd_code_from_complex(complex_id: str) -> str:
    """단지 주소에서 법정동코드 추출"""

    complex = await db.query(Complex).filter(
        Complex.complex_id == complex_id
    ).first()

    # 네이버 API에서 주소 정보 가져오기
    address = complex.address  # 예: "경기도 성남시 분당구 백현동"

    # 법정동코드 매핑 테이블에서 검색
    lawd_code = get_lawd_code_from_address(address)

    return lawd_code  # "41135"
```

### 2. 국토부 API 호출
```python
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

class MOLITAPIClient:
    """국토부 오픈API 클라이언트"""

    BASE_URL = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_apartment_trades(
        self,
        lawd_code: str,
        deal_ymd: str,  # YYYYMM
        num_of_rows: int = 1000,
        page_no: int = 1
    ) -> list:
        """아파트 매매 실거래 조회"""

        url = f"{self.BASE_URL}/getRTMSDataSvcAptTradeDev"

        params = {
            'serviceKey': self.api_key,
            'LAWD_CD': lawd_code,
            'DEAL_YMD': deal_ymd,
            'numOfRows': num_of_rows,
            'pageNo': page_no
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            return self._parse_xml_response(response.content)
        else:
            raise Exception(f"API Error: {response.status_code}")

    def _parse_xml_response(self, xml_content: bytes) -> list:
        """XML 응답 파싱"""

        root = ET.fromstring(xml_content)
        items = []

        for item in root.findall('.//item'):
            trade_data = {
                'deal_amount': self._parse_price(item.find('거래금액').text),
                'construction_year': int(item.find('건축년도').text),
                'deal_year': int(item.find('년').text),
                'deal_month': int(item.find('월').text),
                'deal_day': int(item.find('일').text.strip()),
                'building_name': item.find('아파트').text.strip(),
                'exclusive_area': float(item.find('전용면적').text),
                'floor': int(item.find('층').text),
                'legal_dong': item.find('법정동').text.strip(),
                'jibun': item.find('지번').text,
                'region_code': item.find('지역코드').text,
                'transaction_type': item.find('거래유형').text if item.find('거래유형') is not None else None,
                'cancel_deal_type': item.find('해제여부').text if item.find('해제여부') is not None else None,
            }
            items.append(trade_data)

        return items

    def _parse_price(self, price_str: str) -> int:
        """거래금액 파싱 (콤마 제거 후 만원 단위를 원 단위로)"""
        # "1,250,000,000" -> 1250000000
        return int(price_str.replace(',', '').strip()) * 10000
```

### 3. 단지 매칭 및 저장
```python
async def sync_molit_transactions(complex_id: str, months: int = 12):
    """국토부 실거래가 동기화"""

    # 1. 법정동코드 추출
    lawd_code = await get_lawd_code_from_complex(complex_id)

    # 2. 최근 N개월 데이터 수집
    client = MOLITAPIClient(api_key=settings.MOLIT_API_KEY)

    all_trades = []
    for i in range(months):
        target_date = datetime.now() - timedelta(days=30 * i)
        deal_ymd = target_date.strftime('%Y%m')

        trades = await client.get_apartment_trades(
            lawd_code=lawd_code,
            deal_ymd=deal_ymd
        )
        all_trades.extend(trades)

    # 3. 단지명으로 필터링
    complex = await db.query(Complex).filter(
        Complex.complex_id == complex_id
    ).first()

    matched_trades = [
        t for t in all_trades
        if t['building_name'] == complex.complex_name
    ]

    # 4. DB 저장
    saved_count = 0
    for trade in matched_trades:
        # 중복 체크
        existing = await db.query(Transaction).filter(
            Transaction.complex_id == complex_id,
            Transaction.deal_year == trade['deal_year'],
            Transaction.deal_month == trade['deal_month'],
            Transaction.deal_day == trade['deal_day'],
            Transaction.floor == trade['floor'],
            Transaction.exclusive_area == trade['exclusive_area']
        ).first()

        if not existing:
            transaction = Transaction(
                complex_id=complex_id,
                trade_type='A1',  # 매매
                source='MOLIT',
                **trade
            )
            db.add(transaction)
            saved_count += 1

    await db.commit()

    return {
        'total_trades': len(all_trades),
        'matched_trades': len(matched_trades),
        'saved_count': saved_count
    }
```

## 🎨 UI/UX 설계

### 1. 실거래가 탭 추가
```typescript
// complexes/[id]/page.tsx

<Tabs>
  <Tab label="매물 정보" />
  <Tab label="실거래가" />  {/* 신규 */}
  <Tab label="가격 추이" />  {/* 신규 */}
</Tabs>
```

### 2. 실거래가 테이블
```typescript
<div className="transactions-list">
  <h2>최근 실거래가</h2>
  <table>
    <thead>
      <tr>
        <th>거래일</th>
        <th>층</th>
        <th>면적</th>
        <th>거래금액</th>
        <th>거래유형</th>
      </tr>
    </thead>
    <tbody>
      {transactions.map(tx => (
        <tr key={tx.id}>
          <td>{tx.deal_year}.{tx.deal_month}.{tx.deal_day}</td>
          <td>{tx.floor}층</td>
          <td>{tx.exclusive_area}㎡</td>
          <td>{formatPrice(tx.deal_amount)}</td>
          <td>{tx.transaction_type}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

### 3. 가격 추이 차트
```typescript
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';

<LineChart data={priceHistory}>
  <XAxis dataKey="month" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Line
    type="monotone"
    dataKey="avgPrice"
    stroke="#8884d8"
    name="평균 거래가"
  />
  <Line
    type="monotone"
    dataKey="maxPrice"
    stroke="#82ca9d"
    name="최고가"
  />
  <Line
    type="monotone"
    dataKey="minPrice"
    stroke="#ffc658"
    name="최저가"
  />
</LineChart>
```

## 📡 API 엔드포인트

### 실거래가 조회
```python
@router.get("/transactions/complex/{complex_id}")
async def get_complex_transactions(
    complex_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    area_min: Optional[float] = None,
    area_max: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """단지별 실거래가 조회"""

    query = db.query(Transaction).filter(
        Transaction.complex_id == complex_id
    )

    if start_date:
        query = query.filter(Transaction.deal_year >= int(start_date[:4]))

    if area_min:
        query = query.filter(Transaction.exclusive_area >= area_min)

    transactions = query.order_by(
        Transaction.deal_year.desc(),
        Transaction.deal_month.desc(),
        Transaction.deal_day.desc()
    ).all()

    return transactions
```

### 가격 추이 분석
```python
@router.get("/transactions/complex/{complex_id}/price-trend")
async def get_price_trend(
    complex_id: str,
    months: int = 12,
    area: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """가격 추이 분석"""

    # 최근 N개월 데이터
    cutoff_date = datetime.now() - timedelta(days=30 * months)

    query = db.query(Transaction).filter(
        Transaction.complex_id == complex_id,
        Transaction.deal_year >= cutoff_date.year
    )

    if area:
        # 면적 ±5㎡ 범위
        query = query.filter(
            Transaction.exclusive_area.between(area - 5, area + 5)
        )

    transactions = query.all()

    # 월별 통계
    monthly_stats = {}
    for tx in transactions:
        month_key = f"{tx.deal_year}-{tx.deal_month:02d}"

        if month_key not in monthly_stats:
            monthly_stats[month_key] = []

        monthly_stats[month_key].append(tx.deal_amount)

    # 결과 포맷
    trend = []
    for month, prices in sorted(monthly_stats.items()):
        trend.append({
            'month': month,
            'avgPrice': sum(prices) // len(prices),
            'minPrice': min(prices),
            'maxPrice': max(prices),
            'count': len(prices)
        })

    return trend
```

### 국토부 API 동기화
```python
@router.post("/transactions/sync/{complex_id}")
async def sync_transactions(
    complex_id: str,
    months: int = 12,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """국토부 실거래가 동기화"""

    background_tasks.add_task(
        sync_molit_transactions,
        complex_id=complex_id,
        months=months
    )

    return {
        "message": "실거래가 동기화 시작",
        "complex_id": complex_id,
        "months": months
    }
```

## ⚙️ 설정

### 환경변수
```bash
# .env
MOLIT_API_KEY=your_api_key_here
MOLIT_API_DAILY_LIMIT=1000
```

### 법정동코드 매핑 테이블
```python
# 법정동코드 CSV 다운로드 및 DB 저장
# https://www.code.go.kr/stdcode/regCodeL.do

class LegalDongCode(Base):
    __tablename__ = "legal_dong_codes"

    code = Column(String(10), primary_key=True)
    sido = Column(String(50))
    sigungu = Column(String(50))
    dong = Column(String(50))
    full_name = Column(String(200))
```

## 📅 개발 일정

### Week 1: API 연동 및 데이터 수집
- [ ] 국토부 오픈API 인증키 발급
- [ ] MOLITAPIClient 구현
- [ ] 법정동코드 매핑 데이터 구축
- [ ] Transaction 모델 확장
- [ ] 데이터 수집 및 저장 로직

### Week 2: API 및 분석 기능
- [ ] 실거래가 조회 API
- [ ] 가격 추이 분석 API
- [ ] 면적별 실거래가 통계
- [ ] 단지 매칭 로직 개선

### Week 3: 프론트엔드 개발
- [ ] 실거래가 페이지
- [ ] 가격 추이 차트 (Recharts)
- [ ] 필터링 기능 (기간/면적)
- [ ] 실거래가 탭 UI

## 🔍 고려사항

### 1. 데이터 정합성
- 단지명이 국토부와 네이버에서 다를 수 있음
- 주소 기반 매칭 로직 필요

### 2. API 제한
- 일일 1,000건 제한
- 월 단위 조회이므로 1년 = 12건

### 3. 업데이트 주기
- 국토부 데이터는 월 1회 업데이트
- 매월 초 자동 동기화 설정

## 📚 참고 자료

- [공공데이터포털](https://www.data.go.kr)
- [국토교통부 실거래가 공개시스템](https://rt.molit.go.kr)
- [법정동코드](https://www.code.go.kr)
