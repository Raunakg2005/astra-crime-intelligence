"""
Build a queryable SQLite database from the generated CSVs.

This mirrors the Catalyst Data Store relational schema so the analytics service and
the UI prototype can query real data locally today, and the same DDL/queries port to
Catalyst Data Store later. Adds primary keys, foreign-key-style indexes, and the
"hot" indexes analytics needs (dates, district, sub-head, geo, accused name).

Usage:
    python build_sqlite.py --csv out --db out/ksp.db
"""
from __future__ import annotations

import argparse
import csv
import os
import sqlite3

# table -> (columns with sqlite types). Order matters only for readability.
SCHEMA = {
    "State": "StateID INTEGER PRIMARY KEY, StateName TEXT, NationalityID INTEGER, Active INTEGER",
    "District": "DistrictID INTEGER PRIMARY KEY, DistrictName TEXT, StateID INTEGER, Active INTEGER",
    "UnitType": "UnitTypeID INTEGER PRIMARY KEY, UnitTypeName TEXT, CityDistState TEXT, Hierarchy INTEGER, Active INTEGER",
    "Unit": "UnitID INTEGER PRIMARY KEY, UnitName TEXT, TypeID INTEGER, ParentUnit INTEGER, NationalityID INTEGER, StateID INTEGER, DistrictID INTEGER, Active INTEGER",
    "Rank": "RankID INTEGER PRIMARY KEY, RankName TEXT, Hierarchy INTEGER, Active INTEGER",
    "Designation": "DesignationID INTEGER PRIMARY KEY, DesignationName TEXT, Active INTEGER, SortOrder INTEGER",
    "Employee": "EmployeeID INTEGER PRIMARY KEY, DistrictID INTEGER, UnitID INTEGER, RankID INTEGER, DesignationID INTEGER, KGID TEXT, FirstName TEXT, EmployeeDOB TEXT, GenderID INTEGER, BloodGroupID INTEGER, PhysicallyChallenged INTEGER, AppointmentDate TEXT",
    "CaseCategory": "CaseCategoryID INTEGER PRIMARY KEY, LookupValue TEXT",
    "GravityOffence": "GravityOffenceID INTEGER PRIMARY KEY, LookupValue TEXT",
    "CaseStatusMaster": "CaseStatusID INTEGER PRIMARY KEY, CaseStatusName TEXT",
    "ReligionMaster": "ReligionID INTEGER PRIMARY KEY, ReligionName TEXT",
    "CasteMaster": "caste_master_id INTEGER PRIMARY KEY, caste_master_name TEXT",
    "OccupationMaster": "OccupationID INTEGER PRIMARY KEY, OccupationName TEXT",
    "CrimeHead": "CrimeHeadID INTEGER PRIMARY KEY, CrimeGroupName TEXT, Active INTEGER",
    "CrimeSubHead": "CrimeSubHeadID INTEGER PRIMARY KEY, CrimeHeadID INTEGER, CrimeHeadName TEXT, SeqID INTEGER",
    "Act": "ActCode TEXT PRIMARY KEY, ActDescription TEXT, ShortName TEXT, Active INTEGER",
    "Section": "ActCode TEXT, SectionCode TEXT, SectionDescription TEXT, Active INTEGER",
    "CrimeHeadActSection": "CrimeHeadID INTEGER, ActCode TEXT, SectionCode TEXT",
    "Court": "CourtID INTEGER PRIMARY KEY, CourtName TEXT, DistrictID INTEGER, StateID INTEGER, Active INTEGER",
    "CaseMaster": "CaseMasterID INTEGER PRIMARY KEY, CrimeNo TEXT, CaseNo TEXT, CrimeRegisteredDate TEXT, PolicePersonID INTEGER, PoliceStationID INTEGER, CaseCategoryID INTEGER, GravityOffenceID INTEGER, CrimeMajorHeadID INTEGER, CrimeMinorHeadID INTEGER, CaseStatusID INTEGER, CourtID INTEGER",
    "Inv_OccuranceTime": "CaseMasterID INTEGER PRIMARY KEY, IncidentFromDate TEXT, IncidentToDate TEXT, InfoReceivedPSDate TEXT, latitude REAL, longitude REAL, BriefFacts TEXT",
    "ComplainantDetails": "ComplainantID INTEGER PRIMARY KEY, CaseMasterID INTEGER, ComplainantName TEXT, AgeYear INTEGER, OccupationID INTEGER, ReligionID INTEGER, CasteID INTEGER, GenderID INTEGER",
    "Victim": "VictimMasterID INTEGER PRIMARY KEY, CaseMasterID INTEGER, VictimName TEXT, AgeYear INTEGER, GenderID INTEGER, VictimPolice INTEGER",
    "Accused": "AccusedMasterID INTEGER PRIMARY KEY, CaseMasterID INTEGER, AccusedName TEXT, AgeYear INTEGER, GenderID INTEGER, PersonID TEXT",
    "ActSectionAssociation": "CaseMasterID INTEGER, ActID TEXT, SectionID TEXT, ActOrderID INTEGER, SectionOrderID INTEGER",
    "ArrestSurrender": "ArrestSurrenderID INTEGER PRIMARY KEY, CaseMasterID INTEGER, ArrestSurrenderTypeID INTEGER, ArrestSurrenderDate TEXT, ArrestSurrenderStateId INTEGER, ArrestSurrenderDistrictId INTEGER, PoliceStationID INTEGER, IOID INTEGER, CourtID INTEGER, AccusedMasterID INTEGER, IsAccused INTEGER, IsComplainantAccused INTEGER",
    "inv_arrestsurrenderaccused": "ArrestSurrenderID INTEGER, AccusedMasterID INTEGER",
    "ChargesheetDetails": "CSID INTEGER PRIMARY KEY, CaseMasterID INTEGER, csdate TEXT, cstype TEXT, PolicePersonID INTEGER",
}

# hot indexes for analytics
INDEXES = [
    "CREATE INDEX idx_cm_regdate ON CaseMaster(CrimeRegisteredDate)",
    "CREATE INDEX idx_cm_station ON CaseMaster(PoliceStationID)",
    "CREATE INDEX idx_cm_subhead ON CaseMaster(CrimeMinorHeadID)",
    "CREATE INDEX idx_cm_head ON CaseMaster(CrimeMajorHeadID)",
    "CREATE INDEX idx_cm_status ON CaseMaster(CaseStatusID)",
    "CREATE INDEX idx_inv_geo ON Inv_OccuranceTime(latitude, longitude)",
    "CREATE INDEX idx_acc_case ON Accused(CaseMasterID)",
    "CREATE INDEX idx_acc_name ON Accused(AccusedName)",
    "CREATE INDEX idx_vic_case ON Victim(CaseMasterID)",
    "CREATE INDEX idx_comp_case ON ComplainantDetails(CaseMasterID)",
    "CREATE INDEX idx_asa_case ON ActSectionAssociation(CaseMasterID)",
    "CREATE INDEX idx_arr_case ON ArrestSurrender(CaseMasterID)",
    "CREATE INDEX idx_unit_district ON Unit(DistrictID)",
]


def build(csv_dir: str, db_path: str):
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("PRAGMA journal_mode=OFF")
    cur.execute("PRAGMA synchronous=OFF")

    loaded = {}
    for table, cols in SCHEMA.items():
        cur.execute(f"CREATE TABLE {table} ({cols})")
        csv_path = os.path.join(csv_dir, f"{table}.csv")
        if not os.path.exists(csv_path):
            print(f"  WARN: missing {csv_path}")
            continue
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            placeholders = ",".join("?" * len(header))
            colnames = ",".join(f'"{h}"' for h in header)
            rows = ([v if v != "" else None for v in row] for row in reader)
            cur.executemany(
                f"INSERT INTO {table} ({colnames}) VALUES ({placeholders})", rows
            )
        loaded[table] = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    for idx in INDEXES:
        try:
            cur.execute(idx)
        except sqlite3.OperationalError as e:
            print(f"  index skipped: {e}")

    con.commit()
    cur.execute("ANALYZE")
    con.commit()
    con.close()
    return loaded


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=os.path.join(os.path.dirname(__file__), "out"))
    p.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "out", "ksp.db"))
    args = p.parse_args()
    csv_dir = os.path.abspath(args.csv)
    db_path = os.path.abspath(args.db)
    print(f"Building {db_path} from {csv_dir}")
    loaded = build(csv_dir, db_path)
    total = sum(loaded.values())
    for t, n in sorted(loaded.items()):
        print(f"  {t:30s} {n:>8,} rows")
    print(f"  {'TOTAL':30s} {total:>8,} rows")
    print(f"  DB size: {os.path.getsize(db_path):,} bytes")


if __name__ == "__main__":
    main()
