"""Feature engineering — district x ISO-week panel with lag / rolling / seasonal
features. Used identically at training and inference time (no train/serve skew).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import HIGH_RISK_QUANTILE, RISK_FEATURES


def build_panel(cases: pd.DataFrame) -> pd.DataFrame:
    """Return the full weekly panel with features + next-week target (NaNs kept)."""
    df = cases.copy()
    df["week"] = df["RegDate"].dt.to_period("W").dt.start_time
    agg = (df.groupby(["DistrictID", "DistrictName", "week"])
             .agg(count=("CaseMasterID", "size"),
                  heinous=("heinous", "sum"),
                  cleared=("cleared", "sum"))
             .reset_index())

    # dense weekly grid (fill gaps with 0 so lags are correct)
    weeks = pd.date_range(agg["week"].min(), agg["week"].max(), freq="W-MON")
    frames = []
    for (did, dname), g in agg.groupby(["DistrictID", "DistrictName"]):
        g = g.set_index("week").reindex(weeks, fill_value=0)
        g["DistrictID"], g["DistrictName"] = did, dname
        frames.append(g.reset_index().rename(columns={"index": "week"}))
    panel = pd.concat(frames, ignore_index=True).sort_values(["DistrictID", "week"])

    order = {w: i for i, w in enumerate(sorted(panel["week"].unique()))}
    panel["week_idx"] = panel["week"].map(order)

    def per_district(g):
        g = g.sort_values("week_idx")
        c = g["count"]
        for k in (1, 2, 3, 4):
            g[f"lag{k}"] = c.shift(k)
        g["roll4_mean"] = c.shift(1).rolling(4).mean()
        g["roll4_std"] = c.shift(1).rolling(4).std()
        g["roll8_mean"] = c.shift(1).rolling(8).mean()
        g["roll12_mean"] = c.shift(1).rolling(12).mean()
        g["momentum"] = c.shift(1) - c.shift(1).rolling(4).mean()   # short-term vs medium-term
        g["heinous_lag1"] = g["heinous"].shift(1)
        g["clear_rate_lag1"] = (g["cleared"].shift(1) / c.shift(1)).fillna(0)
        g["district_base"] = c.expanding().mean().shift(1)
        g["target_count"] = c.shift(-1)                              # NEXT week
        return g

    panel = panel.groupby("DistrictID", group_keys=False).apply(per_district)

    m = panel["week"].dt.month
    woy = panel["week"].dt.isocalendar().week.astype(int)
    panel["month_sin"] = np.sin(2 * np.pi * m / 12)
    panel["month_cos"] = np.cos(2 * np.pi * m / 12)
    panel["woy_sin"] = np.sin(2 * np.pi * woy / 52)
    panel["woy_cos"] = np.cos(2 * np.pi * woy / 52)
    return panel.replace([np.inf, -np.inf], np.nan)


def training_frame(panel: pd.DataFrame):
    """Rows with features + target present (for training)."""
    return panel.dropna(subset=RISK_FEATURES + ["target_count"]).copy()


def latest_frame(panel: pd.DataFrame):
    """Most recent complete feature row per district (for forecasting next week)."""
    valid = panel.dropna(subset=RISK_FEATURES)
    return valid.sort_values("week_idx").groupby("DistrictID").tail(1).copy()


def high_risk_labels(frame: pd.DataFrame, thresholds: dict) -> pd.Series:
    """Binary high-risk target: next-week count >= district threshold."""
    return (frame["target_count"] >= frame["DistrictID"].map(thresholds)).astype(int)


def learn_thresholds(train_frame: pd.DataFrame) -> dict:
    """Per-district high-risk threshold, learnt on TRAIN only (no leakage)."""
    return train_frame.groupby("DistrictID")["target_count"].quantile(HIGH_RISK_QUANTILE).to_dict()
