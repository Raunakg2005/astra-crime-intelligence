# Catalyst AppSail — custom OCI runtime.
# The managed Python runtime can't fit the scientific ML stack on its tiny writable disk
# (~242 MB) and doesn't install requirements at build, so we bake all deps into the image's
# read-only layers here. Must be built for linux/amd64 (Catalyst requirement).
FROM python:3.11-slim

WORKDIR /app

# Serving dependencies: core analytics stack + the LangChain/Groq AI copilot.
# Disk is not a constraint inside the image, so both fit.
COPY requirements.txt requirements-chatbot.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-chatbot.txt

# Application code + SQLite DB + champion models (frontend, .git, training code, the 18-model
# NLP bake-off, and CSVs are excluded via .dockerignore).
COPY . .

ENV PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1

# Catalyst injects the port to listen on via X_ZOHO_CATALYST_LISTEN_PORT at runtime.
CMD ["sh", "-c", "python3 -m uvicorn main:app --host 0.0.0.0 --port ${X_ZOHO_CATALYST_LISTEN_PORT:-9000}"]
