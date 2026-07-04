"""Smoke tests for the FastAPI endpoints via TestClient."""
from fastapi.testclient import TestClient

import app as app_module

client = TestClient(app_module.app)


def test_health(dataset):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_kpis_endpoint(dataset):
    r = client.get("/api/kpis")
    assert r.status_code == 200
    assert r.json()["total_cases"] == 900


def test_districts_endpoint(dataset):
    r = client.get("/api/districts")
    assert r.status_code == 200 and isinstance(r.json(), list)


def test_hotspots_endpoint(dataset):
    r = client.get("/api/hotspots", params={"min_samples": 5})
    assert r.status_code == 200 and "clusters" in r.json()


def test_risk_endpoint(dataset):
    r = client.get("/api/risk")
    assert r.status_code == 200 and "districts" in r.json()


def test_nlp_classify_graceful_without_model(dataset):
    """No NLP champion trained in tests -> endpoint must degrade gracefully, not 500."""
    r = client.get("/api/nlp/classify", params={"text": "accused stole a mobile phone"})
    assert r.status_code == 200
    body = r.json()
    assert "error" in body or "predicted_head" in body
