"""Geospatial tools — district summaries and hotspot clustering."""
from langchain_core.tools import tool

from ._client import api_get


@tool
def get_districts() -> dict:
    """Get the per-district summary: case counts, clearance rate, heinous-case
    share, and top crime head for every district. Use this for "which district
    is worst / compare districts" questions."""
    return api_get("/api/districts")


@tool
def get_hotspots(
    district_id: int | None = None,
    crime_head: str | None = None,
    days: int | None = None,
) -> dict:
    """Get spatial crime hotspots (DBSCAN clustering of FIR locations), optionally
    filtered to a district, crime category, and/or a recent time window.

    Args:
        district_id: optional district id to restrict to.
        crime_head: optional crime category to restrict to.
        days: optional — restrict to the last N days.
    """
    return api_get(
        "/api/hotspots",
        {"district_id": district_id, "crime_head": crime_head, "days": days},
    )
