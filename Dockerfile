ARG PY_VERSION=3.12

FROM python:$PY_VERSION-slim
ENV NANOSERP_VERSION=0.0.0

WORKDIR /app
# Install project dependencies.
COPY ./pyproject.toml /app/pyproject.toml
COPY ./README.md /app/README.md
COPY ./nanoserp/__init__.py /app/nanoserp/__init__.py
RUN pip install --no-cache-dir -e .
# Copy source code into the container.
COPY ./nanoserp /app/nanoserp
COPY ./migrations /app/migrations

ENV NANOSERP_PORT=8000
CMD uvicorn \
    --host 0.0.0.0 \
    --port $NANOSERP_PORT \
    nanoserp.api.main:app