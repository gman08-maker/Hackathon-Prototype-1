"""
Scoring math for the app (no Streamlit code in here, so it's easy to test).

How a school's score works:
  1. For each criterion, turn the raw number into a percentile (0 to 1):
     0.9 means the school beats 90% of schools on that criterion.
  2. Multiply each percentile by the weight the user chose.
  3. Divide by the total weight and scale to 0-100.
"""

import numpy as np
import pandas as pd

# key -> (column in results.csv, True if higher is better, label for the UI)
CRITERIA = {
    "affordability": ("net_price", False, "Affordability (low net price)"),
    "tuition": ("sticker_price", False, "Lower published tuition & fees"),
    "earnings": ("earnings_10yr", True, "Earnings 10 years out"),
    "graduation": ("grad_rate", True, "Graduation rate"),
    "low_debt": ("median_debt", False, "Low student debt"),
    "mobility": ("pell_grad_rate", True, "Social mobility (Pell students graduate)"),
    "prestige": ("prestige_score", True, "Prestige (selectivity + wealth)"),
}

# Starting points for the weight sliders (0 = ignore, 10 = very important)
PRESETS = {
    "Student outcomes": {"affordability": 6, "tuition": 4, "earnings": 6, "graduation": 6,
                         "low_debt": 4, "mobility": 8, "prestige": 0},
    "Prestige only (like many rankings)": {"affordability": 0, "tuition": 0, "earnings": 0,
                                           "graduation": 0, "low_debt": 0, "mobility": 0,
                                           "prestige": 10},
    "Equal weights": {key: 5 for key in CRITERIA},
}


def percentiles(df):
    """One column per criterion, each 0-1. Missing values get 0.5 (neutral)."""
    out = pd.DataFrame(index=df.index)
    for key, (col, higher_is_better, _) in CRITERIA.items():
        out[key] = df[col].rank(pct=True, ascending=higher_is_better).fillna(0.5)
    return out


def weighted_score(pcts, weights):
    """Weighted average of the percentiles, scaled to 0-100."""
    w = pd.Series(weights)[pcts.columns]
    if w.sum() == 0:
        return pd.Series(0.0, index=pcts.index)
    return pcts.mul(w).sum(axis=1) / w.sum() * 100


def fragility(pcts, weights, n_runs=500, wiggle=0.2, top_n=20, seed=0):
    """Monte Carlo check: do small weight changes reshuffle the top of the list?

    In each run, every weight is multiplied by a random number between
    (1 - wiggle) and (1 + wiggle), e.g. 0.8 to 1.2 for wiggle=0.2.
    Weights set to 0 stay 0.

    Returns:
      summary  - per school: how often it lands in the top N, and its
                 typical best/worst rank (5th and 95th percentile)
      overlap  - per run: how many of the original top N are still top N
    """
    base = np.array([weights[key] for key in pcts.columns], dtype=float)
    if base.sum() == 0:
        return None, None

    rng = np.random.default_rng(seed)
    factors = rng.uniform(1 - wiggle, 1 + wiggle, size=(n_runs, len(base)))
    run_weights = base * factors                     # shape: runs x criteria

    scores = pcts.to_numpy() @ run_weights.T         # shape: schools x runs
    # rank 1 = highest score, computed separately for every run
    ranks = (-scores).argsort(axis=0).argsort(axis=0) + 1

    baseline = weighted_score(pcts, weights).rank(ascending=False, method="first")
    in_base_top = (baseline <= top_n).to_numpy()
    in_run_top = ranks <= top_n

    summary = pd.DataFrame({
        "baseline_rank": baseline.astype(int),
        "pct_runs_in_top": in_run_top.mean(axis=1) * 100,
        "best_rank": np.percentile(ranks, 5, axis=1).round().astype(int),
        "worst_rank": np.percentile(ranks, 95, axis=1).round().astype(int),
    }, index=pcts.index)
    overlap = in_run_top[in_base_top].sum(axis=0)    # one number per run
    return summary, overlap
