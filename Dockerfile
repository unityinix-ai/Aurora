FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && groupadd --system --gid 10001 aurora \
    && useradd --system --uid 10001 --gid aurora --home-dir /app aurora \
    && mkdir -p /data \
    && chown -R aurora:aurora /app /data

COPY --chown=aurora:aurora . .
USER 10001:10001

EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
