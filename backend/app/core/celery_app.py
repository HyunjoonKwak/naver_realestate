"""
Celery 애플리케이션 설정
"""
import os
from celery import Celery
from celery.schedules import crontab

# Redis 연결 설정
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
celery_app.conf.beat_scheduler = "celery.beat:PersistentScheduler"
celery_app.conf.beat_schedule_filename = "/tmp/celerybeat-schedule"
