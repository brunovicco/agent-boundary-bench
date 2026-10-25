# Docker Hub multi-platform digest resolved 2026-10-25.
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/tmp/uv-cache MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.4
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev && chown -R 10001:10001 /app
USER 10001:10001
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8100 8300
CMD ["abb", "serve", "--scenario", "http", "--host", "0.0.0.0", "--port", "8100"]
