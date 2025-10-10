#!/bin/bash

# 네이버 부동산 로컬 개발 서버 시작 스크립트

echo "🚀 네이버 부동산 로컬 개발 환경 시작..."
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")"

# 1. Docker 서비스 시작
echo "📦 Docker 서비스 시작 (PostgreSQL, Redis)..."
docker-compose up -d postgres redis

# 2초 대기
sleep 2

# 2. Backend API 서버 시작
echo ""
echo "🔧 Backend API 서버 시작..."
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 3초 대기
sleep 3

# 3. Celery Worker 시작
echo ""
echo "⚙️  Celery Worker 시작..."
cd backend
.venv/bin/celery -A app.core.celery_app worker --loglevel=info &
WORKER_PID=$!
cd ..

# 2초 대기
sleep 2

# 4. Celery Beat 시작
echo ""
echo "⏰ Celery Beat 시작..."
cd backend
.venv/bin/celery -A app.core.celery_app beat --scheduler redbeat.RedBeatScheduler --loglevel=info &
BEAT_PID=$!
cd ..

# 2초 대기
sleep 2

# 5. Frontend 시작
echo ""
echo "🎨 Frontend 시작..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ 모든 서비스가 시작되었습니다!"
echo ""
echo "📍 서비스 접속 주소:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000/docs"
echo "   - PostgreSQL: localhost:5433"
echo "   - Redis: localhost:6380"
echo ""
echo "프로세스 ID:"
echo "   - Backend: $BACKEND_PID"
echo "   - Worker: $WORKER_PID"
echo "   - Beat: $BEAT_PID"
echo "   - Frontend: $FRONTEND_PID"
echo ""
echo "종료하려면: ./stop_dev.sh 실행"

# PID 저장
echo "$BACKEND_PID" > .backend.pid
echo "$WORKER_PID" > .worker.pid
echo "$BEAT_PID" > .beat.pid
echo "$FRONTEND_PID" > .frontend.pid
