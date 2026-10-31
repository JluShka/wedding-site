FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/data/rsvp.db \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY app.py .
COPY static ./static

# Ответы гостей хранятся в /data — подключайте туда том, чтобы они не пропали
RUN useradd --create-home --uid 1000 web && mkdir -p /data && chown web:web /data
USER web
VOLUME ["/data"]

EXPOSE 8000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --access-logfile - app:app"]
