"""
Celery 애플리케이션 설정
"""
import os
from pathlib import Path
from celery import Celery
from celery.schedules import crontab

# .env 파일 수동 로드 (Celery worker에서 환경변수 사용)
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

# Redis 연결 설정
# 환경변수 REDIS_URL이 있으면 우선 사용, 없으면 REDIS_HOST/PORT로 구성
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Celery 애플리케이션 생성
celery_app = Celery(
    "naver_realestate",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scheduler", "app.tasks.briefing_tasks"]
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=False,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분 타임아웃
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# 주기적 작업 스케줄 설정 - JSON 파일에서 로드
try:
    from app.core.schedule_manager import load_schedules_from_file
    celery_app.conf.beat_schedule = load_schedules_from_file()
    print(f"✅ 스케줄 로드 완료: {len(celery_app.conf.beat_schedule)}개")
except Exception as e:
    print(f"⚠️  스케줄 로드 실패: {e}")
    # 로드 실패 시 빈 스케줄로 시작
    celery_app.conf.beat_schedule = {}

# Celery beat 설정 (스케줄러)
# RedBeat 사용: Redis 기반 동적 스케줄러 (재시작 없이 스케줄 변경 가능)
celery_app.conf.beat_scheduler = "redbeat.RedBeatScheduler"
celery_app.conf.redbeat_redis_url = REDIS_URL
celery_app.conf.redbeat_key_prefix = "redbeat:"
# Lock timeout을 12시간으로 증가 (Mac 잠자기 대응)
celery_app.conf.redbeat_lock_timeout = 43200  # 12시간 (43200초)
