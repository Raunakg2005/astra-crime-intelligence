"""Central configuration for the KSP crime-forecasting ML pipeline."""
from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)

# where versioned models, cards, experiment logs live
REGISTRY_DIR = os.path.join(HERE, "registry")
EXPERIMENTS_LOG = os.path.join(REGISTRY_DIR, "experiments.jsonl")
MLRUNS_DIR = os.path.join(HERE, "mlruns")          # MLflow local store (if installed)

# the trained-model artefacts the inference service loads (champion, promoted here)
SERVING_DIR = os.path.join(BACKEND, "appsail_ml", "models")

RANDOM_SEED = 42

# ---- task definitions --------------------------------------------------------
# We train two supervised models on a district x ISO-week panel:
#   * classifier: will this district be HIGH-RISK next week? (top-quartile volume)
#   * regressor : how many FIRs next week? (count)
RISK_FEATURES = [
    "lag1", "lag2", "lag3", "lag4", "roll4_mean", "roll4_std", "roll8_mean",
    "roll12_mean", "momentum", "heinous_lag1", "clear_rate_lag1", "district_base",
    "month_sin", "month_cos", "woy_sin", "woy_cos",
]

# temporal-CV settings
CV_SPLITS = 5                 # expanding-window walk-forward folds
TEST_WEEKS_FRACTION = 0.15    # final untouched hold-out (most recent weeks)
HIGH_RISK_QUANTILE = 0.75     # label threshold (per district, learnt on train only)

# hyperparameter search budget
SEARCH_ITERS = 20             # RandomizedSearchCV candidates per model family


def ensure_dirs():
    for d in (REGISTRY_DIR, SERVING_DIR):
        os.makedirs(d, exist_ok=True)
