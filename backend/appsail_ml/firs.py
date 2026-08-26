"""FIR register — list/filter existing FIRs, add new ones, close/reopen cases.

Reads reuse db.load_cases() (the cached denormalised case frame used across the
service); writes go straight to CaseMaster / Inv_OccuranceTime / ComplainantDetails
via a plain sqlite3 connection, then clear the cache so the next read is consistent.
"""
from __future__ import annotations

import random
from datetime import datetime

import db
from analytics import DISTRICT_CENTROIDS

# The DB keeps the full 7-value NCRB-style status (CaseStatusMaster). The FIR
# register groups them into a simple Open/Closed view for the UI: a case is
# "closed" once it's charge-sheeted, convicted, acquitted or closed outright;
# it's still "open" while under investigation or awaiting trial.
OPEN_STATUSES = {1, 7}              # Under Investigation, Pending Trial
CLOSED_STATUSES = {2, 3, 4, 5, 6}   # Charge Sheeted, Closed-Undetected/False, Convicted, Acquitted
REOPEN_STATUS_ID = 1                # "Under Investigation"
KARNATAKA_CENTROID = (15.0, 75.7)   # fallback if a district has no known centroid


def _status_group(status_id: int) -> str:
    return "Open" if status_id in OPEN_STATUSES else "Closed"


def lookups() -> dict:
    """Dropdown data for the Add-FIR form and the register's filters."""
    with db.connect() as con:
        districts = [dict(r) for r in con.execute(
            "SELECT DistrictID AS id, DistrictName AS name FROM District ORDER BY DistrictName")]
        stations = [dict(r) for r in con.execute(
            "SELECT UnitID AS id, UnitName AS name, DistrictID AS district_id FROM Unit "
            "WHERE DistrictID IS NOT NULL ORDER BY UnitName")]
        heads = [dict(r) for r in con.execute(
            "SELECT CrimeHeadID AS id, CrimeGroupName AS name FROM CrimeHead ORDER BY CrimeHeadID")]
        subheads = [dict(r) for r in con.execute(
            "SELECT CrimeSubHeadID AS id, CrimeHeadID AS head_id, CrimeHeadName AS name "
            "FROM CrimeSubHead ORDER BY CrimeHeadID, SeqID")]
        gravities = [dict(r) for r in con.execute(
            "SELECT GravityOffenceID AS id, LookupValue AS name FROM GravityOffence ORDER BY GravityOffenceID")]
        categories = [dict(r) for r in con.execute(
            "SELECT CaseCategoryID AS id, LookupValue AS name FROM CaseCategory ORDER BY CaseCategoryID")]
        statuses = [
            {"id": r["CaseStatusID"], "name": r["CaseStatusName"], "group": _status_group(r["CaseStatusID"])}
            for r in con.execute("SELECT CaseStatusID, CaseStatusName FROM CaseStatusMaster ORDER BY CaseStatusID")
        ]
    return {
        "districts": districts,
        "police_stations": stations,
        "crime_heads": heads,
        "crime_subheads": subheads,
        "gravities": gravities,
        "categories": categories,
        "statuses": statuses,
    }


def list_firs(
    status_group: str | None = None,
    status_id: int | None = None,
    district_id: int | None = None,
    police_station_id: int | None = None,
    crime_head_id: int | None = None,
    crime_subhead_id: int | None = None,
    gravity_id: int | None = None,
    category_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    df = db.load_cases()

    if status_group == "open":
        df = df[df["CaseStatusID"].isin(OPEN_STATUSES)]
    elif status_group == "closed":
        df = df[df["CaseStatusID"].isin(CLOSED_STATUSES)]
    if status_id is not None:
        df = df[df["CaseStatusID"] == status_id]
    if district_id is not None:
        df = df[df["DistrictID"] == district_id]
    if police_station_id is not None:
        df = df[df["PoliceStationID"] == police_station_id]
    if crime_head_id is not None:
        df = df[df["CrimeMajorHeadID"] == crime_head_id]
    if crime_subhead_id is not None:
        df = df[df["CrimeMinorHeadID"] == crime_subhead_id]
    if gravity_id is not None:
        df = df[df["GravityOffenceID"] == gravity_id]
    if category_id is not None:
        df = df[df["CaseCategoryID"] == category_id]
    if date_from:
        df = df[df["RegDate"] >= date_from]
    if date_to:
        df = df[df["RegDate"] <= date_to + " 23:59:59"]
    if q and q.strip():
        ql = q.strip().lower()
        mask = (
            df["CrimeNo"].str.lower().str.contains(ql, na=False, regex=False)
            | df["CaseNo"].str.lower().str.contains(ql, na=False, regex=False)
            | df["DistrictName"].str.lower().str.contains(ql, na=False, regex=False)
            | df["UnitName"].str.lower().str.contains(ql, na=False, regex=False)
        )
        df = df[mask]

    df = df.sort_values("RegDate", ascending=False)
    total = int(len(df))
    start = max(0, (page - 1) * page_size)
    page_df = df.iloc[start : start + page_size]

    rows = []
    for _, r in page_df.iterrows():
        sid = int(r["CaseStatusID"])
        rows.append({
            "case_master_id": int(r["CaseMasterID"]),
            "crime_no": str(r["CrimeNo"]),
            "case_no": str(r["CaseNo"]),
            "registered_date": str(r["CrimeRegisteredDate"])[:10],
            "district_id": int(r["DistrictID"]),
            "district": str(r["DistrictName"]),
            "police_station": str(r["UnitName"]),
            "crime_head": str(r["CrimeHead"]),
            "crime_subhead": str(r["CrimeSubHead"]),
            "gravity": str(r["Gravity"]),
            "category": str(r["Category"]),
            "status_id": sid,
            "status": str(r["Status"]),
            "status_group": _status_group(sid),
            "brief_facts": (str(r["BriefFacts"]) or "")[:220],
        })
    return {"rows": rows, "total": total, "page": page, "page_size": page_size}


def create_fir(payload: dict) -> dict:
    district_id = int(payload["district_id"])
    unit_id = int(payload["police_station_id"])
    category = int(payload.get("category_id") or 1)
    gravity = int(payload["gravity_id"])
    subhead = int(payload["crime_subhead_id"])
    complainant_name = (payload.get("complainant_name") or "").strip()
    brief_facts = (payload.get("brief_facts") or "").strip()
    incident_from = (payload.get("incident_from") or "").strip().replace("T", " ")
    if not incident_from:
        raise ValueError("incident_from is required")
    incident_to = (payload.get("incident_to") or "").strip().replace("T", " ") or incident_from
    info_received = (payload.get("info_received") or "").strip().replace("T", " ") or \
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reg_date = incident_from.split(" ")[0]
    year = int(reg_date[:4])

    con = db.connect()
    try:
        cur = con.cursor()

        head_row = cur.execute(
            "SELECT ch.CrimeHeadID, ch.CrimeGroupName, sh.CrimeHeadName "
            "FROM CrimeSubHead sh JOIN CrimeHead ch ON sh.CrimeHeadID = ch.CrimeHeadID "
            "WHERE sh.CrimeSubHeadID = ?", (subhead,),
        ).fetchone()
        if head_row is None:
            raise ValueError(f"unknown crime sub-head {subhead}")
        head_id, head_name, subhead_name = head_row

        district_row = cur.execute(
            "SELECT DistrictName FROM District WHERE DistrictID = ?", (district_id,)
        ).fetchone()
        if district_row is None:
            raise ValueError(f"unknown district {district_id}")
        district_name = district_row[0]

        unit_row = cur.execute(
            "SELECT UnitName, DistrictID FROM Unit WHERE UnitID = ?", (unit_id,)
        ).fetchone()
        if unit_row is None or unit_row[1] != district_id:
            raise ValueError("police station does not belong to the selected district")
        unit_name = unit_row[0]

        gravity_row = cur.execute(
            "SELECT LookupValue FROM GravityOffence WHERE GravityOffenceID = ?", (gravity,)
        ).fetchone()
        if gravity_row is None:
            raise ValueError(f"unknown gravity {gravity}")
        gravity_name = gravity_row[0]

        category_row = cur.execute(
            "SELECT LookupValue FROM CaseCategory WHERE CaseCategoryID = ?", (category,)
        ).fetchone()
        category_name = category_row[0] if category_row else "FIR"

        # next CaseMasterID + a station/category/year-scoped serial for CrimeNo/CaseNo,
        # following the same format the synthetic generator uses.
        case_id = (cur.execute("SELECT COALESCE(MAX(CaseMasterID), 0) + 1 FROM CaseMaster").fetchone()[0])
        prefix_like = f"{category:01d}{district_id:04d}{unit_id:04d}{year:04d}%"
        serial = 1
        for (cn,) in cur.execute(
            "SELECT CrimeNo FROM CaseMaster WHERE PoliceStationID = ? AND CaseCategoryID = ? AND CrimeNo LIKE ?",
            (unit_id, category, prefix_like),
        ):
            try:
                serial = max(serial, int(cn[-5:]) + 1)
            except ValueError:
                continue
        crime_no = f"{category:01d}{district_id:04d}{unit_id:04d}{year:04d}{serial:05d}"
        case_no = f"{year:04d}{serial:05d}"

        base_lat, base_lng = DISTRICT_CENTROIDS.get(district_id, KARNATAKA_CENTROID)
        lat = round(base_lat + random.uniform(-0.03, 0.03), 6)
        lng = round(base_lng + random.uniform(-0.03, 0.03), 6)

        cur.execute(
            "INSERT INTO CaseMaster (CaseMasterID, CrimeNo, CaseNo, CrimeRegisteredDate, PolicePersonID, "
            "PoliceStationID, CaseCategoryID, GravityOffenceID, CrimeMajorHeadID, CrimeMinorHeadID, "
            "CaseStatusID, CourtID) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (case_id, crime_no, case_no, reg_date, None, unit_id, category, gravity, head_id, subhead, 1, None),
        )
        cur.execute(
            "INSERT INTO Inv_OccuranceTime (CaseMasterID, IncidentFromDate, IncidentToDate, InfoReceivedPSDate, "
            "latitude, longitude, BriefFacts) VALUES (?,?,?,?,?,?,?)",
            (case_id, incident_from, incident_to, info_received, lat, lng, brief_facts),
        )
        if complainant_name:
            comp_id = cur.execute("SELECT COALESCE(MAX(ComplainantID), 0) + 1 FROM ComplainantDetails").fetchone()[0]
            cur.execute(
                "INSERT INTO ComplainantDetails (ComplainantID, CaseMasterID, ComplainantName, AgeYear, "
                "OccupationID, ReligionID, CasteID, GenderID) VALUES (?,?,?,?,?,?,?,?)",
                (comp_id, case_id, complainant_name, payload.get("complainant_age"), None, None, None,
                 payload.get("complainant_gender_id")),
            )
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    db.clear_cache()
    return {
        "case_master_id": case_id,
        "crime_no": crime_no,
        "case_no": case_no,
        "registered_date": reg_date,
        "district_id": district_id,
        "district": district_name,
        "police_station": unit_name,
        "crime_head": head_name,
        "crime_subhead": subhead_name,
        "gravity": gravity_name,
        "category": category_name,
        "status_id": 1,
        "status": "Under Investigation",
        "status_group": "Open",
        "brief_facts": brief_facts[:220],
    }


def update_status(case_master_id: int, status_id: int) -> dict:
    con = db.connect()
    try:
        cur = con.cursor()
        row = cur.execute("SELECT CaseMasterID FROM CaseMaster WHERE CaseMasterID = ?", (case_master_id,)).fetchone()
        if row is None:
            raise KeyError(f"FIR {case_master_id} not found")
        status_row = cur.execute(
            "SELECT CaseStatusName FROM CaseStatusMaster WHERE CaseStatusID = ?", (status_id,)
        ).fetchone()
        if status_row is None:
            raise ValueError(f"unknown status {status_id}")
        cur.execute("UPDATE CaseMaster SET CaseStatusID = ? WHERE CaseMasterID = ?", (status_id, case_master_id))
        con.commit()
        status_name = status_row[0]
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    db.clear_cache()
    return {
        "case_master_id": case_master_id,
        "status_id": status_id,
        "status": status_name,
        "status_group": _status_group(status_id),
    }
