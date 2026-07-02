"""SQLite access + cached dataframe loading for the analytics service.

Locally this reads data/out/ksp.db. On Catalyst AppSail the same queries target the
Catalyst Data Store (swap the connection layer; SQL is standard).
"""
from __future__ import annotations

import functools
import os
import sqlite3

import pandas as pd

# default: repo data/out/ksp.db  (override with KSP_DB env var)
_DEFAULT_DB = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "out", "ksp.db")
)


def db_path() -> str:
    return os.environ.get("KSP_DB", _DEFAULT_DB)


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(db_path())
    con.row_factory = sqlite3.Row
    return con


def query(sql: str, params=()) -> pd.DataFrame:
    with connect() as con:
        return pd.read_sql_query(sql, con, params=params)


@functools.lru_cache(maxsize=1)
def load_cases() -> pd.DataFrame:
    """Denormalised case fact table — the analytical backbone.

    One row per FIR with geography, taxonomy, time, status joined in.
    Cached; call load_cases.cache_clear() after regenerating data.
    """
    sql = """
    SELECT cm.CaseMasterID, cm.CrimeNo, cm.CaseNo, cm.CrimeRegisteredDate,
           cm.CaseCategoryID, cm.GravityOffenceID, cm.CrimeMajorHeadID, cm.CrimeMinorHeadID,
           cm.CaseStatusID, cm.PoliceStationID, cm.CourtID,
           u.UnitName, u.DistrictID,
           d.DistrictName,
           ch.CrimeGroupName AS CrimeHead,
           sh.CrimeHeadName  AS CrimeSubHead,
           g.LookupValue     AS Gravity,
           st.CaseStatusName AS Status,
           cc.LookupValue    AS Category,
           io.IncidentFromDate, io.IncidentToDate, io.InfoReceivedPSDate,
           io.latitude, io.longitude, io.BriefFacts
    FROM CaseMaster cm
    JOIN Unit u              ON cm.PoliceStationID = u.UnitID
    JOIN District d          ON u.DistrictID = d.DistrictID
    JOIN CrimeHead ch        ON cm.CrimeMajorHeadID = ch.CrimeHeadID
    JOIN CrimeSubHead sh     ON cm.CrimeMinorHeadID = sh.CrimeSubHeadID
    JOIN GravityOffence g    ON cm.GravityOffenceID = g.GravityOffenceID
    JOIN CaseStatusMaster st ON cm.CaseStatusID = st.CaseStatusID
    JOIN CaseCategory cc     ON cm.CaseCategoryID = cc.CaseCategoryID
    JOIN Inv_OccuranceTime io ON cm.CaseMasterID = io.CaseMasterID
    """
    df = query(sql)
    df["RegDate"] = pd.to_datetime(df["CrimeRegisteredDate"])
    df["IncidentFrom"] = pd.to_datetime(df["IncidentFromDate"], errors="coerce")
    df["InfoRecv"] = pd.to_datetime(df["InfoReceivedPSDate"], errors="coerce")
    df["hour"] = df["IncidentFrom"].dt.hour
    df["dow"] = df["IncidentFrom"].dt.dayofweek
    df["month"] = df["RegDate"].dt.to_period("M").astype(str)
    df["cleared"] = df["CaseStatusID"].isin([2, 5]).astype(int)
    df["heinous"] = (df["GravityOffenceID"] == 1).astype(int)
    df["report_delay_h"] = (df["InfoRecv"] - df["IncidentFrom"]).dt.total_seconds() / 3600.0
    return df


@functools.lru_cache(maxsize=1)
def load_accused() -> pd.DataFrame:
    """Accused rows joined to case geography/taxonomy — basis for link analysis."""
    sql = """
    SELECT a.AccusedMasterID, a.CaseMasterID, a.AccusedName, a.AgeYear, a.GenderID,
           u.DistrictID, d.DistrictName, cm.CrimeMinorHeadID,
           sh.CrimeHeadName AS CrimeSubHead, cm.CrimeRegisteredDate
    FROM Accused a
    JOIN CaseMaster cm   ON a.CaseMasterID = cm.CaseMasterID
    JOIN Unit u          ON cm.PoliceStationID = u.UnitID
    JOIN District d      ON u.DistrictID = d.DistrictID
    JOIN CrimeSubHead sh ON cm.CrimeMinorHeadID = sh.CrimeSubHeadID
    """
    return query(sql)


def clear_cache():
    load_cases.cache_clear()
    load_accused.cache_clear()
