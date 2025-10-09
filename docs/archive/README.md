# Archive - Deprecated Documentation

이 폴더에는 더 이상 사용하지 않는 문서들이 보관되어 있습니다.

## 📦 아카이브된 문서

### NAS/서버 배포 관련 (Deprecated - 2025-10-10)
- `NAS_DEPLOYMENT.md` - NAS 배포 가이드
- `NAS_DEPLOYMENT_QUICKSTART.md` - NAS 빠른 시작 가이드
- `SYNOLOGY_NAS_DEPLOYMENT.md` - Synology NAS 전용 배포 가이드
- `MULTI_DEVICE_SETUP.md` - 멀티 디바이스 설정 가이드

**아카이브 사유**:
- Playwright 크롤러가 `headless=False` 모드를 사용하여 봇 회피
- 이 모드는 X server (GUI 환경)가 필요함
- NAS/EC2 같은 헤드리스 서버에서는 Xvfb 설치 등 복잡한 설정 필요
- 프로젝트 방향을 **로컬 Mac 개발 환경**에 집중하기로 결정

### 스케줄러 트러블슈팅 관련 (Deprecated - 2025-10-10)
- `SCHEDULER_ISSUE_RESOLVED.md` - 초기 스케줄러 이슈 해결 기록
- `SCHEDULER_SETUP.md` - 스케줄러 초기 설정 가이드
- `SCHEDULER_STATUS_FIX.md` - 스케줄러 상태 표시 버그 수정
- `SCHEDULING_SUMMARY.md` - 스케줄링 기능 요약

**아카이브 사유**:
- 스케줄러 기능이 안정화되고 문서가 CLAUDE.md에 통합됨
- 웹 UI에서 스케줄러 관리 페이지 완성 (http://localhost:3000/scheduler)
- Beat 재시작 기능 추가로 수동 트러블슈팅 불필요
- 중복 문서 제거 및 메인 문서 집중

### AWS EC2 배포 관련 (Deprecated - 2025-10-10)
- `DEPLOYMENT_GUIDE.md` - AWS EC2 배포 가이드
- `FREE_TIER_DEPLOYMENT.md` - 무료/저비용 배포 가이드 (프리티어)

**아카이브 사유**:
- Playwright 크롤러가 `headless=False` 모드를 사용하여 봇 회피
- GUI 환경 필요로 EC2 헤드리스 서버에서 복잡한 Xvfb 설정 필요
- t2.micro (1GB RAM) 스펙으로는 메모리 부족 (OOM) 발생
- 프로젝트 방향을 **로컬 Mac 개발 환경**에 집중하기로 결정

### 프로젝트 진도 관련 (Deprecated - 2025-10-10)
- `PROJECT_OVERVIEW.md` - 초기 프로젝트 기획 문서 (2025-10-03)
- `PROGRESS_SUMMARY.md` - Phase 5까지 진행 상황 (2025-10-04)
- `IMPLEMENTATION_CHECKLIST.md` - 구현 체크리스트

**아카이브 사유**:
- Phase 6, 7 완료 후 내용이 크게 변경됨
- `README.md`가 최신 상태로 잘 관리되고 있어 중복
- 실거래가 기능, 스케줄러 관리, Discord 브리핑 등 많은 기능 추가됨
- 역사적 참고용으로만 보관

### 기술 설계 문서 (Deprecated - 2025-10-10)
- `MOLIT_API_INTEGRATION.md` - 국토부 실거래가 API 연동 설계 문서

**아카이브 사유**:
- 초기 설계 단계 문서로 역할 완료
- 실제 구현은 설계와 일부 다르게 진행됨 (Chart.js 사용, 파일 기반 법정동 코드 등)
- `TRANSACTION_GUIDE.md`가 실제 구현을 정확히 반영
- 설계 문서와 사용자 가이드가 혼재하여 혼란 방지

## 📚 최신 문서

현재 프로젝트의 최신 문서는 다음을 참고하세요:

- **[CLAUDE.md](../../CLAUDE.md)** - AI 어시스턴트를 위한 전체 프로젝트 가이드
- **[README.md](../../README.md)** - 프로젝트 소개 및 빠른 시작
- **[docs/LAPTOP_SETUP.md](../LAPTOP_SETUP.md)** - 맥북에서 개발 환경 설정 가이드
- **[docs/DYNAMIC_SCHEDULING.md](../DYNAMIC_SCHEDULING.md)** - 스케줄러 기능 상세 가이드
- **[docs/TRANSACTION_GUIDE.md](../TRANSACTION_GUIDE.md)** - 실거래가 기능 가이드
- **[docs/DISCORD_BRIEFING_GUIDE.md](../DISCORD_BRIEFING_GUIDE.md)** - Discord 브리핑 설정

## 💡 참고사항

이 문서들은 역사적 참고용으로 보관되며, 일부 정보는 여전히 유용할 수 있습니다.
단, 최신 코드베이스와 호환되지 않을 수 있으니 주의하세요.

**마지막 업데이트**: 2025-10-10
