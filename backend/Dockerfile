# ── Stage 1: dependencies ──────────────────────────────────────────────────────
FROM python:3.11-slim AS deps

WORKDIR /app

# Copy only the requirements file first so Docker can cache this layer
# independently of any source-code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: runtime ───────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Bring installed packages from the deps stage.
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source.
COPY app/ ./app/

# Render and Railway both inject a PORT environment variable.
# We default to 8000 for local Docker runs.
ENV PORT=8000

# Expose the port for documentation purposes (the actual binding is done at
# runtime via the CMD below using the $PORT variable).
EXPOSE ${PORT}

# Start the FastAPI app with uvicorn, binding to 0.0.0.0 so the container's
# port is reachable from outside, and reading the port from the environment.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
