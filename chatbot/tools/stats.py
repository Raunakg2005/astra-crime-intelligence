"""Overview / stats tools — top-line KPIs, trend alerts, time series."""
from langchain_core.tools import tool

from ._client import api_get


@tool
def get_kpis() -> dict:
    """Get top-line crime KPIs: total cases, cases in the last 30 days vs. the
    previous 30 days (with % change), clearance rate, heinous case count,
    number of districts, active alerts, and the date range the data covers.
    Use this for any "how many / what's the rate / how are we doing" question."""
    return api_get("/api/kpis")


@tool
def get_trends(window_days: int = 45, z_threshold: float = 2.0) -> dict:
    """Get emerging-trend / red-zone alerts: crime categories or districts whose
    recent volume is a statistical outlier (z-score) vs. their rolling baseline.

    Args:
        window_days: size of the rolling baseline window in days.
        z_threshold: minimum z-score to flag as an alert (higher = fewer, stronger alerts).
    """
    return api_get("/api/trends", {"window_days": window_days, "z_threshold": z_threshold})


@tool
def get_timeseries(crime_head: str | None = None, district_id: int | None = None) -> dict:
    """Get the case-count time series, optionally filtered to one crime category
    and/or one district. Use this for "how has X trended over time" questions.

    Args:
        crime_head: optional crime category to filter to (e.g. "Theft").
        district_id: optional district id to filter to.
    """
    return api_get("/api/timeseries", {"crime_head": crime_head, "district_id": district_id})
