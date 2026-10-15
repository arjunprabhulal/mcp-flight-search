# Changelog

## 0.3.0

- Works with the current MCP Python SDK (2.x): 0.2.x failed to start once `mcp` 2.x was installed.
- Official `serpapi` client instead of the legacy `google-search-results` package.
- Python 3.10 or later; dependency versions are bounded.
- Structured tool results with an output schema, read-only tool annotations, and validated inputs (IATA codes, ISO dates).
- Flights SerpApi lists only under `other_flights` (often regional carriers) are included after the best ones; reported in #3.
- Errors (no API key, SerpApi errors) come back to the model as clear tool errors.
- Logs go to stderr at INFO level, so they never mix with the stdio protocol, and the API key is never logged.
- `--connection_type http` serves Streamable HTTP (replacing SSE); stdio is the default.
- Tests, CI on Python 3.10 to 3.14, trusted publishing to PyPI, and an MCP Registry entry.
