#!/bin/bash

# 실거래가 API 테스트 스크립트

API_URL="http://localhost:8000"

echo "================================"
echo "실거래가 API 테스트"
echo "================================"
echo ""

# 1. 단지 목록 조회
echo "1. 단지 목록 조회"
echo "GET /api/complexes/"
curl -s "${API_URL}/api/complexes/" | python3 -m json.tool | head -20
echo ""
echo "--------------------------------"
echo ""

# 2. 법정동 코드 파싱 테스트
echo "2. LocationParser 테스트 (Python)"
cd backend
.venv/bin/python << 'EOF'
from app.services.location_parser import LocationParser

parser = LocationParser()

test_addresses = [
    "경기도 성남시 분당구 정자동",
    "서울특별시 강남구 역삼동",
    "경기도 용인시 수지구 죽전동",
    "서울특별시 서초구 반포동",
]

print("\n법정동 코드 추출 테스트:")
print("-" * 60)
for addr in test_addresses:
    code = parser.extract_sigungu_code(addr)
    info = parser.get_location_info(addr)
    print(f"주소: {addr}")
    print(f"  → 시군구 코드: {code}")
    print(f"  → 위치명: {info['location_name']}")
    print()
EOF
cd ..
echo ""
echo "--------------------------------"
echo ""

# 3. MOLIT API 키 확인
echo "3. MOLIT API 키 확인"
if [ -z "$MOLIT_API_KEY" ]; then
    echo "⚠️  환경변수 MOLIT_API_KEY가 설정되지 않았습니다."
    echo "   .env 파일을 확인하세요."
else
    echo "✅ MOLIT_API_KEY: ${MOLIT_API_KEY:0:20}..."
fi
echo ""
echo "--------------------------------"
echo ""

# 4. 실거래가 조회 테스트 (실제 단지가 있는 경우)
echo "4. 실거래가 통계 API 테스트"
echo ""

# 먼저 단지 ID 하나 가져오기
COMPLEX_ID=$(curl -s "${API_URL}/api/complexes/" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['complex_id'] if data else '')" 2>/dev/null)

if [ -z "$COMPLEX_ID" ]; then
    echo "⚠️  등록된 단지가 없습니다."
    echo "   단지를 먼저 추가해주세요."
    echo ""
    echo "예시:"
    echo "  1. http://localhost:3000 접속"
    echo "  2. '새 단지 추가' 클릭"
    echo "  3. 네이버 부동산 URL 입력"
else
    echo "테스트 단지 ID: ${COMPLEX_ID}"
    echo ""

    echo "GET /api/transactions/stats/area-summary/${COMPLEX_ID}?months=6"
    curl -s "${API_URL}/api/transactions/stats/area-summary/${COMPLEX_ID}?months=6" | python3 -m json.tool
    echo ""
fi

echo ""
echo "--------------------------------"
echo ""

# 5. 서버 로그 확인
echo "5. 최근 서버 로그 (실거래가 관련)"
echo ""
echo "📋 실거래가 조회 로그를 확인하려면:"
echo "   Backend 서버 콘솔을 확인하세요."
echo ""

echo "================================"
echo "테스트 완료"
echo "================================"
echo ""
echo "💡 Tips:"
echo "  - 국가정보자원 시스템이 운영 중일 때 실제 데이터 조회 가능"
echo "  - API 키: .env 파일의 MOLIT_API_KEY 확인"
echo "  - 단지 추가: http://localhost:3000에서 진행"
echo ""
