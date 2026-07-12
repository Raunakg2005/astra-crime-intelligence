"""Versioned model registry with champion/challenger promotion.

Every training run writes an immutable, versioned bundle:
    registry/<task>/v<N>/model.joblib
    registry/<task>/v<N>/metadata.json
    registry/<task>/v<N>/model_card.md
A champion pointer (registry/<task>/champion.json) records the promoted version.
A new model is promoted ONLY if it beats the current champion on the hold-out metric
(champion/challenger) — so retraining never silently ships a worse model.

The promoted champion is also copied into appsail_ml/models/ so the inference service
loads it without knowing about the registry internals.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone

import joblib

from config import REGISTRY_DIR, SERVING_DIR


def _task_dir(task: str) -> str:
    d = os.path.join(REGISTRY_DIR, task)
    os.makedirs(d, exist_ok=True)
    return d


def _versions(task: str):
    d = _task_dir(task)
    return sorted(int(x[1:]) for x in os.listdir(d) if x.startswith("v") and x[1:].isdigit())


def next_version(task: str) -> int:
    v = _versions(task)
    return (v[-1] + 1) if v else 1


def champion(task: str):
    p = os.path.join(_task_dir(task), "champion.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def register(task: str, artefact: dict, metadata: dict, card: str,
             primary_metric: str, higher_is_better: bool = True) -> dict:
    """Save a versioned bundle and promote it if it beats the current champion.
    Returns a summary dict {version, promoted, champion_metric, challenger_metric}."""
    version = next_version(task)
    vdir = os.path.join(_task_dir(task), f"v{version}")
    os.makedirs(vdir, exist_ok=True)

    joblib.dump(artefact, os.path.join(vdir, "model.joblib"))
    metadata = {**metadata, "task": task, "version": version,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "primary_metric": primary_metric}
    with open(os.path.join(vdir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)
    with open(os.path.join(vdir, "model_card.md"), "w", encoding="utf-8") as f:
        f.write(card)

    challenger_score = metadata["metrics"][primary_metric]
    champ = champion(task)
    # champ may predate this primary metric (evaluation criterion changed) -> .get, and if the
    # champion can't be scored on the current metric, the challenger defines the new bar → promote.
    champ_score = champ["metrics"].get(primary_metric) if champ else None

    promote = (champ is None or champ_score is None or
               (challenger_score > champ_score if higher_is_better else challenger_score < champ_score))

    if promote:
        _set_champion(task, version, metadata)
        _copy_to_serving(task, vdir)

    return {
        "task": task, "version": version, "promoted": promote,
        "challenger_metric": round(float(challenger_score), 4),
        "champion_metric": round(float(champ_score), 4) if champ_score is not None else None,
        "primary_metric": primary_metric,
    }


def _set_champion(task: str, version: int, metadata: dict):
    with open(os.path.join(_task_dir(task), "champion.json"), "w", encoding="utf-8") as f:
        json.dump({"version": version, "metrics": metadata["metrics"],
                   "promoted_at": datetime.now(timezone.utc).isoformat(),
                   "primary_metric": metadata["primary_metric"]}, f, indent=2, default=str)


# map registry task -> the filename the inference service expects
SERVING_NAMES = {
    "risk_classifier": "risk_classifier.joblib",
    "risk_regressor": "risk_regressor.joblib",
    "anomaly": "anomaly_model.joblib",
}


def _copy_to_serving(task: str, vdir: str):
    os.makedirs(SERVING_DIR, exist_ok=True)
    name = SERVING_NAMES.get(task)
    if name:
        shutil.copyfile(os.path.join(vdir, "model.joblib"), os.path.join(SERVING_DIR, name))


def list_models():
    """Registry overview for the API / UI."""
    out = {}
    if not os.path.isdir(REGISTRY_DIR):
        return out
    for task in os.listdir(REGISTRY_DIR):
        tdir = os.path.join(REGISTRY_DIR, task)
        if not os.path.isdir(tdir):
            continue
        champ = champion(task)
        out[task] = {"versions": _versions(task), "champion": champ}
    return out


def load_champion(task: str):
    champ = champion(task)
    if not champ:
        return None
    vdir = os.path.join(_task_dir(task), f"v{champ['version']}")
    return joblib.load(os.path.join(vdir, "model.joblib"))
