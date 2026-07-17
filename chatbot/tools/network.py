"""Network / link-analysis tools — offender connections and repeat offenders."""
from urllib.parse import quote

from langchain_core.tools import tool

from ._client import api_get


@tool
def get_offender_network(name: str) -> dict:
    """Get the ego network (direct co-offending connections) and profile for a
    single named offender. Use this for "who is X connected to / show me X's
    network" questions.

    Args:
        name: the offender's name, as it appears in case records.
    """
    return api_get(f"/api/network/ego/{quote(name, safe='')}")


@tool
def get_repeat_offenders(min_cases: int = 5, top: int = 25) -> dict:
    """Get the list of repeat offenders — people linked to multiple cases —
    ranked by case count. Use this for "who are the repeat offenders" questions.

    Args:
        min_cases: minimum number of cases an offender must appear in to be included.
        top: max number of offenders to return.
    """
    return api_get("/api/network/repeat-offenders", {"min_cases": min_cases, "top": top})
