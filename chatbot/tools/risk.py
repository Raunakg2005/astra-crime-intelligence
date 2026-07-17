"""Predictive risk tools — trained model's forward-looking district risk scores."""
from langchain_core.tools import tool

from ._client import api_get


@tool
def get_district_risk() -> dict:
    """Get predicted next-week risk scores per district from the trained
    high-risk classifier. Use this for "which districts are predicted to be
    high-risk / where should patrols focus next week" questions."""
    return api_get("/api/risk")
