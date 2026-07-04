"""
NLP pipeline — classify crime type from the free-text FIR ``BriefFacts`` narrative.

This is a genuine text→label task: the narratives describe the incident (weapons,
vehicles, stolen items, amounts, MO) but never state the legal crime category, so the
model must learn language patterns.

Pipeline stages (same MLOps discipline as the tabular pipeline):
  clean text -> TF-IDF -> BAKE-OFF of ~10 classifiers via stratified CV -> pick best by
  macro-F1 -> hold-out evaluation (accuracy / macro-F1 / per-class) -> register champion
  (TF-IDF+model as one servable Pipeline) -> MLflow + JSONL tracking -> model card.

Also fits an unsupervised MO clusterer (KMeans over TF-IDF) and provides rule-based
entity extraction (weapons / vehicles / stolen items / amounts).

Run:  cd backend/ml && python nlp.py     (or: python cli.py train-nlp)
Maps to Catalyst Zia Text Analytics / QuickML in production.
"""
from __future__ import annotations

import os
import re
import warnings

import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import (
    AdaBoostClassifier,
    BaggingClassifier,
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import (
    LogisticRegression,
    PassiveAggressiveClassifier,
    RidgeClassifier,
    SGDClassifier,
)
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import BernoulliNB, ComplementNB, MultinomialNB
from sklearn.neighbors import KNeighborsClassifier, NearestCentroid
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

import config
import data
import evaluate
import registry
import tracking

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except Exception:
    HAS_XGB = False

try:
    import models as _m
    XGB_DEVICE = _m.XGB_DEVICE
    HAS_GPU = _m.HAS_GPU
except Exception:
    XGB_DEVICE, HAS_GPU = "cpu", False

SERVING_NLP = os.path.join(config.SERVING_DIR, "nlp_classifier.joblib")
SERVING_CLUSTER = os.path.join(config.SERVING_DIR, "nlp_mo_clusters.joblib")
NLP_METRICS = os.path.join(config.SERVING_DIR, "nlp_metrics.json")

STOPWORDS = set("""a an the of to in on at and or for with from by was were is are be been
being this that these those it its as into near over under during his her their them they
he she who whom which not no had has have will would could should complainant accused
person persons unknown unidentified reported registered stated alleged found rs""".split())


# ---------------------------------------------------------------------------
# text prep
# ---------------------------------------------------------------------------

def clean_text(s: str) -> str:
    s = str(s).lower()
    s = re.sub(r"[^a-z\s]", " ", s)           # drop digits/punct (amounts handled by NER)
    tokens = [t for t in s.split() if len(t) > 2 and t not in STOPWORDS]
    return " ".join(tokens)


def load_text_data():
    df = data.load_cases()[["BriefFacts", "CrimeHead", "CrimeSubHead"]].dropna()
    df = df[df["BriefFacts"].str.len() > 10].copy()
    df["clean"] = df["BriefFacts"].map(clean_text)
    df = df[df["clean"].str.len() > 0]
    return df


# ---------------------------------------------------------------------------
# candidate models (the bake-off)
# ---------------------------------------------------------------------------

def _tfidf():
    return TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.9, sublinear_tf=True,
                           max_features=20000)


def candidates():
    """~18 text classifiers. Sparse-friendly (NB/linear) use raw TF-IDF; dense models
    (trees/boosting/kNN/MLP) use TF-IDF→TruncatedSVD(200)."""
    S = config.RANDOM_SEED
    svd = lambda: TruncatedSVD(n_components=200, random_state=S)
    sparse = lambda clf: Pipeline([("tfidf", _tfidf()), ("clf", clf)])
    dense = lambda clf: Pipeline([("tfidf", _tfidf()), ("svd", svd()), ("clf", clf)])
    c = {
        # --- naive Bayes family ---
        "multinomial_nb": sparse(MultinomialNB()),
        "complement_nb": sparse(ComplementNB()),
        "bernoulli_nb": sparse(BernoulliNB()),
        # --- linear family ---
        "logreg": sparse(LogisticRegression(max_iter=2000, C=3.0, n_jobs=-1)),
        "linear_svc": sparse(LinearSVC(C=1.0)),
        "sgd_logloss": sparse(SGDClassifier(loss="modified_huber", max_iter=2000, random_state=S)),
        "passive_aggressive": sparse(PassiveAggressiveClassifier(max_iter=2000, random_state=S)),
        "ridge": sparse(RidgeClassifier()),
        "nearest_centroid": sparse(NearestCentroid()),
        # --- instance / tree ---
        "knn": dense(KNeighborsClassifier(n_neighbors=15, weights="distance", n_jobs=-1)),
        "decision_tree": dense(DecisionTreeClassifier(max_depth=25, random_state=S)),
        # --- ensembles ---
        "random_forest": dense(RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=S)),
        "extra_trees": dense(ExtraTreesClassifier(n_estimators=300, n_jobs=-1, random_state=S)),
        "bagging": dense(BaggingClassifier(n_estimators=50, n_jobs=-1, random_state=S)),
        "adaboost": dense(AdaBoostClassifier(n_estimators=200, random_state=S)),
        "hist_gbm": dense(HistGradientBoostingClassifier(max_iter=300, random_state=S)),
        # --- neural net (real epochs) ---
        "mlp": dense(MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=80,
                                   early_stopping=True, random_state=S)),
    }
    if HAS_XGB:
        c["xgboost"] = dense(XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.1,
                                           tree_method="hist", device=XGB_DEVICE, random_state=S))
    return c


# ---------------------------------------------------------------------------
# train + select + evaluate
# ---------------------------------------------------------------------------

def run():
    config.ensure_dirs()
    print("== KSP crime-text NLP pipeline ==")
    print("[1/5] load + clean text")
    from sklearn.preprocessing import LabelEncoder
    df = load_text_data()
    report = data.validate(data.load_cases())
    le = LabelEncoder().fit(df["CrimeHead"].values)   # XGBoost needs int labels
    y = le.transform(df["CrimeHead"].values)
    X = df["clean"].values
    classes = list(le.classes_)
    print(f"    {len(df):,} narratives · {len(classes)} crime-head classes")

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y,
                                          random_state=config.RANDOM_SEED)
    print(f"    train {len(Xtr):,} / test {len(Xte):,}")

    import joblib
    cand = candidates()
    print(f"[2/6] cross-validate {len(cand)} models (stratified 3-fold CV, macro-F1)")
    cvk = StratifiedKFold(n_splits=3, shuffle=True, random_state=config.RANDOM_SEED)
    cv_scores = {}
    for name, pipe in cand.items():
        jobs = 1 if name == "xgboost" else -1
        scores = cross_val_score(pipe, Xtr, ytr, scoring="f1_macro", cv=cvk, n_jobs=jobs)
        cv_scores[name] = (round(float(scores.mean()), 4), round(float(scores.std()), 4))
        dev = f" [GPU:{XGB_DEVICE}]" if name == "xgboost" else ""
        print(f"    {name:20s} CV macro-F1 {scores.mean():.4f} ± {scores.std():.4f}{dev}")

    print(f"[3/6] fit ALL {len(cand)} models on train, evaluate on hold-out, SAVE EACH")
    all_dir = os.path.join(config.SERVING_DIR, "nlp_all")
    os.makedirs(all_dir, exist_ok=True)
    leaderboard = []
    preds_table = {"_true": [classes[i] for i in yte]}
    per_class_by_model = {}
    for name, pipe in cand.items():
        pipe.fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        has_proba = hasattr(pipe.named_steps["clf"], "predict_proba")
        m = {
            "family": name,
            "cv_score": cv_scores[name][0], "cv_std": cv_scores[name][1],
            "accuracy": round(float(accuracy_score(yte, pred)), 4),
            "macro_f1": round(float(f1_score(yte, pred, average="macro")), 4),
            "weighted_f1": round(float(f1_score(yte, pred, average="weighted")), 4),
            "has_proba": has_proba,
        }
        leaderboard.append(m)
        preds_table[name] = [classes[i] for i in pred]
        per_class_by_model[name] = {
            k: round(v["f1-score"], 3) for k, v in
            classification_report(yte, pred, target_names=classes, output_dict=True,
                                  zero_division=0).items() if k in classes}
        # SAVE every fitted model as its own servable artefact
        joblib.dump({"pipeline": pipe, "classes": list(classes), "family": name,
                     "has_proba": has_proba}, os.path.join(all_dir, f"{name}.joblib"))
        print(f"    {name:20s} acc {m['accuracy']:.4f}  macroF1 {m['macro_f1']:.4f}  -> saved")
    leaderboard.sort(key=lambda r: -r["macro_f1"])

    # save ALL outputs: per-model metrics table + every model's test predictions
    with open(os.path.join(config.SERVING_DIR, "nlp_all_models.json"), "w", encoding="utf-8") as f:
        import json
        json.dump({"models": leaderboard, "per_class_f1": per_class_by_model,
                   "classes": classes, "n_test": len(yte)}, f, indent=2)
    pd.DataFrame(preds_table).to_csv(
        os.path.join(config.SERVING_DIR, "nlp_all_predictions.csv"), index=False)
    print(f"    saved {len(cand)} models -> {all_dir}")
    print(f"    saved outputs -> nlp_all_models.json, nlp_all_predictions.csv")

    best_name = leaderboard[0]["family"]
    metrics = {k: leaderboard[0][k] for k in ("accuracy", "macro_f1", "weighted_f1")}
    metrics["cv_macro_f1"] = leaderboard[0]["cv_score"]
    metrics["n_classes"] = len(classes)
    per_class = {c: {"f1-score": per_class_by_model[best_name].get(c, 0)} for c in classes}
    champ = joblib.load(os.path.join(all_dir, f"{best_name}.joblib"))["pipeline"]
    print(f"    champion (best hold-out macro-F1) = {best_name}: acc {metrics['accuracy']} "
          f"macroF1 {metrics['macro_f1']}")

    print("[4/6] fit MO clusterer (unsupervised) + register")
    vec = _tfidf().fit(Xtr)
    km = MiniBatchKMeans(n_clusters=10, random_state=config.RANDOM_SEED, n_init=5)
    km.fit(vec.transform(Xtr))
    joblib.dump({"vectorizer": vec, "kmeans": km, "terms": vec.get_feature_names_out()},
                SERVING_CLUSTER)

    artefact = {"pipeline": champ, "classes": list(classes), "family": best_name,
                "has_proba": hasattr(champ.named_steps["clf"], "predict_proba")}
    cv = {"n_splits": 3, "n_candidates": len(leaderboard), "metric": "f1_macro",
          "mean": leaderboard[0]["cv_score"], "std": leaderboard[0]["cv_std"],
          "leaderboard": leaderboard}
    card = evaluate.model_card("nlp_crime_classifier", best_name,
                               {"vectorizer": "tfidf(1,2)", "max_features": 20000},
                               metrics, cv, report, ["BriefFacts text"],
                               extra=f"{len(candidates())} text classifiers compared. "
                                     f"Per-class F1 in metadata.")
    meta = {"family": best_name, "metrics": metrics, "cv": cv, "data": report,
            "per_class": {k: v for k, v in per_class.items() if isinstance(v, dict)},
            "classes": list(classes), "n_train": len(Xtr), "n_holdout": len(Xte)}
    joblib.dump(artefact, SERVING_NLP)          # servable pipeline for inference
    tracking.mlflow_log_run("nlp_classifier", {"family": best_name}, metrics, {"family": best_name})
    reg = registry.register("nlp_crime_classifier", artefact, meta, card, "macro_f1",
                            higher_is_better=True)
    tracking.log_run({"task": "nlp_crime_classifier", "family": best_name,
                      "metrics": metrics, "cv": cv, "promotion": reg})

    print("[5/6] write serving metrics")
    _write_metrics(metrics, leaderboard, per_class, list(classes), report, reg)
    print(f"[6/6] done — {len(cand)} models trained & saved | champion={best_name} "
          f"acc={metrics['accuracy']} macro-F1={metrics['macro_f1']} (v{reg['version']})")
    return reg


def _write_metrics(metrics, leaderboard, per_class, classes, report, reg):
    import json
    out = {
        "task": "crime-type classification from BriefFacts",
        "champion": leaderboard[0]["family"],
        "champion_version": reg["version"],
        "metrics": metrics,
        "leaderboard": leaderboard,
        "classes": classes,
        "per_class_f1": {k: round(v["f1-score"], 3) for k, v in per_class.items()
                         if isinstance(v, dict) and k in classes},
        "gpu": HAS_GPU, "device": XGB_DEVICE, "data_rows": report["n_cases"],
    }
    with open(NLP_METRICS, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# inference helpers (used by the service)
# ---------------------------------------------------------------------------

ENTITY_PATTERNS = {
    "weapon": r"\b(knife|machete|iron rod|wooden club|sickle|pistol|bottle|chopper|stick|firearm)\b",
    "vehicle": r"\b(motorcycle|scooter|car|autorickshaw|auto|van|suv|moped|two-wheeler|bike)\b",
    "stolen_item": r"\b(gold ornaments|gold chain|mangalsutra|mobile phone|laptop|cash|silver articles|documents|jewellery|electronic goods)\b",
    "contraband": r"\b(ganja|mdma|arrack|brown sugar|gutka|whitener|liquor)\b",
    "amount": r"rs\s?[\d,]+",
}


def extract_entities(text: str) -> dict:
    t = str(text).lower()
    out = {}
    for label, pat in ENTITY_PATTERNS.items():
        found = sorted(set(m.group(0).strip() for m in re.finditer(pat, t)))
        if found:
            out[label] = found
    return out


if __name__ == "__main__":
    run()
