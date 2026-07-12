# KSP Crime Intelligence — Data Layer

Schema-conformant **synthetic** Karnataka FIR dataset that faithfully implements the
official Police FIR ER diagram (27 tables). Real FIR data is confidential, so this
generator produces realistic records seeded with **real Karnataka ground truth**
(districts, geo-coordinates, IPC/NDPS/other acts & sections, NCRB crime-head taxonomy)
and **planted intelligence signal** so every analytics feature has something real to find.

When genuine KSP data becomes available it drops straight into the same schema /
Catalyst Data Store — no code changes downstream.

## Quick start

```bash
# 1. generate CSVs for every schema table (stdlib only, ~seconds)
python generator/generate.py --cases 40000 --seed 42

# 2. build a queryable SQLite DB (mirrors Catalyst Data Store schema)
python build_sqlite.py

# output -> data/out/*.csv  and  data/out/ksp.db
```

## What's realistic / what's planted

| Aspect | How it's modelled |
|---|---|
| Geography | All 31 Karnataka districts, real centroids; police-station units per district weighted by urbanisation |
| Legal data | Real Acts (IPC, NDPS, Arms, POCSO, IT, Excise…) and real Sections mapped to crime sub-heads |
| Taxonomy | NCRB-style CrimeHead → CrimeSubHead hierarchy |
| CrimeNo | Exact 18-digit format: `Category(1) + District(4) + Unit(4) + Year(4) + Serial(5)`; per-station/category/year serials |
| Case mix | Theft/hurt common, murder rare (weighted); heinous flag, gravity, status all coherent |
| **Hotspots** | Incidents cluster around per-district hotspot centres (geospatial signal) |
| **Spatiotemporal** | Night-time skew for burglary/robbery/snatching/NDPS |
| **Emerging trend** | Planted spike: Chain Snatching in Bengaluru City, last 45 days (**≈×25**) → red-zone alert demo |
| **Repeat offenders** | Closed pool of ~1,000 known offenders with stable MO, reused across cases & districts |
| **Networks** | Co-offending "gangs" appear together → connected components / Louvain communities |
| **Signal vs noise** | ~93% of accused are one-off/first-time; only repeat-offender pool recurs (realistic haystack) |
| **Clearance** | Older cases more likely charge-sheeted/convicted; varies by district (socio overlay) |
| **Anomalies** | 160 cases made multivariate outliers (implausible report delay, mass-accused, odd-hour+heinous) with **ground-truth labels** in `GroundTruthAnomalies.csv` so anomaly detection is scored with real precision/recall (not just a flag rate) |

> **Note on entity resolution:** offender names are generated **globally unique** so link/network
> analysis resolves cleanly by exact-name match. This is a *deliberate simplification* — real FIR
> data has name variants/typos/transliteration with no shared person ID, so fuzzy entity
> resolution is a prerequisite for real-data use (see the roadmap in the root README).

## Tables emitted (27)

**Masters/lookups:** State, District, UnitType, Unit, Rank, Designation, Employee,
CaseCategory, GravityOffence, CaseStatusMaster, ReligionMaster, CasteMaster,
OccupationMaster, CrimeHead, CrimeSubHead, Act, Section, CrimeHeadActSection, Court

**Transactions:** CaseMaster, Inv_OccuranceTime, ComplainantDetails, Victim, Accused,
ActSectionAssociation, ArrestSurrender, inv_arrestsurrenderaccused, ChargesheetDetails

## Files

- `generator/reference.py` — real Karnataka ground-truth reference data
- `generator/generate.py` — the generator (stdlib only)
- `build_sqlite.py` — CSV → SQLite loader with PKs + analytics indexes
- `out/` — generated output (git-ignored; regenerate any time)
