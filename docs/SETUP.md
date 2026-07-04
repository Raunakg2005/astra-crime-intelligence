# Setup & Reproduction Guide

Everything needed to go from a fresh clone to a **fully running Astra platform** — the
synthetic dataset, all trained models, the analytics API, and the dashboard. Written so
any teammate can reproduce it end-to-end.

> The dataset and trained models are **not** committed (they're generated). This guide
> regenerates them deterministically (`--seed 42`), so everyone gets identical results.

---

## 1. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11 or 3.12 | for data generation + ML/analytics |
| Node.js | ≥ 18 (22 recommended) | for the React dashboard |
| Git | any | |
| NVIDIA GPU + CUDA | *optional* | XGBoost auto-uses the GPU if present; CPU works fine otherwise |

Check:
```bash
python --version && node --version && npm --version
```

---

## 2. One-time setup

```bash
git clone <repo-url>
cd "hack 1 datathon"

# Python deps (data + ML/analytics)
python -m pip install -r requirements.txt

# Frontend deps
cd frontend && npm install && cd ..
```

> **Tip (Windows):** if you ever see a `UnicodeEncodeError` when a script prints, run it
> with `set PYTHONIOENCODING=utf-8` (cmd) or `$env:PYTHONIOENCODING="utf-8"` (PowerShell).
> The training CLI and fidelity script already handle this automatically.

---

## 3. Generate the dataset

Creates all 27 FIR-schema tables as CSVs, then a queryable SQLite DB.

```bash
# 40,000 synthetic FIRs over 4 years (deterministic with --seed)
python data/generator/generate.py --cases 40000 --seed 42

# load CSVs -> data/out/ksp.db (mirrors the Catalyst Data Store schema)
python data/build_sqlite.py
```

Output → `data/out/` (git-ignored). Options: `--cases N` (default 12000), `--seed S`,
`--out DIR`.

---

## 4. Train the models (the MLOps pipeline)

All models live in `backend/ml`. Run the CLI **from that folder**.

```bash
cd backend/ml

python cli.py train-all      # trains EVERYTHING (tabular + NLP) — recommended
```

Or run each stage individually:

```bash
python cli.py train          # tabular: high-risk classifier + next-week forecaster + anomaly
python cli.py train-nlp      # NLP: 18-classifier bake-off on BriefFacts text
```

**What `train` does** (crime forecasting):
- builds a district×week panel with lag / rolling / seasonality features
- compares 5 model families (LogReg, RandomForest, HistGBM, GBM, XGBoost-GPU) via
  **expanding-window time-series cross-validation** + randomized hyper-parameter search
- tunes the decision threshold, evaluates on an untouched hold-out
- registers the champion (champion/challenger promotion) and logs to MLflow

**What `train-nlp` does** (crime-text classification):
- cleans text → TF-IDF → **bake-off of 18 classifiers** (Naive-Bayes ×3, LogReg, LinearSVC,
  SGD, PassiveAggressive, Ridge, NearestCentroid, kNN, DecisionTree, RandomForest,
  ExtraTrees, Bagging, AdaBoost, HistGBM, **MLP neural-net**, **XGBoost-GPU**)
- selects the champion by hold-out macro-F1
- **saves every model** to `backend/appsail_ml/models/nlp_all/` and all outputs
  (`nlp_all_models.json`, `nlp_all_predictions.csv`)

Artefacts are written to:
- `backend/ml/registry/<task>/v<N>/` — versioned `model.joblib` + `metadata.json` + `model_card.md`
- `backend/appsail_ml/models/` — the champion artefacts the API serves
- `backend/ml/mlruns/` — MLflow tracking store

Inspect what you trained:
```bash
python cli.py list         # registry: versions + champions per task
python cli.py history      # recent experiment runs
python cli.py card risk_classifier    # print a model card

# browse experiments visually (optional):
mlflow ui --backend-store-uri sqlite:///mlruns/mlflow.db
```

Expected ballpark (seed 42, 40k cases): risk ROC-AUC ≈ 0.70, forecast R² ≈ 0.64,
NLP accuracy ≈ 0.86 / macro-F1 ≈ 0.87.

---

## 5. (Optional) Validate data fidelity

Compares the synthetic data to **real published statistics** (NCRB 2022, Census 2011).

```bash
cd backend/analysis
python fidelity.py         # -> FIDELITY_REPORT.md + fidelity_report.json
```

---

## 6. Run the platform (two terminals)

**Terminal A — analytics API** (FastAPI, port 8000):
```bash
cd backend/appsail_ml
python -m uvicorn app:app --port 8000
# docs at http://127.0.0.1:8000/docs
```

**Terminal B — dashboard** (Vite, port 5173, proxies `/api` → :8000):
```bash
cd frontend
npm run dev
# open http://localhost:5173
```

---

## 7. Full sequence (copy-paste)

```bash
python -m pip install -r requirements.txt
python data/generator/generate.py --cases 40000 --seed 42
python data/build_sqlite.py
cd backend/ml && python cli.py train-all && cd ../..
cd backend/appsail_ml && start python -m uvicorn app:app --port 8000 && cd ../..   # 'start' = Windows; use '&' on macOS/Linux
cd frontend && npm install && npm run dev
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `PermissionError: ... ksp.db ... used by another process` | Stop the API (it holds the DB) before re-running `build_sqlite.py` |
| `UnicodeEncodeError` on Windows | `set PYTHONIOENCODING=utf-8` before the command |
| Port 8000 / 5173 already in use | Kill the old process, or change `--port` (update `frontend/vite.config.ts` proxy to match) |
| XGBoost GPU error | It falls back to CPU automatically; ensure NVIDIA drivers if you want GPU |
| `mlflow` import errors | MLflow is optional — training still runs and logs to the JSONL ledger without it |
| Frontend can't reach API | Make sure the API is running on :8000 first; the dev server proxies `/api` to it |

---

## Regenerate-from-scratch checklist
1. `pip install -r requirements.txt` · `cd frontend && npm install`
2. `python data/generator/generate.py --cases 40000 --seed 42`
3. `python data/build_sqlite.py`
4. `cd backend/ml && python cli.py train-all`
5. `cd backend/analysis && python fidelity.py` *(optional)*
6. Run API (`uvicorn`) + dashboard (`npm run dev`)
