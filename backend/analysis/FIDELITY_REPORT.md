# Synthetic FIR Dataset — Fidelity Evaluation

Evaluated 40,000 synthetic FIRs across 31 districts (2022-07-01 → 2026-06-30) against **real published statistics** (NCRB Crime-in-India 2022, Census 2011) and criminological stylized facts.

> **Honesty note.** Metrics labelled *calibrated* reflect properties deliberately built into the generator (agreement is expected, not a discovery). Metrics labelled *emergent* are not directly imposed. Where the data **diverges** from reality it is reported plainly — these gaps motivate replacing the rule-based generator with a fitted generative model (SDV/CTGAN) trained on a real seed.

| Metric | Type | Key value | Target | Verdict |
|---|---|---|---|---|
| population–crime correlation | calibrated (district weights ~ population/urbanisation) | spearman_r=0.777 | Spearman > 0.7 | **PASS** |
| crimes-against-women composition vs NCRB-2022 | partly emergent (sub-head frequency weights) | tvd=0.016 | TVD < 0.15 (good), < 0.30 (fair) | **PASS** |
| women-crime chargesheeting rate vs NCRB-2022 (82.8%) | design choice (status generation) | abs_diff=0.025 | within 0.15 of real | **PASS** |
| offender concentration (Gini of offences/offender) | emergent (offender pool + heavy-tail activity) | gini=0.494 | Gini in [0.55, 0.8] (career-offender finding); FIR-level expected lower | **FAIR** |
| weekly-series lag-1 autocorrelation (momentum realism) | calibrated (AR(1) + trend + seasonality injected) | autocorr_lag1=0.653 | autocorr > threshold (real crime series are autocorrelated) | **PASS** |
| co-offending network modularity (Louvain Q) | planted (hard-coded disjoint co-offending gangs) | modularity_Q=0.596 | Q > 0.3 (clear community structure) | **PASS** |

## Calibrated / planted vs emergent (read this before citing any number)

Population–crime correlation, women-crime composition, and women chargesheeting rate were **calibrated** to published NCRB-2022 / Census-2011 figures, and weekly momentum (AR(1)) and co-offending modularity (hard-coded disjoint gangs) are **planted** structure the pipeline merely recovers — for all five, agreement confirms the generator/pipeline works, it is **not** an independent discovery about reality. Only **offender concentration (Gini)** is genuinely *emergent* (not directly imposed) — and it is the one metric that diverges from the real-world range, which is the honest result to foreground.

## Honest limitation to state in the paper

Offender concentration (Gini = 0.494) is *moderate* and sits just below the classic career-offender range (0.55–0.80). This is expected at the FIR level — unlike conviction records, FIRs contain many one-off and unidentified accused — but the gap, together with the rule-based nature of the generator, is the central threat to validity and motivates fitting a data-driven generator (SDV/CTGAN) on a real seed.

## Sources
- NCRB, *Crime in India 2022*, Karnataka figures.
- Census of India 2011, Karnataka district populations.
- Wolfgang, Figlio & Sellin (1972), chronic-offender concentration.