#!/bin/bash

# Celery Beat 스케줄 확인 스크립트
# 현재 등록된 스케줄과 다음 실행 시간을 표시합니다.

echo "📅 Celery Beat 스케줄 확인"
echo "======================================"

cd backend

.venv/bin/python << 'EOF'
from datetime import datetime, timedelta
from app.core.celery_app import celery_app
from celery.schedules import crontab

# 요일 매핑 (Celery 기준)
DAY_NAMES = {
    0: '일요일',
    1: '월요일',
    2: '화요일',
    3: '수요일',
    4: '목요일',
    5: '금요일',
    6: '토요일'
}

print(f"\n⏰ 현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}")
print(f"   (오늘은 {DAY_NAMES[datetime.now().weekday() + 1 if datetime.now().weekday() < 6 else 0]}입니다)")
print("\n" + "=" * 80)
print("\n📋 등록된 스케줄 목록:\n")

if not celery_app.conf.beat_schedule:
    print("⚠️  등록된 스케줄이 없습니다.")
    print("   schedules.json 파일을 확인하세요.")
    exit(1)

for name, config in celery_app.conf.beat_schedule.items():
    print(f"🔹 {name}")
    print(f"   태스크: {config['task']}")

    schedule = config['schedule']

    # crontab 스케줄 파싱
    if isinstance(schedule, crontab):
        # 시간 정보
        hour = list(schedule.hour)[0] if hasattr(schedule, 'hour') and isinstance(schedule.hour, set) else (schedule.hour if hasattr(schedule, 'hour') else '*')
        minute = list(schedule.minute)[0] if hasattr(schedule, 'minute') and isinstance(schedule.minute, set) else (schedule.minute if hasattr(schedule, 'minute') else '*')

        # 요일 정보
        day_of_week = schedule.day_of_week if hasattr(schedule, 'day_of_week') else '*'

        # 요일 이름 변환
        day_str = '*'
        if day_of_week != '*':
            if isinstance(day_of_week, set):
                if len(day_of_week) == 7:
                    day_str = '매일'
                else:
                    day_names = [DAY_NAMES.get(int(d), str(d)) for d in sorted(day_of_week)]
                    day_str = ', '.join(day_names)
            else:
                day_str = DAY_NAMES.get(int(day_of_week), str(day_of_week))
        else:
            day_str = '매일'

        # 날짜 정보 (월별/분기별)
        day_of_month = schedule.day_of_month if hasattr(schedule, 'day_of_month') else '*'
        month_of_year = schedule.month_of_year if hasattr(schedule, 'month_of_year') else '*'

        # 스케줄 설명
        if month_of_year != '*':
            month_str = str(month_of_year).replace('{', '').replace('}', '')
            day_str = f"{month_str}월 {day_of_month}일"
            print(f"   스케줄: {day_str} {hour:02d}:{minute:02d}")
        else:
            print(f"   스케줄: {day_str} {hour:02d}:{minute:02d}")

        # 다음 실행까지 남은 시간
        now = datetime.now()
        remaining = schedule.remaining_estimate(now)

        # 다음 실행 시간 계산
        next_run = now + remaining

        print(f"   다음 실행: {next_run.strftime('%Y-%m-%d %H:%M:%S %A')}")

        # 남은 시간 포맷팅
        days = remaining.days
        seconds = remaining.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if days > 0:
            print(f"   남은 시간: {days}일 {hours}시간 {minutes}분")
        elif hours > 0:
            print(f"   남은 시간: {hours}시간 {minutes}분")
        else:
            print(f"   남은 시간: {minutes}분")
    else:
        print(f"   스케줄: {schedule}")

    print()

print("=" * 80)
print("\n💡 참고:")
print("   - Celery Beat을 재시작해야 schedules.json 변경사항이 반영됩니다")
print("   - day_of_week: 0=일요일, 1=월요일, 2=화요일, 3=수요일, 4=목요일, 5=금요일, 6=토요일")
print("   - 테스트 시 minute 값을 조정하여 가까운 시간에 실행되도록 설정하세요")
print("\n✨ Celery Beat 재시작:")
print("   1. 실행 중인 Beat 종료: pkill -f 'celery.*beat'")
print("   2. Beat 재시작: ./run_celery_beat.sh")
print()

EOF
