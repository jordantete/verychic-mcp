FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY verychic_mcp ./verychic_mcp
RUN pip install --no-cache-dir .

ENV PORT=8000
EXPOSE 8000

# Transport HTTP distant ; l'hébergeur fournit $PORT.
CMD ["sh", "-c", "verychic-mcp --transport streamable-http --host 0.0.0.0 --port ${PORT:-8000}"]
