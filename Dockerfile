FROM python:3.12-slim

WORKDIR /app

# Install the package + dependencies first (better layer caching).
COPY pyproject.toml README.md ./
COPY cloudfit_api ./cloudfit_api
RUN pip install --no-cache-dir .

# Bundled snapshot lives outside the importable package, so point at it explicitly.
COPY data ./data
ENV CLOUDFIT_SNAPSHOT_PATH=/app/data/gcp_snapshot.json

# Run as a non-root user.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Cloud Run sets $PORT; default to 8080 locally.
EXPOSE 8080
CMD ["sh", "-c", "uvicorn cloudfit_api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
