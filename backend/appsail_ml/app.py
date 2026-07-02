"""
KSP Crime Intelligence — analytics API (FastAPI).

Runs locally with:  uvicorn app:app --reload --port 8000
Deploys to Catalyst AppSail (managed Python runtime) unchanged; only the DB layer
(db.py) is swapped from SQLite to Catalyst Data Store.

All heavy analytics are computed on demand here and cached; in production the nightly
Catalyst Cron job (precompute.py) materialises hotspots/trends/risk into Catalyst Cache.
"""
from __future__ import annotations

import json
import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

import analytics as A
import db

app = FastAPI(
    title="KSP Crime Intelligence API",
    version="1.0.0",
    description="Geospatial, network, predictive and anomaly analytics over the KSP FIR database.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten to the Catalyst web-client origin in prod
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "db": db.db_path()}


@app.get("/api/kpis", tags=["overview"])
def get_kpis():
    return A.kpis()


@app.get("/api/districts", tags=["geospatial"])
def get_districts():
    """District choropleth: counts, clearance, heinous share, top crime head."""
    return A.district_summary()


@app.get("/api/hotspots", tags=["geospatial"])
def get_hotspots(
    district_id: int | None = Query(None),
    crime_head: str | None = Query(None),
    days: int | None = Query(None, description="restrict to last N days"),
    eps_m: int = Query(450, description="DBSCAN neighbourhood radius (metres)"),
    min_samples: int = Query(15),
):
    return A.hotspots(district_id, crime_head, days, eps_m, min_samples)


@app.get("/api/trends", tags=["overview"])
def get_trends(
    window_days: int = Query(45),
    z_threshold: float = Query(2.0),
):
    """Emerging-trend / red-zone alerts (z-score vs rolling baseline)."""
    return {"alerts": A.emerging_trends(window_days=window_days, z_threshold=z_threshold)}


@app.get("/api/timeseries", tags=["overview"])
def get_timeseries(
    crime_head: str | None = Query(None),
    district_id: int | None = Query(None),
):
    return A.timeseries(crime_head, district_id)


@app.get("/api/network/communities", tags=["network"])
def get_communities(min_size: int = Query(3), top: int = Query(15)):
    """Louvain communities in the co-offending graph (organised networks)."""
    return A.communities(min_size=min_size, top=top)


@app.get("/api/network/repeat-offenders", tags=["network"])
def get_repeat_offenders(min_cases: int = Query(5), top: int = Query(25)):
    return {"offenders": A.repeat_offenders(min_cases=min_cases, top=top)}


@app.get("/api/network/ego/{name}", tags=["network"])
def get_ego(name: str):
    """Ego network + profile for a single offender (link analysis)."""
    return A.ego_network(name)


@app.get("/api/anomalies", tags=["ai"])
def get_anomalies(contamination: float = Query(0.01), top: int = Query(30)):
    return A.anomalies(contamination=contamination, top=top)


@app.get("/api/risk", tags=["ai"])
def get_risk():
    """Predictive district risk scores (trained GradientBoosting / Zia AutoML)."""
    return {"districts": A.risk_scores()}


@app.get("/api/model-info", tags=["ai"])
def get_model_info():
    """Training metrics for the persisted models (from train.py -> metrics.json)."""
    path = os.path.join(os.path.dirname(__file__), "models", "metrics.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"trained": False, "message": "run train.py to train models"}


@app.get("/", tags=["overview"])
def root():
    return {
        "service": "KSP Crime Intelligence API",
        "docs": "/docs",
        "endpoints": [r.path for r in app.routes if getattr(r, "path", "").startswith("/api")],
    }
