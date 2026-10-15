FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY mcp_flight_search ./mcp_flight_search
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["mcp-flight-search"]
