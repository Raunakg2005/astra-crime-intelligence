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
import sys
import urllib.parse
import urllib.request

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
import uuid

import analytics as A
import db

_ML_DIR = os.path.join(os.path.dirname(__file__), "..", "ml")
if _ML_DIR not in sys.path:
    sys.path.insert(0, _ML_DIR)

_REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

app = FastAPI(
    title="KSP Crime Intelligence API",
    version="1.0.0",
    description="Geospatial, network, predictive and anomaly analytics over the KSP FIR database.",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)   # compress large GeoJSON responses
# CORS: permissive "*" for local dev; in production set ASTRA_CORS_ORIGINS to the Catalyst
# web-client origin(s) (comma-separated) to lock the API down to the dashboard only.
_cors_origins = [o.strip() for o in os.getenv("ASTRA_CORS_ORIGINS", "*").split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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


@app.get("/api/incidents", tags=["geospatial"])
def get_incidents(
    district_id: int | None = Query(None),
    crime_head: str | None = Query(None),
    days: int | None = Query(None),
):
    """All FIRs as GeoJSON points (real coordinates) for native map clustering."""
    return A.incidents(district_id, crime_head, days)


# ---- free-text place search (villages / areas / streets), not just districts ----
_NOMINATIM = "https://nominatim.openstreetmap.org/search"
_KA_VIEWBOX = "73.6,18.6,78.7,11.4"          # west,north,east,south  (Karnataka)
_GEO_CACHE: dict[str, list] = {}             # in-memory memo (per keystroke → 1 upstream call)


@app.get("/api/geocode", tags=["geospatial"])
def geocode(q: str = Query(..., min_length=2, description="place / village / area / street to find")):
    """Free-text place search over Karnataka via OpenStreetMap Nominatim, so the map can
    fly to ANY village, locality or street — not only the 31 districts. Server-side proxy:
    respects Nominatim's policy (identifying User-Agent, bounded to KA) and is cached, so
    on Catalyst it's fronted by Cache/CDN and Nominatim isn't hit per keystroke."""
    key = q.strip().lower()
    if len(key) < 2:
        return {"results": []}
    if key in _GEO_CACHE:
        return {"results": _GEO_CACHE[key]}

    params = urllib.parse.urlencode({
        "q": q, "format": "jsonv2", "limit": 6,
        "countrycodes": "in", "viewbox": _KA_VIEWBOX, "bounded": 1,
    })
    req = urllib.request.Request(
        f"{_NOMINATIM}?{params}",
        headers={"User-Agent": "Astra-KSP-CrimeIntel/1.0 (KSP datathon; raunakg2005@gmail.com)"},
    )
    results: list[dict] = []
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:   # noqa: S310 (fixed https host)
            data = json.load(resp)
        for it in data:
            try:
                lat, lng = float(it["lat"]), float(it["lon"])
            except (KeyError, ValueError, TypeError):
                continue
            parts = [p.strip() for p in it.get("display_name", "").split(",") if p.strip()]
            results.append({
                "name": it.get("name") or (parts[0] if parts else q),
                "context": ", ".join(p for p in parts[1:4] if not p.isdigit()),
                "type": it.get("type") or it.get("category") or "place",
                "lat": lat, "lng": lng,
            })
    except Exception:
        results = []

    if len(_GEO_CACHE) > 500:                # soft cap so the memo can't grow unbounded
        _GEO_CACHE.clear()
    _GEO_CACHE[key] = results
    return {"results": results}


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
    """Serving metrics for the champion models (pipeline -> metrics.json)."""
    path = os.path.join(os.path.dirname(__file__), "models", "metrics.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"trained": False, "message": "run: cd backend/ml && python cli.py train"}


@app.get("/api/model-registry", tags=["ai"])
def get_model_registry():
    """MLOps view: registered versions, champion per task, selected family, the
    time-series-CV leaderboard of families compared, and pipeline capabilities."""
    reg_dir = os.path.join(_ML_DIR, "registry")
    out = {"tasks": {}, "pipeline": {}}
    try:
        import models as ml_models  # ml/models.py -> capability flags
        out["pipeline"] = {"xgboost": ml_models.HAS_XGB, "gpu": ml_models.HAS_GPU,
                           "device": ml_models.XGB_DEVICE}
    except Exception:
        pass
    try:
        import tracking
        out["pipeline"]["mlflow"] = tracking.HAS_MLFLOW
    except Exception:
        pass
    if not os.path.isdir(reg_dir):
        return out
    for task in sorted(os.listdir(reg_dir)):
        tdir = os.path.join(reg_dir, task)
        champ = os.path.join(tdir, "champion.json")
        if not (os.path.isdir(tdir) and os.path.exists(champ)):
            continue
        cj = json.load(open(champ))
        v = cj["version"]
        md = json.load(open(os.path.join(tdir, f"v{v}", "metadata.json")))
        out["tasks"][task] = {
            "champion_version": v,
            "versions": [int(x[1:]) for x in os.listdir(tdir) if x.startswith("v") and x[1:].isdigit()],
            "family": md.get("family"),
            "metrics": md.get("metrics"),
            "cv": md.get("cv"),
            "n_train": md.get("n_train"),
            "n_holdout": md.get("n_holdout"),
        }
    return out


@app.get("/api/nlp/model-info", tags=["nlp"])
def nlp_model_info():
    """NLP crime-text classifier metrics + model bake-off leaderboard."""
    return A.nlp_model_info()


@app.get("/api/nlp/classify", tags=["nlp"])
def nlp_classify(
    text: str = Query(..., description="FIR BriefFacts narrative to classify"),
    model: str | None = Query(None, description="optional: run a specific saved model"),
):
    """Classify a free-text FIR narrative into a crime head + extract entities.
    Pass ?model=<name> to run any of the 18 saved models instead of the champion."""
    return A.nlp_classify(text, model)


@app.get("/api/nlp/models", tags=["nlp"])
def nlp_all_models():
    """Full comparison of ALL saved NLP models (metrics + per-class F1)."""
    return A.nlp_all_models()


@app.get("/api/nlp/clusters", tags=["nlp"])
def nlp_clusters():
    """Unsupervised modus-operandi clusters over the narratives."""
    return A.nlp_mo_clusters()


_chatbot = None


def _get_chatbot():
    """Lazily construct the chatbot so a missing/bad GROQ_API_KEY only breaks
    /api/chat, not the whole analytics API."""
    global _chatbot
    if _chatbot is None:
        from chatbot.setup import ChatBot

        _chatbot = ChatBot()
    return _chatbot


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str


@app.post("/api/chat", tags=["chat"])
def chat(req: ChatRequest) -> ChatResponse:
    """Talk to the Astra analytics assistant (LangGraph agent over Groq, with
    tools onto this same API). Pass back the returned thread_id on subsequent
    calls to keep conversation memory within a session."""
    if not req.message.strip():
        raise HTTPException(400, "message must not be empty")
    try:
        bot = _get_chatbot()
    except Exception as e:
        raise HTTPException(503, f"Chatbot unavailable: {e}") from e

    thread_id = req.thread_id or str(uuid.uuid4())
    result = bot.agent.invoke(
        {"messages": [{"role": "user", "content": req.message}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    reply = result["messages"][-1].content
    return ChatResponse(response=reply, thread_id=thread_id)


@app.get("/", tags=["overview"])
def root():
    return {
        "service": "KSP Crime Intelligence API",
        "docs": "/docs",
        "endpoints": [r.path for r in app.routes if getattr(r, "path", "").startswith("/api")],
    }
