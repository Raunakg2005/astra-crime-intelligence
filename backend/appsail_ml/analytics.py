"""
Core crime-intelligence analytics.

Real algorithms over the FIR fact tables:
  * hotspots        -> DBSCAN spatial clustering (haversine) + time-of-day profile
  * emerging trends -> z-score of recent window vs rolling historical baseline
  * link analysis   -> co-offending graph, ego networks, Louvain communities
  * anomalies       -> IsolationForest over case features
  * risk scoring    -> district risk from volume + trend + heinous share (Zia-AutoML proxy)
  * temporal        -> monthly series, day-of-week x hour matrix

Everything returns plain JSON-serialisable dicts for the API layer.
"""
from __future__ import annotations

import functools
import math
import os
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

import db

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# The ML pipeline (../ml) owns feature engineering. Inference reuses the SAME code
# so training and serving never drift (identical feature set).
_ML_DIR = os.path.join(os.path.dirname(__file__), "..", "ml")
if _ML_DIR not in sys.path:
    sys.path.insert(0, _ML_DIR)


@functools.lru_cache(maxsize=1)
def _ml_features():
    import features as mlfeatures  # ml/features.py
    return mlfeatures


@functools.lru_cache(maxsize=1)
def _nlp():
    """Load the NLP champion pipeline + MO clusterer + text helpers (from ml/)."""
    import joblib
    import nlp as mlnlp  # ml/nlp.py -> clean_text, extract_entities
    clf_path = os.path.join(MODELS_DIR, "nlp_classifier.joblib")
    cl_path = os.path.join(MODELS_DIR, "nlp_mo_clusters.joblib")
    art = joblib.load(clf_path) if os.path.exists(clf_path) else None
    clusters = joblib.load(cl_path) if os.path.exists(cl_path) else None
    return art, clusters, mlnlp


def nlp_classify(text: str):
    """Classify a free-text FIR narrative into a crime head + extract entities."""
    art, _, mlnlp = _nlp()
    if art is None:
        return {"error": "NLP model not trained — run: cd backend/ml && python cli.py train-nlp"}
    clean = mlnlp.clean_text(text)
    pipe, classes = art["pipeline"], art["classes"]
    if art.get("has_proba") and hasattr(pipe, "predict_proba"):
        proba = pipe.predict_proba([clean])[0]
    else:
        dfun = np.atleast_2d(pipe.decision_function([clean]))[0]
        e = np.exp(dfun - dfun.max())
        proba = e / e.sum()
    order = np.argsort(proba)[::-1][:3]
    return {
        "input": text,
        "predicted_head": classes[int(order[0])],
        "predictions": [{"crime_head": classes[int(i)], "confidence": round(float(proba[i]), 3)}
                        for i in order],
        "entities": mlnlp.extract_entities(text),
    }


def nlp_model_info():
    path = os.path.join(MODELS_DIR, "nlp_metrics.json")
    if os.path.exists(path):
        import json
        with open(path) as f:
            return json.load(f)
    return {"trained": False}


@functools.lru_cache(maxsize=1)
def nlp_mo_clusters():
    """Unsupervised modus-operandi clusters over BriefFacts (top terms + size)."""
    _, clusters, _ = _nlp()
    if clusters is None:
        return {"clusters": []}
    km, terms, vec = clusters["kmeans"], clusters["terms"], clusters["vectorizer"]
    df = db.load_cases()[["BriefFacts", "CrimeHead"]].dropna()
    labels = km.predict(vec.transform(df["BriefFacts"].map(_nlp()[2].clean_text)))
    df = df.assign(cluster=labels)
    centers = km.cluster_centers_
    out = []
    for i in range(km.n_clusters):
        g = df[df["cluster"] == i]
        top_idx = centers[i].argsort()[::-1][:6]
        out.append({
            "cluster": int(i),
            "size": int(len(g)),
            "top_terms": [str(terms[j]) for j in top_idx],
            "dominant_head": g["CrimeHead"].value_counts().idxmax() if len(g) else None,
        })
    out.sort(key=lambda c: -c["size"])
    return {"clusters": out, "n_clusters": km.n_clusters}


@functools.lru_cache(maxsize=8)
def _load_model(name: str):
    """Load a persisted model artefact (trained by train.py). Returns None if the
    pipeline hasn't been run yet, so inference falls back to on-the-fly computation."""
    path = os.path.join(MODELS_DIR, name)
    if not os.path.exists(path):
        return None
    import joblib
    return joblib.load(path)

# reference district centroids (kept here so the service is self-contained)
DISTRICT_CENTROIDS = {
    4001: (12.9716, 77.5946), 4002: (13.2846, 77.5960), 4003: (12.7217, 77.2807),
    4004: (13.1367, 78.1292), 4005: (13.4355, 77.7315), 4006: (13.3379, 77.1173),
    4007: (12.2958, 76.6394), 4008: (12.5223, 76.8954), 4009: (13.0072, 76.0962),
    4010: (11.9261, 76.9438), 4011: (12.3375, 75.8069), 4012: (12.9141, 74.8560),
    4013: (13.3409, 74.7421), 4014: (13.3161, 75.7720), 4015: (13.9299, 75.5681),
    4016: (14.4644, 75.9218), 4017: (14.2251, 76.3980), 4018: (15.1394, 76.9214),
    4019: (15.3350, 76.4600), 4020: (15.3547, 76.1550), 4021: (16.2076, 77.3463),
    4022: (17.3297, 76.8343), 4023: (16.7700, 77.1376), 4024: (17.9106, 77.5199),
    4025: (16.8302, 75.7100), 4026: (16.1691, 75.6615), 4027: (15.8497, 74.4977),
    4028: (15.4589, 75.0078), 4029: (15.4292, 75.6290), 4030: (14.7935, 75.4045),
    4031: (14.7935, 74.6869),
}


def _latest(df):
    return df["RegDate"].max()


# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------

def kpis():
    df = db.load_cases()
    latest = _latest(df)
    last30 = df[df["RegDate"] > latest - timedelta(days=30)]
    prev30 = df[(df["RegDate"] <= latest - timedelta(days=30)) &
                (df["RegDate"] > latest - timedelta(days=60))]
    trends = emerging_trends(z_threshold=2.5)
    return {
        "total_cases": int(len(df)),
        "cases_last_30d": int(len(last30)),
        "cases_prev_30d": int(len(prev30)),
        "mom_change_pct": round(100 * (len(last30) - len(prev30)) / max(1, len(prev30)), 1),
        "clearance_rate_pct": round(100 * df["cleared"].mean(), 1),
        "heinous_cases": int(df["heinous"].sum()),
        "districts": int(df["DistrictID"].nunique()),
        "active_alerts": len(trends),
        "data_from": str(df["RegDate"].min().date()),
        "data_to": str(latest.date()),
    }


# ---------------------------------------------------------------------------
# District choropleth
# ---------------------------------------------------------------------------

def district_summary():
    df = db.load_cases()
    latest = _latest(df)
    recent = df[df["RegDate"] > latest - timedelta(days=90)]
    rec_counts = recent.groupby("DistrictID").size()
    out = []
    for did, g in df.groupby("DistrictID"):
        top_head = g["CrimeHead"].value_counts().idxmax()
        lat, lng = DISTRICT_CENTROIDS.get(int(did), (None, None))
        out.append({
            "district_id": int(did),
            "district": g["DistrictName"].iloc[0],
            "lat": lat, "lng": lng,
            "total_cases": int(len(g)),
            "recent_90d": int(rec_counts.get(did, 0)),
            "clearance_pct": round(100 * g["cleared"].mean(), 1),
            "heinous": int(g["heinous"].sum()),
            "heinous_pct": round(100 * g["heinous"].mean(), 1),
            "top_crime_head": top_head,
        })
    return sorted(out, key=lambda r: -r["total_cases"])


# ---------------------------------------------------------------------------
# Hotspots — DBSCAN spatial clustering
# ---------------------------------------------------------------------------

def hotspots(district_id=None, crime_head=None, days=None, eps_m=450, min_samples=15):
    from sklearn.cluster import DBSCAN

    df = db.load_cases().dropna(subset=["latitude", "longitude"])
    if district_id:
        df = df[df["DistrictID"] == int(district_id)]
    if crime_head:
        df = df[df["CrimeHead"] == crime_head]
    if days:
        latest = _latest(db.load_cases())
        df = df[df["RegDate"] > latest - timedelta(days=int(days))]
    if len(df) < min_samples:
        return {"clusters": [], "n_points": int(len(df))}

    coords = np.radians(df[["latitude", "longitude"]].to_numpy())
    eps = (eps_m / 1000.0) / 6371.0  # metres -> radians
    labels = DBSCAN(eps=eps, min_samples=min_samples, metric="haversine").fit_predict(coords)
    df = df.assign(cluster=labels)

    clusters = []
    for cl, g in df[df["cluster"] >= 0].groupby("cluster"):
        night = int(((g["hour"] >= 20) | (g["hour"] <= 4)).sum())
        peak_hour = int(g["hour"].mode().iloc[0]) if not g["hour"].mode().empty else None
        clusters.append({
            "cluster_id": int(cl),
            "lat": round(float(g["latitude"].mean()), 6),
            "lng": round(float(g["longitude"].mean()), 6),
            "count": int(len(g)),
            "district": g["DistrictName"].iloc[0],
            "dominant_crime": g["CrimeSubHead"].value_counts().idxmax(),
            "dominant_head": g["CrimeHead"].value_counts().idxmax(),
            "peak_hour": peak_hour,
            "night_share_pct": round(100 * night / len(g), 1),
            "heinous_pct": round(100 * g["heinous"].mean(), 1),
        })
    clusters.sort(key=lambda c: -c["count"])
    # intensity score 0-100 for map radius/colour
    if clusters:
        mx = max(c["count"] for c in clusters)
        for c in clusters:
            c["intensity"] = round(100 * c["count"] / mx, 1)
    return {"clusters": clusters, "n_points": int(len(df)),
            "n_clustered": int((labels >= 0).sum()), "n_clusters": len(clusters)}


# ---------------------------------------------------------------------------
# Emerging-trend alerts — z-score vs rolling baseline
# ---------------------------------------------------------------------------

def emerging_trends(window_days=45, baseline_days=365, z_threshold=2.0, min_recent=8):
    df = db.load_cases()
    latest = _latest(df)
    win_start = latest - timedelta(days=window_days)
    base_start = latest - timedelta(days=window_days + baseline_days)

    recent = df[df["RegDate"] > win_start]
    baseline = df[(df["RegDate"] <= win_start) & (df["RegDate"] > base_start)]
    n_base_windows = max(1, baseline_days / window_days)

    alerts = []
    for (did, head), g in recent.groupby(["DistrictID", "CrimeHead"]):
        rec_n = len(g)
        if rec_n < min_recent:
            continue
        # baseline per-window counts for this district+head
        b = baseline[(baseline["DistrictID"] == did) & (baseline["CrimeHead"] == head)]
        # split baseline into equal windows to estimate mean/std of a window count
        if len(b) == 0:
            base_mean, base_std = 0.0, 1.0
        else:
            b = b.copy()
            b["win"] = ((win_start - b["RegDate"]).dt.days // window_days)
            counts = b.groupby("win").size()
            counts = counts.reindex(range(int(n_base_windows)), fill_value=0)
            base_mean = float(counts.mean())
            base_std = float(counts.std(ddof=0)) or 1.0
        z = (rec_n - base_mean) / base_std
        ratio = rec_n / base_mean if base_mean > 0 else float("inf")
        if z >= z_threshold and rec_n > base_mean:
            alerts.append({
                "district_id": int(did),
                "district": g["DistrictName"].iloc[0],
                "crime_head": head,
                "recent_count": int(rec_n),
                "baseline_avg": round(base_mean, 1),
                "z_score": round(z, 1),
                "ratio": round(ratio, 1) if ratio != float("inf") else None,
                "top_subcrime": g["CrimeSubHead"].value_counts().idxmax(),
                "severity": "critical" if z >= 4 else ("high" if z >= 3 else "elevated"),
            })
    return sorted(alerts, key=lambda a: -a["z_score"])


# ---------------------------------------------------------------------------
# Link analysis — co-offending network
# ---------------------------------------------------------------------------

def _cooffending_graph(min_cases=2):
    import networkx as nx

    acc = db.load_accused()
    # keep offenders who appear in >= min_cases OR co-offend with such
    counts = acc.groupby("AccusedName")["CaseMasterID"].nunique()
    repeat = set(counts[counts >= min_cases].index)

    G = nx.Graph()
    # add nodes for repeat offenders
    for name in repeat:
        sub = acc[acc["AccusedName"] == name]
        G.add_node(name, cases=int(sub["CaseMasterID"].nunique()),
                   districts=int(sub["DistrictID"].nunique()),
                   top_mo=sub["CrimeSubHead"].value_counts().idxmax())
    # edges: co-appear in a case
    for cid, g in acc.groupby("CaseMasterID"):
        names = [n for n in g["AccusedName"].unique() if n in repeat]
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                if G.has_edge(a, b):
                    G[a][b]["weight"] += 1
                else:
                    G.add_edge(a, b, weight=1)
    return G


def communities(min_size=3, top=15):
    import community as community_louvain
    import networkx as nx

    G = _cooffending_graph(min_cases=2)
    # only nodes with at least one co-offender matter for communities
    G2 = G.subgraph([n for n in G if G.degree(n) > 0]).copy()
    if G2.number_of_nodes() == 0:
        return {"communities": [], "n_nodes": 0, "n_edges": 0}
    part = community_louvain.best_partition(G2, weight="weight", random_state=42)
    groups = {}
    for node, cid in part.items():
        groups.setdefault(cid, []).append(node)

    acc = db.load_accused()
    out = []
    for cid, members in groups.items():
        if len(members) < min_size:
            continue
        sub = acc[acc["AccusedName"].isin(members)]
        districts = sorted(sub["DistrictName"].unique().tolist())
        out.append({
            "community_id": int(cid),
            "size": len(members),
            "members": sorted(members, key=lambda m: -G2.nodes[m]["cases"]),
            "total_cases": int(sub["CaseMasterID"].nunique()),
            "districts_spanned": len(districts),
            "districts": districts,
            "dominant_mo": sub["CrimeSubHead"].value_counts().idxmax(),
            "internal_edges": int(G2.subgraph(members).number_of_edges()),
        })
    out.sort(key=lambda c: (-c["size"], -c["total_cases"]))
    return {"communities": out[:top], "n_nodes": G2.number_of_nodes(),
            "n_edges": G2.number_of_edges(), "n_communities": len(out)}


def repeat_offenders(min_cases=5, top=25):
    acc = db.load_accused()
    out = []
    for name, g in acc.groupby("AccusedName"):
        n_cases = g["CaseMasterID"].nunique()
        if n_cases < min_cases:
            continue
        out.append({
            "name": name,
            "cases": int(n_cases),
            "districts": int(g["DistrictID"].nunique()),
            "district_names": sorted(g["DistrictName"].unique().tolist()),
            "primary_mo": g["CrimeSubHead"].value_counts().idxmax(),
            "mo_breakdown": g["CrimeSubHead"].value_counts().head(3).to_dict(),
            "age": int(g["AgeYear"].iloc[0]),
        })
    out.sort(key=lambda r: -r["cases"])
    return out[:top]


def ego_network(name, depth=1):
    """Ego graph for one offender: their cases, co-accused, districts, MO."""
    acc = db.load_accused()
    ego_cases = acc[acc["AccusedName"] == name]["CaseMasterID"].unique().tolist()
    if not ego_cases:
        return {"error": f"offender '{name}' not found"}
    co = acc[acc["CaseMasterID"].isin(ego_cases)]
    nodes = [{"id": name, "type": "offender", "kind": "ego",
              "cases": len(ego_cases)}]
    edges = []
    seen = {name}
    for coname, g in co.groupby("AccusedName"):
        if coname == name:
            continue
        shared = g["CaseMasterID"].nunique()
        nodes.append({"id": coname, "type": "offender", "kind": "co-accused",
                      "cases": int(acc[acc["AccusedName"] == coname]["CaseMasterID"].nunique()),
                      "shared_cases": int(shared)})
        edges.append({"source": name, "target": coname, "weight": int(shared),
                      "label": "co-accused"})
        seen.add(coname)
    # case + district context
    ego = acc[acc["AccusedName"] == name]
    for did, g in ego.groupby("DistrictName"):
        nid = f"district:{did}"
        nodes.append({"id": nid, "type": "district", "kind": "location",
                      "cases": int(g["CaseMasterID"].nunique())})
        edges.append({"source": name, "target": nid, "weight": int(g["CaseMasterID"].nunique()),
                      "label": "operates in"})
    return {
        "ego": name,
        "profile": {
            "total_cases": len(ego_cases),
            "districts": int(ego["DistrictID"].nunique()),
            "co_offenders": len(seen) - 1,
            "primary_mo": ego["CrimeSubHead"].value_counts().idxmax(),
            "mo_breakdown": ego["CrimeSubHead"].value_counts().to_dict(),
        },
        "nodes": nodes, "edges": edges,
    }


# ---------------------------------------------------------------------------
# Anomaly detection — IsolationForest
# ---------------------------------------------------------------------------

def anomalies(contamination=0.01, top=30):
    df = db.load_cases().copy()
    df["report_delay_h"] = df["report_delay_h"].clip(lower=0).fillna(0)
    # per-case accused/victim counts
    acc_counts = db.load_accused().groupby("CaseMasterID").size()
    df["n_accused"] = df["CaseMasterID"].map(acc_counts).fillna(0)
    # rarity of this subhead within its district (low = unusual for the area)
    dh = df.groupby(["DistrictID", "CrimeMinorHeadID"]).size().rename("dh_count")
    df = df.merge(dh, on=["DistrictID", "CrimeMinorHeadID"], how="left")
    d_tot = df.groupby("DistrictID").size().rename("d_tot")
    df = df.merge(d_tot, on="DistrictID", how="left")
    df["subhead_rarity"] = 1 - (df["dh_count"] / df["d_tot"])

    feats = df[["hour", "GravityOffenceID", "n_accused", "report_delay_h",
                "subhead_rarity", "heinous"]].fillna(0)
    # prefer the PERSISTED trained model (train.py); fall back to fitting on the fly
    art = _load_model("anomaly_model.joblib")
    if art is not None:
        model = art["model"]
        feats = df[art["features"]].fillna(0)
    else:
        from sklearn.ensemble import IsolationForest
        model = IsolationForest(contamination=contamination, random_state=42, n_estimators=200).fit(feats)
    df["anom_score"] = -model.score_samples(feats)      # higher = more anomalous
    df["is_anom"] = model.predict(feats) == -1

    flagged = df[df["is_anom"]].nlargest(top, "anom_score")
    out = []
    for _, r in flagged.iterrows():
        reasons = []
        if r["report_delay_h"] > 72:
            reasons.append(f"reported {int(r['report_delay_h'])}h after incident")
        if r["subhead_rarity"] > 0.98:
            reasons.append(f"rare crime type for {r['DistrictName']}")
        if r["n_accused"] >= 4:
            reasons.append(f"{int(r['n_accused'])} accused")
        if r["hour"] in (1, 2, 3, 4):
            reasons.append(f"unusual hour ({int(r['hour'])}:00)")
        if r["heinous"]:
            reasons.append("heinous offence")
        out.append({
            "case_id": int(r["CaseMasterID"]),
            "crime_no": r["CrimeNo"],
            "district": r["DistrictName"],
            "crime": r["CrimeSubHead"],
            "date": str(r["RegDate"].date()),
            "score": round(float(r["anom_score"]), 3),
            "reasons": reasons or ["multivariate outlier"],
        })
    return {"anomalies": out, "n_flagged": int(df["is_anom"].sum()),
            "total_cases": int(len(df))}


# ---------------------------------------------------------------------------
# Predictive risk scoring (Zia AutoML proxy)
# ---------------------------------------------------------------------------

def _risk_scores_trained():
    """Forecast-based risk scoring using persisted models. Returns None if unavailable."""
    reg_art = _load_model("risk_regressor.joblib")
    clf_art = _load_model("risk_classifier.joblib")
    if reg_art is None or clf_art is None:
        return None

    mlf = _ml_features()
    panel = mlf.build_panel(db.load_cases())
    latest = mlf.latest_frame(panel)   # most recent complete feature row per district
    if latest.empty:
        return None
    X = latest[reg_art["features"]]
    pred_count = np.clip(reg_art["model"].predict(X), 0, None)
    hi_prob = clf_art["model"].predict_proba(latest[clf_art["features"]])[:, 1]

    pc_norm = (pred_count - pred_count.min()) / (pred_count.max() - pred_count.min() + 1e-9)
    df = db.load_cases()
    latest2 = _latest(df)
    r30 = df[df["RegDate"] > latest2 - timedelta(days=30)].groupby("DistrictID").size()
    heinous = df.groupby("DistrictID")["heinous"].mean()

    out = []
    for i, (_, row) in enumerate(latest.iterrows()):
        did = int(row["DistrictID"])
        score = 100 * (0.6 * float(hi_prob[i]) + 0.4 * float(pc_norm[i]))
        lat, lng = DISTRICT_CENTROIDS.get(did, (None, None))
        out.append({
            "district_id": did,
            "district": row["DistrictName"],
            "lat": lat, "lng": lng,
            "risk_score": round(score, 1),
            "predicted_next_week": int(round(float(pred_count[i]))),
            "high_risk_probability": round(float(hi_prob[i]), 3),
            "recent_30d": int(r30.get(did, 0)),
            "trend_pct": round(float((row["lag1"] - row["roll4_mean"]) / (row["roll4_mean"] + 1) * 100), 1),
            "heinous_share_pct": round(float(heinous.get(did, 0)) * 100, 1),
            "risk_band": "High" if score >= 60 else ("Medium" if score >= 35 else "Low"),
            "model": "GradientBoosting (trained)",
        })
    return sorted(out, key=lambda r: -r["risk_score"])


def risk_scores():
    """Predictive district risk.

    Uses the TRAINED models (train.py) when available: a GradientBoosting regressor
    forecasts next-week FIR count and a classifier gives the high-risk probability per
    district, combined into a 0-100 score. Falls back to a transparent heuristic blend
    (recent volume + trend + heinous share) if models aren't present yet.
    On Catalyst this is served by Zia AutoML."""
    trained = _risk_scores_trained()
    if trained is not None:
        return trained
    df = db.load_cases()
    latest = _latest(df)
    r30 = df[df["RegDate"] > latest - timedelta(days=30)].groupby("DistrictID").size()
    p30 = df[(df["RegDate"] <= latest - timedelta(days=30)) &
             (df["RegDate"] > latest - timedelta(days=60))].groupby("DistrictID").size()
    heinous = df.groupby("DistrictID")["heinous"].mean()
    vol = df.groupby("DistrictID").size()

    def norm(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-9)

    trend = (r30 - p30) / (p30 + 1)
    out = []
    for did in vol.index:
        v = norm(vol).get(did, 0)
        t = float(np.clip(trend.get(did, 0), -1, 3)) / 3
        h = float(heinous.get(did, 0))
        score = 100 * (0.45 * v + 0.35 * max(t, 0) + 0.20 * h)
        lat, lng = DISTRICT_CENTROIDS.get(int(did), (None, None))
        out.append({
            "district_id": int(did),
            "district": df[df["DistrictID"] == did]["DistrictName"].iloc[0],
            "lat": lat, "lng": lng,
            "risk_score": round(float(score), 1),
            "recent_30d": int(r30.get(did, 0)),
            "trend_pct": round(float(trend.get(did, 0)) * 100, 1),
            "heinous_share_pct": round(h * 100, 1),
            "risk_band": "High" if score >= 60 else ("Medium" if score >= 30 else "Low"),
        })
    return sorted(out, key=lambda r: -r["risk_score"])


# ---------------------------------------------------------------------------
# Temporal patterns
# ---------------------------------------------------------------------------

def timeseries(crime_head=None, district_id=None):
    df = db.load_cases()
    if crime_head:
        df = df[df["CrimeHead"] == crime_head]
    if district_id:
        df = df[df["DistrictID"] == int(district_id)]
    monthly = df.groupby("month").size().reset_index(name="count")
    # day-of-week x hour matrix (for temporal heatmap)
    mat = (df.dropna(subset=["hour", "dow"])
             .groupby(["dow", "hour"]).size().reset_index(name="count"))
    return {
        "monthly": monthly.to_dict("records"),
        "dow_hour": mat.to_dict("records"),
        "by_head": df["CrimeHead"].value_counts().to_dict(),
    }
