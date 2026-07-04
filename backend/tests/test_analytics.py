"""Tests for the analytics service functions (run against the session dataset)."""
import analytics as A


def test_kpis(dataset):
    k = A.kpis()
    assert k["total_cases"] == 900
    assert 0 <= k["clearance_rate_pct"] <= 100
    assert k["districts"] > 0


def test_district_summary(dataset):
    d = A.district_summary()
    assert isinstance(d, list) and d
    row = d[0]
    for key in ("district", "total_cases", "clearance_pct", "top_crime_head", "lat", "lng"):
        assert key in row


def test_hotspots_structure(dataset):
    h = A.hotspots(min_samples=5)          # low threshold for the small dataset
    assert set(["clusters", "n_points", "n_clusters"]).issubset(h)
    assert isinstance(h["clusters"], list)


def test_emerging_trends(dataset):
    alerts = A.emerging_trends(z_threshold=1.5, min_recent=3)
    assert isinstance(alerts, list)
    for a in alerts:
        assert {"district", "crime_head", "z_score", "severity"}.issubset(a)


def test_repeat_offenders_and_ego(dataset):
    offs = A.repeat_offenders(min_cases=2, top=5)
    assert isinstance(offs, list)
    if offs:
        ego = A.ego_network(offs[0]["name"])
        assert ego["ego"] == offs[0]["name"]
        assert ego["nodes"] and "profile" in ego


def test_communities(dataset):
    c = A.communities(min_size=2, top=5)
    assert "communities" in c and "n_nodes" in c


def test_anomalies_fallback(dataset):
    """No trained model in tests -> analytics fits Isolation Forest on the fly."""
    a = A.anomalies(top=5)
    assert "anomalies" in a and a["total_cases"] == 900


def test_risk_scores(dataset):
    r = A.risk_scores()
    assert isinstance(r, list) and r
    assert {"district", "risk_score", "risk_band"}.issubset(r[0])


def test_risk_scores_heuristic_is_json_safe(dataset, monkeypatch):
    """Regression: with no trained models (CI), the heuristic fallback must not emit
    NaN/inf (FastAPI's JSON encoder rejects them). Forces the fallback path."""
    import json
    import math
    monkeypatch.setattr(A, "_risk_scores_trained", lambda: None)
    r = A.risk_scores()
    json.dumps(r)                                   # must not raise
    for row in r:
        for key in ("risk_score", "trend_pct", "heinous_share_pct"):
            assert math.isfinite(row[key]), f"{key} not finite for {row['district']}"


def test_timeseries(dataset):
    ts = A.timeseries()
    assert ts["monthly"] and ts["by_head"]
