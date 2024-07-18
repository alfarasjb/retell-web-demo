FROM python:3.12.3-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app


RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt
FROM python:3.12.3-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .

EXPOSE 8080
ENV PORT=8080
ENV HOST=0.0.0.0
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
