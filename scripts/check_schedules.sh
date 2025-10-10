#!/bin/bash

# Celery Beat 스케줄 확인 스크립트 (API 기반)
# RedBeat 동적 스케줄을 포함한 모든 스케줄 정보를 표시합니다.

BASE_URL="http://localhost:8000"

# 색상 코드
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📅 Celery Beat 스케줄 확인${NC}"
echo "======================================"
echo ""

# 서버 상태 확인
echo "🔍 서버 연결 확인 중..."
if ! curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ 오류: API 서버에 연결할 수 없습니다.${NC}"
    echo ""
    echo "서버를 시작하세요:"
    echo "  cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ 서버 연결 성공${NC}"
echo ""

# 현재 시간 표시
echo -e "${BLUE}⏰ 현재 시간:${NC} $(date '+%Y-%m-%d %H:%M:%S %A')"
echo ""
echo "======================================"
echo ""

# 스케줄 정보 가져오기
echo -e "${BLUE}📋 등록된 스케줄 목록:${NC}"
echo ""

SCHEDULES=$(curl -s "$BASE_URL/api/scheduler/schedule")

# jq가 설치되어 있는지 확인
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq가 설치되어 있지 않습니다. JSON을 파싱할 수 없습니다.${NC}"
    echo ""
    echo "jq 설치 방법:"
    echo "  brew install jq"
    echo ""
    echo "Raw JSON 출력:"
    echo "$SCHEDULES" | python3 -m json.tool
    exit 0
fi

# 스케줄 개수 확인
SCHEDULE_COUNT=$(echo "$SCHEDULES" | jq '.schedules | length')

if [ "$SCHEDULE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  등록된 스케줄이 없습니다.${NC}"
    echo ""
    echo "스케줄 추가 방법:"
    echo "  1. 웹 UI: http://localhost:3000/scheduler"
    echo "  2. API: POST $BASE_URL/api/scheduler/schedule"
    echo ""
    exit 0
fi

# 요일 매핑
declare -A DAY_NAMES=(
    ["0"]="일요일"
    ["1"]="월요일"
    ["2"]="화요일"
    ["3"]="수요일"
    ["4"]="목요일"
    ["5"]="금요일"
    ["6"]="토요일"
    ["*"]="매일"
)

# 각 스케줄 정보 표시
echo "$SCHEDULES" | jq -r '.schedules[] | @json' | while IFS= read -r schedule; do
    NAME=$(echo "$schedule" | jq -r '.name')
    TASK=$(echo "$schedule" | jq -r '.task')
    HOUR=$(echo "$schedule" | jq -r '.hour')
    MINUTE=$(echo "$schedule" | jq -r '.minute')
    DAY_OF_WEEK=$(echo "$schedule" | jq -r '.day_of_week // "*"')
    COMPLEX_ID=$(echo "$schedule" | jq -r '.complex_id // "all"')
    DESCRIPTION=$(echo "$schedule" | jq -r '.description // "N/A"')

    echo -e "${GREEN}🔹 $NAME${NC}"
    echo "   태스크: $TASK"

    # 대상 단지 표시
    if [ "$COMPLEX_ID" != "all" ] && [ "$COMPLEX_ID" != "null" ]; then
        echo "   대상 단지: $COMPLEX_ID"
    else
        echo "   대상 단지: 전체 단지"
    fi

    # 요일 변환
    if [[ "$DAY_OF_WEEK" == *","* ]]; then
        # 여러 요일 (쉼표로 구분)
        IFS=',' read -ra DAYS <<< "$DAY_OF_WEEK"
        DAY_STR=""
        for day in "${DAYS[@]}"; do
            if [ -n "$DAY_STR" ]; then
                DAY_STR="$DAY_STR, "
            fi
            DAY_STR="$DAY_STR${DAY_NAMES[$day]:-$day}"
        done
    elif [ "$DAY_OF_WEEK" == "*" ]; then
        DAY_STR="매일"
    elif [[ "$DAY_OF_WEEK" == "MONTHLY_"* ]]; then
        # 월간 스케줄
        DAY=$(echo "$DAY_OF_WEEK" | sed 's/MONTHLY_//')
        DAY_STR="매월 ${DAY}일"
    elif [[ "$DAY_OF_WEEK" == "QUARTERLY_"* ]]; then
        # 분기별 스케줄
        DAY=$(echo "$DAY_OF_WEEK" | sed 's/QUARTERLY_//')
        DAY_STR="매 분기 ${DAY}일"
    else
        DAY_STR="${DAY_NAMES[$DAY_OF_WEEK]:-$DAY_OF_WEEK}"
    fi

    echo "   스케줄: $DAY_STR $(printf "%02d:%02d" $HOUR $MINUTE)"

    if [ "$DESCRIPTION" != "N/A" ]; then
        echo "   설명: $DESCRIPTION"
    fi

    echo ""
done

echo "======================================"
echo ""

# 최근 작업 이력 표시
echo -e "${BLUE}📊 최근 크롤링 작업 (최근 5개):${NC}"
echo ""

JOBS=$(curl -s "$BASE_URL/api/scheduler/jobs?limit=5")
JOB_COUNT=$(echo "$JOBS" | jq '.jobs | length')

if [ "$JOB_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  크롤링 작업 이력이 없습니다.${NC}"
else
    echo "$JOBS" | jq -r '.jobs[] | @json' | while IFS= read -r job; do
        COMPLEX_ID=$(echo "$job" | jq -r '.complex_id // "all"')
        STATUS=$(echo "$job" | jq -r '.status')
        STARTED=$(echo "$job" | jq -r '.started_at')
        COMPLETED=$(echo "$job" | jq -r '.completed_at // "진행 중"')
        ARTICLES_COLLECTED=$(echo "$job" | jq -r '.articles_collected // 0')

        # 상태별 색상
        if [ "$STATUS" == "completed" ]; then
            STATUS_COLOR="${GREEN}"
            STATUS_TEXT="✅ 완료"
        elif [ "$STATUS" == "failed" ]; then
            STATUS_COLOR="${RED}"
            STATUS_TEXT="❌ 실패"
        else
            STATUS_COLOR="${YELLOW}"
            STATUS_TEXT="⏳ 진행중"
        fi

        echo -e "${STATUS_COLOR}${STATUS_TEXT}${NC} | 단지: $COMPLEX_ID | 수집: ${ARTICLES_COLLECTED}건"
        echo "   시작: $STARTED"
        if [ "$COMPLETED" != "진행 중" ]; then
            echo "   완료: $COMPLETED"
        fi
        echo ""
    done
fi

echo "======================================"
echo ""

# Beat 상태 확인
echo -e "${BLUE}🔄 Celery Beat 상태:${NC}"
echo ""

BEAT_RUNNING=$(pgrep -f 'celery.*beat' > /dev/null && echo "true" || echo "false")

if [ "$BEAT_RUNNING" == "true" ]; then
    echo -e "${GREEN}✅ Celery Beat 실행 중${NC}"

    # Beat 프로세스 정보
    BEAT_PID=$(pgrep -f 'celery.*beat')
    BEAT_UPTIME=$(ps -p $BEAT_PID -o etime= 2>/dev/null | xargs)

    if [ -n "$BEAT_UPTIME" ]; then
        echo "   PID: $BEAT_PID"
        echo "   실행 시간: $BEAT_UPTIME"
    fi
else
    echo -e "${RED}❌ Celery Beat 실행 중이 아님${NC}"
    echo ""
    echo "Beat 시작 방법:"
    echo "  cd backend && ./run_celery_beat.sh"
    echo ""
    echo "또는 웹 UI에서 재시작:"
    echo "  http://localhost:3000/scheduler (🔄 재활성화 버튼 클릭)"
fi

echo ""

# Worker 상태 확인
WORKER_RUNNING=$(pgrep -f 'celery.*worker' > /dev/null && echo "true" || echo "false")

if [ "$WORKER_RUNNING" == "true" ]; then
    echo -e "${GREEN}✅ Celery Worker 실행 중${NC}"

    # Worker 프로세스 정보
    WORKER_PID=$(pgrep -f 'celery.*worker')
    WORKER_UPTIME=$(ps -p $WORKER_PID -o etime= 2>/dev/null | xargs)

    if [ -n "$WORKER_UPTIME" ]; then
        echo "   PID: $WORKER_PID"
        echo "   실행 시간: $WORKER_UPTIME"
    fi
else
    echo -e "${RED}❌ Celery Worker 실행 중이 아님${NC}"
    echo ""
    echo "Worker 시작 방법:"
    echo "  cd backend && ./run_celery_worker.sh"
fi

echo ""
echo "======================================"
echo ""
echo -e "${BLUE}💡 유용한 명령어:${NC}"
echo ""
echo "  스케줄 관리 (웹):  http://localhost:3000/scheduler"
echo "  API 문서:          http://localhost:8000/docs"
echo "  수동 크롤링:       curl -X POST $BASE_URL/api/scheduler/trigger/all"
echo "  Beat 재시작 (웹):  http://localhost:3000/scheduler (🔄 재활성화)"
echo "  Beat 재시작 (CLI): pkill -f 'celery.*beat' && cd backend && ./run_celery_beat.sh"
echo ""
