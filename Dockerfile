FROM node:22-bookworm-slim AS frontend
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM rclone/rclone:1.75.1 AS rclone
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data FRONTEND_DIR=/app/frontend/dist
WORKDIR /app
COPY --from=rclone /usr/local/bin/rclone /usr/local/bin/rclone
COPY requirements.lock pyproject.toml ./
COPY telegram_vault/ ./telegram_vault/
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps . \
    && useradd --uid 10001 --create-home vault \
    && mkdir -p /data/db /data/session /data/cache /config/rclone \
    && chown -R vault:vault /data /config/rclone && chmod 700 /data /data/db /data/session /data/cache
COPY --from=frontend /ui/dist ./frontend/dist
USER vault
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=3)"
CMD ["telegram-vault", "serve", "--host", "0.0.0.0", "--port", "8080"]
