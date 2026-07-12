"""End-to-end training pipeline (the MLOps entry point).

Stages:  validate data -> engineer features -> temporal hold-out split ->
         model selection (multi-family, RandomizedSearch over expanding-window
         time-series CV) -> refit -> hold-out evaluation -> register + champion/
         challenger promotion -> experiment tracking (JSONL + MLflow).

Run:  python -m ml.cli train        (or: python pipeline.py)
"""
from __future__ import annotations

import csv as _csv
import os
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

import config
import data
import evaluate
import features as F
import models
import registry
import tracking

warnings.filterwarnings("ignore")


def _temporal_split(frame: pd.DataFrame):
    cut = frame["week_idx"].quantile(1 - config.TEST_WEEKS_FRACTION)
    return frame[frame["week_idx"] <= cut].copy(), frame[frame["week_idx"] > cut].copy()


def _select_model(candidates, X, y, scoring):
    """RandomizedSearch over each family with expanding-window time-series CV; return
    the best family/estimator and a CV report."""
    tscv = TimeSeriesSplit(n_splits=config.CV_SPLITS)
    results = []
    for name, (pipe, space) in candidates.items():
        search = RandomizedSearchCV(
            pipe, space, n_iter=config.SEARCH_ITERS, scoring=scoring, cv=tscv,
            random_state=config.RANDOM_SEED, n_jobs=models.search_n_jobs(name),
            refit=True, error_score="raise",
        )
        search.fit(X, y)
        results.append((name, search.best_estimator_, search.best_params_,
                        float(search.best_score_)))
        dev = f" [GPU:{models.XGB_DEVICE}]" if name == "xgboost" else ""
        print(f"    {name:14s} CV {scoring}: {search.best_score_:.4f}{dev}")
    results.sort(key=lambda r: -r[3])
    best = results[0]
    cv_report = {"n_splits": config.CV_SPLITS, "n_candidates": len(candidates),
                 "metric": scoring, "mean": best[3], "std": 0.0,
                 "leaderboard": [{"family": r[0], "cv_score": round(r[3], 4)} for r in results]}
    return best, cv_report


# ---------------------------------------------------------------------------

def train_classifier(train, holdout, data_report):
    print("  [classifier] high-risk next-week…")
    thresholds = F.learn_thresholds(train)
    Xtr, ytr = train[config.RISK_FEATURES], F.high_risk_labels(train, thresholds)
    Xho, yho = holdout[config.RISK_FEATURES], F.high_risk_labels(holdout, thresholds)

    (family, est, params, cv_score), cv = _select_model(
        models.classifier_candidates(), Xtr, ytr, "roc_auc")

    proba = est.predict_proba(Xho)[:, 1]
    thr, thr_f1 = evaluate.best_threshold(yho, proba)
    metrics = evaluate.classifier_metrics(yho, proba, threshold=thr)
    metrics["operating_threshold"] = round(thr, 3)
    metrics["cv_roc_auc"] = round(cv_score, 4)

    # naive persistence baseline: predict "high-risk next week" iff the CURRENT week is already
    # at/above the district high-risk threshold — the honest bar the trained model must beat.
    base_pred = (holdout["count"].to_numpy()
                 >= holdout["DistrictID"].map(thresholds).to_numpy()).astype(int)
    metrics["baseline_persistence_f1"] = round(float(f1_score(yho, base_pred, zero_division=0)), 4)
    metrics["baseline_persistence_accuracy"] = round(float(accuracy_score(yho, base_pred)), 4)

    artefact = {"model": est, "features": config.RISK_FEATURES, "thresholds": thresholds,
                "operating_threshold": thr, "family": family}
    card = evaluate.model_card("risk_classifier", family, params, metrics, cv, data_report,
                               config.RISK_FEATURES,
                               extra=f"Operating threshold tuned to F1-optimal **{thr:.2f}**.")
    meta = {"family": family, "params": params, "metrics": metrics, "cv": cv,
            "data": data_report, "n_train": int(len(train)), "n_holdout": int(len(holdout))}
    tracking.mlflow_log_run("classifier", {"family": family, **params}, metrics, {"family": family})
    reg = registry.register("risk_classifier", artefact, meta, card, "roc_auc", higher_is_better=True)
    tracking.log_run({"task": "risk_classifier", "family": family, "metrics": metrics,
                      "cv": cv, "params": params, "promotion": reg})
    print(f"    -> best={family}  holdout ROC-AUC={metrics['roc_auc']}  F1={metrics['f1']}  "
          f"promoted={reg['promoted']} (v{reg['version']})")
    return reg, metrics


def train_regressor(train, holdout, data_report):
    print("  [regressor] next-week count…")
    Xtr, ytr = train[config.RISK_FEATURES], train["target_count"]
    Xho, yho = holdout[config.RISK_FEATURES], holdout["target_count"]

    (family, est, params, cv_score), cv = _select_model(
        models.regressor_candidates(), Xtr, ytr, "neg_mean_absolute_error")

    pred = np.clip(est.predict(Xho), 0, None)
    # naive persistence baseline for a t+1 forecast = the CURRENT (last completed) week's count,
    # i.e. holdout["count"] (count[t]) — NOT lag1 (=count[t-1], which is two weeks before the
    # target and understates the baseline, inflating the apparent skill).
    metrics = evaluate.regressor_metrics(yho, pred, baseline=holdout["count"])
    metrics["cv_mae"] = round(-cv_score, 4)

    artefact = {"model": est, "features": config.RISK_FEATURES, "family": family}
    card = evaluate.model_card("risk_regressor", family, params, metrics, cv, data_report,
                               config.RISK_FEATURES,
                               extra="Baseline = last completed week's count (naive persistence, count[t] for the t+1 target).")
    meta = {"family": family, "params": params, "metrics": metrics, "cv": cv,
            "data": data_report, "n_train": int(len(train)), "n_holdout": int(len(holdout))}
    tracking.mlflow_log_run("regressor", {"family": family, **params}, metrics, {"family": family})
    # lower MAE is better
    reg = registry.register("risk_regressor", artefact, meta, card, "mae", higher_is_better=False)
    tracking.log_run({"task": "risk_regressor", "family": family, "metrics": metrics,
                      "cv": cv, "params": params, "promotion": reg})
    print(f"    -> best={family}  holdout MAE={metrics['mae']} (baseline {metrics['baseline_mae']})  "
          f"R2={metrics['r2']}  promoted={reg['promoted']} (v{reg['version']})")
    return reg, metrics


def _load_anomaly_ground_truth() -> set:
    """Planted-anomaly CaseMasterIDs written by the generator (GroundTruthAnomalies.csv),
    used to score the detector with real precision/recall. Empty set if absent."""
    path = os.path.join(os.path.dirname(data.db.db_path()), "GroundTruthAnomalies.csv")
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {int(r["CaseMasterID"]) for r in _csv.DictReader(f)}


def train_anomaly(cases, data_report):
    print("  [anomaly] isolation forest…")
    df = cases.copy()
    df["report_delay_h"] = df["report_delay_h"].clip(lower=0).fillna(0)
    acc = data.db.load_accused().groupby("CaseMasterID").size()
    df["n_accused"] = df["CaseMasterID"].map(acc).fillna(0)
    dh = df.groupby(["DistrictID", "CrimeMinorHeadID"]).size().rename("dh_count")
    df = df.merge(dh, on=["DistrictID", "CrimeMinorHeadID"], how="left")
    dt = df.groupby("DistrictID").size().rename("d_tot")
    df = df.merge(dt, on="DistrictID", how="left")
    df["subhead_rarity"] = 1 - df["dh_count"] / df["d_tot"]
    feats = ["hour", "GravityOffenceID", "n_accused", "report_delay_h", "subhead_rarity", "heinous"]
    X = df[feats].fillna(0)

    model = IsolationForest(contamination=0.01, n_estimators=300, random_state=config.RANDOM_SEED).fit(X)
    pred = model.predict(X)                 # -1 = flagged
    score = -model.score_samples(X)         # higher = more anomalous
    flagged = int((pred == -1).sum())
    metrics = {"n_cases": int(len(df)), "flagged": flagged,
               "flagged_pct": round(100 * flagged / len(df), 3)}

    # ---- score the detector against the generator's planted ground truth ----
    gt = _load_anomaly_ground_truth()
    if gt:
        y_true = df["CaseMasterID"].isin(gt).to_numpy().astype(int)
        n_pos = int(y_true.sum())
        if n_pos > 0:
            flag_mask = (pred == -1)
            tp = int((flag_mask & (y_true == 1)).sum())
            order = np.argsort(-score)
            topk = order[:n_pos]                                       # flag exactly n_planted by score
            metrics.update({
                "n_planted": n_pos,
                "roc_auc": round(float(roc_auc_score(y_true, score)), 4),
                "avg_precision": round(float(average_precision_score(y_true, score)), 4),
                "recall_at_contamination": round(tp / n_pos, 4),
                "precision_at_contamination": round(tp / max(1, flagged), 4),
                "precision_at_k": round(float(y_true[topk].sum() / n_pos), 4),
            })
    has_gt = "roc_auc" in metrics
    primary = "roc_auc" if has_gt else "flagged_pct"

    artefact = {"model": model, "features": feats}
    extra = ("Unsupervised IsolationForest (contamination=1%). Scored against "
             f"{metrics.get('n_planted', 0)} generator-planted ground-truth anomalies: "
             "ROC-AUC / average-precision are threshold-free; recall/precision are at the 1% "
             "flag cut; precision@k flags exactly the number planted."
             if has_gt else
             "Unsupervised; contamination=1%. No ground-truth labels present → only the flag "
             "RATE is reported (a design target, not a validated detection metric).")
    card = evaluate.model_card(
        "anomaly", "IsolationForest", {"contamination": 0.01, "n_estimators": 300},
        metrics, {"n_splits": 0, "n_candidates": 1, "mean": None, "std": None},
        data_report, feats, extra=extra,
        metrics_heading=("Detection metrics vs planted ground-truth anomalies" if has_gt
                         else "Flag rate (no ground truth available)"),
        selection="Unsupervised IsolationForest over the full case table (no train/CV split)")
    meta = {"family": "IsolationForest", "params": {"contamination": 0.01}, "metrics": metrics,
            "cv": {}, "data": data_report}
    tracking.mlflow_log_run("anomaly", {"family": "IsolationForest"}, metrics, {"family": "IsolationForest"})
    reg = registry.register("anomaly", artefact, meta, card, primary, higher_is_better=True)
    tracking.log_run({"task": "anomaly", "metrics": metrics, "promotion": reg})
    if has_gt:
        print(f"    -> flagged {flagged}/{len(df)}  planted={metrics['n_planted']}  "
              f"ROC-AUC={metrics['roc_auc']}  recall@1%={metrics['recall_at_contamination']}  "
              f"P@k={metrics['precision_at_k']}  (v{reg['version']})")
    else:
        print(f"    -> flagged {flagged}/{len(df)}  (no ground truth)  (v{reg['version']})")
    return reg, metrics


def run():
    config.ensure_dirs()
    print("== KSP crime-forecasting MLOps pipeline ==")
    print("[1/4] load + validate data")
    cases = data.load_cases()
    report = data.validate(cases)
    print(f"    {report['n_cases']:,} cases · {report['n_districts']} districts · "
          f"{report['date_from']}→{report['date_to']} · fp {report['data_fingerprint']}")
    if report["warnings"]:
        print("    warnings:", report["warnings"])

    print("[2/4] engineer features")
    panel = F.build_panel(cases)
    frame = F.training_frame(panel)
    train, holdout = _temporal_split(frame)
    # order rows chronologically so TimeSeriesSplit folds are genuinely forward-in-time.
    # (build_panel sorts by (DistrictID, week); left unsorted, TimeSeriesSplit would fold by
    # DISTRICT block, not by time — a cross-district split masquerading as a temporal one.)
    train = train.sort_values(["week_idx", "DistrictID"]).reset_index(drop=True)
    print(f"    panel {len(frame)} rows · train {len(train)} / hold-out {len(holdout)} "
          f"({panel['week_idx'].nunique()} weeks, {frame['DistrictID'].nunique()} districts)")

    print("[3/4] train + select + evaluate")
    clf_reg, clf_m = train_classifier(train, holdout, report)
    reg_reg, reg_m = train_regressor(train, holdout, report)
    an_reg, an_m = train_anomaly(cases, report)

    print("[4/4] write serving metrics + champions")
    _write_serving_metrics(report, clf_m, reg_m, an_m, clf_reg, reg_reg)
    print(f"== done ==  MLflow:{tracking.HAS_MLFLOW} | XGBoost:{models.HAS_XGB} | "
          f"GPU:{models.HAS_GPU} ({models.XGB_DEVICE})")
    return {"classifier": clf_reg, "regressor": reg_reg, "anomaly": an_reg}


def _write_serving_metrics(report, clf_m, reg_m, an_m, clf_reg, reg_reg):
    """Back-compat metrics.json consumed by /api/model-info + UI model card."""
    import json
    import os
    out = {
        "risk": {
            "classifier": {"roc_auc": clf_m["roc_auc"], "f1": clf_m["f1"],
                           "precision": clf_m["precision"], "recall": clf_m["recall"],
                           "accuracy": clf_m["accuracy"], "pr_auc": clf_m["pr_auc"],
                           "cv_roc_auc": clf_m.get("cv_roc_auc"),
                           "baseline_persistence_f1": clf_m.get("baseline_persistence_f1"),
                           "positive_rate_test": clf_m["positive_rate"]},
            "regressor": {"mae": reg_m["mae"], "baseline_mae_persistence": reg_m["baseline_mae"],
                          "skill_vs_baseline_pct": reg_m.get("skill_vs_baseline_pct"),
                          "r2": reg_m["r2"], "rmse": reg_m["rmse"]},
            "champion_versions": {"classifier": clf_reg["version"], "regressor": reg_reg["version"]},
        },
        "anomaly": {"n_cases": an_m["n_cases"], "flagged": an_m["flagged"],
                    "n_planted": an_m.get("n_planted"), "roc_auc": an_m.get("roc_auc"),
                    "avg_precision": an_m.get("avg_precision"),
                    "recall_at_contamination": an_m.get("recall_at_contamination"),
                    "precision_at_k": an_m.get("precision_at_k")},
        "data_rows": report["n_cases"], "data_fingerprint": report["data_fingerprint"],
        "families": {"classifier": clf_reg, "regressor": reg_reg},
    }
    os.makedirs(config.SERVING_DIR, exist_ok=True)
    with open(os.path.join(config.SERVING_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)


if __name__ == "__main__":
    run()
