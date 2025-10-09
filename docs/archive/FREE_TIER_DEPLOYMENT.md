# 무료/저비용 배포 가이드 (프리티어 활용)

## ⚠️ t2.micro 제약사항

**t2.micro 스펙:**
- vCPU: 1개
- 메모리: **1GB** ⚠️
- 네트워크: 낮음

**현재 프로젝트 메모리 사용량:**
- PostgreSQL: ~150MB
- Redis: ~50MB
- FastAPI: ~100MB
- Next.js: ~300MB
- **총 예상: ~600-800MB**

❌ **문제점**: 시스템 메모리 포함 시 **메모리 부족 (OOM) 발생 가능**

---

## 🎯 해결 방안

### 옵션 1: 프리티어 최적화 (권장) ⭐

**전략: 서비스 분리 + 외부 무료 서비스 활용**

```
┌─────────────────┐
│ AWS EC2 t2.micro│
│  (프리티어)      │
│                 │
│ ✅ FastAPI      │
│ ✅ Next.js      │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ 외부 무료 서비스 │
│                 │
│ ✅ ElephantSQL  │ (PostgreSQL 무료)
│ ✅ Redis Cloud  │ (Redis 무료)
└─────────────────┘
```

#### 1-1. 무료 PostgreSQL: ElephantSQL
- **용량**: 20MB 무료
- **연결**: 5개 동시 연결
- **URL**: https://www.elephantsql.com/

```bash
# 가입 후 받은 연결 정보
DATABASE_URL=postgres://user:password@tiny.db.elephantsql.com/dbname
```

#### 1-2. 무료 Redis: Redis Cloud (Upstash)
- **용량**: 10,000 commands/day 무료
- **메모리**: 256MB
- **URL**: https://upstash.com/

```bash
# 가입 후 받은 연결 정보
REDIS_URL=rediss://default:password@host.upstash.io:6379
```

#### 1-3. t2.micro에서 실행
```bash
# EC2에서는 API + Frontend만 실행
# PostgreSQL, Redis는 외부 서비스 사용

# .env 파일
DATABASE_URL=postgres://user:password@tiny.db.elephantsql.com/dbname
REDIS_URL=rediss://default:password@host.upstash.io:6379

# 메모리 사용량: ~400MB (충분!)
```

---

### 옵션 2: Static Export (가장 저렴) 💰

**전략: Frontend를 정적 파일로 배포**

```
┌─────────────────┐
│ Vercel (무료)    │ ← Frontend (Static)
│ Next.js         │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ AWS EC2 t2.micro│ ← Backend API만
│ FastAPI         │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ 외부 무료 DB     │
│ ElephantSQL     │
│ Upstash Redis   │
└─────────────────┘
```

#### 장점
- ✅ Frontend 무료 (Vercel)
- ✅ EC2는 API만 실행 (~200MB)
- ✅ 속도 빠름 (CDN)

---

### 옵션 3: Docker 최적화 (고급)

**전략: t2.micro에서 모두 실행하되 메모리 최적화**

```bash
# docker-compose.yml 수정
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: naver_realestate
      # 메모리 제한 설정
      POSTGRES_SHARED_BUFFERS: 128MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 256MB
    mem_limit: 200m  # 메모리 제한

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 50mb --maxmemory-policy allkeys-lru
    mem_limit: 100m  # 메모리 제한
```

#### 스왑 파일 추가 (필수)
```bash
# 2GB 스왑 파일 생성
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 확인
free -h
```

#### Next.js 메모리 최적화
```json
// package.json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "NODE_OPTIONS='--max-old-space-size=256' next start"
  }
}
```

---

## 🚀 추천 배포 방법 (프리티어 최대 활용)

### 단계별 가이드

#### 1. 외부 무료 DB/Redis 설정

**ElephantSQL (PostgreSQL)**
1. https://www.elephantsql.com/ 가입
2. "Create New Instance" → Tiny Turtle (무료)
3. 연결 정보 복사

**Upstash (Redis)**
1. https://upstash.com/ 가입
2. "Create Database" → Free tier
3. 연결 정보 복사

#### 2. EC2 t2.micro 설정

```bash
# 1. EC2 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 2. 스왑 파일 생성 (필수!)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 3. 기본 도구 설치
sudo apt update && sudo apt install -y git python3.11 python3.11-venv python3-pip nodejs npm

# 4. 프로젝트 클론
git clone https://github.com/your-username/naver_realestate.git
cd naver_realestate
```

#### 3. 환경변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
# 외부 PostgreSQL (ElephantSQL)
DATABASE_URL=postgres://user:password@tiny.db.elephantsql.com/dbname

# 외부 Redis (Upstash)
REDIS_URL=rediss://default:password@host.upstash.io:6379

# API 설정
API_HOST=0.0.0.0
API_PORT=8000

# Frontend 설정
NEXT_PUBLIC_API_URL=http://your-ec2-ip:8000
EOF
```

#### 4. Backend 설치 및 실행

```bash
# Python 환경 설정
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Playwright 설치 (크롤링 필요시)
playwright install chromium
playwright install-deps

# DB 초기화
cd ..
backend/venv/bin/python reset_db.py

# API 서버 실행 (백그라운드)
nohup backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

#### 5. Frontend 빌드 및 실행

```bash
# 프론트엔드 빌드
cd frontend
npm install
npm run build

# 프로덕션 모드 실행 (메모리 최적화)
NODE_OPTIONS='--max-old-space-size=256' nohup npm start > frontend.log 2>&1 &
```

#### 6. Nginx 설정 (선택)

```bash
# Nginx 설치
sudo apt install nginx -y

# 설정
sudo nano /etc/nginx/sites-available/default
```

```nginx
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📊 메모리 사용량 비교

| 구성 | PostgreSQL | Redis | API | Frontend | 총 메모리 |
|------|-----------|-------|-----|----------|----------|
| **로컬 (모두 실행)** | 150MB | 50MB | 100MB | 300MB | **600MB** ❌ |
| **외부 DB/Redis** | 0MB | 0MB | 100MB | 200MB | **300MB** ✅ |
| **Static Export** | 0MB | 0MB | 100MB | 0MB | **100MB** ✅✅ |

---

## 💰 비용 비교

| 방법 | 월 비용 | 장점 | 단점 |
|------|---------|------|------|
| **t2.micro + 외부 DB** | $0 (12개월) | 완전 무료 | DB 용량 제한 |
| **Lightsail $5** | $5/월 | 간단함 | 유료 |
| **t3.medium** | $30/월 | 충분한 스펙 | 비쌈 |
| **Vercel + Railway** | $0-5/월 | 관리 불필요 | 제한적 |

---

## 🎯 최종 추천 (t2.micro 기준)

### 방법 1: 외부 서비스 활용 (추천) ⭐
```
EC2 t2.micro (무료)
  ├── FastAPI
  └── Next.js (빌드 모드)

외부 서비스 (무료)
  ├── ElephantSQL (20MB)
  └── Upstash Redis (256MB)

총 비용: $0 (12개월)
```

### 방법 2: 하이브리드 (최고 성능)
```
Vercel (무료)
  └── Next.js Frontend

EC2 t2.micro (무료)
  └── FastAPI

외부 DB (무료)
  ├── ElephantSQL
  └── Upstash Redis

총 비용: $0 (12개월)
```

---

## ⚠️ 주의사항

### t2.micro 제한사항
1. **메모리**: 1GB → 스왑 파일 필수
2. **CPU 크레딧**: 과도한 사용 시 성능 저하
3. **네트워크**: 제한적

### 모니터링
```bash
# 메모리 확인
free -h

# 프로세스 확인
top

# 로그 확인
tail -f api.log
tail -f frontend.log
```

### 자동 재시작 (OOM 방지)
```bash
# Systemd 서비스로 변경 (자동 재시작)
sudo systemctl enable naver-api
sudo systemctl enable naver-frontend
```

---

## 🚀 빠른 시작 스크립트

```bash
#!/bin/bash
# EC2 t2.micro 자동 설정 스크립트

# 1. 스왑 파일 생성
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. 기본 도구 설치
sudo apt update && sudo apt install -y git python3.11 python3.11-venv nodejs npm

# 3. 프로젝트 클론
git clone https://github.com/your-username/naver_realestate.git
cd naver_realestate

# 4. Backend 설정
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Frontend 빌드
cd ../frontend
npm install
npm run build

# 완료!
echo "✅ 설치 완료! .env 파일을 설정하고 서비스를 시작하세요."
```

---

## 📚 참고 링크

- [ElephantSQL](https://www.elephantsql.com/) - 무료 PostgreSQL
- [Upstash](https://upstash.com/) - 무료 Redis
- [Vercel](https://vercel.com/) - 무료 Frontend 호스팅
- [AWS 프리티어](https://aws.amazon.com/free/)

---

## 결론

**t2.micro로 운영 가능하지만:**
1. ✅ **외부 DB/Redis 필수** (메모리 부족 방지)
2. ✅ **스왑 파일 필수** (2GB 권장)
3. ✅ **Frontend 빌드 모드** (dev 모드는 메모리 많이 사용)
4. ⚠️ **크롤링은 별도 실행** (메모리 부족 위험)

**더 나은 선택:**
- 💡 Lightsail $5/월 (1GB RAM, 고정 IP)
- 💡 12개월 후 t3.small로 업그레이드 ($15/월)
