#!/bin/bash

# Celery Worker와 Beat를 중지하는 스크립트

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Celery 서비스 중지 중..."

# Worker 중지
if [ -f celery_worker.pid ]; then
    WORKER_PID=$(cat celery_worker.pid)
    if ps -p $WORKER_PID > /dev/null 2>&1; then
        echo "   Worker (PID: $WORKER_PID) 중지..."
        kill $WORKER_PID
        rm celery_worker.pid
    else
        echo "   Worker 프로세스를 찾을 수 없습니다."
        rm celery_worker.pid
    fi
else
    echo "   Worker PID 파일이 없습니다."
fi

# Beat 중지
if [ -f celery_beat.pid ]; then
    BEAT_PID=$(cat celery_beat.pid)
    if ps -p $BEAT_PID > /dev/null 2>&1; then
        echo "   Beat (PID: $BEAT_PID) 중지..."
        kill $BEAT_PID
        rm celery_beat.pid
    else
        echo "   Beat 프로세스를 찾을 수 없습니다."
        rm celery_beat.pid
    fi
else
    echo "   Beat PID 파일이 없습니다."
fi

echo ""
echo "✅ Celery 서비스 중지 완료!"
