FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

# Xvfb 설치 (가상 디스플레이 서버 - Playwright headless=False 지원)
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Xvfb와 함께 실행 (가상 디스플레이로 headless=False 지원)
CMD xvfb-run -a uvicorn app.main:app --host 0.0.0.0 --port 8000
