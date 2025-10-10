# DevTool - 통합 개발 도구

Naver Real Estate 프로젝트의 모든 스크립트, 테스트, 서비스를 하나의 인터페이스로 관리하는 CLI 도구입니다.

## 🚀 빠른 시작

```bash
# DevTool 실행
./devtool
```

## 📋 주요 기능

### 1. 🗄️ 데이터베이스 관리
- **데이터 확인**: 단지/매물/실거래가 조회
- **마이그레이션**: 외래키 제약조건 추가
- **초기화**: 전체 DB 리셋 (개발용)
- **PostgreSQL 접속**: psql 직접 연결

### 2. 🧪 테스트 실행
- **API 테스트**: 기본 엔드포인트 검증
- **실거래가 테스트**: MOLIT API 연동 확인
- **Discord 브리핑**: 알림 전송 테스트
- **전체 테스트**: 모든 테스트 일괄 실행

### 3. 📊 모니터링 & 상태
- **스케줄 확인**: Celery Beat 스케줄 및 크롤링 상태
- **로그 모니터링**: 실시간 로그 확인
- **Docker 상태**: 컨테이너 모니터링
- **프로세스 상태**: 서비스 실행 여부 확인
- **웹 UI**: 브라우저에서 바로 열기

### 4. 🚀 서비스 관리
- **일괄 시작/중지**: 모든 서비스 한 번에
- **Docker 관리**: 컨테이너 시작/중지
- **개별 제어**: Backend, Worker, Beat, Frontend 각각 관리

### 5. 📚 문서 접근
- 시작 가이드
- 개발 가이드 (CLAUDE.md)
- 스크립트 문서
- 테스트 문서
- 프로젝트 구조

## 🎯 메뉴 구조

```
DevTool 메인 메뉴
├── 1) 데이터베이스 관리
│   ├── 1) 데이터베이스 내용 확인
│   ├── 2) 마이그레이션 (외래키 추가)
│   ├── 3) 초기화 (위험)
│   └── 4) PostgreSQL 접속
│
├── 2) 테스트 실행
│   ├── 1) API 테스트
│   ├── 2) 실거래가 API 테스트
│   ├── 3) Discord 브리핑 테스트
│   └── 4) 전체 테스트
│
├── 3) 모니터링 & 상태
│   ├── 1) 스케줄 & 크롤링 상태
│   ├── 2) 로그 실시간 보기
│   ├── 3) Docker 컨테이너 상태
│   ├── 4) 프로세스 상태
│   └── 5) 웹 UI 열기
│
├── 4) 서비스 관리
│   ├── 1) 모든 서비스 시작
│   ├── 2) 모든 서비스 중지
│   ├── 3) Docker 시작
│   ├── 4) Docker 중지
│   └── 5) 개별 서비스 관리
│       ├── Backend API 시작/중지
│       ├── Celery Worker 시작/중지
│       ├── Celery Beat 시작/중지
│       └── Frontend 시작/중지
│
└── 5) 문서 보기
    ├── 1) 시작 가이드
    ├── 2) 개발 가이드
    ├── 3) 스크립트 문서
    ├── 4) 테스트 문서
    └── 5) 프로젝트 구조
```

## 💡 사용 예시

### 시나리오 1: 프로젝트 처음 시작

```bash
./devtool

# 메뉴에서 선택:
4 → 3  # Docker 컨테이너 시작
4 → 1  # 모든 서비스 시작
3 → 1  # 스케줄 상태 확인
```

### 시나리오 2: 테스트 실행

```bash
./devtool

# 메뉴에서 선택:
2 → 4  # 전체 테스트 실행
```

### 시나리오 3: 데이터베이스 확인

```bash
./devtool

# 메뉴에서 선택:
1 → 1  # 데이터 확인
1 → 4  # PostgreSQL 접속
```

### 시나리오 4: 로그 모니터링

```bash
./devtool

# 메뉴에서 선택:
3 → 2  # 실시간 로그 보기
```

## 🎨 UI 미리보기

```
╔════════════════════════════════════════════════════════════╗
║  🛠️  Naver Real Estate DevTool                          ║
║  통합 개발 도구 - Scripts, Tests, DB, Monitoring    ║
╔════════════════════════════════════════════════════════════╗

📊 시스템 상태 확인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ PostgreSQL (포트 5433)
  ✅ Redis (포트 6380)
  ✅ Backend API (포트 8000)
  ✅ Frontend (포트 3000)
  ✅ Celery Worker
  ✅ Celery Beat

📋 메인 메뉴
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1) 🗄️  데이터베이스 관리
  2) 🧪 테스트 실행
  3) 📊 모니터링 & 상태 확인
  4) 🚀 서비스 관리
  5) 📚 문서 보기

  0) 종료

선택:
```

## 🔗 기존 도구와의 통합

DevTool은 기존의 모든 스크립트와 도구를 하나로 통합합니다:

### Scripts 디렉토리
- `check_data.py` → 메뉴 1-1
- `migrate_db.py` → 메뉴 1-2
- `reset_db.py` → 메뉴 1-3
- `check_schedules.sh` → 메뉴 3-1

### Tests 디렉토리
- `test_api.sh` → 메뉴 2-1
- `test_transaction_api.sh` → 메뉴 2-2
- `test_discord_briefing.sh` → 메뉴 2-3

### 서비스 스크립트
- `start_all.sh` → 메뉴 4-1
- `stop_all.sh` → 메뉴 4-2
- `logs_all.sh` → 메뉴 3-2

### 문서
- `README_STARTUP.md` → 메뉴 5-1
- `CLAUDE.md` → 메뉴 5-2
- `scripts/README.md` → 메뉴 5-3
- `tests/README.md` → 메뉴 5-4
- `docs/PROJECT_STRUCTURE.md` → 메뉴 5-5

## 🛠️ 고급 기능

### 명령줄 옵션

```bash
# 도움말 표시
./devtool --help

# 대화형 메뉴 시작 (기본)
./devtool
```

### 색상 코드

- 🟢 **녹색**: 성공/실행 중
- 🔴 **빨간색**: 실패/중지
- 🟡 **노란색**: 경고/주의 필요
- 🔵 **파란색**: 정보
- 🟣 **보라색**: 헤더/강조

## 📝 개발자 노트

### 아키텍처

DevTool은 Bash 스크립트로 작성된 대화형 CLI 도구입니다:

1. **메뉴 시스템**: 계층형 메뉴 구조
2. **상태 체크**: 실시간 서비스 상태 확인
3. **프로세스 관리**: pkill, nohup을 활용한 서비스 제어
4. **로그 통합**: 모든 로그를 logs/ 디렉토리에 저장

### 확장 방법

새로운 기능을 추가하려면:

1. 해당 메뉴 함수에 케이스 추가
2. 스크립트 또는 명령 실행 로직 구현
3. 사용자 피드백 표시

예시:
```bash
# test_menu() 함수에 추가
5)
    echo ""
    ./tests/new_test.sh
    echo ""
    read -p "엔터를 눌러 계속..."
    test_menu
    ;;
```

## 🔧 트러블슈팅

### 문제: DevTool이 실행되지 않음

```bash
# 실행 권한 확인
ls -l devtool

# 권한 부여
chmod +x devtool
```

### 문제: 상태 체크가 정확하지 않음

```bash
# 수동으로 프로세스 확인
ps aux | grep uvicorn
ps aux | grep celery
docker ps
```

### 문제: 서비스 시작 실패

```bash
# 로그 확인
cat logs/backend.log
cat logs/worker.log
cat logs/beat.log
cat logs/frontend.log
```

## 🎯 Best Practices

1. **시작 순서**
   - Docker → Backend/Worker/Beat → Frontend

2. **종료 순서**
   - Frontend → Worker/Beat → Backend → Docker (유지)

3. **디버깅**
   - 상태 확인 → 로그 확인 → 개별 서비스 재시작

4. **테스트**
   - API 서버 실행 확인 → 테스트 실행

## 📚 관련 문서

- [README_STARTUP.md](README_STARTUP.md) - 프로젝트 시작 가이드
- [CLAUDE.md](CLAUDE.md) - 개발 가이드
- [scripts/README.md](scripts/README.md) - 스크립트 문서
- [tests/README.md](tests/README.md) - 테스트 문서

## 🤝 기여

DevTool 개선 제안:
1. 새로운 메뉴 항목 추가
2. 더 나은 상태 체크 로직
3. 에러 처리 강화
4. UI/UX 개선

---

**💡 Tip**: DevTool을 alias로 등록하면 어디서든 실행 가능!

```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
alias dev='cd /Users/specialrisk_mac/code_work/naver_realestate && ./devtool'

# 사용
dev
```
