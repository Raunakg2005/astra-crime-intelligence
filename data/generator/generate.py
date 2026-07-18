"""
KSP Crime Intelligence — synthetic FIR dataset generator.

Emits one CSV per table of the official Police FIR ER schema into ``data/out``.
Uses only the Python standard library (portable, zero-install).

The generator deliberately *plants signal* so every analytics feature has something
real to find:
  * geospatial hotspots      -> incidents cluster around hotspot centres per district
  * spatiotemporal pattern   -> certain crimes skew to night hours
  * emerging-trend alert      -> a recent spike in one district+category (last ~45 days)
  * repeat offenders / network-> a reusable offender pool, co-offending groups, stable MO
  * anomalies                 -> planted deviant cases (extreme report delay / mass-accused /
                                 odd-hour) written with ground-truth labels so the anomaly
                                 detector can be scored with real precision/recall
  * socio-economic correlation-> district crime rate correlates with an urbanisation index

Usage:
    python generate.py --cases 40000 --seed 42 --out ../out
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import random
from datetime import datetime, timedelta

try:
    import reference as ref                       # standalone (dir on path) + pytest fixture
except ModuleNotFoundError:                        # imported as data.generator.generate from repo root
    from data.generator import reference as ref


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def weighted_choice(rng, items, weights):
    return rng.choices(items, weights=weights, k=1)[0]


def rand_name(rng, gender_id):
    if gender_id == 2:
        first = rng.choice(ref.FIRST_NAMES_F)
    else:
        first = rng.choice(ref.FIRST_NAMES_M)
    return f"{first} {rng.choice(ref.LAST_NAMES)}"


_INITIALS = "ABCDGHJKLMNPRSTVY"


def unique_offender_name(rng, gender_id, used):
    """Realistic Karnataka name with a middle initial (e.g. 'Ravi K. Gowda'),
    guaranteed globally unique across the offender pool so link/network analysis
    resolves each offender to a single node instead of merging distinct people."""
    for _ in range(200):
        first = rng.choice(ref.FIRST_NAMES_F if gender_id == 2 else ref.FIRST_NAMES_M)
        init = rng.choice(_INITIALS)
        last = rng.choice(ref.LAST_NAMES)
        name = f"{first} {init}. {last}"
        if name not in used:
            used.add(name)
            return name
    # fallback: append a numeric suffix (extremely rare)
    name = f"{first} {init}. {last} {len(used)}"
    used.add(name)
    return name


def jitter_point(rng, lat, lng, spread):
    """Return a point near (lat,lng) with gaussian spread in degrees."""
    return round(lat + rng.gauss(0, spread), 6), round(lng + rng.gauss(0, spread), 6)


class Writer:
    """Buffered CSV writer keyed by table name."""

    def __init__(self, outdir):
        self.outdir = outdir
        os.makedirs(outdir, exist_ok=True)
        self._files = {}
        self._writers = {}

    def table(self, name, header):
        f = open(os.path.join(self.outdir, f"{name}.csv"), "w", newline="", encoding="utf-8")
        w = csv.writer(f)
        w.writerow(header)
        self._files[name] = f
        self._writers[name] = w
        return w

    def close(self):
        for f in self._files.values():
            f.close()


# ---------------------------------------------------------------------------
# main generation
# ---------------------------------------------------------------------------

def generate(num_cases: int, seed: int, outdir: str):
    rng = random.Random(seed)
    w = Writer(outdir)

    # ---- static / master tables -------------------------------------------
    w.table("State", ["StateID", "StateName", "NationalityID", "Active"]).writerow(
        [ref.STATE["StateID"], ref.STATE["StateName"], ref.STATE["NationalityID"], 1]
    )

    tw = w.table("District", ["DistrictID", "DistrictName", "StateID", "Active"])
    for did, name, *_ in ref.DISTRICTS:
        tw.writerow([did, name, ref.STATE["StateID"], 1])

    tw = w.table("UnitType", ["UnitTypeID", "UnitTypeName", "CityDistState", "Hierarchy", "Active"])
    for utid, name, level, hier in ref.UNIT_TYPES:
        tw.writerow([utid, name, level, hier, 1])

    tw = w.table("Rank", ["RankID", "RankName", "Hierarchy", "Active"])
    for rid, name, hier in ref.RANKS:
        tw.writerow([rid, name, hier, 1])

    tw = w.table("Designation", ["DesignationID", "DesignationName", "Active", "SortOrder"])
    for did, name, so in ref.DESIGNATIONS:
        tw.writerow([did, name, 1, so])

    tw = w.table("CaseCategory", ["CaseCategoryID", "LookupValue"])
    for cid, name in ref.CASE_CATEGORIES:
        tw.writerow([cid, name])

    tw = w.table("GravityOffence", ["GravityOffenceID", "LookupValue"])
    for gid, name in ref.GRAVITY_OFFENCES:
        tw.writerow([gid, name])

    tw = w.table("CaseStatusMaster", ["CaseStatusID", "CaseStatusName"])
    for sid, name in ref.CASE_STATUSES:
        tw.writerow([sid, name])

    tw = w.table("ReligionMaster", ["ReligionID", "ReligionName"])
    for rid, name in ref.RELIGIONS:
        tw.writerow([rid, name])

    tw = w.table("CasteMaster", ["caste_master_id", "caste_master_name"])
    for cid, name in ref.CASTES:
        tw.writerow([cid, name])

    tw = w.table("OccupationMaster", ["OccupationID", "OccupationName"])
    for oid, name in ref.OCCUPATIONS:
        tw.writerow([oid, name])

    tw = w.table("CrimeHead", ["CrimeHeadID", "CrimeGroupName", "Active"])
    for hid, name in ref.CRIME_HEADS:
        tw.writerow([hid, name, 1])

    tw = w.table("CrimeSubHead", ["CrimeSubHeadID", "CrimeHeadID", "CrimeHeadName", "SeqID"])
    for shid, hid, name, seq in ref.CRIME_SUBHEADS:
        tw.writerow([shid, hid, name, seq])

    tw = w.table("Act", ["ActCode", "ActDescription", "ShortName", "Active"])
    for code, desc, short in ref.ACTS:
        tw.writerow([code, desc, short, 1])

    tw = w.table("Section", ["ActCode", "SectionCode", "SectionDescription", "Active"])
    for actcode, sec, desc, _sh in ref.SECTIONS:
        tw.writerow([actcode, sec, desc, 1])

    tw = w.table("CrimeHeadActSection", ["CrimeHeadID", "ActCode", "SectionCode"])
    for actcode, sec, _desc, sh in ref.SECTIONS:
        tw.writerow([ref.SUBHEAD_TO_HEAD[sh], actcode, sec])

    # ---- Units (police stations) ------------------------------------------
    # Each district gets a set of police stations proportional to its weight.
    units = []          # (UnitID, UnitName, TypeID, ParentUnit, StateID, DistrictID)
    units_by_district = {}
    next_unit_id = 1001
    tw = w.table("Unit", ["UnitID", "UnitName", "TypeID", "ParentUnit", "NationalityID",
                          "StateID", "DistrictID", "Active"])
    for did, dname, lat, lng, span, weight in ref.DISTRICTS:
        n_stations = max(3, min(30, int(round(weight * 1.6))))
        district_units = []
        for i in range(n_stations):
            uid = next_unit_id
            next_unit_id += 1
            if dname == "Bengaluru City" and i < len(ref.BENGALURU_STATIONS):
                sname = f"{ref.BENGALURU_STATIONS[i]} PS"
            else:
                stem = dname.split()[0]
                suffix = ref.GENERIC_STATION_SUFFIXES[i % len(ref.GENERIC_STATION_SUFFIXES)]
                sname = f"{stem} {suffix} PS" if i > 0 else f"{stem} Town PS"
            tw.writerow([uid, sname, 7, None, 1, ref.STATE["StateID"], did, 1])
            district_units.append(uid)
            units.append((uid, sname, did))
        units_by_district[did] = district_units
    w._files  # noqa

    # ---- Courts ------------------------------------------------------------
    courts_by_district = {}
    next_court_id = 5001
    tw = w.table("Court", ["CourtID", "CourtName", "DistrictID", "StateID", "Active"])
    for did, dname, *_ in ref.DISTRICTS:
        n_courts = rng.randint(2, 4)
        clist = []
        court_kinds = ["JMFC Court", "Sessions Court", "District & Sessions Court", "CJM Court"]
        for i in range(n_courts):
            cid = next_court_id
            next_court_id += 1
            cname = f"{dname} {court_kinds[i % len(court_kinds)]}"
            tw.writerow([cid, cname, did, ref.STATE["StateID"], 1])
            clist.append(cid)
        courts_by_district[did] = clist

    # ---- Employees (officers) ---------------------------------------------
    employees_by_unit = {}
    next_emp_id = 10001
    tw = w.table("Employee", ["EmployeeID", "DistrictID", "UnitID", "RankID", "DesignationID",
                              "KGID", "FirstName", "EmployeeDOB", "GenderID", "BloodGroupID",
                              "PhysicallyChallenged", "AppointmentDate"])
    for uid, uname, did in units:
        emp_list = []
        n_emp = rng.randint(4, 9)
        for _ in range(n_emp):
            eid = next_emp_id
            next_emp_id += 1
            gender = weighted_choice(rng, [1, 2], [0.85, 0.15])
            rank = weighted_choice(rng, [8, 9, 10, 11, 12], [1, 2, 3, 4, 6])
            desig = rng.choice([1, 2, 2, 2, 5])
            dob = datetime(rng.randint(1970, 1998), rng.randint(1, 12), rng.randint(1, 28))
            appt = datetime(rng.randint(1998, 2020), rng.randint(1, 12), rng.randint(1, 28))
            kgid = f"KG{rng.randint(100000, 999999)}"
            tw.writerow([eid, did, uid, rank, desig, kgid, rand_name(rng, gender),
                         dob.strftime("%Y-%m-%d"), gender, rng.randint(1, 8), 0,
                         appt.strftime("%Y-%m-%d")])
            emp_list.append(eid)
        employees_by_unit[uid] = emp_list

    # ---- Hotspot centres (planted geospatial signal) ----------------------
    # Each district gets 1-4 hotspot centres; a share of incidents cluster there.
    hotspots = {}
    for did, dname, lat, lng, span, weight in ref.DISTRICTS:
        n_hot = 1 + int(weight // 8)
        hotspots[did] = [jitter_point(rng, lat, lng, span * 0.35) for _ in range(n_hot)]

    # ---- Offender pool (planted network / repeat-offender signal) ---------
    # A finite pool of offenders reused across cases. Some are "prolific" (many
    # cases), and offenders belong to co-offending "gangs" that appear together.
    OFFENDER_POOL = max(150, num_cases // 32)
    offenders = []   # dict per offender
    used_names = set()   # keep offender identities globally unique for clean link analysis
    for oi in range(OFFENDER_POOL):
        home = weighted_choice(rng, [d[0] for d in ref.DISTRICTS],
                               [d[5] for d in ref.DISTRICTS])
        gender = weighted_choice(rng, [1, 2, 3], [0.9, 0.09, 0.01])
        # preferred MO = a specific sub-head (stable modus operandi)
        pref_mo = weighted_choice(rng, list(ref.SUBHEAD_WEIGHTS.keys()),
                                  list(ref.SUBHEAD_WEIGHTS.values()))
        # prolificacy: heavy-ish tail but capped so no single offender is unrealistic.
        # Most offenders appear a handful of times; a few "prolific" ones ~20-45 cases.
        activity = min(rng.paretovariate(1.3), 30.0)
        offenders.append({
            "name": unique_offender_name(rng, gender, used_names), "gender": gender,
            "home": home, "pref_mo": pref_mo, "activity": activity,
            "age": rng.randint(18, 60),
        })
    # gangs: groups of 2-5 offenders that co-offend
    gangs = []
    n_gangs = OFFENDER_POOL // 15
    for _ in range(n_gangs):
        size = rng.randint(2, 5)
        members = rng.sample(range(OFFENDER_POOL), size)
        gangs.append(members)
    offender_gang = {}
    for gi, members in enumerate(gangs):
        for m in members:
            offender_gang[m] = gi
    offender_activity_weights = [o["activity"] for o in offenders]

    # ---- date range & spike config ----------------------------------------
    END = datetime(2026, 6, 30)
    START = END - timedelta(days=365 * 4)   # 4 years of history (more panel rows for forecasting)
    total_days = (END - START).days
    # emerging-trend spike: Chain Snatching (206) in Bengaluru City in last 45 days
    SPIKE_DISTRICT = 4001
    SPIKE_SUBHEAD = 206
    SPIKE_WINDOW_START = END - timedelta(days=45)

    # ---- spatiotemporal intensity field over (district, week) --------------
    # Real crime volume has structure: per-district trends (some rising, some
    # falling), yearly seasonality, and week-to-week MOMENTUM (autocorrelation).
    # We build an intensity per (district, week) from base rate x trend x seasonal
    # x an AR(1) momentum process, then sample each case's (district, week) from it.
    # This makes next-week volume genuinely predictable (so the ML models learn a
    # real signal) instead of white noise.
    n_weeks = total_days // 7 + 1
    cells = []          # (district_id, week_index)
    cell_weights = []
    for did, dname, dlat, dlng, dspan, base_w in ref.DISTRICTS:
        slope = rng.gauss(0.0, 0.28)         # long-run trend (kept modest so district
                                             # totals stay tied to population base rate)
        phase = rng.uniform(0, 2 * math.pi)  # seasonal phase
        ar = 0.0
        for wk in range(n_weeks):
            ar = 0.7 * ar + rng.gauss(0, 0.28)        # AR(1) momentum
            month = (START + timedelta(days=wk * 7)).month
            seasonal = 1 + 0.22 * math.sin(2 * math.pi * month / 12 + phase)
            if month in (3, 4, 10):                    # mild festival/summer bumps
                seasonal *= 1.12
            trend = max(0.2, 1 + slope * (wk / n_weeks))
            intensity = base_w * trend * seasonal * math.exp(ar)
            # planted Bengaluru spike: raise volume in the last ~6 weeks
            if did == SPIKE_DISTRICT and (START + timedelta(days=wk * 7)) >= SPIKE_WINDOW_START - timedelta(days=7):
                intensity *= 1.7
            cells.append((did, wk))
            cell_weights.append(max(0.01, intensity))
    # pre-sample every case's (district, week) from the intensity field in one pass
    case_cells = rng.choices(range(len(cells)), weights=cell_weights, k=num_cases)

    # per-(unit, category, year) running serials for CrimeNo
    serials = {}

    # ---- open transaction-table writers -----------------------------------
    cm_w = w.table("CaseMaster", ["CaseMasterID", "CrimeNo", "CaseNo", "CrimeRegisteredDate",
                                  "PolicePersonID", "PoliceStationID", "CaseCategoryID",
                                  "GravityOffenceID", "CrimeMajorHeadID", "CrimeMinorHeadID",
                                  "CaseStatusID", "CourtID"])
    inv_w = w.table("Inv_OccuranceTime", ["CaseMasterID", "IncidentFromDate", "IncidentToDate",
                                          "InfoReceivedPSDate", "latitude", "longitude", "BriefFacts"])
    comp_w = w.table("ComplainantDetails", ["ComplainantID", "CaseMasterID", "ComplainantName",
                                            "AgeYear", "OccupationID", "ReligionID", "CasteID", "GenderID"])
    vic_w = w.table("Victim", ["VictimMasterID", "CaseMasterID", "VictimName", "AgeYear",
                               "GenderID", "VictimPolice"])
    acc_w = w.table("Accused", ["AccusedMasterID", "CaseMasterID", "AccusedName", "AgeYear",
                                "GenderID", "PersonID"])
    asa_w = w.table("ActSectionAssociation", ["CaseMasterID", "ActID", "SectionID",
                                              "ActOrderID", "SectionOrderID"])
    arr_w = w.table("ArrestSurrender", ["ArrestSurrenderID", "CaseMasterID", "ArrestSurrenderTypeID",
                                        "ArrestSurrenderDate", "ArrestSurrenderStateId",
                                        "ArrestSurrenderDistrictId", "PoliceStationID", "IOID",
                                        "CourtID", "AccusedMasterID", "IsAccused", "IsComplainantAccused"])
    junc_w = w.table("inv_arrestsurrenderaccused", ["ArrestSurrenderID", "AccusedMasterID"])
    cs_w = w.table("ChargesheetDetails", ["CSID", "CaseMasterID", "csdate", "cstype", "PolicePersonID"])

    # id counters
    comp_id = 1
    vic_id = 1
    acc_id = 1
    arr_id = 1
    cs_id = 1

    district_lookup = {d[0]: d for d in ref.DISTRICTS}
    subhead_ids = list(ref.SUBHEAD_WEIGHTS.keys())
    subhead_weights = list(ref.SUBHEAD_WEIGHTS.values())

    # planted anomalies: a small share of cases made statistically deviant on features the
    # IsolationForest actually sees (report delay, accused count, hour). Their CaseMasterIDs +
    # type are written to GroundTruthAnomalies.csv so detection can be scored (precision/recall).
    anomaly_target = max(30, num_cases // 250)
    anomalies_made = 0
    planted_anomalies = []          # (CaseMasterID, kind)

    for case_i in range(1, num_cases + 1):
        # --- district + week drawn from the spatiotemporal intensity field ---
        did, wk = cells[case_cells[case_i - 1]]
        reg_date = START + timedelta(days=wk * 7 + rng.randint(0, 6))
        if reg_date > END:
            reg_date = END

        # --- choose crime sub-head ---
        subhead = weighted_choice(rng, subhead_ids, subhead_weights)

        # --- inject emerging-trend spike ---
        if reg_date >= SPIKE_WINDOW_START and did == SPIKE_DISTRICT and rng.random() < 0.55:
            subhead = SPIKE_SUBHEAD

        head = ref.SUBHEAD_TO_HEAD[subhead]

        # --- decide up-front whether THIS case is a planted anomaly + how it deviates. Genuine
        #     anomalies are MULTIVARIATE outliers (weird on several axes at once); a case that is
        #     extreme on only ONE feature barely stands out to IsolationForest. So each anomaly
        #     has a primary deviation (its kind) and, most of the time (~70%), a secondary one —
        #     which lifts detection to a realistic, imperfect level (recall ~0.6, not 1.0). The
        #     deviation targets are recorded here and applied at each field below. ---
        anomaly_kind = None
        anom_delay_days = anom_n_accused = anom_hour = None
        anom_heinous = False
        if anomalies_made < anomaly_target and rng.random() < 0.006:
            anomalies_made += 1
            anomaly_kind = weighted_choice(rng, ["report_delay", "mass_accused", "odd_hour"], [4, 3, 3])
            planted_anomalies.append((case_i, anomaly_kind))
            secondary = rng.random() < 0.7
            if anomaly_kind == "report_delay":
                anom_delay_days = rng.randint(13, 210)          # report filed 2 wks–7 mths after the incident
                if secondary:
                    anom_n_accused = rng.randint(7, 16)
            elif anomaly_kind == "mass_accused":
                anom_n_accused = rng.randint(9, 20)             # far outside the usual 1–4
                if secondary:
                    anom_delay_days = rng.randint(8, 125)
            else:  # odd_hour
                anom_hour = rng.choice([1, 2, 3, 4])            # deep pre-dawn + flagged heinous
                anom_heinous = True
                if secondary:
                    anom_n_accused = rng.randint(7, 14)

        # --- category (mostly FIR) ---
        if subhead in (103,) and rng.random() < 0.4:
            category = 3  # UDR for some homicide-adjacent
        else:
            category = weighted_choice(rng, [1, 3, 4, 8], [0.86, 0.06, 0.05, 0.03])

        # --- gravity ---
        if anom_heinous:
            gravity = 1                          # anomaly: heinous gravity on an otherwise ordinary case
        elif subhead in ref.HEINOUS_SUBHEADS:
            gravity = 1
        elif subhead in (104, 202, 203, 601, 301):
            gravity = 3
        else:
            gravity = weighted_choice(rng, [2, 4], [0.6, 0.4])

        # --- police station within district ---
        unit_id = rng.choice(units_by_district[did])
        io_id = rng.choice(employees_by_unit[unit_id])

        # --- location: ~68% of incidents cluster tightly (~280m) around a district
        # hotspot centre; the rest scatter across the district. Tight clusters make
        # DBSCAN hotspots crisp and actionable instead of one city-wide blob.
        d_lat, d_lng, d_span = district_lookup[did][2], district_lookup[did][3], district_lookup[did][4]
        if rng.random() < 0.68:
            hc = rng.choice(hotspots[did])
            lat, lng = jitter_point(rng, hc[0], hc[1], 0.0025)   # ~280m std, fixed
        else:
            lat, lng = jitter_point(rng, d_lat, d_lng, d_span * 0.5)

        # --- time of day (night bias for certain crimes) ---
        if anom_hour is not None:
            hour = anom_hour                        # anomaly: deep pre-dawn, unusual for most crimes
        elif subhead in ref.NIGHT_SUBHEADS:
            hour = weighted_choice(rng, list(range(24)),
                                   [3,3,3,2,2,1,1,1,1,1,1,1,1,2,2,2,3,4,6,8,9,9,7,5])
        else:
            hour = weighted_choice(rng, list(range(24)),
                                   [1,1,1,1,1,1,2,3,5,7,8,8,7,6,6,6,6,6,6,5,4,3,2,1])
        # odd-hour anomalies keep the incident AT that hour (no back-dating) so the stored hour is deep-night
        back_h = 0 if anom_hour is not None else rng.randint(0, 8)
        incident_from = reg_date.replace(hour=hour, minute=rng.randint(0, 59)) - timedelta(hours=back_h)
        incident_to = incident_from + timedelta(minutes=rng.randint(5, 240))
        if anom_delay_days is not None:
            info_recv = incident_to + timedelta(days=anom_delay_days)   # implausibly delayed report
        else:
            info_recv = incident_to + timedelta(hours=rng.randint(0, 20))

        # --- status (older cases more likely resolved) ---
        age_days = (END - reg_date).days
        if age_days > 400:
            status = weighted_choice(rng, [2, 3, 4, 5, 6, 7], [5, 3, 1, 2, 1, 2])
        elif age_days > 120:
            status = weighted_choice(rng, [1, 2, 3, 7], [4, 4, 2, 2])
        else:
            status = weighted_choice(rng, [1, 2], [7, 3])
        # NCRB-2022 calibration: crimes against women have a high chargesheeting rate
        # (~82.8% in Karnataka) -> push most women-crime cases to charge-sheeted/trial.
        if subhead in ref.WOMEN_SUBHEADS and status not in (2, 5) and rng.random() < 0.8:
            status = weighted_choice(rng, [2, 7, 5], [7, 2, 1])

        court_id = rng.choice(courts_by_district[did]) if status in (2, 5, 6, 7) else None

        # --- CrimeNo / CaseNo ---
        year = reg_date.year
        skey = (unit_id, category, year)
        serials[skey] = serials.get(skey, 0) + 1
        serial = serials[skey]
        crime_no = f"{category:01d}{did:04d}{unit_id:04d}{year:04d}{serial:05d}"
        case_no = f"{year:04d}{serial:05d}"

        brief = make_brief(rng, subhead, district_lookup[did][1])

        cm_w.writerow([case_i, crime_no, case_no, reg_date.strftime("%Y-%m-%d"),
                       io_id, unit_id, category, gravity, head, subhead, status, court_id])
        inv_w.writerow([case_i, incident_from.strftime("%Y-%m-%d %H:%M:%S"),
                        incident_to.strftime("%Y-%m-%d %H:%M:%S"),
                        info_recv.strftime("%Y-%m-%d %H:%M:%S"), lat, lng, brief])

        # --- complainant ---
        c_gender = 2 if subhead in ref.WOMEN_SUBHEADS and rng.random() < 0.8 else weighted_choice(rng, [1, 2], [0.6, 0.4])
        comp_w.writerow([comp_id, case_i, rand_name(rng, c_gender), rng.randint(18, 70),
                         rng.choice([o[0] for o in ref.OCCUPATIONS]),
                         weighted_choice(rng, [r[0] for r in ref.RELIGIONS], [70, 13, 6, 3, 2, 2, 4]),
                         weighted_choice(rng, [c[0] for c in ref.CASTES], [25, 30, 20, 10, 5, 5, 3, 2]),
                         c_gender])
        comp_id += 1

        # --- victims (women crimes / body crimes have victims) ---
        n_victims = 0
        if head in (1, 3, 4) or subhead in (301, 302, 303, 304, 305):
            n_victims = weighted_choice(rng, [1, 2, 3], [8, 2, 1])
        elif rng.random() < 0.25:
            n_victims = 1
        for _ in range(n_victims):
            v_gender = 2 if subhead in ref.WOMEN_SUBHEADS else weighted_choice(rng, [1, 2], [0.6, 0.4])
            vic_w.writerow([vic_id, case_i, rand_name(rng, v_gender), rng.randint(1, 80),
                            v_gender, 0])
            vic_id += 1

        # --- accused: realistic mix of KNOWN repeat offenders (from pool) and
        # ONE-OFF / first-time / unknown accused (fresh identities that never recur).
        # This gives link-analysis a real signal-vs-noise problem to solve.
        case_accused_ids = []
        n_accused = weighted_choice(rng, [1, 2, 3, 4], [62, 24, 10, 4])
        if anom_n_accused is not None:
            n_accused = anom_n_accused              # anomaly: mass-accused spike, far outside the usual 1–4
        # A case involves the known-offender network ~38% of the time; organised
        # (gang/property/NDPS) crimes lean higher, opportunistic crimes lower.
        p_known = 0.82 if subhead in (201, 202, 203, 205, 206, 701, 704, 601) else 0.6
        involves_known = rng.random() < p_known

        # people = list of ("pool", idx) or ("oneoff", name/age/gender)
        people = []
        if involves_known:
            seed_idx = pick_offender(rng, offenders, offender_activity_weights, subhead)
            people.append(("pool", seed_idx))
            if seed_idx in offender_gang and n_accused > 1:
                gang_members = [m for m in gangs[offender_gang[seed_idx]] if m != seed_idx]
                rng.shuffle(gang_members)
                for m in gang_members:
                    if len(people) >= n_accused:
                        break
                    people.append(("pool", m))
        while len(people) < n_accused:
            # remaining slots: sometimes another known offender, usually a one-off
            if involves_known and rng.random() < 0.35:
                people.append(("pool", pick_offender(rng, offenders, offender_activity_weights, subhead)))
            else:
                g = weighted_choice(rng, [1, 2, 3], [0.9, 0.09, 0.01])
                # one-off accused are distinct real people who appear exactly once;
                # give them globally-unique names so they don't masquerade as repeats.
                people.append(("oneoff", (unique_offender_name(rng, g, used_names),
                                          rng.randint(18, 62), g)))

        for pi, person in enumerate(people):
            if person[0] == "pool":
                off = offenders[person[1]]
                name, age, gender, oidx = off["name"], off["age"], off["gender"], person[1]
            else:
                name, age, gender = person[1]
                oidx = None
            acc_w.writerow([acc_id, case_i, name, age, gender, f"A{pi+1}"])
            case_accused_ids.append((acc_id, oidx))
            acc_id += 1

        # --- act/section associations coherent with sub-head ---
        secs = ref.SECTIONS_BY_SUBHEAD.get(subhead, [("IPC", "34", "Common intention")])
        chosen_secs = secs if len(secs) == 1 else rng.sample(secs, k=min(len(secs), rng.randint(1, 2)))
        for order, (actcode, seccode, _desc) in enumerate(chosen_secs, start=1):
            asa_w.writerow([case_i, actcode, seccode, order, order])

        # --- arrests (for a share of cases, esp. resolved ones) ---
        arrest_prob = 0.7 if status in (2, 5) else (0.35 if status == 7 else 0.12)
        if rng.random() < arrest_prob and case_accused_ids:
            arr_type = weighted_choice(rng, [1, 2], [0.85, 0.15])  # 1=Arrest, 2=Surrender
            arr_date = reg_date + timedelta(days=rng.randint(0, 90))
            if arr_date > END:
                arr_date = END
            primary_acc = case_accused_ids[0][0]
            arr_w.writerow([arr_id, case_i, arr_type, arr_date.strftime("%Y-%m-%d"),
                            ref.STATE["StateID"], did, unit_id, io_id,
                            court_id or rng.choice(courts_by_district[did]),
                            primary_acc, 1, 0])
            for acc_master_id, _oidx in case_accused_ids:
                junc_w.writerow([arr_id, acc_master_id])
            arr_id += 1

        # --- chargesheet for charge-sheeted / convicted ---
        if status in (2, 5, 6):
            cs_date = reg_date + timedelta(days=rng.randint(30, 180))
            if cs_date > END:
                cs_date = END
            cstype = "A" if status in (2, 5, 6) else "C"
            cs_w.writerow([cs_id, case_i, cs_date.strftime("%Y-%m-%d %H:%M:%S"), cstype, io_id])
            cs_id += 1

    # --- anomaly ground truth (not a schema table; consumed only by the anomaly evaluator) ---
    gt_w = w.table("GroundTruthAnomalies", ["CaseMasterID", "AnomalyType"])
    for cid, kind in planted_anomalies:
        gt_w.writerow([cid, kind])

    w.close()
    return {
        "cases": num_cases,
        "districts": len(ref.DISTRICTS),
        "units": len(units),
        "offenders": OFFENDER_POOL,
        "gangs": len(gangs),
        "spike": f"subhead {SPIKE_SUBHEAD} in district {SPIKE_DISTRICT}, last 45 days",
        "planted_anomalies": len(planted_anomalies),
    }


def pick_offender(rng, offenders, activity_weights, subhead):
    """Prefer offenders whose stable MO matches this crime sub-head, else fall back
    to activity-weighted choice (prolific repeat offenders reused more)."""
    if rng.random() < 0.55:
        matches = [i for i, o in enumerate(offenders) if o["pref_mo"] == subhead]
        if matches:
            mw = [offenders[i]["activity"] for i in matches]
            return rng.choices(matches, weights=mw, k=1)[0]
    return rng.choices(range(len(offenders)), weights=activity_weights, k=1)[0]


BRIEF_PLACES = ["the KSRTC bus stand", "the market road", "a residential layout",
                "the highway junction", "a commercial complex", "the temple street",
                "the railway station area", "the main road", "an ATM kiosk",
                "a farmhouse on the outskirts", "the industrial estate", "a lodge"]


def make_brief(rng, subhead, district_name):
    """Realistic BriefFacts narrative that DESCRIBES the incident with entities but
    never names the crime category — a genuine corpus for the NLP classifier."""
    head = ref.SUBHEAD_TO_HEAD.get(subhead, 2)
    r = rng.random()
    if r < 0.20:
        # ~20% vague / low-signal briefs -> forces realistic (not perfect) accuracy
        t = rng.choice(ref.GENERIC_BRIEFS)
    elif r < 0.28 and head in ref.CONFUSABLE_BRIEFS:
        # ~8% confusable briefs shared with a neighbouring head -> class-boundary ambiguity
        t = rng.choice(ref.CONFUSABLE_BRIEFS[head])
    else:
        templates = ref.BRIEF_SUBHEAD_TEMPLATES.get(subhead) or ref.BRIEF_HEAD_TEMPLATES.get(head) \
            or ["An incident was reported at {place} and is under investigation."]
        t = rng.choice(templates)
    place = f"{rng.choice(BRIEF_PLACES)} in {district_name}"
    return t.format(
        place=place,
        item=rng.choice(ref.NLP_ENTITIES["item"]),
        weapon=rng.choice(ref.NLP_ENTITIES["weapon"]),
        vehicle=rng.choice(ref.NLP_ENTITIES["vehicle"]),
        contraband=rng.choice(ref.NLP_ENTITIES["contraband"]),
        pretext=rng.choice(ref.NLP_ENTITIES["pretext"]),
        relation=rng.choice(ref.RELATIONS),
        value=f"{rng.randint(2, 500) * 1000:,}",
    )


def main():
    p = argparse.ArgumentParser(description="Generate synthetic KSP FIR dataset.")
    p.add_argument("--cases", type=int, default=40000, help="number of FIR cases")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "out"))
    args = p.parse_args()

    outdir = os.path.abspath(args.out)
    print(f"Generating {args.cases} cases -> {outdir}")
    stats = generate(args.cases, args.seed, outdir)
    print("Done:", stats)
    # list output files
    for fn in sorted(os.listdir(outdir)):
        path = os.path.join(outdir, fn)
        size = os.path.getsize(path)
        print(f"  {fn:32s} {size:>10,} bytes")


if __name__ == "__main__":
    main()
