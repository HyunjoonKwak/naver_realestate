# Database Utility Scripts

이 디렉토리에는 데이터베이스 관리 및 디버깅을 위한 유틸리티 스크립트가 포함되어 있습니다.

## 스크립트 목록

### 1. migrate_db.py

**목적**: 기존 데이터베이스에 외래키(Foreign Key) 제약조건 추가

**기능**:
- Phase 1 개선사항: Complex 테이블과 연관 테이블 간 외래키 제약조건 추가
- CASCADE DELETE 규칙 적용 (단지 삭제 시 연관 데이터 자동 삭제)
- 기존 데이터 보존하면서 스키마 업데이트

**사용법**:
```bash
# 프로젝트 루트에서 실행
cd /Users/specialrisk_mac/code_work/naver_realestate
backend/.venv/bin/python scripts/migrate_db.py
```

**주의사항**:
- 이미 외래키가 추가된 데이터베이스에서는 재실행하지 마세요
- 실행 전 데이터베이스 백업 권장
- 한 번만 실행하면 됩니다

**추가되는 외래키**:
- `Article.complex_id` → `Complex.complex_id` (CASCADE)
- `Transaction.complex_id` → `Complex.complex_id` (CASCADE)
- `ArticleSnapshot.complex_id` → `Complex.complex_id` (CASCADE)
- `ArticleChange.complex_id` → `Complex.complex_id` (CASCADE)

---

### 2. reset_db.py

**목적**: 데이터베이스 전체 초기화 (모든 테이블 삭제 후 재생성)

**기능**:
- 모든 테이블 DROP
- SQLAlchemy 모델 기반으로 테이블 재생성
- 외래키 제약조건 포함 (migrate_db.py 실행 필요 없음)

**사용법**:
```bash
# 프로젝트 루트에서 실행
cd /Users/specialrisk_mac/code_work/naver_realestate
backend/.venv/bin/python scripts/reset_db.py
```

**경고**:
- **모든 데이터가 삭제됩니다!**
- 운영 환경에서는 절대 사용하지 마세요
- 개발 환경에서 깨끗한 상태로 시작할 때만 사용

**사용 시나리오**:
- 스키마를 크게 변경한 후 새로 시작할 때
- 테스트 데이터를 완전히 제거하고 싶을 때
- 데이터베이스 마이그레이션 오류가 발생했을 때

---

### 3. check_data.py

**목적**: 데이터베이스 내용 확인 및 디버깅

**기능**:
- 단지(Complex) 목록 조회
- 매물(Article) 목록 조회
- 실거래가(Transaction) 목록 조회
- 각 테이블의 데이터 개수 확인

**사용법**:
```bash
# 프로젝트 루트에서 실행
cd /Users/specialrisk_mac/code_work/naver_realestate
backend/.venv/bin/python scripts/check_data.py
```

**출력 예시**:
```
=== 단지 정보 ===
단지 개수: 3

단지 ID: 12345
단지명: 동탄역 롯데캐슬
주소: 경기도 화성시 동탄반송길 25
...

=== 매물 정보 ===
매물 개수: 150

매물번호: 2412345678
단지ID: 12345
거래유형: 매매
가격: 85,000
...

=== 실거래가 정보 ===
거래 개수: 50
...
```

**사용 시나리오**:
- 크롤링 후 데이터가 제대로 저장되었는지 확인
- 특정 단지의 매물 수 확인
- 실거래가 데이터 업데이트 확인
- API 개발 중 데이터 구조 파악

---

## 실행 환경 요구사항

모든 스크립트는 다음 조건에서 실행되어야 합니다:

1. **Python 가상환경**: backend/.venv 활성화 필요
2. **환경변수**: DATABASE_URL이 `.env` 파일에 설정되어 있어야 함
3. **Docker**: PostgreSQL 컨테이너가 실행 중이어야 함

### 환경 확인
```bash
# 1. Docker 컨테이너 확인
docker ps

# 2. PostgreSQL 연결 확인
docker exec -it naver_realestate-postgres-1 psql -U postgres -d naver_realestate -c "\dt"

# 3. 환경변수 확인
cat backend/.env | grep DATABASE_URL
```

---

## 데이터베이스 스키마 정보

현재 데이터베이스는 다음 테이블로 구성됩니다:

- **complexes**: 아파트 단지 마스터 데이터
- **articles**: 매물 정보 (현재 활성 매물)
- **transactions**: 실거래가 정보 (국토교통부 공공데이터)
- **article_snapshots**: 매물 변동 추적용 스냅샷
- **article_changes**: 감지된 매물 변화 (NEW/REMOVED/PRICE_UP/PRICE_DOWN)
- **article_history**: 레거시 변동 이력
- **crawl_jobs**: 크롤링 작업 이력

자세한 스키마 정보는 [backend/app/models/complex.py](../backend/app/models/complex.py)를 참조하세요.

---

## 트러블슈팅

### 오류: `ModuleNotFoundError: No module named 'app'`

**원인**: Python 경로 문제

**해결**:
```bash
# backend 디렉토리를 PYTHONPATH에 추가
cd /Users/specialrisk_mac/code_work/naver_realestate
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
backend/.venv/bin/python scripts/check_data.py
```

### 오류: `sqlalchemy.exc.OperationalError: could not connect to server`

**원인**: PostgreSQL 컨테이너가 실행 중이 아님

**해결**:
```bash
# Docker 컨테이너 시작
docker-compose up -d postgres
```

### 외래키 제약조건 오류

**원인**: migrate_db.py를 이미 실행했는데 다시 실행

**해결**: 이미 적용되었으므로 무시하거나, reset_db.py로 초기화 후 migrate_db.py 재실행

---

## 관련 문서

- [프로젝트 구조 문서](../docs/PROJECT_STRUCTURE.md)
- [API 문서](http://localhost:8000/docs) (서버 실행 후)
- [메인 README](../README_STARTUP.md)
- [테스트 스크립트](../tests/README.md)
