"""
Shared test fixtures.

Generates a small synthetic dataset once per test session into a temp dir, builds the
SQLite DB, and points the service at it via KSP_DB — so tests run against real generated
data without touching the developer's data/out.
"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# make the project's flat-import modules importable
for p in ["data/generator", "data", "backend/appsail_ml", "backend/ml"]:
    sys.path.insert(0, str(ROOT / p))


@pytest.fixture(scope="session", autouse=True)
def dataset(tmp_path_factory):
    """Generate ~900 FIRs + build SQLite once; expose via KSP_DB for the whole session."""
    import build_sqlite
    import generate

    out = tmp_path_factory.mktemp("ksp_data")
    generate.generate(num_cases=900, seed=123, outdir=str(out))
    db_path = out / "ksp.db"
    build_sqlite.build(str(out), str(db_path))

    os.environ["KSP_DB"] = str(db_path)
    import db
    db.clear_cache()
    yield {"out": out, "db": db_path}


@pytest.fixture(scope="session")
def cases(dataset):
    import db
    return db.load_cases()
