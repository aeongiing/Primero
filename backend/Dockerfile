FROM python:3.12-slim

# 런타임 환경
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 의존성 먼저 설치 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 앱 소스 복사
COPY app ./app

# Render/Railway 등은 $PORT 를 주입한다. 로컬 기본값 8000.
ENV PORT=8000
EXPOSE 8000

# 셸 형태로 실행해 $PORT 치환이 동작하게 한다.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
