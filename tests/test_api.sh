#!/bin/bash

# FastAPI 테스트 스크립트

echo "================================"
echo "🧪 API 엔드포인트 테스트"
echo "================================"
echo ""

BASE_URL="http://localhost:8000"

echo "1️⃣  루트 엔드포인트"
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""

echo "2️⃣  헬스 체크"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

echo "3️⃣  단지 목록"
curl -s "$BASE_URL/api/complexes/" | python3 -m json.tool
echo ""

# 첫 번째 단지 ID 동적으로 가져오기
COMPLEX_ID=$(curl -s "$BASE_URL/api/complexes/" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['complex_id'] if data else '')" 2>/dev/null)

if [ -z "$COMPLEX_ID" ]; then
    echo "⚠️  등록된 단지가 없습니다. 단지를 먼저 추가하세요."
    echo ""
else
    echo "4️⃣  단지 상세 ($COMPLEX_ID)"
    curl -s "$BASE_URL/api/complexes/$COMPLEX_ID" | python3 -m json.tool | head -50
    echo ""

    echo "5️⃣  단지 통계 ($COMPLEX_ID)"
    curl -s "$BASE_URL/api/complexes/$COMPLEX_ID/stats" | python3 -m json.tool
    echo ""
fi

echo "6️⃣  매물 검색 (최근 3건)"
curl -s "$BASE_URL/articles/?limit=3" | python3 -m json.tool | head -40
echo ""

if [ ! -z "$COMPLEX_ID" ]; then
    echo "7️⃣  평형별 실거래가 요약 ($COMPLEX_ID)"
    curl -s "$BASE_URL/api/transactions/stats/area-summary/$COMPLEX_ID?months=6" | python3 -m json.tool
    echo ""
fi

echo "✅ 테스트 완료!"
echo ""
echo "📖 API 문서: http://localhost:8000/docs"
echo "📖 ReDoc: http://localhost:8000/redoc"
