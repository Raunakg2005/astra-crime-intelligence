"""All tools exposed to the chatbot agent, grouped by dashboard area."""
from .geospatial import get_districts, get_hotspots
from .network import get_offender_network, get_repeat_offenders
from .nlp import classify_narrative
from .risk import get_district_risk
from .stats import get_kpis, get_timeseries, get_trends

all_tools = [
    get_kpis,
    get_trends,
    get_timeseries,
    get_districts,
    get_hotspots,
    get_district_risk,
    classify_narrative,
    get_offender_network,
    get_repeat_offenders,
]
