FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . .

RUN uv sync --frozen --no-editable --no-dev --compile-bytecode

FROM gcr.io/distroless/python3-debian12

EXPOSE 8000/tcp

COPY --from=builder /app/.venv /venv

ENTRYPOINT ["/venv/bin/pantheon-assignment"]