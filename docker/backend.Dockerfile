FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/packages/backend
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

ARG UID=1000
ARG GID=1000

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --non-unique --gid "${GID}" app \
    && useradd --gid "${GID}" --uid "${UID}" --create-home --shell /bin/bash app

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir uv

WORKDIR /app/packages/backend

COPY packages/backend/pyproject.toml packages/backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=app:app packages/backend /app/packages/backend

USER app:app
WORKDIR /app/packages/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
