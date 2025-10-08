"""
스케줄 설정 파일 관리
"""
import json
import os
from pathlib import Path
from celery.schedules import crontab
from typing import Dict, Any

# 설정 파일 경로
CONFIG_DIR = Path(__file__).parent.parent / "config"
SCHEDULE_FILE = CONFIG_DIR / "schedules.json"


def load_schedules_from_file() -> Dict[str, Any]:
    """
    JSON 파일에서 스케줄 설정을 로드

    Returns:
        스케줄 설정 딕셔너리

    Note:
        day_of_week 값:
        - Celery crontab: 0=일요일, 1=월요일, 2=화요일, 3=수요일, 4=목요일, 5=금요일, 6=토요일
        - schedules.json에서도 동일한 값 사용 (0-6)
    """
    if not SCHEDULE_FILE.exists():
        # 파일이 없으면 빈 딕셔너리 반환
        return {}

    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            schedules_data = json.load(f)

        # JSON 형식을 Celery beat_schedule 형식으로 변환
        beat_schedule = {}
        for name, config in schedules_data.items():
            if not config.get('enabled', True):
                # enabled=False인 스케줄은 스킵
                continue

            schedule_config = config['schedule']
            day_of_week = schedule_config.get('day_of_week', '*')

            # 문자열을 정수로 변환 (필요시)
            if day_of_week != '*' and not isinstance(day_of_week, (list, tuple)):
                if isinstance(day_of_week, str) and day_of_week.isdigit():
                    day_of_week = int(day_of_week)

            # crontab 객체 생성
            if day_of_week == '*':
                # 매일
                schedule_obj = crontab(
                    hour=schedule_config['hour'],
                    minute=schedule_config['minute']
                )
            elif day_of_week == 'QUARTERLY_1':
                # 분기별 1일 (1월, 4월, 7월, 10월 1일)
                schedule_obj = crontab(
                    hour=schedule_config['hour'],
                    minute=schedule_config['minute'],
                    day_of_month='1',
                    month_of_year='1,4,7,10'
                )
            elif day_of_week == 'QUARTERLY_15':
                # 분기별 15일 (1월, 4월, 7월, 10월 15일)
                schedule_obj = crontab(
                    hour=schedule_config['hour'],
                    minute=schedule_config['minute'],
                    day_of_month='15',
                    month_of_year='1,4,7,10'
                )
            elif day_of_week == 'MONTHLY_1':
                # 매월 1일
                schedule_obj = crontab(
                    hour=schedule_config['hour'],
                    minute=schedule_config['minute'],
                    day_of_month='1'
                )
            elif day_of_week == 'MONTHLY_15':
                # 매월 15일
                schedule_obj = crontab(
                    hour=schedule_config['hour'],
                    minute=schedule_config['minute'],
                    day_of_month='15'
                )
            else:
                # 매주 특정 요일
                schedule_obj = crontab(
                    hour=schedule_config['hour'],
                    minute=schedule_config['minute'],
                    day_of_week=day_of_week
                )

            beat_schedule[name] = {
                'task': config['task'],
                'schedule': schedule_obj,
                'options': {'expires': 3600}
            }

        return beat_schedule

    except Exception as e:
        print(f"스케줄 파일 로드 실패: {e}")
        return {}


def save_schedules_to_file(schedules: Dict[str, Any]) -> bool:
    """
    스케줄 설정을 JSON 파일에 저장

    Args:
        schedules: 스케줄 설정 딕셔너리

    Returns:
        성공 여부
    """
    try:
        # config 디렉토리 생성 (없으면)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Celery beat_schedule 형식을 JSON 형식으로 변환
        schedules_data = {}
        for name, config in schedules.items():
            schedule = config['schedule']

            # crontab 객체에서 값 추출
            if hasattr(schedule, 'hour'):
                hour = schedule.hour
                minute = schedule.minute
                day_of_week = getattr(schedule, 'day_of_week', '*')

                # day_of_week가 set인 경우 문자열로 변환
                if isinstance(day_of_week, set):
                    if len(day_of_week) == 7:  # 모든 요일
                        day_of_week = '*'
                    else:
                        day_of_week = ','.join(map(str, sorted(day_of_week)))

                schedules_data[name] = {
                    'task': config['task'],
                    'schedule': {
                        'hour': hour,
                        'minute': minute,
                        'day_of_week': str(day_of_week)
                    },
                    'enabled': True,
                    'description': config.get('description', '')
                }

        # JSON 파일에 저장
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedules_data, f, indent=2, ensure_ascii=False)

        return True

    except Exception as e:
        print(f"스케줄 파일 저장 실패: {e}")
        return False


def get_schedule_raw_data() -> Dict[str, Any]:
    """
    JSON 파일에서 원본 스케줄 데이터 로드 (crontab 변환 없이)

    Returns:
        원본 스케줄 데이터
    """
    if not SCHEDULE_FILE.exists():
        return {}

    try:
        with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"스케줄 파일 로드 실패: {e}")
        return {}


def update_schedule_in_file(name: str, schedule_data: Dict[str, Any]) -> bool:
    """
    특정 스케줄 업데이트

    Args:
        name: 스케줄 이름
        schedule_data: 스케줄 데이터

    Returns:
        성공 여부
    """
    try:
        schedules = get_schedule_raw_data()
        schedules[name] = schedule_data

        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedules, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"스케줄 업데이트 실패: {e}")
        return False


def delete_schedule_from_file(name: str) -> bool:
    """
    특정 스케줄 삭제

    Args:
        name: 스케줄 이름

    Returns:
        성공 여부
    """
    try:
        schedules = get_schedule_raw_data()
        if name in schedules:
            del schedules[name]

        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            json.dump(schedules, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"스케줄 삭제 실패: {e}")
        return False
