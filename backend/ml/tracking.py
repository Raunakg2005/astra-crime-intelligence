"""Experiment tracking.

Always logs every run to an append-only JSONL ledger (self-contained, deploys on
Catalyst). If MLflow is installed it *also* logs to MLflow so you get the standard
`mlflow ui` experience — but MLflow is optional, never a hard dependency.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from config import EXPERIMENTS_LOG, MLRUNS_DIR, REGISTRY_DIR

try:
    import mlflow
    HAS_MLFLOW = True
except Exception:  # pragma: no cover
    HAS_MLFLOW = False


def _now():
    return datetime.now(timezone.utc).isoformat()


def log_run(run: dict):
    """Append a run record (params + metrics + metadata) to the JSONL ledger."""
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    run = {"logged_at": _now(), **run}
    with open(EXPERIMENTS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(run, default=str) + "\n")


def mlflow_log_run(run_name: str, params: dict, metrics: dict, tags: dict | None = None):
    """Log one self-contained MLflow run (own start/end) — one per trained model, so
    param keys never collide. No-op if MLflow isn't installed; never breaks training."""
    if not HAS_MLFLOW:
        return
    try:
        os.makedirs(MLRUNS_DIR, exist_ok=True)
        uri = "sqlite:///" + os.path.join(MLRUNS_DIR, "mlflow.db").replace("\\", "/")
        mlflow.set_tracking_uri(uri)
        mlflow.set_experiment("ksp-crime-forecast")
        with mlflow.start_run(run_name=f"{run_name}-{_now()}"):
            mlflow.log_params({k: str(v)[:250] for k, v in params.items()})
            mlflow.log_metrics({k: float(v) for k, v in metrics.items()
                                if isinstance(v, (int, float))})
            for k, v in (tags or {}).items():
                mlflow.set_tag(k, v)
    except Exception as e:  # tracking must never break training
        print(f"    (mlflow log skipped: {e})")


def read_history(limit: int = 50):
    if not os.path.exists(EXPERIMENTS_LOG):
        return []
    with open(EXPERIMENTS_LOG, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return rows[-limit:]
