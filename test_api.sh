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
curl -s "$BASE_URL/complexes/" | python3 -m json.tool
echo ""

echo "4️⃣  단지 상세 (109208)"
curl -s "$BASE_URL/complexes/109208" | python3 -m json.tool | head -50
echo ""

echo "5️⃣  단지 통계 (109208)"
curl -s "$BASE_URL/complexes/109208/stats" | python3 -m json.tool
echo ""

echo "6️⃣  매물 검색 (최근 3건)"
curl -s "$BASE_URL/articles/?limit=3" | python3 -m json.tool | head -40
echo ""

echo "7️⃣  최근 실거래가"
curl -s "$BASE_URL/transactions/recent" | python3 -m json.tool
echo ""

echo "8️⃣  가격 추이 (109208)"
curl -s "$BASE_URL/transactions/stats/price-trend?complex_id=109208&months=12" | python3 -m json.tool
echo ""

echo "✅ 테스트 완료!"
echo ""
echo "📖 API 문서: http://localhost:8000/docs"
echo "📖 ReDoc: http://localhost:8000/redoc"
