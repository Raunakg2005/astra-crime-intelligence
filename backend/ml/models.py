"""Candidate model families + hyperparameter search spaces.

The pipeline trains and cross-validates *several* families per task and keeps the
best — not a single hard-coded estimator. XGBoost is used if installed, otherwise
the sklearn ensembles (always available) are the candidates.
"""
from __future__ import annotations

from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import RANDOM_SEED

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGB = True
except Exception:  # pragma: no cover
    HAS_XGB = False


def _gpu_available() -> bool:
    """True if a CUDA GPU is usable by XGBoost."""
    if not HAS_XGB:
        return False
    try:
        import subprocess
        subprocess.check_output(["nvidia-smi"], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


HAS_GPU = _gpu_available()
XGB_DEVICE = "cuda" if HAS_GPU else "cpu"


def search_n_jobs(name: str) -> int:
    """GPU models fit sequentially (n_jobs=1) so parallel folds don't contend for GPU
    memory; CPU models parallelise across cores."""
    return 1 if (name == "xgboost" and HAS_GPU) else -1


def _pipe(est, scale=False):
    steps = []
    if scale:
        steps.append(("scale", StandardScaler()))
    steps.append(("model", est))
    return Pipeline(steps)


def classifier_candidates():
    """dict: name -> (pipeline, param_distributions for RandomizedSearchCV)."""
    c = {
        "logreg": (
            _pipe(LogisticRegression(max_iter=2000, class_weight="balanced"), scale=True),
            {"model__C": [0.01, 0.1, 0.3, 1.0, 3.0, 10.0]},
        ),
        "random_forest": (
            _pipe(RandomForestClassifier(random_state=RANDOM_SEED, class_weight="balanced_subsample")),
            {"model__n_estimators": [200, 400, 600],
             "model__max_depth": [4, 6, 8, None],
             "model__min_samples_leaf": [1, 3, 5, 10]},
        ),
        "hist_gbm": (
            _pipe(HistGradientBoostingClassifier(random_state=RANDOM_SEED)),
            {"model__max_depth": [3, 4, 6, None],
             "model__learning_rate": [0.03, 0.05, 0.1],
             "model__max_iter": [200, 300, 500],
             "model__l2_regularization": [0.0, 1.0, 5.0]},
        ),
        "grad_boost": (
            _pipe(GradientBoostingClassifier(random_state=RANDOM_SEED)),
            {"model__n_estimators": [200, 300, 500],
             "model__max_depth": [2, 3, 4],
             "model__learning_rate": [0.03, 0.05, 0.1],
             "model__subsample": [0.8, 0.9, 1.0]},
        ),
    }
    if HAS_XGB:
        c["xgboost"] = (
            _pipe(XGBClassifier(random_state=RANDOM_SEED, eval_metric="logloss",
                                tree_method="hist", device=XGB_DEVICE, n_jobs=2)),
            {"model__n_estimators": [200, 400, 600],
             "model__max_depth": [3, 4, 6],
             "model__learning_rate": [0.03, 0.05, 0.1],
             "model__subsample": [0.8, 1.0],
             "model__colsample_bytree": [0.8, 1.0]},
        )
    return c


def regressor_candidates():
    r = {
        "ridge": (
            _pipe(Ridge(random_state=RANDOM_SEED), scale=True),
            {"model__alpha": [0.1, 1.0, 3.0, 10.0, 30.0]},
        ),
        "random_forest": (
            _pipe(RandomForestRegressor(random_state=RANDOM_SEED)),
            {"model__n_estimators": [200, 400, 600],
             "model__max_depth": [4, 6, 8, None],
             "model__min_samples_leaf": [1, 3, 5, 10]},
        ),
        "hist_gbm": (
            _pipe(HistGradientBoostingRegressor(random_state=RANDOM_SEED)),
            {"model__max_depth": [3, 4, 6, None],
             "model__learning_rate": [0.03, 0.05, 0.1],
             "model__max_iter": [200, 300, 500],
             "model__l2_regularization": [0.0, 1.0, 5.0]},
        ),
        "grad_boost": (
            _pipe(GradientBoostingRegressor(random_state=RANDOM_SEED)),
            {"model__n_estimators": [200, 300, 500],
             "model__max_depth": [2, 3, 4],
             "model__learning_rate": [0.03, 0.05, 0.1],
             "model__subsample": [0.8, 0.9, 1.0]},
        ),
    }
    if HAS_XGB:
        r["xgboost"] = (
            _pipe(XGBRegressor(random_state=RANDOM_SEED, tree_method="hist",
                               device=XGB_DEVICE, n_jobs=2)),
            {"model__n_estimators": [200, 400, 600],
             "model__max_depth": [3, 4, 6],
             "model__learning_rate": [0.03, 0.05, 0.1],
             "model__subsample": [0.8, 1.0],
             "model__colsample_bytree": [0.8, 1.0]},
        )
    return r
