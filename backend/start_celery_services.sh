#!/bin/bash

# Celery Worker와 Beat를 백그라운드에서 시작하는 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Celery 서비스 시작 중..."

# Worker 시작
echo "👷 Celery Worker 시작..."
nohup .venv/bin/celery -A app.core.celery_app worker --loglevel=info --pool=solo > logs/celery_worker.log 2>&1 &
WORKER_PID=$!
echo $WORKER_PID > celery_worker.pid
echo "   Worker PID: $WORKER_PID"

# Beat 시작
echo "⏰ Celery Beat 시작..."
nohup .venv/bin/celery -A app.core.celery_app beat --loglevel=info > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo $BEAT_PID > celery_beat.pid
echo "   Beat PID: $BEAT_PID"

echo ""
echo "✅ Celery 서비스 시작 완료!"
echo ""
echo "로그 확인:"
echo "   tail -f logs/celery_worker.log"
echo "   tail -f logs/celery_beat.log"
echo ""
echo "종료하려면:"
echo "   ./stop_celery_services.sh"
