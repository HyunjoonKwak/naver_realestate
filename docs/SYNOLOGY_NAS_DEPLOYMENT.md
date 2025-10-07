# Synology NAS 배포 가이드

## 🎯 Synology NAS의 장점

### EC2 vs Synology NAS

| 항목 | AWS EC2 t2.micro | Synology NAS | 승자 |
|------|------------------|--------------|------|
| **비용** | $0 (12개월) → 이후 유료 | $0 (이미 보유) | 🏆 NAS |
| **메모리** | 1GB (부족) | 모델에 따라 다름 | 🏆 NAS |
| **전력** | 항상 켜짐 | 항상 켜짐 | 동일 |
| **속도** | 빠름 | 로컬 네트워크 초고속 | 🏆 NAS |
| **관리** | SSH | DSM (웹 UI) | 🏆 NAS |
| **외부 접속** | 쉬움 | QuickConnect/DDNS | 동일 |
| **Docker** | 설치 필요 | 내장 | 🏆 NAS |

### Synology NAS가 유리한 이유

✅ **비용**: 월 비용 $0 (전기세만)
✅ **Docker 지원**: Container Manager 내장
✅ **웹 UI**: DSM으로 쉬운 관리
✅ **외부 접속**: QuickConnect 무료
✅ **백업**: 자동 스냅샷
✅ **보안**: 방화벽 내장
✅ **업타임**: 24/7 운영 최적화

---

## 📋 사전 요구사항

### 1. Synology NAS 모델 확인

| 시리즈 | Docker 지원 | 추천 메모리 | 프로젝트 적합성 |
|--------|------------|------------|----------------|
| DS920+, DS918+ | ✅ | 4GB+ | ⭐⭐⭐⭐⭐ 완벽 |
| DS220+, DS218+ | ✅ | 2GB+ | ⭐⭐⭐⭐ 좋음 |
| DS120j, DS118 | ❌ | 512MB | ❌ 불가능 |

**확인 방법:**
- DSM → 제어판 → 정보 센터 → 일반

### 2. DSM 버전 및 Docker 패키지명

| DSM 버전 | 패키지명 (모델에 따라 다름) | 비고 |
|----------|---------------------------|------|
| **DSM 7.2+** | Container Manager 또는 Docker | 최신 버전 |
| **DSM 7.0-7.1** | Container Manager 또는 Docker | 모델에 따라 다름 |
| **DSM 6.x** | Docker | 구 버전 |

**패키지 센터에서 확인:**
- "Container Manager" 검색 → 없으면
- "Docker" 검색 → **있으면 Docker 사용하세요!**

> ⚠️ **중요**: DSM 7.x이더라도 모델에 따라 "Docker"로 표시될 수 있습니다.
> 예: DS716+II (DSM 7.1.1) → "Docker" 사용 ✅
> 두 패키지는 동일한 기능을 제공하며, 이름만 다릅니다.

**DSM 버전 확인:**
- DSM → 제어판 → 정보 센터 → 일반
- 또는 좌측 상단 DSM 로고 클릭

### 3. 필요한 패키지

**DSM 7.0 이상:**
- ✅ **Container Manager** (필수)
- Git Server (선택)
- Web Station (선택)

**DSM 6.x:**
- ✅ **Docker** (필수)
- Git Server (선택)
- Web Station (선택)

---

## 🚀 배포 방법

### 방법 1: Docker / Container Manager (추천) ⭐

**장점:**
- ✅ 웹 UI로 쉬운 관리
- ✅ 자동 재시작 설정
- ✅ 리소스 모니터링
- ✅ 로그 확인 간편

#### 1-1. Docker 패키지 설치

**모든 DSM 버전 (간단한 방법):**
1. DSM → 패키지 센터
2. 검색창에 "**Docker**" 입력 및 설치
3. 실행

> 💡 **패키지 이름 참고**:
> - 일부 최신 모델: "Container Manager"로 표시
> - 대부분의 모델: "Docker"로 표시
> - DS716+II (DSM 7.1.1) → "Docker" ✅
> - **두 이름 모두 동일한 기능입니다**

> ⚠️ **찾을 수 없는 경우**:
> - NAS 모델이 Docker를 지원하지 않을 수 있습니다
> - ARM 기반 일부 모델은 제한이 있습니다
> - CPU가 Intel/AMD x64가 아닌 경우 확인 필요

#### 1-2. 프로젝트 코드 업로드

**방법 A: SSH를 통한 Git Clone (권장)**

```bash
# 1. SSH 활성화: DSM → 제어판 → 터미널 및 SNMP → SSH 서비스 활성화

# 2. SSH 접속
ssh admin@your-nas-ip

# 3. Docker 디렉토리로 이동
cd /volume1/docker

# 4. Git clone
sudo git clone https://github.com/your-username/naver_realestate.git

# 5. 환경변수 파일 생성
cd naver_realestate
sudo nano .env
```

**.env 파일 내용:**
```bash
# MOLIT API 키 (필수)
MOLIT_API_KEY=your_molit_api_key_here

# Discord 웹훅 (선택)
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
```

**방법 B: File Station 사용**

1. File Station → `docker` 폴더로 이동
2. 프로젝트 폴더 전체를 압축(ZIP)하여 업로드
3. 압축 해제
4. `.env` 파일 생성 (위 내용 참고)

#### 1-3. Docker 이미지 빌드 및 실행

**SSH로 빌드 (권장)**

```bash
# 1. 프로젝트 디렉토리로 이동
cd /volume1/docker/naver_realestate

# 2. .env 파일이 있는지 확인
cat .env

# 3. Docker Compose로 빌드 및 시작
sudo docker-compose up -d --build

# 4. 컨테이너 상태 확인
sudo docker-compose ps

# 5. 로그 확인
sudo docker-compose logs -f api
```

**Container Manager UI 사용**

1. Container Manager → 프로젝트
2. "생성" 클릭
3. 프로젝트 이름: `naver_realestate`
4. 경로: `/volume1/docker/naver_realestate` 선택
5. 소스: "기존 docker-compose.yml 사용"
6. "실행" 클릭

#### 1-4. 데이터베이스 초기화

```bash
# SSH 접속 후 실행
cd /volume1/docker/naver_realestate

# 데이터베이스 마이그레이션 (Foreign Keys 적용)
sudo docker-compose exec api python migrate_db.py

# 또는 테이블만 재생성 (Legacy)
# sudo docker-compose exec api python reset_db.py
```

---

### 방법 2: 컨테이너 관리 및 모니터링

#### 2-1. 컨테이너 관리 명령어

```bash
# SSH 접속 후 프로젝트 디렉토리로 이동
cd /volume1/docker/naver_realestate

# 전체 컨테이너 시작
sudo docker-compose up -d

# 전체 컨테이너 중지
sudo docker-compose down

# 특정 컨테이너 재시작
sudo docker-compose restart api
sudo docker-compose restart celery_worker

# 컨테이너 상태 확인
sudo docker-compose ps

# 로그 확인 (실시간)
sudo docker-compose logs -f api
sudo docker-compose logs -f celery_worker
sudo docker-compose logs -f celery_beat

# 특정 컨테이너에 접속
sudo docker-compose exec api bash
sudo docker-compose exec postgres psql -U postgres -d naver_realestate
```

#### 2-2. Task Scheduler로 자동 시작 설정

1. DSM → 제어판 → 작업 스케줄러
2. "생성" → 예약된 작업 → 사용자 정의 스크립트
3. 일반 설정:
   - 작업: `Naver Realestate Auto Start`
   - 사용자: `root`
4. 스케줄:
   - 부팅 시 실행
5. 작업 설정:
   ```bash
   cd /volume1/docker/naver_realestate && docker-compose up -d
   ```

---

## 🌐 외부 접속 설정

### 방법 1: QuickConnect (가장 쉬움) ⭐

1. DSM → 제어판 → QuickConnect
2. QuickConnect ID 등록: `your-id`
3. 접속 URL: `http://your-id.quickconnect.to`

**앱별 포트 포워딩:**
- API: `http://your-id.quickconnect.to:8000`
- Frontend: `http://your-id.quickconnect.to:3000`

### 방법 2: DDNS + 포트 포워딩

#### 2-1. DDNS 설정

1. DSM → 제어판 → 외부 액세스 → DDNS
2. 추가:
   - 서비스 공급자: Synology
   - 호스트 이름: `yourname.synology.me`
3. 확인

#### 2-2. 라우터 포트 포워딩

| 외부 포트 | 내부 IP | 내부 포트 | 설명 |
|----------|---------|-----------|------|
| 80 | NAS IP | 80 | HTTP |
| 443 | NAS IP | 443 | HTTPS |
| 3000 | NAS IP | 3000 | Frontend |
| 8000 | NAS IP | 8000 | API |

#### 2-3. Synology 방화벽 설정

1. DSM → 제어판 → 보안 → 방화벽
2. 규칙 추가:
   - 포트: 3000, 8000
   - 프로토콜: TCP
   - 액션: 허용

### 방법 3: Reverse Proxy (최고급)

#### 3-1. Web Station + Reverse Proxy

1. 패키지 센터 → Web Station 설치
2. DSM → 제어판 → 로그인 포털 → 고급 → Reverse Proxy
3. "생성" 클릭

**Frontend 설정:**
- 소스:
  - 프로토콜: HTTPS
  - 호스트 이름: `yourname.synology.me`
  - 포트: 443
- 대상:
  - 프로토콜: HTTP
  - 호스트 이름: localhost
  - 포트: 3000

**API 설정:**
- 소스:
  - 프로토콜: HTTPS
  - 호스트 이름: `yourname.synology.me`
  - 포트: 443
  - 경로: `/api`
- 대상:
  - 프로토콜: HTTP
  - 호스트 이름: localhost
  - 포트: 8000

**결과:**
- Frontend: `https://yourname.synology.me`
- API: `https://yourname.synology.me/api`

---

## 🔒 보안 설정

### 1. SSL 인증서 (Let's Encrypt)

1. DSM → 제어판 → 보안 → 인증서
2. "추가" → "Let's Encrypt 인증서 추가"
3. 도메인 이름: `yourname.synology.me`
4. 이메일 입력
5. "적용"

**자동 갱신**: Synology가 자동으로 갱신

### 2. 방화벽 규칙

```bash
# 필요한 포트만 허용
- 포트 80, 443: 웹 접속
- 포트 3000, 8000: 앱 접속 (임시)
- 포트 22: SSH (관리용, IP 제한 권장)
```

### 3. 2단계 인증

1. DSM → 개인 → 계정
2. 2단계 인증 활성화

---

## 📊 모니터링

### 1. Resource Monitor

1. DSM → Resource Monitor
2. 확인 항목:
   - CPU 사용률
   - 메모리 사용량
   - 네트워크 트래픽

### 2. Container Manager 모니터링

1. Container Manager → 컨테이너
2. 각 컨테이너 클릭 → 세부 정보
   - CPU 사용량
   - 메모리 사용량
   - 로그

### 3. 로그 확인

```bash
# SSH로 접속
ssh admin@your-nas-ip

# Docker 로그 확인
docker logs naver_api
docker logs naver_frontend
docker logs naver_db
docker logs naver_redis

# 실시간 로그
docker logs -f naver_api
```

---

## 🔄 자동 백업

### 1. Hyper Backup (권장)

1. 패키지 센터 → Hyper Backup 설치
2. 백업 작업 생성:
   - 소스: `/volume1/docker/naver_realestate`
   - 대상: 외장 하드 or 클라우드
   - 스케줄: 매일 새벽 3시

### 2. Snapshot Replication

1. 패키지 센터 → Snapshot Replication 설치
2. 스냅샷 설정:
   - 공유 폴더: `docker`
   - 스케줄: 매일

### 3. 데이터베이스 백업 스크립트

```bash
#!/bin/bash
# /volume1/docker/naver_realestate/backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/volume1/docker/naver_realestate/backups"

mkdir -p $BACKUP_DIR

# PostgreSQL 백업
docker exec naver_db pg_dump -U postgres naver_realestate > $BACKUP_DIR/db_backup_$DATE.sql

# 30일 이상된 백업 삭제
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql"
```

**Task Scheduler 등록:**
- 스케줄: 매일 새벽 3시
- 사용자: root
- 스크립트: `bash /volume1/docker/naver_realestate/backup_db.sh`

---

## 🔧 트러블슈팅

### 문제 1: "No container found for api_1" 에러

**증상:** `docker-compose exec api python migrate_db.py` 실행 시 에러

**원인:** 컨테이너가 시작되지 않았거나 이름이 다름

**해결 순서:**

```bash
# 1. 현재 실행 중인 컨테이너 확인
sudo docker-compose ps

# 2. 컨테이너가 없으면 시작
sudo docker-compose up -d

# 3. 빌드가 필요한 경우
sudo docker-compose up -d --build

# 4. 로그 확인 (빌드 진행 상황)
sudo docker-compose logs -f

# 5. 컨테이너 이름 확인 후 실행
sudo docker ps
# 예: naver_realestate_api로 표시되면
sudo docker exec naver_realestate_api python migrate_db.py

# 또는 docker-compose로 실행
sudo docker-compose exec api python migrate_db.py
```

**빌드 시간:**
- 최초 실행: 5-10분 소요 (Playwright 브라우저 다운로드)
- "Application startup complete" 메시지가 나올 때까지 대기

### 문제 2: 빌드 중 "no space left on device" 에러

**증상:** Docker 이미지 빌드 중 디스크 공간 부족

**해결:**
```bash
# 사용하지 않는 Docker 이미지/컨테이너 삭제
sudo docker system prune -a

# 디스크 공간 확인
df -h
```

### 문제 3: 메모리 부족

**증상:** 컨테이너가 자주 재시작됨

**해결:**
1. Docker → 컨테이너 → 세부 정보
2. 리소스 제한 설정:
   - PostgreSQL: 512MB
   - Redis: 256MB
   - API: 1GB
   - Frontend: 512MB

### 문제 4: 포트 충돌

**증상:** `Port already in use` 에러

**해결:**
```bash
# 포트 사용 확인
sudo netstat -tuln | grep :3000
sudo netstat -tuln | grep :8000

# 또는
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 문제 5: 권한 문제

**증상:** `Permission denied` 에러

**해결:**
```bash
# 폴더 권한 변경
sudo chown -R root:root /volume1/docker/naver_realestate
sudo chmod -R 755 /volume1/docker/naver_realestate

# .env 파일 권한
sudo chmod 644 /volume1/docker/naver_realestate/.env
```

### 문제 6: Playwright 브라우저 다운로드 실패

**증상:** "Browser executable doesn't exist" 에러

**해결:**
```bash
# 컨테이너 내부에서 수동 설치
sudo docker-compose exec api bash
playwright install chromium
playwright install-deps chromium
exit

# 컨테이너 재시작
sudo docker-compose restart api
```

### 문제 7: systemd 패키지 설치 오류

**증상:** Docker 빌드 중 "Failed to take /etc/passwd lock" 또는 systemd 관련 오류

**원인:** Playwright 의존성 설치 시 systemd가 포함되어 Docker 컨테이너에서 충돌

**해결:** Microsoft 공식 Playwright Python 이미지 사용 (이미 수정됨)
```bash
# 프로젝트 업데이트
cd /volume1/code_work/naver_realestate
sudo git pull

# 빌드 캐시 삭제 후 재빌드
sudo docker-compose build --no-cache api
sudo docker-compose up -d

# 로그 확인
sudo docker-compose logs -f api
```

**참고:** backend/Dockerfile이 `mcr.microsoft.com/playwright/python:v1.49.0-noble` 이미지를 사용하도록 변경되었습니다. 이 이미지는 Playwright와 Chromium이 사전 설치되어 있어 빌드 시간도 단축됩니다.

### 문제 8: Frontend 빌드 오류 "Module not found: Can't resolve '@/lib/api'"

**증상:** Next.js 빌드 중 모듈을 찾을 수 없음

**원인:** `npm ci --only=production`으로 devDependencies가 설치되지 않아 빌드 실패

**해결:** 최신 Dockerfile 사용 (이미 수정됨)
```bash
# 프로젝트 업데이트
cd /volume1/code_work/naver_realestate
sudo git pull

# Frontend만 재빌드
sudo docker-compose build --no-cache frontend
sudo docker-compose up -d
```

**참고:** frontend/Dockerfile이 `npm ci` (모든 의존성) → 빌드 → `npm prune --production` (프로덕션만 유지) 순서로 변경되었습니다.

---

## 📈 성능 최적화

### 1. SSD 캐시 (SSD 있는 경우)

1. DSM → 저장소 관리자 → SSD 캐시
2. "생성" → 읽기-쓰기 캐시
3. 선택: `/volume1/docker`

### 2. 메모리 업그레이드

- 권장: 8GB 이상
- 확인: DSM → 제어판 → 정보 센터

### 3. Docker 이미지 최적화

```yaml
# Alpine 기반 이미지 사용 (더 가벼움)
postgres:15-alpine  # 150MB vs 350MB
redis:7-alpine      # 30MB vs 110MB
python:3.11-alpine  # 45MB vs 900MB
node:18-alpine      # 170MB vs 1GB
```

---

## 💰 비용 비교

| 항목 | Synology NAS | AWS EC2 (t3.medium) |
|------|-------------|---------------------|
| **초기 비용** | $0 (이미 보유) | $0 |
| **월 비용** | ~$5 (전기세) | ~$30 |
| **연 비용** | ~$60 | ~$360 |
| **5년 비용** | ~$300 | ~$1,800 |

**절감액: 5년간 $1,500 절약** 💰

---

## 🎯 Synology NAS 추천 설정

### 최소 사양
- CPU: Intel/AMD (Docker 지원)
- 메모리: 4GB+
- DSM: 7.0+
- 저장 공간: 10GB+ (Docker 이미지 + 데이터)

### 권장 설정
```yaml
프로젝트 구조:
/volume1/docker/naver_realestate/
├── docker-compose.yml
├── .env                      # 환경변수 (필수)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   └── migrate_db.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
└── docs/

실행 중인 컨테이너:
- naver_realestate_db          (PostgreSQL)
- naver_realestate_redis        (Redis)
- naver_realestate_api          (FastAPI 백엔드)
- naver_realestate_celery_worker (크롤링 워커)
- naver_realestate_celery_beat   (스케줄러)
- naver_realestate_frontend     (Next.js 프론트엔드)

총 메모리 사용: ~3GB
```

### 외부 접속
- QuickConnect: `yourname.quickconnect.to`
- DDNS: `yourname.synology.me`
- Reverse Proxy: HTTPS 적용

### 자동화
- 부팅 시 자동 시작 (Task Scheduler)
- 매일 새벽 3시 백업 (Hyper Backup)
- 매일 오전 9시, 오후 6시 크롤링 (Task Scheduler)

---

## 📚 참고 자료

- [Synology DSM 가이드](https://www.synology.com/dsm)
- [Container Manager 가이드](https://www.synology.com/dsm/feature/docker)
- [QuickConnect 설정](https://www.synology.com/quickconnect)
- [Reverse Proxy 설정](https://kb.synology.com/DSM/help/DSM/AdminCenter/application_appportalias)

---

## 🚀 빠른 시작 가이드 (5분)

### 1단계: NAS 준비
```bash
# DSM → 패키지 센터 → Container Manager 설치
# DSM → 제어판 → 터미널 및 SNMP → SSH 활성화
```

### 2단계: SSH 접속 및 프로젝트 Clone
```bash
ssh admin@your-nas-ip
cd /volume1/docker
sudo git clone https://github.com/your-username/naver_realestate.git
cd naver_realestate
```

### 3단계: 환경변수 설정
```bash
# .env.example을 복사하여 .env 생성
sudo cp .env.example .env
sudo nano .env

# MOLIT_API_KEY를 실제 값으로 변경
# 저장: Ctrl+O, 종료: Ctrl+X
```

### 4단계: Docker Compose 실행
```bash
# 빌드 및 시작 (최초 5-10분 소요)
sudo docker-compose up -d --build

# 상태 확인
sudo docker-compose ps

# 로그 확인
sudo docker-compose logs -f
```

### 5단계: 데이터베이스 마이그레이션
```bash
# 데이터베이스 테이블 생성
sudo docker-compose exec api python migrate_db.py
```

### 6단계: 접속 확인
- API: http://your-nas-ip:8000/docs
- Frontend: http://your-nas-ip:3000

완료! 🎉

---

## ✅ 최종 체크리스트

### 필수 설정 (5분)
- [ ] Container Manager 설치
- [ ] SSH 활성화
- [ ] Git clone 프로젝트
- [ ] .env 파일 생성 및 MOLIT_API_KEY 설정
- [ ] `docker-compose up -d --build` 실행
- [ ] 데이터베이스 마이그레이션 (`migrate_db.py`)
- [ ] 웹 브라우저로 접속 확인

### 선택 설정 (추가 10분)
- [ ] QuickConnect 외부 접속 설정
- [ ] Task Scheduler 부팅 시 자동 시작
- [ ] Hyper Backup 자동 백업 설정
- [ ] Reverse Proxy + SSL 인증서 (HTTPS)

### 보안 설정
- [ ] 방화벽 규칙 (필요한 포트만 허용)
- [ ] 2단계 인증 활성화
- [ ] SSH 포트 변경 (선택)

### 모니터링
- [ ] Container Manager에서 리소스 사용량 확인
- [ ] 로그 주기적 확인 (`docker-compose logs`)
- [ ] 백업 정상 동작 확인

---

## 🎉 결론

**Synology NAS는 이 프로젝트에 완벽합니다!**

✅ **장점:**
1. 비용 절감 (월 $5 vs $30)
2. 쉬운 관리 (웹 UI)
3. 자동 백업
4. 24/7 운영
5. 로컬 네트워크 초고속

✅ **추천:**
- 메모리 4GB+ NAS 소유 시 강력 추천
- EC2보다 훨씬 경제적
- 관리도 더 쉬움

🚀 **시작하기:**
1. Container Manager 설치
2. docker-compose.yml 업로드
3. 프로젝트 배포
4. 완료!
