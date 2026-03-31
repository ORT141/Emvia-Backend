FROM python:3.11-alpine AS build
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apk add --no-cache --virtual .build-deps \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev \
    musl-dev \
    cargo

RUN python -m pip install --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && rm -rf /root/.cache

COPY app ./app

FROM python:3.11-alpine AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app

COPY --from=build /install /usr/local
COPY --from=build /app /app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
