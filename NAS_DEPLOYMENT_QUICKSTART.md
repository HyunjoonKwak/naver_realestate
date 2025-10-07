# Synology NAS 배포 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 전제조건
- Synology NAS (DSM 7.0+, Docker 지원)
- 메모리 4GB 이상
- MOLIT API 키 ([발급받기](https://www.data.go.kr/))

---

## 📝 배포 단계

### 1️⃣ Docker 패키지 설치 (1분)

**모든 DSM 버전:**
1. DSM 로그인
2. 패키지 센터 열기
3. "**Docker**" 검색 및 설치

> 💡 **패키지 이름 참고**:
> - 대부분 모델: "Docker"로 표시
> - 일부 최신 모델: "Container Manager"로 표시
> - DS716+II (DSM 7.1.1) → "Docker" ✅
> - **두 이름 모두 같은 기능입니다. Docker를 검색하세요!**

### 2️⃣ SSH 활성화 (1분)
1. 제어판 → 터미널 및 SNMP
2. "SSH 서비스 활성화" 체크
3. 포트: 22 (기본값)

### 3️⃣ 프로젝트 Clone (1분)
```bash
# SSH 접속
ssh admin@your-nas-ip

# Docker 디렉토리로 이동
cd /volume1/docker

# 프로젝트 Clone
sudo git clone https://github.com/your-username/naver_realestate.git
cd naver_realestate
```

### 4️⃣ 환경변수 설정 (1분)
```bash
# .env 파일 생성
sudo cp .env.example .env
sudo nano .env
```

**필수 입력:**
```bash
MOLIT_API_KEY=여기에_실제_API_키_입력
```

**저장:** `Ctrl + O` → `Enter` → `Ctrl + X`

### 5️⃣ Docker Compose 실행 (5-10분)
```bash
# 빌드 및 시작 (최초 실행 시 5-10분 소요)
sudo docker-compose up -d --build

# 진행 상황 확인
sudo docker-compose logs -f
```

**빌드 완료 대기:** "Application startup complete" 메시지 확인

### 6️⃣ 데이터베이스 초기화 (30초)
```bash
# 데이터베이스 마이그레이션
sudo docker-compose exec api python migrate_db.py
```

### 7️⃣ 접속 확인 ✅
브라우저에서 접속:
- **프론트엔드:** http://your-nas-ip:3000
- **API 문서:** http://your-nas-ip:8000/docs

---

## 🎯 완료! 다음 단계

### 단지 추가하기
1. 프론트엔드 접속 (http://your-nas-ip:3000)
2. "단지 목록" → "새 단지 추가"
3. 네이버 부동산 URL 입력
4. 크롤링 시작

### 스케줄 설정하기
1. "스케줄러" 메뉴
2. 자동 크롤링 일정 등록
3. 매일 자동 업데이트

---

## 🔧 유용한 명령어

### 컨테이너 관리
```bash
# 전체 컨테이너 시작
sudo docker-compose up -d

# 전체 컨테이너 중지
sudo docker-compose down

# 특정 컨테이너 재시작
sudo docker-compose restart api

# 컨테이너 상태 확인
sudo docker-compose ps

# 실시간 로그 확인
sudo docker-compose logs -f api
```

### 데이터베이스 관리
```bash
# PostgreSQL 접속
sudo docker-compose exec postgres psql -U postgres -d naver_realestate

# 데이터베이스 백업
sudo docker-compose exec postgres pg_dump -U postgres naver_realestate > backup.sql

# 데이터베이스 복원
cat backup.sql | sudo docker-compose exec -T postgres psql -U postgres -d naver_realestate
```

---

## ⚙️ 부팅 시 자동 시작 설정

### Task Scheduler 설정 (추천)
1. DSM → 제어판 → 작업 스케줄러
2. "생성" → 예약된 작업 → 사용자 정의 스크립트
3. 설정:
   - 작업명: `Naver Realestate Auto Start`
   - 사용자: `root`
   - 스케줄: 부팅 시 실행
4. 작업 설정:
```bash
cd /volume1/docker/naver_realestate && docker-compose up -d
```

---

## 🌐 외부 접속 설정 (선택)

### QuickConnect (가장 쉬움)
1. DSM → 제어판 → QuickConnect
2. QuickConnect ID 등록
3. 접속: `http://your-id.quickconnect.to:3000`

### DDNS + 포트포워딩
1. DSM → 제어판 → 외부 액세스 → DDNS
2. 서비스: Synology
3. 호스트명: `yourname.synology.me`
4. 라우터 포트포워딩:
   - 외부 3000 → 내부 3000 (Frontend)
   - 외부 8000 → 내부 8000 (API)

---

## 🔒 보안 설정 (권장)

### 1. 방화벽 규칙
DSM → 제어판 → 보안 → 방화벽
- 포트 3000, 8000 허용 (특정 IP만)

### 2. 2단계 인증
DSM → 개인 → 계정 → 2단계 인증 활성화

### 3. SSL 인증서 (HTTPS)
DSM → 제어판 → 보안 → 인증서 → Let's Encrypt

---

## 🆘 트러블슈팅

### 문제: 컨테이너가 시작되지 않음
```bash
# 로그 확인
sudo docker-compose logs api

# 일반적인 원인:
# 1. .env 파일이 없음 → cp .env.example .env
# 2. 포트 충돌 → sudo netstat -tuln | grep 8000
# 3. 메모리 부족 → Container Manager에서 확인
```

### 문제: "MOLIT_API_KEY가 설정되지 않았습니다"
```bash
# .env 파일 확인
cat .env

# API 키가 있는지 확인
# 없으면 편집: sudo nano .env
# 저장 후 재시작: sudo docker-compose restart api
```

### 문제: 데이터베이스 연결 오류
```bash
# PostgreSQL 상태 확인
sudo docker-compose ps postgres

# PostgreSQL 재시작
sudo docker-compose restart postgres

# 데이터베이스 재초기화 (데이터 삭제됨!)
sudo docker-compose down -v
sudo docker-compose up -d
sudo docker-compose exec api python migrate_db.py
```

---

## 📚 추가 문서

- [상세 배포 가이드](docs/SYNOLOGY_NAS_DEPLOYMENT.md)
- [프로젝트 README](CLAUDE.md)
- [API 문서](http://your-nas-ip:8000/docs)

---

## 💡 팁

1. **메모리 부족 시:** Container Manager → 컨테이너 → 리소스 제한 설정
2. **크롤링 속도 조절:** 스케줄러에서 실행 간격 조정
3. **백업 자동화:** Hyper Backup으로 매일 자동 백업 설정
4. **로그 모니터링:** `docker-compose logs -f` 명령어로 실시간 확인

---

## 🎉 성공!

이제 Synology NAS에서 네이버 부동산 트래킹 시스템이 24/7 운영됩니다!

**다음 할 일:**
1. ✅ 관심 있는 아파트 단지 추가
2. ✅ 스케줄러로 자동 크롤링 설정
3. ✅ Discord 웹훅으로 알림 받기 (선택)
4. ✅ 주간 브리핑 확인

**질문이나 문제가 있나요?**
- 이슈 등록: GitHub Issues
- 문서 확인: [docs/](docs/)
