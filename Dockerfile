# Stage 1: install exact runtime dependencies into a temporary prefix.
FROM python:3.11.11-slim-bookworm AS builder
WORKDIR /build
COPY requirements-runtime.txt .
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements-runtime.txt

# Stage 2: keep only runtime dependencies, source code, and trained model.
FROM python:3.11.11-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000
WORKDIR /app
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
COPY --from=builder /install /usr/local
COPY src ./src
COPY model.joblib ./model.joblib
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
