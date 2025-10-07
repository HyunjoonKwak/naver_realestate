#!/bin/bash
# Celery Beat (스케줄러) 실행 스크립트

cd "$(dirname "$0")"

echo "⏰ Celery Beat (스케줄러) 시작..."
.venv/bin/celery -A app.core.celery_app beat --loglevel=info
