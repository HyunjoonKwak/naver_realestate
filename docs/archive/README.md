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

## 📚 최신 문서

현재 프로젝트의 최신 문서는 다음을 참고하세요:

- **[CLAUDE.md](../../CLAUDE.md)** - AI 어시스턴트를 위한 전체 프로젝트 가이드
- **[README.md](../../README.md)** - 프로젝트 소개 및 빠른 시작
- **[docs/DYNAMIC_SCHEDULING.md](../DYNAMIC_SCHEDULING.md)** - 스케줄러 기능 상세 가이드
- **[docs/TRANSACTION_GUIDE.md](../TRANSACTION_GUIDE.md)** - 실거래가 기능 가이드
- **[docs/DISCORD_BRIEFING_GUIDE.md](../DISCORD_BRIEFING_GUIDE.md)** - Discord 브리핑 설정

## 💡 참고사항

이 문서들은 역사적 참고용으로 보관되며, 일부 정보는 여전히 유용할 수 있습니다.
단, 최신 코드베이스와 호환되지 않을 수 있으니 주의하세요.

**마지막 업데이트**: 2025-10-10
