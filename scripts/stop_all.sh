#!/bin/bash

# 네이버 부동산 로컬 개발 환경 종료 스크립트

echo "🛑 네이버 부동산 로컬 개발 환경 종료 중..."
echo ""

# 프로세스 종료
echo "Backend API 종료..."
pkill -f "uvicorn app.main" || echo "  (프로세스 없음)"

echo "Celery Worker 종료..."
pkill -f "celery.*worker" || echo "  (프로세스 없음)"

echo "Celery Beat 종료..."
pkill -f "celery.*beat" || echo "  (프로세스 없음)"

echo "Frontend 종료..."
pkill -f "next dev" || echo "  (프로세스 없음)"

sleep 2

# Docker는 유지 (데이터 보존)
echo ""
echo "📦 Docker 서비스는 계속 실행 중입니다 (데이터 보존)"
echo "   Docker도 종료하려면: docker-compose down"
echo ""
echo "✅ 모든 개발 서버가 종료되었습니다!"
