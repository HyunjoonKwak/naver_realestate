#!/bin/bash

# 네이버 부동산 로컬 개발 환경 통합 시작 스크립트
# 모든 서비스를 백그라운드로 실행하고 로그를 통합 관리

set -e  # 에러 발생 시 스크립트 중단

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

# 로그 디렉토리 생성
mkdir -p "$LOG_DIR"

echo "🚀 네이버 부동산 로컬 개발 환경 시작..."
echo ""

# 기존 프로세스 정리
echo "🧹 기존 프로세스 정리 중..."
pkill -f "uvicorn app.main" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 2

# 1. Docker 서비스 시작
echo "📦 Docker 서비스 시작 (PostgreSQL, Redis)..."
docker-compose up -d postgres redis
sleep 3

# 2. Backend API 서버 시작
echo "🔧 Backend API 서버 시작..."
cd "$PROJECT_ROOT/backend"
nohup .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
  > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
sleep 3

# 3. Celery Worker 시작
echo "⚙️  Celery Worker 시작..."
cd "$PROJECT_ROOT/backend"
nohup .venv/bin/celery -A app.core.celery_app worker --loglevel=info \
  > "$LOG_DIR/worker.log" 2>&1 &
WORKER_PID=$!
echo "   PID: $WORKER_PID"
sleep 2

# 4. Celery Beat 시작
echo "⏰ Celery Beat 시작..."
cd "$PROJECT_ROOT/backend"
nohup .venv/bin/celery -A app.core.celery_app beat --scheduler redbeat.RedBeatScheduler --loglevel=info \
  > "$LOG_DIR/beat.log" 2>&1 &
BEAT_PID=$!
echo "   PID: $BEAT_PID"
sleep 2

# 5. Frontend 시작
echo "🎨 Frontend 시작..."
cd "$PROJECT_ROOT/frontend"
nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "   PID: $FRONTEND_PID"
sleep 3

echo ""
echo "✅ 모든 서비스가 시작되었습니다!"
echo ""
echo "📍 서비스 접속 주소:"
echo "   - Frontend:        http://localhost:3000"
echo "   - Backend API:     http://localhost:8000/docs"
echo "   - Scheduler:       http://localhost:3000/scheduler"
echo ""
echo "📊 로그 확인:"
echo "   - Backend:         tail -f $LOG_DIR/backend.log"
echo "   - Celery Worker:   tail -f $LOG_DIR/worker.log"
echo "   - Celery Beat:     tail -f $LOG_DIR/beat.log"
echo "   - Frontend:        tail -f $LOG_DIR/frontend.log"
echo ""
echo "🛑 종료하려면: ./stop_all.sh"
echo ""

# 서비스 상태 확인
echo "⏳ 서비스 준비 중..."
sleep 5

# API 서버 확인
if curl -s http://localhost:8000/api/scheduler/status > /dev/null 2>&1; then
    echo "✅ Backend API: 정상 작동"
else
    echo "⚠️  Backend API: 확인 필요 (로그: tail -f $LOG_DIR/backend.log)"
fi

# Frontend 확인
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend: 정상 작동"
else
    echo "⚠️  Frontend: 확인 필요 (로그: tail -f $LOG_DIR/frontend.log)"
fi

echo ""
echo "💡 팁: './logs_all.sh' 명령으로 모든 로그를 실시간으로 볼 수 있습니다"
