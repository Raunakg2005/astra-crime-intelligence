# Astra — Complete Project Documentation

**AI-Driven Crime Analytics & Intelligence Platform for the Karnataka State Police (KSP) /
State Crime Records Bureau (SCRB).** Hack2skill Datathon 2026.

This is the full technical reference. For a quick tour see [README](../README.md); to
reproduce see [SETUP](SETUP.md); for numbers see [RESULTS](RESULTS.md).

## Table of Contents
1. [Overview & Problem](#1-overview--problem)
2. [System Architecture](#2-system-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Data Layer](#4-data-layer)
5. [Analytics & ML Service](#5-analytics--ml-service)
6. [MLOps Training Pipeline](#6-mlops-training-pipeline)
7. [NLP Crime-Text Pipeline](#7-nlp-crime-text-pipeline)
8. [Fidelity Evaluation](#8-fidelity-evaluation)
9. [API Reference](#9-api-reference)
10. [Frontend](#10-frontend)
11. [Deployment (Zoho Catalyst)](#11-deployment-zoho-catalyst)
12. [Design Decisions](#12-design-decisions)
13. [Limitations, Ethics & Roadmap](#13-limitations-ethics--roadmap)

---

## 1. Overview & Problem

KSP holds extensive crime records but the analytical ecosystem suffers from **data silos and
Excel-based reporting**, **no AI-driven analytics**, **fragmented information** at SCRB, and
**reactive policing**. Astra converts the FIR database into:

- **Advanced visualization** — interactive dashboards + geospatial maps of crime clusters.
- **Network & link analysis** — connecting suspects, victims, locations to reveal organised
  crime and recurring Modus Operandi (MO).
- **Predictive & anomaly intelligence** — forecasting high-risk areas, flagging deviant cases.

Because real FIR microdata is confidential, Astra runs on a **schema-faithful synthetic
dataset** (privacy-by-construction) that is validated against real published statistics.

---

## 2. System Architecture

```
 ┌─────────────────────┐     ┌──────────────────────────┐     ┌────────────────────┐
 │  Data Layer         │     │  ML / MLOps (backend/ml) │     │  Analytics API     │
 │  generator + SQLite │────▶│  features → CV model      │────▶│  FastAPI           │
 │  (27-table schema)  │     │  selection → registry     │     │  (Catalyst AppSail)│
 └─────────────────────┘     │  → MLflow → champions     │     └─────────┬──────────┘
           │                 └──────────────────────────┘               │ /api
           │                                                             ▼
           │                                              ┌────────────────────────────┐
           └─────────────────────────────────────────────│  React SPA (Web Hosting)   │
                                                          │  Overview · Geo · Network  │
                                                          │  Predictive · NLP          │
                                                          └────────────────────────────┘
```

**Flow:** the generator produces the FIR dataset → SQLite (mirrors Catalyst Data Store). The
MLOps pipeline trains/validates/registers models. The FastAPI service reads the DB + loads the
champion models and exposes analytics over `/api`. The React dashboard consumes `/api`.

**Languages/runtimes:** Python 3.12 (data, ML, API), TypeScript/React (UI), SQLite locally
(Catalyst Data Store in production).

---

## 3. Repository Structure

```
data/
  generator/reference.py   real KA ground truth (districts, geo, acts/sections, taxonomy,
                           narrative templates, entity vocab)
  generator/generate.py    the synthetic FIR generator (stdlib only)
  build_sqlite.py          CSV → SQLite loader (schema + indexes)
  out/                     generated CSVs + ksp.db  (git-ignored)

backend/
  appsail_ml/
    db.py                  cached denormalised dataframes from SQLite
    analytics.py           all analytics + model-serving logic
    app.py                 FastAPI app (endpoints)
    models/                served champion artefacts + metrics json  (binaries git-ignored)
  ml/
    config.py              paths, feature list, CV settings
    data.py                data loading + validation gates + fingerprint
    features.py            district×week panel + lag/rolling/seasonal features
    models.py              candidate model families + search spaces (GPU-aware)
    evaluate.py            metrics, thresholds, model-card generation
    tracking.py            MLflow (sqlite) + JSONL experiment ledger
    registry.py            versioned registry + champion/challenger promotion
    pipeline.py            tabular training orchestration
    nlp.py                 NLP text pipeline (18-model bake-off)
    cli.py                 train | train-nlp | train-all | list | history | card
    registry/              versioned metadata + model cards  (joblib git-ignored)
    mlruns/                MLflow store  (git-ignored)
  analysis/
    reference_real.py      real published stats (NCRB 2022, Census 2011) — cited
    fidelity.py            synthetic-vs-real fidelity evaluation
    FIDELITY_REPORT.md     generated report

frontend/
  src/api.ts               typed API client + crime-head colour map
  src/components/          Layout, ui (KpiCard, Section, badges…)
  src/pages/               Overview, Geospatial, Network, Predictive, NlpIntel
  vite.config.ts           dev server + /api proxy

docs/                      SETUP · RESULTS · DOCUMENTATION · PAPER_OUTLINE
```

---

## 4. Data Layer

### 4.1 The FIR schema (27 tables)

Faithful implementation of the official Police FIR ER diagram.

**Transaction tables**
- `CaseMaster` — one row per FIR (CrimeNo, CaseNo, dates, FKs to station, category, gravity,
  crime head/sub-head, status, court, registering officer).
- `Inv_OccuranceTime` — 1:1 with a case: incident timestamps, latitude/longitude, `BriefFacts`.
- `ComplainantDetails`, `Victim`, `Accused` — parties to a case.
- `ActSectionAssociation` — legal acts & sections invoked per case.
- `ArrestSurrender` + `inv_arrestsurrenderaccused` — arrest/surrender events (junction to accused).
- `ChargesheetDetails` — chargesheet records.

**Master / lookup tables**
- Geography: `State`, `District`, `Unit` (police stations), `UnitType`.
- Org: `Employee`, `Rank`, `Designation`, `Court`.
- Taxonomy: `CrimeHead` (8 major heads) → `CrimeSubHead` (37 sub-heads), `CrimeHeadActSection`.
- Legal: `Act`, `Section`.
- Case lookups: `CaseCategory`, `GravityOffence`, `CaseStatusMaster`.
- Person lookups: `ReligionMaster`, `CasteMaster`, `OccupationMaster`.

**CrimeNo format** (18 digits): `Category(1) + District(4) + Unit(4) + Year(4) + Serial(5)`.
A running serial is maintained per (station, category, year). `CaseNo` = `Year(4) + Serial(5)`.

### 4.2 The synthetic generator (`generate.py`)

Stdlib-only. Emits every table as CSV. Realistic by seeding **real** Karnataka ground truth
(31 districts + geo-centroids, IPC/NDPS/etc. acts & sections, NCRB crime-head taxonomy) and by
**planting signal** so every analytics feature has something to find:

| Signal | Mechanism |
|---|---|
| Geospatial hotspots | ~68% of incidents cluster tightly (~280 m) around per-district hotspot centres |
| Spatiotemporal | night-hour skew for burglary/robbery/snatching/NDPS |
| Emerging trend | planted **Chain-Snatching spike in Bengaluru** in the last ~45 days |
| Temporal structure | per-(district, week) **intensity field** = base-rate × trend × seasonality × **AR(1) momentum** → makes forecasting learnable |
| Repeat offenders | closed offender pool with stable MO, heavy-tail activity, reused across cases/districts |
| Networks | co-offending "gangs" that appear together → communities |
| Signal vs noise | a realistic share of one-off / first-time accused |
| NLP corpus | `BriefFacts` narratives that describe incidents (weapons/vehicles/items/amounts) **without naming the crime** |

**Calibration to real marginals** (NCRB 2022): crimes-against-women sub-head composition,
women-crime chargesheeting rate (~82.8%), and district volume ∝ population.

Key knobs live near the top of `generate()` and in `reference.py` (`SUBHEAD_WEIGHTS`,
hotspot spread, offender-pool size, `p_known`, AR/trend/seasonality coefficients).

### 4.3 SQLite build (`build_sqlite.py`)

Loads CSVs into `ksp.db` with primary keys and analytics indexes (dates, district, sub-head,
geo, accused name). The schema mirrors the Catalyst Data Store; the same SQL ports over.

---

## 5. Analytics & ML Service (`backend/appsail_ml`)

### 5.1 `db.py`
Cached (`lru_cache`) denormalised dataframes: `load_cases()` (one row per FIR with geography,
taxonomy, time, status joined) and `load_accused()` (accused joined to case geography). Reads
`data/out/ksp.db` (override via `KSP_DB` env var).

### 5.2 `analytics.py` — the algorithms
| Function | Method |
|---|---|
| `kpis` | headline counts, clearance, month-over-month change |
| `district_summary` | per-district counts, clearance, heinous share, top head (choropleth) |
| `hotspots` | **DBSCAN** (haversine metric) clustering + time-of-day profile + intensity |
| `emerging_trends` | **z-score** of recent window vs rolling baseline (red-zone alerts) |
| `communities` | co-offending graph → **Louvain** community detection |
| `repeat_offenders`, `ego_network` | repeat-offender profiles + ego graph for one offender |
| `anomalies` | **Isolation Forest** over case features (loads trained model) |
| `risk_scores` | forecast-based district risk (loads trained regressor + classifier) |
| `timeseries` | monthly series + day-of-week × hour matrix |
| `nlp_classify`, `nlp_all_models`, `nlp_mo_clusters` | NLP serving (§7) |

Trained models are loaded (not re-fit) via `_load_model`; if absent, functions fall back to
on-the-fly computation. Feature engineering for risk reuses `backend/ml/features.py` so
**training and serving never drift**.

### 5.3 `app.py`
FastAPI app with CORS, wrapping `analytics.py`. See the [API Reference](#9-api-reference).

---

## 6. MLOps Training Pipeline (`backend/ml`)

A real pipeline, not one-shot fitting. Run: `cd backend/ml && python cli.py train`.

**Stages:** validate data → engineer features → **model selection** (multi-family,
RandomizedSearch over **expanding-window time-series CV**) → F1-optimal threshold → **untouched
temporal hold-out** evaluation → **register + champion/challenger promotion** → experiment
tracking (MLflow + JSONL) → auto model card.

**Two supervised tasks** on a district×week panel:
- *High-risk classifier* — will a district be top-quartile next week? (families: LogReg, RF,
  HistGBM, GBM, XGBoost-GPU). Selected by CV ROC-AUC.
- *Volume regressor* — next-week FIR count (families: Ridge, RF, HistGBM, GBM, XGBoost-GPU).
  Selected by CV MAE; reported against a naive-persistence baseline.
- *Anomaly* — Isolation Forest (unsupervised), versioned like the others.

**Feature set** (`features.py`): lags 1–4, rolling mean/std (4/8/12 weeks), momentum,
heinous-lag, clearance-rate-lag, district base rate, month & week-of-year seasonality (sin/cos).

**Model registry** (`registry.py`): each run writes `registry/<task>/v<N>/{model.joblib,
metadata.json, model_card.md}`; a `champion.json` pointer records the promoted version; a new
model is promoted **only if it beats the incumbent** on the hold-out metric, and the champion
is copied to `appsail_ml/models/` for serving.

**Tracking** (`tracking.py`): every run appends to `registry/experiments.jsonl`; if MLflow is
installed it also logs to a local SQLite store (`mlruns/`, browse with `mlflow ui`).

**GPU:** `models.py` detects an NVIDIA GPU and sets XGBoost `device="cuda"` (CPU fallback).

**CLI** (`cli.py`): `train`, `train-nlp`, `train-all`, `list`, `history`, `card <task>`. On
Catalyst this CLI is the unit a **Cron** job invokes for scheduled retraining.

Results: see [RESULTS.md](RESULTS.md).

---

## 7. NLP Crime-Text Pipeline (`backend/ml/nlp.py`)

Classify the crime **head** (8 classes) from the free-text `BriefFacts` narrative — a genuine
task because narratives never name the crime category.

**Stages:** clean text (lowercase, strip digits/punct, stopwords) → **TF-IDF** (1–2 grams,
20k features) → **bake-off of 18 classifiers** → select champion by hold-out macro-F1.

**Models:** MultinomialNB, ComplementNB, BernoulliNB, LogReg, LinearSVC, SGD, PassiveAggressive,
Ridge, NearestCentroid, kNN, DecisionTree, RandomForest, ExtraTrees, Bagging, AdaBoost, HistGBM,
**MLP (neural net)**, **XGBoost (GPU)**. Dense models use TF-IDF→TruncatedSVD(200).

**Every model is saved** to `models/nlp_all/*.joblib`; all outputs to `nlp_all_models.json`
(metrics + per-class F1) and `nlp_all_predictions.csv` (all 18 models' test predictions). Any
model is runnable via `/api/nlp/classify?model=<name>`.

**Also:** rule-based **entity extraction** (weapons / vehicles / stolen items / amounts /
contraband) and **MiniBatchKMeans MO clustering** over narratives (top terms per cluster).

Maps to Catalyst **Zia Text Analytics / QuickML** in production.

---

## 8. Fidelity Evaluation (`backend/analysis`)

Validates the synthetic data against **real published statistics** — the credibility core for
a paper. `reference_real.py` holds cited real data (NCRB *Crime in India 2022* Karnataka
figures; Census 2011 district populations). `fidelity.py` computes:

| Check | Type | Result |
|---|---|---|
| District crime ↔ Census population (Spearman) | calibrated | 0.777 ✅ |
| Women-crime composition vs NCRB (TVD) | calibrated | 0.009 ✅ |
| Women chargesheeting vs 82.8% | calibrated | Δ0.023 ✅ |
| Weekly momentum (lag-1 autocorrelation) | calibrated | 0.642 ✅ |
| Co-offending modularity (Louvain Q) | emergent | 0.631 ✅ |
| Offender concentration (Gini) | emergent | 0.496 ⚠️ (FIR-level expected lower) |

It **distinguishes calibrated from emergent** properties and reports divergences honestly.
Run: `cd backend/analysis && python fidelity.py`. Full write-up in
[FIDELITY_REPORT.md](../backend/analysis/FIDELITY_REPORT.md) and [PAPER_OUTLINE.md](PAPER_OUTLINE.md).

---

## 9. API Reference

Base URL (local): `http://127.0.0.1:8000`. Interactive docs at `/docs`. All responses JSON.

| Method · Path | Query params | Returns |
|---|---|---|
| `GET /health` | — | service status + DB path |
| `GET /api/kpis` | — | totals, clearance %, MoM change, active alerts |
| `GET /api/districts` | — | per-district choropleth data (counts, clearance, top head, lat/lng) |
| `GET /api/hotspots` | `district_id?`, `crime_head?`, `days?`, `eps_m?`, `min_samples?` | DBSCAN clusters (centroid, count, peak hour, night %, intensity) |
| `GET /api/trends` | `window_days?`, `z_threshold?` | emerging-trend / red-zone alerts |
| `GET /api/timeseries` | `crime_head?`, `district_id?` | monthly series + day-of-week×hour matrix |
| `GET /api/network/communities` | `min_size?`, `top?` | Louvain communities (members, districts, MO) |
| `GET /api/network/repeat-offenders` | `min_cases?`, `top?` | repeat-offender profiles |
| `GET /api/network/ego/{name}` | — | ego network (nodes/edges) + profile for an offender |
| `GET /api/anomalies` | `contamination?`, `top?` | Isolation-Forest flagged cases + reasons |
| `GET /api/risk` | — | predictive district risk (score, predicted next-week, probability) |
| `GET /api/model-info` | — | champion tabular-model metrics (`metrics.json`) |
| `GET /api/model-registry` | — | registry: versions, champions, CV leaderboard, GPU/MLflow flags |
| `GET /api/nlp/model-info` | — | NLP champion metrics + leaderboard |
| `GET /api/nlp/classify` | `text` (req), `model?` | crime-head prediction (top-3 + confidence) + entities |
| `GET /api/nlp/models` | — | full comparison of all 18 saved NLP models |
| `GET /api/nlp/clusters` | — | modus-operandi clusters (top terms, size, dominant head) |

---

## 10. Frontend (`frontend/`)

React 18 + Vite + TypeScript + Tailwind. Dark "command-center" theme. `src/api.ts` is a typed
Axios client; `HEAD_COLORS` gives crime heads consistent colours across views.

**Pages** (`src/pages/`):
- **Overview** — KPIs, emerging-trend alerts, monthly volume (Recharts area), crime composition, top districts.
- **Geospatial** — MapLibre GL map (free CARTO dark tiles), district drill-down, DBSCAN hotspot layer with pulsing red-zones, crime-head filter.
- **Network** (Link Analysis) — Cytoscape ego graph, repeat-offender list, Louvain community cards.
- **Predictive** — risk-landscape scatter, district risk ranking, anomaly radar, **model card** (family, CV leaderboard, GPU/MLflow badges, metrics).
- **NlpIntel** (NLP Text AI) — live classifier (predictions + extracted entities) with a per-model selector, 18-model leaderboard, MO clusters.

**Dev:** `npm run dev` (port 5173) proxies `/api` → `:8000` (`vite.config.ts`). Build: `npm run build`.

---

## 11. Deployment (Zoho Catalyst)

Deployment on Catalyst is **mandatory** for the datathon; each capability maps to its service:

| Capability | Catalyst service |
|---|---|
| React SPA hosting | Web Client Hosting |
| Serverless backend logic | Serverless Functions + API Gateway |
| Python ML/analytics service | AppSail (managed runtime) |
| Relational DB (FIR schema) | Data Store |
| Predictive tabular ML | Zia AutoML |
| LLM/RAG + no-code ML | QuickML |
| OCR / text analytics | Zia Services |
| Auth (RBAC) · Cache · Object storage | Authentication · Cache · Stratus |
| Scheduled retraining | Cron (invokes `cli.py train`) |
| Real-time spike alerts | Signals + Event Functions |
| Report generation (PDF) | SmartBrowz |
| Email / push alerts | Mail · Push Notifications |
| CI/CD | Pipelines |

The local stack is built to mirror this: SQLite ⇄ Data Store, FastAPI ⇄ AppSail, Vite SPA ⇄
Web Hosting, the training CLI ⇄ Cron.

---

## 12. Design Decisions

- **Synthetic data, not scraped/real** — real FIR microdata is confidential; a schema-faithful,
  seed-controlled, privacy-preserving synthetic dataset makes the work shareable and reproducible.
- **Rule-based generator with real calibration** — fast, transparent, and calibrated to NCRB
  marginals; the fidelity suite quantifies the gap and motivates a future learned generator.
- **Time-series CV + temporal hold-out** — the only correct evaluation for forecasting (never
  train on the future).
- **Champion/challenger registry** — retraining never silently ships a worse model.
- **Shared feature code between train & serve** — eliminates train/serve skew.
- **Every NLP model saved** — reproducibility + lets reviewers inspect any model.
- **Honest reporting** — accuracy is not used as the headline for imbalanced tasks; divergences
  in fidelity are reported, not hidden.

---

## 13. Limitations, Ethics & Roadmap

**Limitations** — data is synthetic (results are not empirical crime findings); the generator
is rule-based (several marginals hand-calibrated); offender concentration sits below the
career-offender range; templated narratives limit NLP linguistic diversity.

**Ethics** — predictive policing risks bias, feedback loops and over-policing. Astra is
decision-support, **not** automated enforcement: synthetic-only data, transparent model cards
and open metrics, human-in-the-loop framing, and an explicit non-goal of individual-level
predictive policing. Fairness auditing is required before any real-data use.

**Roadmap**
- AI copilot (QuickML LLM serving + RAG over IPC & case facts) + PDF reports (SmartBrowz).
- Full Catalyst deployment config + CI/CD (Pipelines) + Auth (RBAC) + Cron/Signals alerts.
- Replace the rule-based generator with a **learned model (SDV/CTGAN)** on a real seed, and
  re-validate with the fidelity suite.

---

*See also: [README](../README.md) · [SETUP](SETUP.md) · [RESULTS](RESULTS.md) ·
[PAPER_OUTLINE](PAPER_OUTLINE.md) · [FIDELITY_REPORT](../backend/analysis/FIDELITY_REPORT.md) ·
[data/README](../data/README.md)*
