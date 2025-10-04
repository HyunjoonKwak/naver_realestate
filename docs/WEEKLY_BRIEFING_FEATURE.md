# 주간 변동사항 브리핑 기능 설계

## 📋 개요

단지별 주간 변동사항을 자동으로 분석하고 요약하여 사용자에게 제공하는 기능

## 🎯 목표

사용자가 한눈에 단지의 변화를 파악할 수 있도록:
- 매물 증감 현황
- 가격 변동 추이
- 특이사항 및 인사이트

## 📊 수집 데이터

### 1. 매물 증감
- **신규 매물**: 이번 주 새로 등록된 매물
- **소멸 매물**: 이번 주 삭제된 매물 (거래 완료 추정)
- **변동 없음**: 지속적으로 존재하는 매물

### 2. 가격 변동
- **가격 인상**: 매물별 가격 인상 내역
- **가격 인하**: 매물별 가격 인하 내역
- **평균 변동률**: 면적별/전체 평균 가격 변동률

### 3. 특이사항
- **급등/급락**: 10% 이상 가격 변동
- **거래 급증**: 주간 거래 완료 매물 급증
- **신규 평형**: 새로운 면적 매물 등장
- **최저가 갱신**: 역대 최저가 경신
- **최고가 갱신**: 역대 최고가 경신

## 🗂️ 데이터 구조

### WeeklySnapshot 테이블
```sql
CREATE TABLE weekly_snapshots (
    id SERIAL PRIMARY KEY,
    complex_id VARCHAR(50) NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,

    -- 매물 수 통계
    total_articles INTEGER,
    sale_articles INTEGER,
    lease_articles INTEGER,

    -- 신규/소멸
    new_articles_count INTEGER,
    removed_articles_count INTEGER,

    -- 가격 통계
    avg_sale_price BIGINT,
    avg_lease_price BIGINT,
    min_sale_price BIGINT,
    max_sale_price BIGINT,

    -- JSON 상세 데이터
    new_articles_detail JSONB,
    removed_articles_detail JSONB,
    price_changes_detail JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(complex_id, week_start_date)
);
```

### WeeklyBriefing 테이블
```sql
CREATE TABLE weekly_briefings (
    id SERIAL PRIMARY KEY,
    complex_id VARCHAR(50) NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,

    -- 요약 정보
    summary TEXT,
    highlights JSONB,  -- 주요 변동사항
    insights JSONB,    -- AI 인사이트

    -- 통계
    article_change_rate FLOAT,  -- 매물 증감률
    price_change_rate FLOAT,    -- 평균 가격 변동률

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(complex_id, week_start_date)
);
```

## 🔄 처리 플로우

### 1. 주간 스냅샷 생성 (매일 자동)
```python
async def create_daily_snapshot(complex_id: str):
    """매일 저녁 현재 매물 상태를 스냅샷으로 저장"""
    articles = await get_all_articles(complex_id)

    snapshot = {
        'date': datetime.now().date(),
        'complex_id': complex_id,
        'articles': articles,
        'stats': calculate_stats(articles)
    }

    await save_snapshot(snapshot)
```

### 2. 주간 비교 분석 (매주 월요일)
```python
async def analyze_weekly_changes(complex_id: str):
    """지난 주 스냅샷과 비교하여 변동사항 분석"""

    # 이번 주 / 지난 주 스냅샷
    this_week = await get_week_snapshots(complex_id, weeks_ago=0)
    last_week = await get_week_snapshots(complex_id, weeks_ago=1)

    # 매물 증감 분석
    new_articles = find_new_articles(this_week, last_week)
    removed_articles = find_removed_articles(this_week, last_week)

    # 가격 변동 분석
    price_changes = analyze_price_changes(this_week, last_week)

    # 특이사항 감지
    anomalies = detect_anomalies(price_changes)

    return {
        'new_articles': new_articles,
        'removed_articles': removed_articles,
        'price_changes': price_changes,
        'anomalies': anomalies
    }
```

### 3. 브리핑 리포트 생성
```python
async def generate_briefing(complex_id: str, analysis: dict):
    """분석 결과를 기반으로 브리핑 생성"""

    summary = f"""
    📊 {complex.name} 주간 브리핑 ({week_start} ~ {week_end})

    📈 매물 현황
    - 전체: {total_count}건 ({change_rate:+.1f}%)
    - 신규: {new_count}건
    - 소멸: {removed_count}건 (거래 완료 추정)

    💰 가격 동향
    - 평균 가격: {avg_price} ({price_change_rate:+.1f}%)
    - 인상: {price_up_count}건
    - 인하: {price_down_count}건

    ⚠️ 특이사항
    {anomalies_text}
    """

    await save_briefing({
        'complex_id': complex_id,
        'summary': summary,
        'highlights': get_highlights(analysis),
        'insights': generate_ai_insights(analysis)
    })
```

## 🎨 UI/UX 설계

### 1. 대시보드 위젯
```typescript
// 대시보드에 주간 브리핑 카드 추가
<div className="weekly-briefing-card">
  <h3>이번 주 변동사항</h3>
  <div className="briefing-summary">
    <div className="metric">
      <span className="label">신규 매물</span>
      <span className="value positive">+5건</span>
    </div>
    <div className="metric">
      <span className="label">평균 가격</span>
      <span className="value negative">-2.3%</span>
    </div>
  </div>
  <Link href={`/complexes/${id}/briefing`}>
    상세 보기 →
  </Link>
</div>
```

### 2. 단지별 브리핑 페이지
```
/complexes/[id]/briefing

📊 향촌현대5차 주간 브리핑
2025.09.30 - 2025.10.06

┌─────────────────────────┐
│  매물 현황              │
├─────────────────────────┤
│ 전체: 24건 (+3건, +14%) │
│ 신규: 5건               │
│ 소멸: 2건               │
└─────────────────────────┘

┌─────────────────────────┐
│  가격 동향              │
├─────────────────────────┤
│ 평균: 12억 5천 (-1.8%)  │
│ 최저: 11억 8천 (신규)   │
│ 최고: 13억 2천 (유지)   │
└─────────────────────────┘

⚠️ 특이사항
• 106동 1204호 급락 (-15%)
• 59A형 신규 매물 3건 등장
• 전세 가격 전반적 하락 추세
```

### 3. 주간 트렌드 차트
```typescript
// Recharts를 활용한 주간 트렌드
<LineChart data={weeklyData}>
  <XAxis dataKey="week" />
  <YAxis />
  <Line
    type="monotone"
    dataKey="avgPrice"
    stroke="#8884d8"
    name="평균 가격"
  />
  <Line
    type="monotone"
    dataKey="articleCount"
    stroke="#82ca9d"
    name="매물 수"
  />
</LineChart>
```

## 🔔 알림 설정

### 1. 브리핑 알림 조건
- **매주 월요일 오전 9시**: 주간 브리핑 자동 발송
- **특이사항 발생 시**: 즉시 알림
  - 가격 10% 이상 변동
  - 매물 50% 이상 증감
  - 신규 평형 등장

### 2. 알림 채널
- 이메일
- 앱 푸시 (향후)
- Slack/Discord 웹훅

## 📈 분석 지표

### 1. 매물 증감률
```python
article_change_rate = (this_week_count - last_week_count) / last_week_count * 100
```

### 2. 가격 변동률
```python
# 면적별 평균 가격 변동률
area_price_change = {}
for area in areas:
    this_week_avg = calculate_avg_price(this_week, area)
    last_week_avg = calculate_avg_price(last_week, area)
    change_rate = (this_week_avg - last_week_avg) / last_week_avg * 100
    area_price_change[area] = change_rate
```

### 3. 거래 추정
```python
# 소멸된 매물 = 거래 완료 추정
estimated_deals = removed_articles.filter(
    lambda a: a.days_on_market < 30  # 30일 이내 소멸
)
```

## 🤖 AI 인사이트 (향후)

### GPT 기반 시장 분석
```python
async def generate_ai_insights(analysis: dict) -> str:
    prompt = f"""
    다음 부동산 데이터를 분석하여 투자 인사이트를 제공하세요:

    단지: {complex_name}
    매물 증감: {article_change}
    가격 변동: {price_change}
    특이사항: {anomalies}

    1. 현재 시장 상황 요약
    2. 가격 동향 분석
    3. 투자 전략 제안
    """

    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

## 📅 개발 일정

### Phase 1: 데이터 수집 (1주)
- [x] WeeklySnapshot 테이블 설계
- [ ] 일일 스냅샷 생성 로직
- [ ] 스냅샷 저장 API

### Phase 2: 분석 엔진 (1주)
- [ ] 매물 증감 분석
- [ ] 가격 변동 분석
- [ ] 특이사항 감지 알고리즘

### Phase 3: 브리핑 생성 (1주)
- [ ] 주간 비교 로직
- [ ] 브리핑 리포트 생성
- [ ] 하이라이트 추출

### Phase 4: UI 개발 (1주)
- [ ] 브리핑 페이지
- [ ] 주간 트렌드 차트
- [ ] 대시보드 위젯

### Phase 5: 알림 시스템 (1주)
- [ ] 이메일 발송
- [ ] 스케줄링 (매주 월요일)
- [ ] 특이사항 즉시 알림

## 🎯 성공 지표

- 주간 브리핑 생성 성공률 > 95%
- 특이사항 감지 정확도 > 90%
- 사용자 브리핑 열람률 > 60%
- 알림 클릭률 > 40%

## 🔒 보안 고려사항

- 개인정보 비식별화
- 알림 구독 동의 관리
- 데이터 보관 기간 설정 (최대 1년)

## 📚 참고 자료

- [시계열 데이터 분석](https://en.wikipedia.org/wiki/Time_series)
- [이상 감지 알고리즘](https://en.wikipedia.org/wiki/Anomaly_detection)
- [부동산 시장 분석 방법론](https://www.example.com)
