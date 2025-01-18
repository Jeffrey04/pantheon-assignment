FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . .

RUN uv sync --frozen --no-editable --no-dev --compile-bytecode && \
    # distroless's cpython is in /usr/bin/python
    rm /app/.venv/bin/python && \
    ln -s /usr/bin/python /app/.venv/bin/python

FROM gcr.io/distroless/python3-debian12

EXPOSE 8081/tcp

COPY --from=builder /app/.venv /app/.venv

ENTRYPOINT ["/app/.venv/bin/pantheon-assignment"]