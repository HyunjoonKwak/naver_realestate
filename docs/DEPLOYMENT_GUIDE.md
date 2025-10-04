# AWS EC2 배포 가이드

## 📋 목차
1. [EC2 인스턴스 설정](#ec2-인스턴스-설정)
2. [Docker 설치](#docker-설치)
3. [프로젝트 배포](#프로젝트-배포)
4. [운영 환경 설정](#운영-환경-설정)
5. [도메인 및 HTTPS 설정](#도메인-및-https-설정)

---

## EC2 인스턴스 설정

### 1. 인스턴스 스펙 권장사항

| 용도 | 인스턴스 타입 | vCPU | 메모리 | 비용/월 |
|------|--------------|------|--------|---------|
| 테스트 | t3.small | 2 | 2GB | ~$15 |
| 운영(소규모) | t3.medium | 2 | 4GB | ~$30 |
| 운영(중규모) | t3.large | 2 | 8GB | ~$60 |

**권장**: t3.medium (PostgreSQL, Redis, API, Frontend 모두 실행 가능)

### 2. 보안 그룹 설정

인바운드 규칙:

| 타입 | 프로토콜 | 포트 | 소스 | 설명 |
|------|----------|------|------|------|
| SSH | TCP | 22 | My IP | SSH 접속 |
| HTTP | TCP | 80 | 0.0.0.0/0 | 웹 접속 |
| HTTPS | TCP | 443 | 0.0.0.0/0 | 보안 웹 접속 |
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | Next.js (임시) |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | FastAPI (임시) |

### 3. 스토리지

- 루트 볼륨: 30GB 이상 (gp3)
- DB 데이터가 많아질 경우 추가 EBS 볼륨 권장

---

## Docker 설치

### Ubuntu/Debian 기준

```bash
# 1. EC2 인스턴스 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 2. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 3. Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 4. Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker

# 6. 설치 확인
docker --version
docker-compose --version
```

---

## 프로젝트 배포

### 1. 코드 다운로드

```bash
# Git 설치
sudo apt install git -y

# 프로젝트 클론
git clone https://github.com/your-username/naver_realestate.git
cd naver_realestate
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/naver_realestate
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=naver_realestate

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://your-ec2-ip:8000
EOF
```

### 3. Python 환경 설정

```bash
# Python 3.11+ 설치
sudo apt install python3.11 python3.11-venv python3-pip -y

# 가상환경 생성
cd backend
python3.11 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
playwright install-deps
```

### 4. Node.js 설치 (Frontend)

```bash
# Node.js 18+ 설치
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 프론트엔드 의존성 설치
cd ../frontend
npm install
npm run build
```

### 5. Docker 컨테이너 시작

```bash
# 프로젝트 루트로 이동
cd ..

# Docker Compose로 PostgreSQL, Redis 시작
docker-compose up -d

# 컨테이너 상태 확인
docker-compose ps
```

### 6. 데이터베이스 초기화

```bash
# DB 테이블 생성
backend/venv/bin/python reset_db.py

# (선택) 초기 데이터 크롤링
backend/venv/bin/python advanced_crawler.py
```

---

## 운영 환경 설정

### 1. Systemd 서비스 생성 (자동 시작)

#### FastAPI 서비스

```bash
sudo nano /etc/systemd/system/naver-api.service
```

```ini
[Unit]
Description=Naver Real Estate API
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/naver_realestate
Environment="PATH=/home/ubuntu/naver_realestate/backend/venv/bin"
ExecStart=/home/ubuntu/naver_realestate/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Next.js 서비스

```bash
sudo nano /etc/systemd/system/naver-frontend.service
```

```ini
[Unit]
Description=Naver Real Estate Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/naver_realestate/frontend
ExecStart=/usr/bin/npm start
Restart=always
Environment="PORT=3000"

[Install]
WantedBy=multi-user.target
```

#### 서비스 시작

```bash
# 서비스 활성화 및 시작
sudo systemctl enable naver-api naver-frontend
sudo systemctl start naver-api naver-frontend

# 상태 확인
sudo systemctl status naver-api
sudo systemctl status naver-frontend

# 로그 확인
sudo journalctl -u naver-api -f
sudo journalctl -u naver-frontend -f
```

### 2. Nginx 리버스 프록시 설정

```bash
# Nginx 설치
sudo apt install nginx -y

# 설정 파일 생성
sudo nano /etc/nginx/sites-available/naver-realestate
```

```nginx
# API 서버
upstream api_backend {
    server 127.0.0.1:8000;
}

# Frontend 서버
upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://api_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Docs
    location /docs {
        proxy_pass http://api_backend/docs;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://api_backend/redoc;
        proxy_set_header Host $host;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/naver-realestate /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. 방화벽 설정 (UFW)

```bash
# UFW 활성화
sudo ufw enable

# 필요한 포트 허용
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# 상태 확인
sudo ufw status
```

---

## 도메인 및 HTTPS 설정

### 1. 도메인 연결

- Route 53 또는 다른 DNS 서비스에서 A 레코드 추가
- EC2 Elastic IP를 도메인에 연결

### 2. Let's Encrypt SSL 인증서

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# SSL 인증서 발급 및 자동 설정
sudo certbot --nginx -d your-domain.com

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

자동으로 Nginx 설정이 HTTPS로 업데이트됩니다.

---

## 자동 크롤링 스케줄링 (Cron)

```bash
# Cron 작업 추가
crontab -e
```

```cron
# 매일 오전 9시, 오후 6시 크롤링
0 9,18 * * * cd /home/ubuntu/naver_realestate && backend/venv/bin/python advanced_crawler.py >> /var/log/naver-crawler.log 2>&1
```

---

## 모니터링 및 로그

### 1. 로그 위치

```bash
# API 로그
sudo journalctl -u naver-api -f

# Frontend 로그
sudo journalctl -u naver-frontend -f

# Nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Docker 로그
docker-compose logs -f
```

### 2. 디스크 사용량 모니터링

```bash
# 디스크 사용량 확인
df -h

# Docker 정리 (주기적으로 실행)
docker system prune -a -f
```

---

## 백업 전략

### 1. 데이터베이스 백업

```bash
# 백업 스크립트 생성
cat > ~/backup-db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"
mkdir -p $BACKUP_DIR

# PostgreSQL 백업
docker exec naver_realestate_db pg_dump -U postgres naver_realestate > $BACKUP_DIR/db_backup_$DATE.sql

# 30일 이상된 백업 삭제
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql"
EOF

chmod +x ~/backup-db.sh

# Cron으로 매일 새벽 3시 백업
crontab -e
# 0 3 * * * /home/ubuntu/backup-db.sh
```

### 2. S3 백업 (선택)

```bash
# AWS CLI 설치
sudo apt install awscli -y

# S3 업로드 추가
aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql s3://your-bucket/backups/
```

---

## 비용 최적화

### 1. 스팟 인스턴스 사용
- 70% 할인
- 개발/테스트 환경에 적합

### 2. Reserved Instance
- 1년 약정: 40% 할인
- 3년 약정: 60% 할인

### 3. 대안: AWS Lightsail
- 고정 가격 ($10/월부터)
- 더 간단한 관리
- 작은 프로젝트에 적합

---

## 트러블슈팅

### 문제 1: 메모리 부족
```bash
# 스왑 파일 생성 (4GB)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 문제 2: Docker 컨테이너 재시작
```bash
# 자동 재시작 설정
docker-compose up -d --restart=always
```

### 문제 3: 포트 충돌
```bash
# 포트 사용 확인
sudo lsof -i :8000
sudo lsof -i :3000

# 프로세스 종료
sudo kill -9 <PID>
```

---

## 운영 체크리스트

### 배포 전
- [ ] EC2 인스턴스 생성 및 보안 그룹 설정
- [ ] 도메인 구입 및 DNS 설정
- [ ] 환경 변수 설정 (.env)
- [ ] SSL 인증서 발급

### 배포
- [ ] Docker 설치
- [ ] 코드 배포
- [ ] 데이터베이스 초기화
- [ ] Systemd 서비스 등록
- [ ] Nginx 설정

### 배포 후
- [ ] HTTPS 동작 확인
- [ ] API 엔드포인트 테스트
- [ ] 프론트엔드 접속 확인
- [ ] 크롤링 스케줄 설정
- [ ] 백업 스크립트 설정
- [ ] 모니터링 설정

---

## 접속 URL

배포 완료 후:

- **프론트엔드**: https://your-domain.com
- **API 문서**: https://your-domain.com/docs
- **API 엔드포인트**: https://your-domain.com/api/

---

## 추가 고려사항

### 1. RDS 사용 (프로덕션 권장)
- 자동 백업
- Multi-AZ 고가용성
- 자동 패치

### 2. ElastiCache (Redis)
- 관리형 Redis
- 자동 백업

### 3. CloudWatch
- 로그 수집
- 메트릭 모니터링
- 알람 설정

### 4. Load Balancer
- 트래픽 분산
- SSL 종료
- Health Check

---

## 참고 링크

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
