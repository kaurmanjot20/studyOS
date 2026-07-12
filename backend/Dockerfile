FROM python:3.12-slim

# System deps for parsing/OCR are added in the phase that needs them.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Node.js is required to run MCP servers (npx @modelcontextprotocol/server-*).
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Run migrations then start the API. `entrypoint.sh` keeps startup logic in one place.
# Invoked via bash so it works regardless of the file's exec bit on the host.
CMD ["bash", "entrypoint.sh"]
