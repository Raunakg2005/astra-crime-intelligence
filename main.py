"""Catalyst AppSail ASGI entrypoint.

Top-level module so the start command is `python3 -m uvicorn main:app` (the documented
Catalyst pattern). Re-exports the FastAPI analytics app from backend/appsail_ml. The
managed runtime runs the start command without a shell, so app-config.json wraps it in
`sh -c '... ${X_ZOHO_CATALYST_LISTEN_PORT}'` for env-var expansion.
"""
from backend.appsail_ml.app import app  # noqa: F401  (ASGI target for `uvicorn main:app`)
