#!/bin/bash

# 네이버 부동산 로컬 개발 서버 종료 스크립트

echo "🛑 네이버 부동산 로컬 개발 환경 종료..."
echo ""

# 프로젝트 루트로 이동
cd "$(dirname "$0")"

# PID 파일에서 프로세스 종료
if [ -f .backend.pid ]; then
    PID=$(cat .backend.pid)
    echo "Backend API 종료 (PID: $PID)..."
    kill $PID 2>/dev/null || echo "  (이미 종료됨)"
    rm .backend.pid
fi

if [ -f .worker.pid ]; then
    PID=$(cat .worker.pid)
    echo "Celery Worker 종료 (PID: $PID)..."
    kill $PID 2>/dev/null || echo "  (이미 종료됨)"
    rm .worker.pid
fi

if [ -f .beat.pid ]; then
    PID=$(cat .beat.pid)
    echo "Celery Beat 종료 (PID: $PID)..."
    kill $PID 2>/dev/null || echo "  (이미 종료됨)"
    rm .beat.pid
fi

if [ -f .frontend.pid ]; then
    PID=$(cat .frontend.pid)
    echo "Frontend 종료 (PID: $PID)..."
    kill $PID 2>/dev/null || echo "  (이미 종료됨)"
    rm .frontend.pid
fi

echo ""
echo "Docker 서비스 종료..."
docker-compose down

echo ""
echo "✅ 모든 서비스가 종료되었습니다!"
