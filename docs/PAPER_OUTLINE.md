# Paper Outline — Astra: A Privacy-Preserving Synthetic FIR Benchmark & Crime-Intelligence Platform

> Honest, publishable framing. The contribution is the **generator + open benchmark + platform**,
> NOT empirical claims about real Karnataka crime (the data is synthetic). Suggested venues:
> applied-AI / data-science-for-social-good / digital-government workshops, or a dataset track.

## Abstract (what to claim)
- Real FIR microdata is confidential → research and reproducibility are blocked.
- We release **(1)** a schema-faithful synthetic FIR generator for Karnataka (27-table official
  ER schema), **(2)** an open crime-analytics benchmark with four tasks (hotspot detection,
  crime forecasting, offender-network analysis, crime-text classification), and **(3)** an
  end-to-end platform deployed on a managed cloud (Zoho Catalyst).
- We **validate fidelity** against published NCRB-2022 and Census-2011 aggregates and report
  where the synthetic data matches and where it diverges.

## 1. Introduction
- Problem: data silos, Excel-based reporting, no advanced analytics at SCRB; confidentiality
  prevents open research.
- Contributions (list the three above). Emphasise **privacy-by-construction** (no real PII).

## 2. Related Work
- Synthetic data generation (SDV, CTGAN, Gaussian copula; differential privacy).
- Crime hotspot detection (KDE, DBSCAN), crime forecasting (spatio-temporal models),
  co-offending / link analysis, crime-text NLP. (Fill with citations.)

## 3. The Synthetic FIR Generator
- 27-table relational schema (CaseMaster → Victim/Accused/Complainant/ArrestSurrender, Act/Section,
  CrimeHead hierarchy, geography, Employee/Court).
- Real ground truth seeded in: 31 districts + geo-centroids, IPC/NDPS/etc. acts & sections,
  NCRB crime-head taxonomy.
- Generative process: per-(district, week) intensity field = base-rate × trend × seasonality ×
  AR(1) momentum; planted hotspots; offender pool with co-offending gangs; leak-free `BriefFacts`
  narratives for NLP.
- **Calibration** to published marginals (district population, crimes-against-women composition,
  chargesheeting rate).

## 4. Fidelity Evaluation  ← the credibility core (see `backend/analysis/FIDELITY_REPORT.md`)
Validate against NCRB-2022 + Census-2011 + criminological stylized facts. Distinguish
**calibrated** (agreement expected) from **emergent** properties.

| Property | Value | Verdict |
|---|---|---|
| District crime ↔ Census population (Spearman) | 0.777 | PASS (calibrated) |
| Crimes-against-women composition vs NCRB (TVD) | 0.009 | PASS (calibrated) |
| Women-crime chargesheeting vs NCRB 82.8% | Δ 0.023 | PASS (calibrated) |
| Weekly momentum (lag-1 autocorrelation) | 0.642 | PASS (calibrated) |
| Co-offending network modularity (Louvain Q) | 0.631 | PASS (emergent) |
| Offender concentration (Gini) | 0.496 | FAIR (emergent; FIR-level < career-offender range) |

Reproduce: `cd backend/analysis && python fidelity.py`.

## 5. Benchmark Tasks & Baselines
- **Hotspot detection** — DBSCAN (haversine) + time-of-day profiling.
- **Crime forecasting** — district×week panel; time-series CV; champion vs naive-persistence
  baseline (report MAE skill, ROC-AUC for high-risk classification).
- **Offender-network analysis** — co-offending graph, Louvain communities, repeat-offender linkage.
- **Crime-text classification** — TF-IDF + 18-model bake-off; champion accuracy ≈ 0.86, macro-F1 ≈ 0.88.
- Report metrics with CV, confidence intervals; ablations.

## 6. System / MLOps
- Serverless API + Python analytics service; **model registry with champion/challenger**,
  time-series CV, MLflow tracking, scheduled retraining; Catalyst-native deployment mapping.

## 7. Limitations (state plainly — reviewers will demand this)
- Data is **synthetic**; results are not empirical findings about real crime.
- Generator is **rule-based**; several marginals are hand-calibrated, not learned. Offender
  concentration is below the career-offender range. → **Future work: fit SDV/CTGAN on a real
  seed and re-run the fidelity suite; add differential-privacy guarantees.**
- No real external validity; templated narratives limit linguistic diversity.
- **Fidelity is mostly calibrated/planted recovery, not discovery.** Five of six fidelity checks
  validate properties built into the generator (population weighting, women-crime mix,
  chargesheet rate, weekly AR(1) momentum, hard-coded co-offending gangs); only offender-Gini is
  genuinely emergent — and it diverges from the real-world range. We report the distinction
  explicitly rather than presenting planted-signal recovery as independent validation.
- **Entity resolution is solved by construction.** Offenders have globally-unique exact-match
  names, so link analysis never faces the real-world problem of name variants / transliteration
  / missing shared IDs. → **Future work: noisy-name generator mode + fuzzy resolution
  (Jaro-Winkler + age/gender corroboration) with reported resolution precision/recall.**
- **Short-horizon forecasting barely beats persistence.** Weekly counts are strongly
  autocorrelated; the volume model beats naive persistence by only ~5% MAE and the high-risk
  classifier matches it at the operating point (its value is probability ranking, ROC-AUC ≈ 0.70).
  The **anomaly detector**, by contrast, is validated against 160 planted ground-truth anomalies
  (ROC-AUC 0.98, recall@1% 0.66) rather than a bare flag rate.

## 8. Ethics & Responsible Use (mandatory)
- Predictive policing risks: feedback loops, bias amplification, over-policing of marginalized
  areas; disparate impact of "risk scores".
- Mitigations: synthetic-only data (no surveillance of real people), transparency (model cards,
  open metrics), human-in-the-loop framing (decision-support, not automated enforcement),
  explicit non-goals (no individual-level predictive policing).
- Recommend fairness auditing before any real-data deployment.

## 9. Conclusion
- Open, privacy-preserving benchmark + platform lowers the barrier to reproducible crime-analytics
  research; fidelity suite makes the synthetic-real gap measurable and honest.

---
### Reproducibility checklist
- Data: `python data/generator/generate.py --cases 40000 --seed 42` (deterministic).
- Fidelity: `python backend/analysis/fidelity.py`.
- Models: `cd backend/ml && python cli.py train-all` (registry + MLflow).
- Everything seed-controlled; data fingerprint logged per run.
