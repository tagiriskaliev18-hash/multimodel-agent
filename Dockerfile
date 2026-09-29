# ========================================================
# ⚡ AI Duo & Multi-Model Gateway Docker Application Image
# Adaptive to Nous Hermes, OpenAI (GPT-4o), Groq & Ollama
# ========================================================

FROM python:3.12-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copy application modules and static assets
COPY server /app/server
COPY ai-chat /app/ai-chat
COPY portal /app/portal
COPY tools /app/tools

# Create non-root user for security
RUN adduser --disabled-password --gecos "" aiduouser && \
    chown -R aiduouser:aiduouser /app
USER aiduouser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/healthz || exit 1

CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
