# 테스트 스크립트 가이드

이 디렉토리에는 API 및 기능 테스트를 위한 스크립트가 포함되어 있습니다.

## 📋 테스트 스크립트 목록

### 1. **test_api.sh** - 기본 API 테스트

**목적**: 주요 API 엔드포인트가 정상 작동하는지 확인

**테스트 항목**:
- ✅ 헬스 체크
- ✅ 단지 목록 조회
- ✅ 단지 상세 정보
- ✅ 단지 통계
- ✅ 매물 검색
- ✅ 실거래가 통계

**사용 방법**:
```bash
cd /Users/specialrisk_mac/code_work/naver_realestate
./tests/test_api.sh
```

**사전 요구사항**:
- Backend API 서버 실행 중 (localhost:8000)
- 최소 1개 이상의 단지 등록

**개선사항**:
- ✅ 동적 단지 ID 조회 (하드코딩 제거)
- ✅ API 경로 수정 (`/api/` prefix 추가)

---

### 2. **test_discord_briefing.sh** - Discord 브리핑 테스트

**목적**: Discord Webhook을 통한 주간 브리핑 전송 테스트

**테스트 항목**:
- ✅ .env 파일 존재 확인
- ✅ DISCORD_WEBHOOK_URL 설정 확인
- ✅ 브리핑 생성 및 Discord 전송

**사용 방법**:
```bash
cd /Users/specialrisk_mac/code_work/naver_realestate
./tests/test_discord_briefing.sh
```

**사전 요구사항**:
- `.env` 파일에 `DISCORD_WEBHOOK_URL` 설정
- PostgreSQL 실행 중
- 크롤링된 데이터 및 변동사항 존재

**Discord Webhook 설정**:
1. Discord 서버 → 채널 설정 → 연동 → 웹후크
2. 웹후크 URL 복사
3. `.env` 파일에 추가:
   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

**주의사항**:
- 변동사항이 없으면 브리핑이 전송되지 않음
- 먼저 크롤링을 실행하여 변동사항 생성 필요

---

### 3. **test_transaction_api.sh** - 실거래가 API 테스트

**목적**: 국토교통부 실거래가 API 연동 및 통계 기능 테스트

**테스트 항목**:
- ✅ 단지 목록 조회
- ✅ LocationParser (법정동 코드 추출)
- ✅ MOLIT API 키 확인
- ✅ 실거래가 통계 조회

**사용 방법**:
```bash
cd /Users/specialrisk_mac/code_work/naver_realestate
./tests/test_transaction_api.sh
```

**사전 요구사항**:
- Backend API 서버 실행 중
- `.env` 파일에 `MOLIT_API_KEY` 설정
- 최소 1개 이상의 단지 등록

**MOLIT API 키 발급**:
1. https://www.data.go.kr/data/15058017/openapi.do 접속
2. 로그인 → 활용신청
3. 발급받은 키를 `.env`에 추가:
   ```bash
   MOLIT_API_KEY=your_api_key_here
   ```

**LocationParser 테스트 주소**:
- 경기도 성남시 분당구 정자동
- 서울특별시 강남구 역삼동
- 경기도 용인시 수지구 죽전동
- 서울특별시 서초구 반포동

---

## 🚀 전체 테스트 실행

모든 테스트를 순차적으로 실행:

```bash
cd /Users/specialrisk_mac/code_work/naver_realestate/tests
./test_api.sh
./test_transaction_api.sh
./test_discord_briefing.sh
```

## 📝 테스트 전 체크리스트

- [ ] Docker 서비스 실행 (`docker-compose up -d`)
- [ ] Backend API 서버 실행 (포트 8000)
- [ ] 데이터베이스 마이그레이션 완료
- [ ] `.env` 파일 설정 완료
  - [ ] `MOLIT_API_KEY`
  - [ ] `DISCORD_WEBHOOK_URL` (Discord 테스트 시)
- [ ] 최소 1개 단지 등록 완료

## 🐛 문제 해결

### API 서버 응답 없음
```bash
# 서버 상태 확인
curl http://localhost:8000/health

# 로그 확인
tail -f logs/backend.log
```

### 단지가 없음
```bash
# 브라우저에서 단지 추가
# http://localhost:3000 → 새 단지 추가
```

### MOLIT API 키 에러
```bash
# .env 파일 확인
cat .env | grep MOLIT_API_KEY

# 키 유효성 확인 (공공데이터포털)
```

### Discord 브리핑 전송 실패
```bash
# Webhook URL 테스트
curl -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "테스트 메시지"}'
```

## 💡 추가 팁

### 개별 API 호출 테스트
```bash
# 단지 목록
curl http://localhost:8000/api/complexes/ | jq

# 특정 단지 상세
curl http://localhost:8000/api/complexes/109208 | jq

# 실거래가 통계
curl "http://localhost:8000/api/transactions/stats/area-summary/109208?months=6" | jq
```

### Python 대화형 테스트
```bash
cd backend
.venv/bin/python

# Python 인터프리터에서
>>> from app.services.location_parser import LocationParser
>>> parser = LocationParser()
>>> parser.extract_sigungu_code("경기도 성남시 분당구")
'41135'
```

## 📚 관련 문서

- [README_STARTUP.md](../README_STARTUP.md) - 서비스 시작 가이드
- [CLAUDE.md](../CLAUDE.md) - 프로젝트 개발 가이드
- [API 문서](http://localhost:8000/docs) - Swagger UI (서버 실행 중)
