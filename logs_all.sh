#!/bin/bash

# 모든 로그를 실시간으로 보여주는 스크립트

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

echo "📊 모든 서비스 로그 실시간 모니터링"
echo "   (Ctrl+C로 종료)"
echo ""

# 로그 디렉토리가 없으면 생성
mkdir -p "$LOG_DIR"

# 로그 파일들이 없으면 생성
touch "$LOG_DIR/backend.log"
touch "$LOG_DIR/worker.log"
touch "$LOG_DIR/beat.log"
touch "$LOG_DIR/frontend.log"

# 모든 로그를 동시에 출력
tail -f "$LOG_DIR"/*.log
