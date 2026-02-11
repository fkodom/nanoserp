ARG PY_VERSION=3.12

FROM python:$PY_VERSION-slim
ENV {{REPO_NAME_ALLCAPS}}_VERSION=0.0.0

WORKDIR /app
# Install project dependencies.
COPY ./pyproject.toml /app/pyproject.toml
COPY ./README.md /app/README.md
COPY ./{{REPO_NAME_SNAKECASE}}/__init__.py /app/{{REPO_NAME_SNAKECASE}}/__init__.py
RUN pip install --no-cache-dir -e .
# Copy source code into the container.
COPY ./{{REPO_NAME_SNAKECASE}} /app/{{REPO_NAME_SNAKECASE}}
COPY ./migrations /app/migrations

ENV {{REPO_NAME_ALLCAPS}}_PORT=8000
CMD uvicorn \
    --host 0.0.0.0 \
    --port ${{REPO_NAME_ALLCAPS}}_PORT \
    {{REPO_NAME_SNAKECASE}}.api.main:app