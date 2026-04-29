FROM python:3.12-slim-bookworm AS build_base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV USERNAME=appify_user
RUN groupadd -g 10010 $USERNAME \
 && useradd -u 10010 -g 10010 -m -d /home/$USERNAME $USERNAME

WORKDIR /home/$USERNAME

COPY --chown=$USERNAME:$USERNAME pyproject.toml uv.lock* ./
COPY --chown=$USERNAME:$USERNAME src ./src

RUN uv sync --no-dev


FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

ENV USERNAME=appify_user
RUN groupadd -g 10010 $USERNAME \
 && useradd -u 10010 -g 10010 -m -d /home/$USERNAME $USERNAME

WORKDIR /home/$USERNAME

COPY --from=build_base --chown=$USERNAME:$USERNAME /home/$USERNAME/.venv ./.venv
COPY --chown=$USERNAME:$USERNAME src ./src

USER $USERNAME

ENV PATH=/home/$USERNAME/.venv/bin:$PATH \
    PYTHONPATH=/home/$USERNAME/src

EXPOSE 8080

CMD ["gunicorn", "appify_connector.main:app", \
     "--workers", "3", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", \
     "--timeout", "60", \
     "--keep-alive", "120"]
