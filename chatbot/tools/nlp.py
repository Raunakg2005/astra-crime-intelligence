"""NLP tools — free-text FIR narrative classification."""
from langchain_core.tools import tool

from ._client import api_get


@tool
def classify_narrative(text: str) -> dict:
    """Classify a free-text FIR narrative (what happened, in the complainant's
    words) into a crime head category, using the trained champion NLP model.
    Use this when the user pastes or describes an incident and wants to know
    what type of crime it is.

    Args:
        text: the FIR narrative / description of the incident.
    """
    return api_get("/api/nlp/classify", {"text": text})
