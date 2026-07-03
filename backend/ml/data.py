"""Data access + validation for the ML pipeline.

Reads the FIR fact tables (via the service's db layer) and runs data-quality gates
before any training happens — a real pipeline fails fast on bad data rather than
silently training on it.
"""
from __future__ import annotations

import hashlib
import os
import sys

import pandas as pd

# reuse the service DB layer
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "appsail_ml"))
import db  # noqa: E402


class DataValidationError(Exception):
    pass


def load_cases() -> pd.DataFrame:
    db.clear_cache()
    return db.load_cases()


def validate(df: pd.DataFrame) -> dict:
    """Data-quality gates. Raises DataValidationError on hard failures; returns a
    report of soft checks for logging."""
    errors, warnings = [], []

    if len(df) < 2000:
        errors.append(f"too few cases: {len(df)} (< 2000)")

    required = ["CaseMasterID", "DistrictID", "CrimeMajorHeadID", "RegDate", "cleared", "heinous"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"missing columns: {missing}")

    if "RegDate" in df.columns:
        span_days = (df["RegDate"].max() - df["RegDate"].min()).days
        if span_days < 365:
            errors.append(f"time span too short for forecasting: {span_days}d (< 365)")
        null_dates = int(df["RegDate"].isna().sum())
        if null_dates:
            warnings.append(f"{null_dates} null RegDate rows")

    if "DistrictID" in df.columns and df["DistrictID"].nunique() < 5:
        errors.append(f"too few districts: {df['DistrictID'].nunique()}")

    if "cleared" in df.columns and not df["cleared"].isin([0, 1]).all():
        warnings.append("cleared contains non-binary values")

    if errors:
        raise DataValidationError("; ".join(errors))

    return {
        "n_cases": int(len(df)),
        "n_districts": int(df["DistrictID"].nunique()),
        "date_from": str(df["RegDate"].min().date()),
        "date_to": str(df["RegDate"].max().date()),
        "span_days": int((df["RegDate"].max() - df["RegDate"].min()).days),
        "warnings": warnings,
        "data_fingerprint": fingerprint(df),
    }


def fingerprint(df: pd.DataFrame) -> str:
    """Stable hash of the data used for a training run (reproducibility / lineage)."""
    h = hashlib.sha256()
    h.update(str(len(df)).encode())
    h.update(str(df["CaseMasterID"].sum()).encode())
    h.update(str(df["RegDate"].min()).encode())
    h.update(str(df["RegDate"].max()).encode())
    return h.hexdigest()[:16]
