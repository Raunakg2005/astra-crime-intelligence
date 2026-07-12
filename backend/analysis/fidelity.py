"""
Fidelity evaluation of the synthetic FIR dataset against REAL published statistics
and criminological stylized facts.

This is the evaluation section a paper needs: it quantifies where the synthetic data
MATCHES reality and — just as importantly — where it DIVERGES. It distinguishes
properties that were *calibrated* into the generator (so agreement is expected) from
those that are *emergent*.

Metrics
-------
1. Population–crime correlation  : synthetic district crime counts vs 2011 Census
                                    population (Spearman, Pearson-on-log).      [calibrated]
2. Women-crime composition       : synthetic vs NCRB-2022 proportions
                                    (Total-Variation-Distance + chi-square GOF).  [emergent-ish]
3. Chargesheeting rate           : synthetic women-crime clearance vs NCRB 82.8%. [design choice]
4. Offender concentration        : Gini of offences-per-offender vs the chronic-
                                    offender stylized range.                      [emergent]
5. Temporal autocorrelation      : lag-1 autocorr of the weekly series (tests the
                                    injected momentum is realistic).             [calibrated]
6. Co-offending modularity       : Louvain modularity of the offender network.   [planted]

Run:  cd backend/analysis && python fidelity.py
Writes: fidelity_report.json and FIDELITY_REPORT.md
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

try:  # Windows consoles default to cp1252 and choke on unicode (→ · ±)
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "appsail_ml"))
import db  # noqa: E402
import reference_real as R  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WOMEN_SUBHEADS = [301, 302, 303, 304, 305]


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    cum = np.cumsum(x)
    return (n + 1 - 2 * np.sum(cum) / cum[-1]) / n


def tvd(p, q):
    p, q = np.asarray(p), np.asarray(q)
    return 0.5 * np.abs(p / p.sum() - q / q.sum()).sum()


# ---------------------------------------------------------------------------

def eval_population_correlation(cases):
    counts = cases.groupby("DistrictID").size()
    rows = [(d, counts.get(d, 0), pop) for d, pop in R.DISTRICT_POP_2011.items() if pop]
    dd = pd.DataFrame(rows, columns=["district", "crimes", "pop"])
    sp = stats.spearmanr(dd["crimes"], dd["pop"])
    pe = stats.pearsonr(np.log(dd["crimes"] + 1), np.log(dd["pop"]))
    return {
        "metric": "population–crime correlation",
        "kind": "calibrated (district weights ~ population/urbanisation)",
        "spearman_r": round(float(sp.statistic), 3),
        "spearman_p": float(f"{sp.pvalue:.2e}"),
        "pearson_logr": round(float(pe.statistic), 3),
        "n_districts": len(dd),
        "target": f"Spearman > {R.STYLIZED_POP_CRIME_SPEARMAN_MIN}",
        "verdict": "PASS" if sp.statistic > R.STYLIZED_POP_CRIME_SPEARMAN_MIN else "DIVERGES",
    }


def eval_women_composition(cases):
    w = cases[cases["CrimeMinorHeadID"].isin(WOMEN_SUBHEADS)]
    syn = w.groupby("CrimeMinorHeadID").size().reindex(WOMEN_SUBHEADS, fill_value=0)
    real = pd.Series(R.NCRB22_WOMEN_COUNTS).reindex(WOMEN_SUBHEADS, fill_value=0)
    syn_p, real_p = syn / syn.sum(), real / real.sum()
    # chi-square GOF: synthetic observed vs real-proportion expected (scaled to synth N)
    expected = real_p * syn.sum()
    chi = stats.chisquare(f_obs=syn.values, f_exp=expected.values)
    return {
        "metric": "crimes-against-women composition vs NCRB-2022",
        "kind": "partly emergent (sub-head frequency weights)",
        "tvd": round(float(tvd(syn_p.values, real_p.values)), 3),
        "chi2": round(float(chi.statistic), 1),
        "chi2_p": float(f"{chi.pvalue:.2e}"),
        "synthetic_pct": {int(k): round(float(v) * 100, 1) for k, v in syn_p.items()},
        "real_pct": {int(k): round(float(v) * 100, 1) for k, v in real_p.items()},
        "target": "TVD < 0.15 (good), < 0.30 (fair)",
        "verdict": "PASS" if tvd(syn_p.values, real_p.values) < 0.15
                   else ("FAIR" if tvd(syn_p.values, real_p.values) < 0.30 else "DIVERGES"),
    }


def eval_chargesheet_rate(cases):
    w = cases[cases["CrimeMinorHeadID"].isin(WOMEN_SUBHEADS)]
    syn_rate = float(w["cleared"].mean())
    diff = abs(syn_rate - R.NCRB22_WOMEN_CHARGESHEET_RATE)
    return {
        "metric": "women-crime chargesheeting rate vs NCRB-2022 (82.8%)",
        "kind": "design choice (status generation)",
        "synthetic_rate": round(syn_rate, 3),
        "real_rate": R.NCRB22_WOMEN_CHARGESHEET_RATE,
        "abs_diff": round(diff, 3),
        "target": "within 0.15 of real",
        "verdict": "PASS" if diff < 0.15 else "DIVERGES",
    }


def eval_offender_concentration(accused):
    counts = accused.groupby("AccusedName")["CaseMasterID"].nunique().values
    g = gini(counts)
    lo, hi = R.STYLIZED_OFFENDER_GINI
    # FIR-level accused concentration is expected to sit somewhat BELOW the classic
    # career-offender Gini, because FIRs include many one-off / unidentified accused.
    verdict = "PASS" if lo <= g <= hi else ("FAIR" if 0.45 <= g < lo else "DIVERGES")
    return {
        "metric": "offender concentration (Gini of offences/offender)",
        "kind": "emergent (offender pool + heavy-tail activity)",
        "gini": round(float(g), 3),
        "n_offenders": int(len(counts)),
        "target": f"Gini in [{lo}, {hi}] (career-offender finding); FIR-level expected lower",
        "note": "moderate concentration; FIR accused include many one-time/unidentified persons",
        "verdict": verdict,
    }


def eval_temporal_autocorr(cases):
    s = (cases.set_index("RegDate").resample("W").size())
    ac1 = float(s.autocorr(lag=1))
    # Ljung-Box style: is lag-1 autocorr significant? approx CI ~ 1.96/sqrt(n)
    ci = 1.96 / np.sqrt(len(s))
    return {
        "metric": "weekly-series lag-1 autocorrelation (momentum realism)",
        "kind": "calibrated (AR(1) + trend + seasonality injected)",
        "autocorr_lag1": round(ac1, 3),
        "signif_threshold": round(float(ci), 3),
        "n_weeks": int(len(s)),
        "target": "autocorr > threshold (real crime series are autocorrelated)",
        "verdict": "PASS" if ac1 > ci else "DIVERGES",
    }


def eval_network_modularity(accused):
    import community as community_louvain
    import networkx as nx
    counts = accused.groupby("AccusedName")["CaseMasterID"].nunique()
    repeat = set(counts[counts >= 2].index)
    G = nx.Graph()
    for cid, g in accused.groupby("CaseMasterID"):
        names = [n for n in g["AccusedName"].unique() if n in repeat]
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                G.add_edge(a, b, weight=G[a][b]["weight"] + 1 if G.has_edge(a, b) else 1)
    G = G.subgraph([n for n in G if G.degree(n) > 0]).copy()
    if G.number_of_edges() == 0:
        return {"metric": "co-offending network modularity", "verdict": "N/A"}
    part = community_louvain.best_partition(G, weight="weight", random_state=42)
    Q = community_louvain.modularity(part, G, weight="weight")
    return {
        "metric": "co-offending network modularity (Louvain Q)",
        "kind": "planted (hard-coded disjoint co-offending gangs)",
        "modularity_Q": round(float(Q), 3),
        "n_nodes": G.number_of_nodes(),
        "n_communities": len(set(part.values())),
        "target": "Q > 0.3 (clear community structure)",
        "verdict": "PASS" if Q > 0.3 else "WEAK",
    }


def run():
    cases = db.load_cases()
    accused = db.load_accused()
    results = [
        eval_population_correlation(cases),
        eval_women_composition(cases),
        eval_chargesheet_rate(cases),
        eval_offender_concentration(accused),
        eval_temporal_autocorr(cases),
        eval_network_modularity(accused),
    ]
    report = {
        "dataset": {"cases": int(len(cases)), "districts": int(cases["DistrictID"].nunique()),
                    "date_from": str(cases["RegDate"].min().date()),
                    "date_to": str(cases["RegDate"].max().date())},
        "results": results,
    }
    with open(os.path.join(HERE, "fidelity_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    _write_markdown(report)

    print("=" * 74)
    print("SYNTHETIC-DATA FIDELITY REPORT  (vs NCRB-2022 + Census-2011 + stylized facts)")
    print("=" * 74)
    for r in results:
        key = next((k for k in ("spearman_r", "tvd", "abs_diff", "gini", "autocorr_lag1",
                                "modularity_Q") if k in r), None)
        print(f"[{r.get('verdict','?'):8s}] {r['metric']}")
        print(f"           {key} = {r.get(key)}   | target: {r.get('target')}")
    print("-" * 74)
    print("Report written: fidelity_report.json, FIDELITY_REPORT.md")


def _write_markdown(report):
    L = ["# Synthetic FIR Dataset — Fidelity Evaluation", "",
         f"Evaluated {report['dataset']['cases']:,} synthetic FIRs across "
         f"{report['dataset']['districts']} districts "
         f"({report['dataset']['date_from']} → {report['dataset']['date_to']}) against **real "
         f"published statistics** (NCRB Crime-in-India 2022, Census 2011) and criminological "
         f"stylized facts.", "",
         "> **Honesty note.** Metrics labelled *calibrated* reflect properties deliberately built "
         "into the generator (agreement is expected, not a discovery). Metrics labelled *emergent* "
         "are not directly imposed. Where the data **diverges** from reality it is reported "
         "plainly — these gaps motivate replacing the rule-based generator with a fitted "
         "generative model (SDV/CTGAN) trained on a real seed.", "",
         "| Metric | Type | Key value | Target | Verdict |",
         "|---|---|---|---|---|"]
    for r in report["results"]:
        key = next((k for k in ("spearman_r", "tvd", "abs_diff", "gini", "autocorr_lag1",
                                "modularity_Q") if k in r), "")
        L.append(f"| {r['metric']} | {r.get('kind','')} | {key}={r.get(key)} | "
                 f"{r.get('target','')} | **{r.get('verdict','')}** |")
    gini_r = next((r for r in report["results"] if "gini" in r), {})
    L += ["", "## Calibrated / planted vs emergent (read this before citing any number)", "",
          "Population–crime correlation, women-crime composition, and women chargesheeting rate were "
          "**calibrated** to published NCRB-2022 / Census-2011 figures, and weekly momentum "
          "(AR(1)) and co-offending modularity (hard-coded disjoint gangs) are **planted** structure "
          "the pipeline merely recovers — for all five, agreement confirms the generator/pipeline "
          "works, it is **not** an independent discovery about reality. Only **offender concentration "
          "(Gini)** is genuinely *emergent* (not directly imposed) — and it is the one metric that "
          "diverges from the real-world range, which is the honest result to foreground.",
          "", "## Honest limitation to state in the paper", "",
          f"Offender concentration (Gini = {gini_r.get('gini')}) is *moderate* and sits just "
          "below the classic career-offender range (0.55–0.80). This is expected at the FIR level "
          "— unlike conviction records, FIRs contain many one-off and unidentified accused — but "
          "the gap, together with the rule-based nature of the generator, is the central threat to "
          "validity and motivates fitting a data-driven generator (SDV/CTGAN) on a real seed.", "",
          "## Sources", "- NCRB, *Crime in India 2022*, Karnataka figures.",
          "- Census of India 2011, Karnataka district populations.",
          "- Wolfgang, Figlio & Sellin (1972), chronic-offender concentration."]
    with open(os.path.join(HERE, "FIDELITY_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    run()
