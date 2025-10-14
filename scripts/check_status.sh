#!/bin/bash

# 네이버 부동산 서비스 상태 체크 스크립트
# 로컬 및 NAS에서 실행 중인 프론트엔드와 백엔드 상태를 확인합니다.

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 아이콘
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"

echo ""
echo -e "${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  🏠 네이버 부동산 서비스 상태 체크                    ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ========================================
# 로컬 서비스 상태 체크
# ========================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🖥️  로컬 서비스 상태 (localhost)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Docker 서비스 체크
echo -e "${YELLOW}📦 Docker 컨테이너${NC}"
if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "naver_realestate"; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep "naver_realestate" | while read line; do
        echo -e "  ${GREEN}${CHECK}${NC} $line"
    done
else
    echo -e "  ${RED}${CROSS} Docker 컨테이너가 실행 중이지 않습니다${NC}"
fi
echo ""

# PostgreSQL 체크
echo -e "${YELLOW}🗄️  PostgreSQL (포트 5433)${NC}"
if nc -z localhost 5433 2>/dev/null; then
    echo -e "  ${GREEN}${CHECK} PostgreSQL이 실행 중입니다${NC}"
    if command -v psql &> /dev/null; then
        DB_INFO=$(PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d naver_realestate -t -c "SELECT COUNT(*) FROM pg_catalog.pg_tables WHERE schemaname = 'public';" 2>/dev/null || echo "0")
        echo -e "  ${INFO} 테이블 수: $(echo $DB_INFO | xargs)"
    fi
else
    echo -e "  ${RED}${CROSS} PostgreSQL이 실행 중이지 않습니다${NC}"
fi
echo ""

# Redis 체크
echo -e "${YELLOW}🔄 Redis (포트 6380)${NC}"
if nc -z localhost 6380 2>/dev/null; then
    echo -e "  ${GREEN}${CHECK} Redis가 실행 중입니다${NC}"
    if command -v redis-cli &> /dev/null; then
        REDIS_INFO=$(redis-cli -p 6380 info keyspace 2>/dev/null | grep "keys=" | head -1)
        if [ -n "$REDIS_INFO" ]; then
            echo -e "  ${INFO} $REDIS_INFO"
        fi
    fi
else
    echo -e "  ${RED}${CROSS} Redis가 실행 중이지 않습니다${NC}"
fi
echo ""

# Backend API 체크
echo -e "${YELLOW}🔧 Backend API (포트 8000)${NC}"
if nc -z localhost 8000 2>/dev/null; then
    echo -e "  ${GREEN}${CHECK} Backend API가 실행 중입니다${NC}"
    # 프로세스 확인
    if ps aux | grep -v grep | grep "uvicorn app.main" > /dev/null; then
        PID=$(ps aux | grep -v grep | grep "uvicorn app.main" | awk '{print $2}' | head -1)
        echo -e "  ${INFO} PID: $PID"
    fi
    # Health check
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}${CHECK} Health check: OK${NC}"
    else
        echo -e "  ${YELLOW}${WARNING} Health check: 응답 없음${NC}"
    fi
    # API 문서
    echo -e "  ${INFO} API 문서: ${BLUE}http://localhost:8000/docs${NC}"
else
    echo -e "  ${RED}${CROSS} Backend API가 실행 중이지 않습니다${NC}"
fi
echo ""

# Celery Worker 체크
echo -e "${YELLOW}⚙️  Celery Worker${NC}"
if ps aux | grep -v grep | grep "celery.*worker" > /dev/null; then
    echo -e "  ${GREEN}${CHECK} Celery Worker가 실행 중입니다${NC}"
    PID=$(ps aux | grep -v grep | grep "celery.*worker" | awk '{print $2}' | head -1)
    echo -e "  ${INFO} PID: $PID"
else
    echo -e "  ${RED}${CROSS} Celery Worker가 실행 중이지 않습니다${NC}"
fi
echo ""

# Celery Beat 체크
echo -e "${YELLOW}⏰ Celery Beat (스케줄러)${NC}"
if ps aux | grep -v grep | grep "celery.*beat" > /dev/null; then
    echo -e "  ${GREEN}${CHECK} Celery Beat가 실행 중입니다${NC}"
    PID=$(ps aux | grep -v grep | grep "celery.*beat" | awk '{print $2}' | head -1)
    echo -e "  ${INFO} PID: $PID"
else
    echo -e "  ${RED}${CROSS} Celery Beat가 실행 중이지 않습니다${NC}"
fi
echo ""

# Frontend 체크
echo -e "${YELLOW}🎨 Frontend (포트 3000)${NC}"
if nc -z localhost 3000 2>/dev/null; then
    echo -e "  ${GREEN}${CHECK} Frontend가 실행 중입니다${NC}"
    # 프로세스 확인
    if ps aux | grep -v grep | grep "next dev" > /dev/null; then
        PID=$(ps aux | grep -v grep | grep "next dev" | awk '{print $2}' | head -1)
        echo -e "  ${INFO} PID: $PID"
    fi
    echo -e "  ${INFO} URL: ${BLUE}http://localhost:3000${NC}"
else
    echo -e "  ${RED}${CROSS} Frontend가 실행 중이지 않습니다${NC}"
fi
echo ""

# ========================================
# NAS 서비스 상태 체크
# ========================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🏢 NAS 서비스 상태 (원격)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# NAS IP 주소 (기본값, 환경변수로 덮어쓸 수 있음)
NAS_IP=${NAS_IP:-"192.168.0.100"}
NAS_BACKEND_PORT=${NAS_BACKEND_PORT:-"8000"}
NAS_FRONTEND_PORT=${NAS_FRONTEND_PORT:-"3000"}
NAS_POSTGRES_PORT=${NAS_POSTGRES_PORT:-"5433"}
NAS_REDIS_PORT=${NAS_REDIS_PORT:-"6380"}

echo -e "${INFO} NAS IP: ${BLUE}$NAS_IP${NC}"
echo -e "${INFO} 환경변수로 변경 가능: export NAS_IP=<your_nas_ip>"
echo ""

# NAS Backend API 체크
echo -e "${YELLOW}🔧 NAS Backend API (포트 $NAS_BACKEND_PORT)${NC}"
if timeout 3 curl -s http://$NAS_IP:$NAS_BACKEND_PORT/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}${CHECK} NAS Backend API가 실행 중입니다${NC}"
    # API 버전 확인
    VERSION=$(curl -s http://$NAS_IP:$NAS_BACKEND_PORT/ 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    if [ -n "$VERSION" ]; then
        echo -e "  ${INFO} 버전: $VERSION"
    fi
    echo -e "  ${INFO} API 문서: ${BLUE}http://$NAS_IP:$NAS_BACKEND_PORT/docs${NC}"
else
    echo -e "  ${RED}${CROSS} NAS Backend API에 접근할 수 없습니다${NC}"
    echo -e "  ${WARNING} NAS가 실행 중인지 또는 IP 주소가 올바른지 확인하세요"
fi
echo ""

# NAS Frontend 체크
echo -e "${YELLOW}🎨 NAS Frontend (포트 $NAS_FRONTEND_PORT)${NC}"
if timeout 3 curl -s http://$NAS_IP:$NAS_FRONTEND_PORT > /dev/null 2>&1; then
    echo -e "  ${GREEN}${CHECK} NAS Frontend가 실행 중입니다${NC}"
    echo -e "  ${INFO} URL: ${BLUE}http://$NAS_IP:$NAS_FRONTEND_PORT${NC}"
else
    echo -e "  ${RED}${CROSS} NAS Frontend에 접근할 수 없습니다${NC}"
fi
echo ""

# NAS PostgreSQL 체크
echo -e "${YELLOW}🗄️  NAS PostgreSQL (포트 $NAS_POSTGRES_PORT)${NC}"
if nc -z $NAS_IP $NAS_POSTGRES_PORT 2>/dev/null; then
    echo -e "  ${GREEN}${CHECK} NAS PostgreSQL이 실행 중입니다${NC}"
else
    echo -e "  ${RED}${CROSS} NAS PostgreSQL에 접근할 수 없습니다${NC}"
fi
echo ""

# NAS Redis 체크
echo -e "${YELLOW}🔄 NAS Redis (포트 $NAS_REDIS_PORT)${NC}"
if nc -z $NAS_IP $NAS_REDIS_PORT 2>/dev/null; then
    echo -e "  ${GREEN}${CHECK} NAS Redis가 실행 중입니다${NC}"
else
    echo -e "  ${RED}${CROSS} NAS Redis에 접근할 수 없습니다${NC}"
fi
echo ""

# ========================================
# 요약 및 권장사항
# ========================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 요약 및 권장사항${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 로컬 상태 요약
LOCAL_SERVICES=0
LOCAL_RUNNING=0

# 각 서비스 체크
nc -z localhost 5433 2>/dev/null && LOCAL_RUNNING=$((LOCAL_RUNNING + 1)); LOCAL_SERVICES=$((LOCAL_SERVICES + 1))
nc -z localhost 6380 2>/dev/null && LOCAL_RUNNING=$((LOCAL_RUNNING + 1)); LOCAL_SERVICES=$((LOCAL_SERVICES + 1))
nc -z localhost 8000 2>/dev/null && LOCAL_RUNNING=$((LOCAL_RUNNING + 1)); LOCAL_SERVICES=$((LOCAL_SERVICES + 1))
ps aux | grep -v grep | grep "celery.*worker" > /dev/null && LOCAL_RUNNING=$((LOCAL_RUNNING + 1)); LOCAL_SERVICES=$((LOCAL_SERVICES + 1))
ps aux | grep -v grep | grep "celery.*beat" > /dev/null && LOCAL_RUNNING=$((LOCAL_RUNNING + 1)); LOCAL_SERVICES=$((LOCAL_SERVICES + 1))
nc -z localhost 3000 2>/dev/null && LOCAL_RUNNING=$((LOCAL_RUNNING + 1)); LOCAL_SERVICES=$((LOCAL_SERVICES + 1))

echo -e "${YELLOW}🖥️  로컬:${NC} $LOCAL_RUNNING/$LOCAL_SERVICES 서비스 실행 중"

if [ $LOCAL_RUNNING -eq $LOCAL_SERVICES ]; then
    echo -e "  ${GREEN}${CHECK} 모든 로컬 서비스가 정상 작동 중입니다${NC}"
elif [ $LOCAL_RUNNING -eq 0 ]; then
    echo -e "  ${RED}${CROSS} 로컬 서비스가 실행 중이지 않습니다${NC}"
    echo -e "  ${INFO} 시작하려면: ${BLUE}./scripts/start_all.sh${NC}"
else
    echo -e "  ${YELLOW}${WARNING} 일부 로컬 서비스가 실행 중이지 않습니다${NC}"
    echo -e "  ${INFO} 문제 해결: ${BLUE}./devtool${NC} → 모니터링 & 상태"
fi
echo ""

# NAS 상태 요약
NAS_SERVICES=0
NAS_RUNNING=0

timeout 3 curl -s http://$NAS_IP:$NAS_BACKEND_PORT/health > /dev/null 2>&1 && NAS_RUNNING=$((NAS_RUNNING + 1)); NAS_SERVICES=$((NAS_SERVICES + 1))
timeout 3 curl -s http://$NAS_IP:$NAS_FRONTEND_PORT > /dev/null 2>&1 && NAS_RUNNING=$((NAS_RUNNING + 1)); NAS_SERVICES=$((NAS_SERVICES + 1))

echo -e "${YELLOW}🏢 NAS:${NC} $NAS_RUNNING/$NAS_SERVICES 서비스 실행 중"

if [ $NAS_RUNNING -eq $NAS_SERVICES ]; then
    echo -e "  ${GREEN}${CHECK} 모든 NAS 서비스가 정상 작동 중입니다${NC}"
elif [ $NAS_RUNNING -eq 0 ]; then
    echo -e "  ${RED}${CROSS} NAS 서비스에 접근할 수 없습니다${NC}"
    echo -e "  ${INFO} NAS에서 Docker 컨테이너 확인: ${BLUE}docker ps${NC}"
else
    echo -e "  ${YELLOW}${WARNING} 일부 NAS 서비스가 실행 중이지 않습니다${NC}"
fi
echo ""

# 추가 정보
echo -e "${PURPLE}💡 유용한 명령어${NC}"
echo -e "  - 모든 서비스 시작: ${BLUE}./scripts/start_all.sh${NC}"
echo -e "  - 모든 서비스 중지: ${BLUE}./scripts/stop_all.sh${NC}"
echo -e "  - 실시간 로그 보기: ${BLUE}./scripts/logs_all.sh${NC}"
echo -e "  - DevTool 실행: ${BLUE}./devtool${NC}"
echo -e "  - 스케줄 확인: ${BLUE}./scripts/check_schedules.sh${NC}"
echo ""
echo -e "${PURPLE}🌐 접속 주소${NC}"
echo -e "  - 로컬 Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e "  - 로컬 Backend: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  - NAS Frontend: ${BLUE}http://$NAS_IP:$NAS_FRONTEND_PORT${NC}"
echo -e "  - NAS Backend: ${BLUE}http://$NAS_IP:$NAS_BACKEND_PORT/docs${NC}"
echo ""

