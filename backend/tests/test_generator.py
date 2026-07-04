"""Tests for the synthetic FIR generator."""
import csv
import os

import generate
import reference as ref

EXPECTED_TABLES = {
    "State", "District", "UnitType", "Unit", "Rank", "Designation", "Employee",
    "CaseCategory", "GravityOffence", "CaseStatusMaster", "ReligionMaster", "CasteMaster",
    "OccupationMaster", "CrimeHead", "CrimeSubHead", "Act", "Section", "CrimeHeadActSection",
    "Court", "CaseMaster", "Inv_OccuranceTime", "ComplainantDetails", "Victim", "Accused",
    "ActSectionAssociation", "ArrestSurrender", "inv_arrestsurrenderaccused", "ChargesheetDetails",
}


def _rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_emits_all_27_tables(tmp_path):
    generate.generate(num_cases=200, seed=1, outdir=str(tmp_path))
    produced = {f[:-4] for f in os.listdir(tmp_path) if f.endswith(".csv")}
    missing = EXPECTED_TABLES - produced
    assert not missing, f"missing tables: {missing}"


def test_crimeno_format(tmp_path):
    generate.generate(num_cases=200, seed=1, outdir=str(tmp_path))
    rows = _rows(tmp_path / "CaseMaster.csv")
    assert rows
    for r in rows[:50]:
        cn = r["CrimeNo"]
        assert len(cn) == 18 and cn.isdigit(), f"bad CrimeNo {cn}"
        # category(1)+district(4)+unit(4)+year(4)+serial(5)
        assert r["CaseNo"] == cn[9:]          # last 9 digits = year+serial
        assert int(cn[9:13]) >= 2020          # plausible year


def test_case_counts_and_relations(tmp_path):
    generate.generate(num_cases=300, seed=2, outdir=str(tmp_path))
    cases = _rows(tmp_path / "CaseMaster.csv")
    inv = _rows(tmp_path / "Inv_OccuranceTime.csv")
    assert len(cases) == 300
    assert len(inv) == 300                    # 1:1 occurrence per case
    # every case has a complainant
    comp_case_ids = {r["CaseMasterID"] for r in _rows(tmp_path / "ComplainantDetails.csv")}
    assert len(comp_case_ids) == 300


def test_brieffacts_have_no_label_leakage(tmp_path):
    """Narratives must not contain the literal crime-head names (NLP integrity)."""
    generate.generate(num_cases=400, seed=3, outdir=str(tmp_path))
    heads = {h[1].lower() for h in ref.CRIME_HEADS}  # e.g. "cyber crimes"
    for r in _rows(tmp_path / "Inv_OccuranceTime.csv"):
        bf = r["BriefFacts"].lower()
        assert not any(h in bf for h in heads), f"leaked head name in: {bf[:60]}"


def test_repeat_offenders_exist(tmp_path):
    generate.generate(num_cases=600, seed=4, outdir=str(tmp_path))
    from collections import Counter
    names = Counter(r["AccusedName"] for r in _rows(tmp_path / "Accused.csv"))
    assert max(names.values()) >= 3, "expected some repeat offenders"
