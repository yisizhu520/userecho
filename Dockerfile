# Unified Monolithic Dockerfile
# Builds Frontend + Backend + Nginx + Supervisor in one image

# ==========================================
# Stage 1: Build Frontend
# ==========================================
FROM guergeiro/pnpm:lts-latest-slim AS frontend-builder
WORKDIR /app/front

# Copy source code and install dependencies
COPY front/ .
RUN pnpm install --frozen-lockfile
# 设置构建缓存目录以加速后续构建
RUN --mount=type=cache,target=/app/front/node_modules/.cache \
    pnpm build:antd

# ==========================================
# Stage 2: Build Backend Environment
# ==========================================
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS backend-builder
WORKDIR /app/server

# Install dependencies (utilizing cache)
COPY server/pyproject.toml server/uv.lock ./
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/venv

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-default-groups --group server --no-install-project

# ==========================================
# Stage 3: Final Monolithic Image
# ==========================================
FROM python:3.10-slim-bookworm

# Install Nginx, Supervisor and System Deps
# Replace sources for China (Optional, can be removed if specific to user region)
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Virtual Environment
COPY --from=backend-builder /app/venv /fba/.venv
ENV PATH="/fba/.venv/bin:$PATH"

# Copy Backend Code
WORKDIR /fba/backend
COPY server/ .

# Copy Frontend Build Artifacts
COPY --from=frontend-builder /app/front/apps/web-antd/dist /var/www/fba_ui

# Copy Configurations
COPY deploy/monolith/supervisord.conf /etc/supervisor/supervisord.conf
COPY deploy/monolith/nginx.conf /etc/nginx/nginx.conf

# Prepare Directories
RUN mkdir -p /var/log/fba /var/log/supervisor /var/run \
    && mkdir -p /fba/backend/app/static /fba/backend/static/upload

EXPOSE 80

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
