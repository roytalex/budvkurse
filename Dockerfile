FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/beckend
COPY beckend/requirements-lock.txt /tmp/requirements-lock.txt
RUN pip install --no-cache-dir -r /tmp/requirements-lock.txt && useradd --create-home app
COPY --chown=app:app beckend /app/beckend
COPY --chown=app:app frontend /app/frontend
COPY --chown=app:app assets /app/assets
COPY --chown=app:app vendor /app/vendor
RUN mkdir -p /app/beckend/uploads && chown app:app /app/beckend/uploads
USER app
EXPOSE 8000
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --no-access-log"]
