FROM python:3.12.3-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Create virtual environment
RUN python -m venv /app/.venv

# Copy requirements and install dependencies
COPY requirements.txt .
RUN /app/.venv/bin/pip install -r requirements.txt

FROM python:3.12.3-slim-bookworm

WORKDIR /app

# Copy virtual environment and application code
COPY --from=builder /app/.venv /app/.venv
COPY . .

# Ensure the virtual environment's bin directory is in the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the desired port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
