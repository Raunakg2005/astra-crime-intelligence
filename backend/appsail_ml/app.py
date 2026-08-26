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

# Put this dir (flat imports: analytics, db), backend/ml (models, tracking) and the repo root
# (the chatbot package) on sys.path BEFORE importing them — so the app boots both locally
# (CWD = this dir) AND when launched as "backend.appsail_ml.app:app" from the repo root on
# Catalyst AppSail, where none of these are otherwise importable.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "..", "ml"), os.path.join(_HERE, "..", "..")):
    _p = os.path.abspath(_p)
    if _p not in sys.path:
        sys.path.insert(0, _p)
_ML_DIR = os.path.abspath(os.path.join(_HERE, "..", "ml"))   # referenced by /api/model-registry

import analytics as A
import db
import firs as F

app = FastAPI(
    title="KSP Crime Intelligence API",
    version="1.0.0",
    description="Geospatial, network, predictive and anomaly analytics over the KSP FIR database.",
)

# Response gzip is OPT-IN. Behind the Catalyst AppSail gateway, app-level gzip is BROKEN:
# the gateway forwards the compressed body but strips the `Content-Encoding: gzip` header,
# so the browser tries to read gzip bytes as plain text and every response over the size
# threshold fails with "Failed to fetch" on body read (small ones under the threshold pass,
# which is why it looks intermittent). On Catalyst we therefore leave gzip OFF and let the
# gateway negotiate compression. Set ASTRA_ENABLE_GZIP=1 for a standalone run (e.g. local,
# no gateway) to shrink the large GeoJSON/incidents payloads.
if os.getenv("ASTRA_ENABLE_GZIP", "").strip():
    app.add_middleware(GZipMiddleware, minimum_size=1000)
# CORS is OPT-IN. On Catalyst AppSail the API gateway already injects a permissive
# `access-control-allow-origin: *` onto responses; if we ALSO add one here the response
# carries two Access-Control-Allow-Origin headers, which every browser rejects
# ("Failed to fetch") — so on Catalyst we leave ASTRA_CORS_ORIGINS unset and let the
# gateway handle CORS. Set ASTRA_CORS_ORIGINS (comma-separated origins) only where no such
# gateway sits in front of the app (e.g. local cross-origin dev without the Vite proxy).
_cors_env = os.getenv("ASTRA_CORS_ORIGINS", "").strip()
if _cors_env:
    _cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
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


class FirCreateRequest(BaseModel):
    district_id: int
    police_station_id: int
    crime_subhead_id: int
    gravity_id: int
    category_id: int | None = None
    incident_from: str
    incident_to: str | None = None
    info_received: str | None = None
    complainant_name: str
    complainant_age: int | None = None
    complainant_gender_id: int | None = None
    brief_facts: str


class FirStatusRequest(BaseModel):
    status_id: int


@app.get("/api/firs", tags=["firs"])
def get_firs(
    status_group: str | None = Query(None, pattern="^(open|closed)$"),
    status_id: int | None = Query(None),
    district_id: int | None = Query(None),
    police_station_id: int | None = Query(None),
    crime_head_id: int | None = Query(None),
    crime_subhead_id: int | None = Query(None),
    gravity_id: int | None = Query(None),
    category_id: int | None = Query(None),
    date_from: str | None = Query(None, description="registered on/after, YYYY-MM-DD"),
    date_to: str | None = Query(None, description="registered on/before, YYYY-MM-DD"),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Paginated FIR register — filter by status/district/station/crime taxonomy/gravity/
    date range, free-text search over crime no / case no / district / police station."""
    return F.list_firs(
        status_group, status_id, district_id, police_station_id, crime_head_id,
        crime_subhead_id, gravity_id, category_id, date_from, date_to, q, page, page_size,
    )


@app.get("/api/firs/lookups", tags=["firs"])
def get_firs_lookups():
    """Dropdown data (districts, police stations, crime taxonomy, statuses) for the
    Add-FIR form and the register's filters."""
    return F.lookups()


@app.post("/api/firs", tags=["firs"])
def post_fir(req: FirCreateRequest):
    """Register a new FIR (status starts as 'Under Investigation')."""
    try:
        return F.create_fir(req.model_dump())
    except (ValueError, KeyError) as e:
        raise HTTPException(400, str(e)) from e


@app.patch("/api/firs/{case_master_id}/status", tags=["firs"])
def patch_fir_status(case_master_id: int, req: FirStatusRequest):
    """Close or reopen a FIR by setting its case status."""
    try:
        return F.update_status(case_master_id, req.status_id)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


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


import threading
import time as _time

_chatbot = None
_chatbot_lock = threading.Lock()
_chatbot_warm_secs = None      # how long construction took (seconds), for diagnostics
_chatbot_error = None          # last construction error, for diagnostics


def _get_chatbot():
    """Construct the chatbot once, thread-safely. Importing LangChain/LangGraph and
    building the agent is heavy (10s+ on a small container); doing it lazily inside the
    first /api/chat request blew past AppSail's ~30s request limit, so the bot never
    finished building and every request timed out. We now warm it at startup (see
    _warm_chatbot) — this remains the single construction path, guarded by a lock so a
    request that races the warm-up waits for the same instance instead of building a second."""
    global _chatbot, _chatbot_warm_secs, _chatbot_error
    if _chatbot is None:
        with _chatbot_lock:
            if _chatbot is None:
                from chatbot.setup import ChatBot

                t0 = _time.time()
                try:
                    _chatbot = ChatBot()
                    _chatbot_warm_secs = round(_time.time() - t0, 1)
                except Exception as e:
                    _chatbot_error = f"{type(e).__name__}: {e}"
                    raise
    return _chatbot


@app.on_event("startup")
def _warm_chatbot():
    """Kick off chatbot construction at container boot in a daemon thread, OFF the request
    path, so the first user message doesn't pay the import/build cost. Non-blocking: uvicorn
    binds the port immediately (container stays healthy) while this warms in the background."""
    def _bg():
        try:
            _get_chatbot()
            print(f"[warmup] chatbot ready in {_chatbot_warm_secs}s")
        except Exception as e:            # e.g. missing/invalid GROQ_API_KEY — chat path reports it
            print(f"[warmup] chatbot not ready: {e}")
    threading.Thread(target=_bg, daemon=True).start()


@app.get("/api/chat/diag", tags=["chat"])
def chat_diag():
    """Ops probe for the chatbot: is it warmed, how long did it take, and — critically — can
    this container reach ITSELF at 127.0.0.1:$PORT (which is exactly what the bot's tools do)?"""
    import urllib.request
    port = os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT", "9000")
    out = {
        "chatbot_warmed": _chatbot is not None,
        "warm_secs": _chatbot_warm_secs,
        "last_error": _chatbot_error,
        "groq_key_set": bool(os.getenv("GROQ_API_KEY")),
        "listen_port": port,
    }
    t0 = _time.time()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=6) as r:
            out["self_call"] = {"status": r.status, "secs": round(_time.time() - t0, 2)}
    except Exception as e:
        out["self_call"] = {"error": f"{type(e).__name__}: {e}", "secs": round(_time.time() - t0, 2)}
    return out


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
    # Retry once on Groq's transient `tool_use_failed` (the LLM occasionally emits a
    # malformed tool call — a fresh sample usually parses fine). Other errors (bad key,
    # rate limit, outage) surface immediately as a clean 503 rather than a raw 500.
    last_err = None
    for attempt in range(2):
        try:
            result = bot.agent.invoke(
                {"messages": [{"role": "user", "content": req.message}]},
                config={"configurable": {"thread_id": thread_id}},
            )
            reply = result["messages"][-1].content
            return ChatResponse(response=reply, thread_id=thread_id)
        except Exception as e:
            last_err = e
            if "tool_use_failed" in str(e) and attempt == 0:
                continue          # one clean retry
            raise HTTPException(503, f"Chatbot unavailable: {e}") from e
    raise HTTPException(503, f"Chatbot unavailable: {last_err}")


@app.get("/", tags=["overview"])
def root():
    return {
        "service": "KSP Crime Intelligence API",
        "docs": "/docs",
        "endpoints": [r.path for r in app.routes if getattr(r, "path", "").startswith("/api")],
    }
