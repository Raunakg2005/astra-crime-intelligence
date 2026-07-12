# Model Results & Performance

Full performance of every model trained in Astra, with the metric used to select each
champion. All numbers are reproducible from `--seed 42`, 40,000 synthetic FIRs.

**Experimental setup**
- Dataset: 40,000 FIRs · 31 districts · 4 years (2022-07 → 2026-06) · seed 42
- Tabular tasks: district×week panel, **expanding-window time-series CV** over rows ordered
  forward-in-time (chronological folds, not cross-district) for selection; **untouched
  most-recent-weeks hold-out** for reporting (no future leakage); every task benchmarked against
  a **naive baseline** (last-week persistence / majority)
- NLP task: 80/20 stratified split, **stratified 3-fold CV** for selection, hold-out for reporting
- Hardware: NVIDIA RTX 5060 (XGBoost on CUDA); all others CPU
- Regenerate: `cd backend/ml && python cli.py train-all`

---

## Task 1 — High-Risk District Classification (next week)

Predict whether a district will be in its top-quartile crime volume next week (binary).
**Champion selected by CV ROC-AUC**; threshold tuned for F1; reported on the temporal hold-out.

### Model bake-off (5 families, forward-in-time CV)
| Rank | Model | CV ROC-AUC |
|---|---|---|
| 🏆 1 | **Logistic Regression** | **0.6428** |
| 2 | Gradient Boosting | 0.6181 |
| 3 | Random Forest | 0.6146 |
| 4 | XGBoost (GPU) | 0.6138 |
| 5 | HistGradientBoosting | 0.6072 |

### Champion (Logistic Regression) — hold-out
| Metric | Value |
|---|---|
| ROC-AUC | **0.699** |
| PR-AUC | 0.414 |
| F1 | 0.492 |
| Precision | 0.382 |
| Recall | 0.693 |
| Accuracy | 0.637 |
| Positive rate (base) | 0.254 |
| **Naive persistence baseline — F1 / accuracy** | **0.512 / 0.748** |

> **Honest read:** the model has genuine *ranking* skill (ROC-AUC 0.70 ≫ 0.5), but at the
> F1-tuned operating point it only **matches** naive persistence ("high-risk this week →
> high-risk next week"): model F1 0.49 vs persistence 0.51. District risk is strongly
> autocorrelated, so persistence is a hard baseline to beat on the binary decision — the model's
> value is in its calibrated probability ranking, not a large accuracy lift. Accuracy is not the
> headline (classes are imbalanced; the persistence baseline gets 0.75 by leaning negative).

---

## Task 2 — Next-Week FIR Volume Forecast (regression)

Predict each district's FIR count next week. **Champion selected by CV MAE**; reported on the
hold-out against a **correctly-specified naive persistence baseline** — the last *completed*
week's count (`count[t]` for the `t+1` target), not `count[t-1]`.

### Model bake-off (5 families, forward-in-time CV)
| Rank | Model | CV MAE (lower better) |
|---|---|---|
| 🏆 1 | **Ridge** | **2.608** |
| 2 | Random Forest | 2.697 |
| 3 | Gradient Boosting | 2.722 |
| 4 | HistGradientBoosting | 2.725 |
| 5 | XGBoost (GPU) | 2.740 |

### Champion (Ridge) — hold-out
| Metric | Value |
|---|---|
| MAE | **2.496** |
| Naive persistence baseline MAE | 2.631 |
| **Skill vs baseline** | **+5.1%** |
| RMSE | 3.486 |
| R² | **0.649** |

> **Honest read:** weekly counts are strongly autocorrelated, so naive persistence is already a
> strong baseline. The model explains most of the variance (R² 0.65) and beats persistence by a
> **modest ~5%** on MAE — not the +15.7% previously reported, which came from comparing against a
> mis-specified two-weeks-prior baseline. Small but real, and honestly benchmarked.

---

## Task 3 — Anomaly Detection (scored against planted ground truth)

Isolation Forest (300 trees, contamination 1%) over 40,000 cases. Features: incident hour,
gravity, #accused, report delay, sub-head rarity, heinous flag. The model is **unsupervised**,
but the generator plants **160 ground-truth anomalies** (multivariate outliers — implausible
report delay, mass-accused, odd-hour+heinous — logged to `GroundTruthAnomalies.csv`), so the
detector can be scored with **real precision/recall**, not just a flag rate.

| Metric | Value | Meaning |
|---|---|---|
| **ROC-AUC** | **0.981** | ranks planted anomalies above normal cases (threshold-free) |
| **Average precision** | **0.565** | vs a 0.4% base rate (≈140× a random detector) |
| **Recall @ 1% flag budget** | **0.663** | of 160 planted anomalies, ~106 land in the top-400 flagged |
| **Precision @ k** | **0.519** | flagging exactly 160 by score, ~52% are true planted anomalies |
| Precision @ 1% flag budget | 0.265 | at the 1% cut, planted anomalies share the budget with natural outliers |

> The detector genuinely recovers most planted anomalies (recall 0.66, ROC-AUC 0.98) while
> honestly missing subtle single-dimension deviations — a realistic, *validated* result rather
> than the previous "1% flagged", which was just the `contamination` hyperparameter restated.

---

## Task 4 — NLP Crime-Text Classification (18-model bake-off)

Classify the crime **head** (8 classes) from the free-text FIR `BriefFacts` narrative
(TF-IDF features; narratives contain **no** category names → genuine text task).
**Champion selected by hold-out macro-F1.** Test set = 8,000 narratives.

### All 18 models
| Rank | Model | CV macro-F1 | Accuracy | Macro-F1 | Weighted-F1 | proba |
|---|---|---|---|---|---|---|
| 🏆 1 | **MLP (neural net)** | 0.878 | **0.856** | **0.878** | 0.860 | ✅ |
| 2 | Ridge | 0.871 | 0.854 | 0.875 | 0.857 | — |
| 3 | Multinomial NB | 0.873 | 0.854 | 0.875 | 0.857 | ✅ |
| 4 | Nearest Centroid | 0.876 | 0.852 | 0.877 | 0.857 | ✅ |
| 5 | Logistic Regression | 0.868 | 0.850 | 0.869 | 0.852 | ✅ |
| 6 | SGD (log-loss) | 0.862 | 0.848 | 0.867 | 0.850 | ✅ |
| 7 | Linear SVC | 0.860 | 0.848 | 0.863 | 0.849 | — |
| 8 | Decision Tree | 0.862 | 0.842 | 0.855 | 0.843 | ✅ |
| 9 | kNN (k=15) | 0.843 | 0.837 | 0.841 | 0.837 | ✅ |
| 10 | HistGradientBoosting | 0.841 | 0.837 | 0.840 | 0.837 | ✅ |
| 11 | Extra Trees | 0.844 | 0.837 | 0.841 | 0.837 | ✅ |
| 12 | Random Forest | 0.845 | 0.837 | 0.841 | 0.837 | ✅ |
| 13 | XGBoost (GPU) | 0.836 | 0.836 | 0.838 | 0.836 | ✅ |
| 14 | Passive Aggressive | 0.835 | 0.835 | 0.836 | 0.836 | — |
| 15 | Bagging | 0.839 | 0.835 | 0.836 | 0.835 | ✅ |
| 16 | Complement NB | 0.848 | 0.827 | 0.850 | 0.840 | ✅ |
| 17 | Bernoulli NB | 0.854 | 0.824 | 0.855 | 0.845 | ✅ |
| 18 | AdaBoost | 0.797 | 0.795 | 0.801 | 0.794 | ✅ |

> Every model is saved (`backend/appsail_ml/models/nlp_all/*.joblib`) and individually
> runnable via `/api/nlp/classify?model=<name>`. Full metrics + all test predictions in
> `nlp_all_models.json` / `nlp_all_predictions.csv`.

### Champion (MLP) — per-class F1
| Crime head | F1 |
|---|---|
| Crimes Against Children | 0.931 |
| Offences Against State / Special Laws | 0.889 |
| Crimes Against Public Order & Safety | 0.881 |
| Cyber Crimes | 0.881 |
| Crimes Against Women | 0.878 |
| Economic Offences | 0.878 |
| Crimes Against Body | 0.866 |
| Crimes Against Property | 0.821 |

*Property is the hardest class (it overlaps with violent-property crimes like robbery) — an
honest, expected confusion.*

---

## Data Fidelity (synthetic vs. real published statistics)

Validated against **NCRB Crime-in-India 2022** and **Census 2011** (`backend/analysis/`).

| Check | Value | Type | Target | Verdict |
|---|---|---|---|---|
| District crime ↔ Census population (Spearman) | 0.777 | calibrated | > 0.70 | ✅ PASS |
| Women-crime composition vs NCRB (Total-Variation-Distance) | 0.016 | calibrated | < 0.15 | ✅ PASS |
| Women chargesheeting vs NCRB 82.8% | Δ 0.025 | design choice | < 0.15 | ✅ PASS |
| Weekly momentum (lag-1 autocorrelation) | 0.653 | planted (AR(1)) | > threshold | ✅ PASS |
| Co-offending network modularity (Louvain Q) | 0.596 | planted (gangs) | > 0.30 | ✅ PASS |
| Offender concentration (Gini) | 0.494 | **emergent** | 0.55–0.80 | ⚠️ FAIR (FIR-level expected lower) |

> The first five rows validate properties **calibrated or planted into the generator** (agreement
> is expected — the pipeline recovers what was built in). Only offender-concentration Gini is
> genuinely **emergent**, and it is the one that diverges — the honest headline.

Full report: [`backend/analysis/FIDELITY_REPORT.md`](../backend/analysis/FIDELITY_REPORT.md).

---

## Summary

| Task | Best model | Headline metric |
|---|---|---|
| High-risk classification | Logistic Regression | ROC-AUC **0.70** (≈ persistence at operating point) |
| Volume forecast | Ridge | R² **0.65** · **+5.1%** MAE vs naive persistence |
| Anomaly detection | Isolation Forest | ROC-AUC **0.98** · recall@1% **0.66** vs planted ground truth |
| Crime-text NLP | MLP neural-net | Accuracy **0.86** · macro-F1 **0.88** |

*Champions are auto-promoted into the model registry (champion/challenger) and served by the
API. See [`SETUP.md`](SETUP.md) to reproduce and [`PAPER_OUTLINE.md`](PAPER_OUTLINE.md) for the
academic write-up.*
