"""Shared HTTP helper for tools that call the Astra analytics API (backend/appsail_ml)."""
import requests

from ..configs import chatbot_config


def api_get(path: str, params: dict | None = None) -> dict:
    """GET a path off the analytics API and return parsed JSON.

    Raises so the agent's tool-calling loop sees the failure instead of
    silently getting an empty result.
    """
    url = f"{chatbot_config.api_base_url}{path}"
    resp = requests.get(url, params=params or {}, timeout=chatbot_config.api_timeout_s)
    resp.raise_for_status()
    return resp.json()
