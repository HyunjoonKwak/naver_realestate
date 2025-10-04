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

### 2. DSM 버전
- **DSM 7.0 이상** 필요 (Container Manager 지원)

### 3. 필요한 패키지
- Container Manager (Docker)
- Git Server (선택)
- Web Station (선택)

---

## 🚀 배포 방법

### 방법 1: Docker Container Manager (추천) ⭐

**장점:**
- ✅ 웹 UI로 쉬운 관리
- ✅ 자동 재시작 설정
- ✅ 리소스 모니터링
- ✅ 로그 확인 간편

#### 1-1. Container Manager 설치

1. DSM → 패키지 센터
2. "Container Manager" 검색 및 설치
3. 실행

#### 1-2. docker-compose.yml 업로드

**방법 A: File Station 사용**

1. File Station → `docker` 폴더 생성
2. `docker/naver_realestate` 폴더 생성
3. `docker-compose.yml` 업로드

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: naver_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: naver_realestate
    volumes:
      - /volume1/docker/naver_realestate/postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: always

  redis:
    image: redis:7-alpine
    container_name: naver_redis
    volumes:
      - /volume1/docker/naver_realestate/redis_data:/data
    ports:
      - "6379:6379"
    restart: always

  api:
    image: python:3.11-slim
    container_name: naver_api
    working_dir: /app
    volumes:
      - /volume1/docker/naver_realestate/backend:/app
    environment:
      DATABASE_URL: postgresql://postgres:your_password@postgres:5432/naver_realestate
      REDIS_URL: redis://redis:6379/0
    ports:
      - "8000:8000"
    command: >
      sh -c "
        pip install -r requirements.txt &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000
      "
    depends_on:
      - postgres
      - redis
    restart: always

  frontend:
    image: node:18-alpine
    container_name: naver_frontend
    working_dir: /app
    volumes:
      - /volume1/docker/naver_realestate/frontend:/app
    environment:
      NEXT_PUBLIC_API_URL: http://your-nas-ip:8000
      PORT: 3000
    ports:
      - "3000:3000"
    command: >
      sh -c "
        npm install &&
        npm run build &&
        npm start
      "
    depends_on:
      - api
    restart: always
```

#### 1-3. Container Manager에서 실행

1. Container Manager → 프로젝트
2. "생성" 클릭
3. 프로젝트 이름: `naver_realestate`
4. 경로: `/docker/naver_realestate`
5. 소스: "docker-compose.yml 업로드"
6. "실행" 클릭

#### 1-4. 코드 배포

**SSH 접속 (권장)**

```bash
# 1. SSH 활성화: DSM → 제어판 → 터미널 및 SNMP → SSH 서비스 활성화

# 2. SSH 접속
ssh admin@your-nas-ip

# 3. 프로젝트 디렉토리로 이동
cd /volume1/docker/naver_realestate

# 4. Git clone
sudo git clone https://github.com/your-username/naver_realestate.git temp
sudo mv temp/backend .
sudo mv temp/frontend .
sudo rm -rf temp

# 5. 컨테이너 재시작
docker-compose restart
```

---

### 방법 2: Task Scheduler (스크립트 실행)

**장점:**
- ✅ 정기 크롤링 자동화
- ✅ 재부팅 시 자동 시작

#### 2-1. 스크립트 작성

```bash
# /volume1/docker/naver_realestate/start.sh
#!/bin/bash

cd /volume1/docker/naver_realestate

# Docker Compose 시작
docker-compose up -d

# 크롤링 (선택)
# docker exec naver_api python advanced_crawler.py
```

#### 2-2. Task Scheduler 설정

1. DSM → 제어판 → 작업 스케줄러
2. "생성" → 예약된 작업 → 사용자 정의 스크립트
3. 일반 설정:
   - 작업: `Naver Realestate Start`
   - 사용자: `root`
4. 스케줄:
   - 부팅 시 실행
5. 작업 설정:
   ```bash
   bash /volume1/docker/naver_realestate/start.sh
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

### 문제 1: 메모리 부족

**증상:** 컨테이너가 자주 재시작됨

**해결:**
1. Container Manager → 컨테이너 → 세부 정보
2. 리소스 제한 설정:
   - PostgreSQL: 512MB
   - Redis: 256MB
   - API: 512MB
   - Frontend: 512MB

### 문제 2: 포트 충돌

**증상:** `Port already in use` 에러

**해결:**
```bash
# 포트 사용 확인
sudo netstat -tuln | grep :3000
sudo netstat -tuln | grep :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 문제 3: 권한 문제

**증상:** `Permission denied` 에러

**해결:**
```bash
# 폴더 권한 변경
sudo chown -R 1000:1000 /volume1/docker/naver_realestate
sudo chmod -R 755 /volume1/docker/naver_realestate
```

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

### 권장 설정
```yaml
프로젝트 구조:
/volume1/docker/naver_realestate/
├── docker-compose.yml
├── backend/
├── frontend/
├── postgres_data/
├── redis_data/
└── backups/

컨테이너:
- PostgreSQL: 512MB 메모리 제한
- Redis: 256MB 메모리 제한
- API: 512MB 메모리 제한
- Frontend: 512MB 메모리 제한

총 메모리 사용: ~2GB
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

## ✅ 최종 체크리스트

### 초기 설정
- [ ] Container Manager 설치
- [ ] SSH 활성화
- [ ] 프로젝트 폴더 생성
- [ ] docker-compose.yml 업로드

### 배포
- [ ] 코드 업로드 (Git clone)
- [ ] 환경 변수 설정 (.env)
- [ ] 컨테이너 시작
- [ ] 데이터베이스 초기화

### 외부 접속
- [ ] QuickConnect 설정
- [ ] DDNS 설정 (선택)
- [ ] 포트 포워딩 (선택)
- [ ] Reverse Proxy (선택)
- [ ] SSL 인증서 (선택)

### 보안
- [ ] 방화벽 설정
- [ ] 2단계 인증
- [ ] SSL 인증서

### 자동화
- [ ] 부팅 시 자동 시작
- [ ] 정기 백업
- [ ] 정기 크롤링

### 모니터링
- [ ] Resource Monitor 확인
- [ ] 컨테이너 로그 확인
- [ ] 백업 확인

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
