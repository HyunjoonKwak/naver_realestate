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
    include=["app.tasks.scheduler"]
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

# 주기적 작업 스케줄 설정
celery_app.conf.beat_schedule = {
    # 매일 오전 6시에 모든 단지 크롤링
    "crawl-all-complexes-morning": {
        "task": "app.tasks.scheduler.crawl_all_complexes",
        "schedule": crontab(hour=6, minute=0),  # 매일 06:00
        "options": {"expires": 3600},  # 1시간 내에 실행되지 않으면 취소
    },
    # 매일 오후 6시에 모든 단지 크롤링
    "crawl-all-complexes-evening": {
        "task": "app.tasks.scheduler.crawl_all_complexes",
        "schedule": crontab(hour=18, minute=0),  # 매일 18:00
        "options": {"expires": 3600},
    },
    # 매주 월요일 오전 2시에 오래된 스냅샷 정리
    "cleanup-old-snapshots": {
        "task": "app.tasks.scheduler.cleanup_old_snapshots",
        "schedule": crontab(hour=2, minute=0, day_of_week=1),  # 매주 월요일 02:00
        "options": {"expires": 7200},
    },
}

# Celery beat 설정 (스케줄러)
celery_app.conf.beat_scheduler = "celery.beat:PersistentScheduler"
celery_app.conf.beat_schedule_filename = "/tmp/celerybeat-schedule"
