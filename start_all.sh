#!/bin/bash

# 네이버 부동산 전체 서비스 시작 스크립트

echo "🚀 네이버 부동산 시스템 시작 중..."

# 1. Docker 서비스 시작 (PostgreSQL, Redis)
echo ""
echo "📦 Docker 서비스 시작 (PostgreSQL, Redis)..."
docker-compose up -d postgres redis

# 2. API 서버 시작
echo ""
echo "🔧 API 서버 시작 중..."
cd backend
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"' &
sleep 2

# 3. Celery Worker 시작
echo ""
echo "👷 Celery Worker 시작 중..."
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && ./run_celery_worker.sh"' &
sleep 2

# 4. Celery Beat 시작
echo ""
echo "⏰ Celery Beat (스케줄러) 시작 중..."
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && ./run_celery_beat.sh"' &
sleep 2

# 5. 프론트엔드 시작
echo ""
echo "🎨 프론트엔드 시작 중..."
cd ../frontend
osascript -e 'tell application "Terminal" to do script "cd \"'$(pwd)'\" && npm run dev"' &

echo ""
echo "✅ 모든 서비스 시작 완료!"
echo ""
echo "📊 접속 정보:"
echo "   - 프론트엔드: http://localhost:3000"
echo "   - API 서버: http://localhost:8000"
echo "   - API 문서: http://localhost:8000/docs"
echo ""
echo "💡 각 서비스는 별도의 터미널 창에서 실행됩니다."
echo "💡 종료하려면 각 터미널 창에서 Ctrl+C를 누르세요."
