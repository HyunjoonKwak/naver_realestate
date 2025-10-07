#!/bin/bash
# Celery Worker 실행 스크립트

cd "$(dirname "$0")"

echo "🚀 Celery Worker 시작..."
.venv/bin/celery -A app.core.celery_app worker --loglevel=info --pool=solo
