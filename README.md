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
- [x] **Trained ML + MLOps** — `train.py` pipeline: GradientBoosting high-risk classifier
      (ROC-AUC 0.66) + next-week count regressor (MAE beats naive baseline, R² 0.56) with
      a **temporal train/test split**, persisted `.joblib` artefacts + `metrics.json`,
      served loaded at inference; model card surfaced in the UI
- [x] **React dashboard** — Overview, Geospatial (MapLibre), Link Analysis (Cytoscape),
      Predictive AI; command-center UI wired to live API, builds clean, no console errors
- [ ] AI copilot (QuickML LLM serving + RAG) + PDF reports (SmartBrowz)
- [ ] Catalyst deploy config + CI/CD + auth + alerts

## Run it locally (two terminals)

```bash
# 0. data + trained models (one-time / after data changes)
cd data && python generator/generate.py --cases 12000 && python build_sqlite.py
cd ../backend/appsail_ml && pip install -r ../../requirements.txt && python train.py

# 1. analytics API
python -m uvicorn app:app --port 8000
# 2. dashboard (proxies /api -> :8000)
cd ../../frontend && npm install && npm run dev   # http://localhost:5173
```

## Run the data layer

```bash
cd data
python generator/generate.py --cases 12000 --seed 42
python build_sqlite.py
```
