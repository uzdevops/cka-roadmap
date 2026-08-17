# syntax=docker/dockerfile:1

# ---------- stage 1: build the virtualenv ----------
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

# build-essential and binutils are needed only here; neither reaches the
# final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential binutils \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Trim the virtualenv: the installer itself is not needed at runtime, compiled
# extensions ship with debug symbols we never read, and bytecode caches are
# regenerated on demand. Together this is ~90 MB.
RUN pip uninstall -y pip setuptools wheel 2>/dev/null || true \
    && find /opt/venv -name '*.so' -exec strip --strip-unneeded {} + 2>/dev/null || true \
    && find /opt/venv -name '__pycache__' -type d -prune -exec rm -rf {} + \
    && find /opt/venv -name '*.pyc' -delete \
    && rm -rf /opt/venv/lib/python3.12/site-packages/pip* \
              /opt/venv/lib/python3.12/site-packages/setuptools* \
              /opt/venv/lib/python3.12/site-packages/pkg_resources


# ---------- stage 2: runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# curl is here purely for the compose / Kubernetes healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --create-home app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app alembic.ini pytest.ini entrypoint.sh ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app app ./app
COPY --chown=app:app tests ./tests

RUN chmod +x /app/entrypoint.sh

USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=6 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
