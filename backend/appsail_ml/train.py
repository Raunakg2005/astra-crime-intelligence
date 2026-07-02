"""
Model training pipeline for KSP Crime Intelligence (MLOps entry point).

Trains, evaluates (with a proper TEMPORAL train/test split so we never leak the
future), and PERSISTS three model artefacts consumed by the inference service:

  1. risk_classifier.joblib  — predicts whether a district will be HIGH-RISK next week
                               (GradientBoosting, district-week panel + lag features)
  2. risk_regressor.joblib   — predicts next-week FIR count per district
  3. anomaly_model.joblib    — IsolationForest over case features (fit once, served loaded)

Metrics are written to models/metrics.json and printed. On Catalyst this pipeline maps
to Zia AutoML (tabular training) / QuickML pipelines; the artefacts + metrics are the
same contract. Re-run any time after regenerating data:

    python train.py
"""
from __future__ import annotations

import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    IsolationForest,
)
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

import db

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

RISK_FEATURES = [
    "lag1", "lag2", "lag3", "lag4", "roll4_mean", "roll4_std", "roll8_mean",
    "heinous_lag1", "clear_rate_lag1", "district_base", "month_sin", "month_cos",
]


# ---------------------------------------------------------------------------
# feature engineering — district x ISO-week panel with lag features
# ---------------------------------------------------------------------------

def _panel_raw() -> pd.DataFrame:
    df = db.load_cases().copy()
    df["week"] = df["RegDate"].dt.to_period("W").dt.start_time
    grp = df.groupby(["DistrictID", "DistrictName", "week"])
    panel = grp.agg(
        count=("CaseMasterID", "size"),
        heinous=("heinous", "sum"),
        cleared=("cleared", "sum"),
    ).reset_index()

    # dense weekly grid per district (fill missing weeks with 0)
    all_weeks = pd.date_range(panel["week"].min(), panel["week"].max(), freq="W-MON")
    frames = []
    for (did, dname), g in panel.groupby(["DistrictID", "DistrictName"]):
        g = g.set_index("week").reindex(all_weeks, fill_value=0)
        g["DistrictID"] = did
        g["DistrictName"] = dname
        g = g.reset_index().rename(columns={"index": "week"})
        frames.append(g)
    panel = pd.concat(frames, ignore_index=True).sort_values(["DistrictID", "week"])

    # week ordinal (for temporal split)
    week_order = {w: i for i, w in enumerate(sorted(panel["week"].unique()))}
    panel["week_idx"] = panel["week"].map(week_order)

    # lag / rolling features (computed within district, no cross-district leakage)
    def feats(g):
        g = g.sort_values("week_idx")
        for k in (1, 2, 3, 4):
            g[f"lag{k}"] = g["count"].shift(k)
        g["roll4_mean"] = g["count"].shift(1).rolling(4).mean()
        g["roll4_std"] = g["count"].shift(1).rolling(4).std()
        g["roll8_mean"] = g["count"].shift(1).rolling(8).mean()
        g["heinous_lag1"] = g["heinous"].shift(1)
        g["clear_rate_lag1"] = (g["cleared"].shift(1) / g["count"].shift(1)).fillna(0)
        g["district_base"] = g["count"].expanding().mean().shift(1)
        # TARGET = next week's count
        g["target_count"] = g["count"].shift(-1)
        return g

    panel = panel.groupby("DistrictID", group_keys=False).apply(feats)
    panel["month"] = panel["week"].dt.month
    panel["month_sin"] = np.sin(2 * np.pi * panel["month"] / 12)
    panel["month_cos"] = np.cos(2 * np.pi * panel["month"] / 12)
    panel = panel.replace([np.inf, -np.inf], np.nan)
    return panel


def build_panel() -> pd.DataFrame:
    """Training panel — rows with both features and the next-week target present."""
    return _panel_raw().dropna(subset=RISK_FEATURES + ["target_count"])


def latest_features() -> pd.DataFrame:
    """Most recent complete feature row per district — used at inference to forecast
    the upcoming week (target unknown)."""
    raw = _panel_raw().dropna(subset=RISK_FEATURES)
    return raw.sort_values("week_idx").groupby("DistrictID").tail(1)


# ---------------------------------------------------------------------------
# train + evaluate
# ---------------------------------------------------------------------------

def train_risk(panel: pd.DataFrame):
    # temporal split: earliest 75% of weeks -> train, latest 25% -> test
    cut = panel["week_idx"].quantile(0.75)
    train = panel[panel["week_idx"] <= cut]
    test = panel[panel["week_idx"] > cut]

    # HIGH-RISK label: next-week count >= district's 75th-pct (threshold learnt on TRAIN)
    thr = train.groupby("DistrictID")["target_count"].quantile(0.75).to_dict()
    def label(df):
        return (df["target_count"] >= df["DistrictID"].map(thr)).astype(int)
    y_train_c, y_test_c = label(train), label(test)

    Xtr, Xte = train[RISK_FEATURES], test[RISK_FEATURES]

    clf = GradientBoostingClassifier(n_estimators=250, max_depth=3, learning_rate=0.05,
                                     subsample=0.9, random_state=42)
    clf.fit(Xtr, y_train_c)
    p_prob = clf.predict_proba(Xte)[:, 1]
    p_pred = (p_prob >= 0.5).astype(int)
    clf_metrics = {
        "roc_auc": round(float(roc_auc_score(y_test_c, p_prob)), 3),
        "accuracy": round(float(accuracy_score(y_test_c, p_pred)), 3),
        "precision": round(float(precision_score(y_test_c, p_pred, zero_division=0)), 3),
        "recall": round(float(recall_score(y_test_c, p_pred, zero_division=0)), 3),
        "f1": round(float(f1_score(y_test_c, p_pred, zero_division=0)), 3),
        "positive_rate_test": round(float(y_test_c.mean()), 3),
    }

    reg = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05,
                                    subsample=0.9, random_state=42)
    reg.fit(Xtr, train["target_count"])
    r_pred = np.clip(reg.predict(Xte), 0, None)
    # naive baseline = last week's value (lag1) to prove the model adds value
    baseline_mae = float(mean_absolute_error(test["target_count"], test["lag1"]))
    reg_metrics = {
        "mae": round(float(mean_absolute_error(test["target_count"], r_pred)), 3),
        "baseline_mae_lag1": round(baseline_mae, 3),
        "r2": round(float(r2_score(test["target_count"], r_pred)), 3),
    }

    joblib.dump({"model": clf, "features": RISK_FEATURES, "thresholds": thr},
                os.path.join(MODELS_DIR, "risk_classifier.joblib"))
    joblib.dump({"model": reg, "features": RISK_FEATURES},
                os.path.join(MODELS_DIR, "risk_regressor.joblib"))

    importances = dict(sorted(
        zip(RISK_FEATURES, [round(float(x), 3) for x in clf.feature_importances_]),
        key=lambda kv: -kv[1]))
    return {
        "classifier": clf_metrics,
        "regressor": reg_metrics,
        "n_train_rows": int(len(train)),
        "n_test_rows": int(len(test)),
        "feature_importance": importances,
    }


def train_anomaly():
    df = db.load_cases().copy()
    df["report_delay_h"] = df["report_delay_h"].clip(lower=0).fillna(0)
    acc_counts = db.load_accused().groupby("CaseMasterID").size()
    df["n_accused"] = df["CaseMasterID"].map(acc_counts).fillna(0)
    dh = df.groupby(["DistrictID", "CrimeMinorHeadID"]).size().rename("dh_count")
    df = df.merge(dh, on=["DistrictID", "CrimeMinorHeadID"], how="left")
    d_tot = df.groupby("DistrictID").size().rename("d_tot")
    df = df.merge(d_tot, on="DistrictID", how="left")
    df["subhead_rarity"] = 1 - (df["dh_count"] / df["d_tot"])
    feat_cols = ["hour", "GravityOffenceID", "n_accused", "report_delay_h",
                 "subhead_rarity", "heinous"]
    X = df[feat_cols].fillna(0)
    model = IsolationForest(contamination=0.01, n_estimators=200, random_state=42)
    model.fit(X)
    joblib.dump({"model": model, "features": feat_cols},
                os.path.join(MODELS_DIR, "anomaly_model.joblib"))
    return {"n_cases": int(len(df)), "features": feat_cols,
            "flagged": int((model.predict(X) == -1).sum())}


def main():
    print("Building district×week panel …")
    panel = build_panel()
    print(f"  panel rows: {len(panel)}  ({panel['DistrictID'].nunique()} districts, "
          f"{panel['week_idx'].nunique()} weeks)")

    print("Training predictive-risk models (temporal split) …")
    risk = train_risk(panel)
    print("Training anomaly model …")
    anom = train_anomaly()

    metrics = {"risk": risk, "anomaly": anom,
               "data_rows": int(len(db.load_cases()))}
    with open(os.path.join(MODELS_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    c, r = risk["classifier"], risk["regressor"]
    print("\n=== HIGH-RISK CLASSIFIER (next-week) ===")
    print(f"  ROC-AUC {c['roc_auc']} | F1 {c['f1']} | precision {c['precision']} | recall {c['recall']}")
    print("=== NEXT-WEEK COUNT REGRESSOR ===")
    print(f"  MAE {r['mae']} vs naive-baseline {r['baseline_mae_lag1']} | R² {r['r2']}")
    print("=== ANOMALY MODEL ===")
    print(f"  fitted on {anom['n_cases']} cases, flags {anom['flagged']}")
    print(f"\nArtefacts + metrics written to {MODELS_DIR}")
    print("Top risk features:", list(risk["feature_importance"].items())[:4])


if __name__ == "__main__":
    main()
