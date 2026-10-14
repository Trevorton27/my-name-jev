"""Distribution drift detection metrics."""

from __future__ import annotations

import numpy as np


def population_stability_index(reference: list[float], current: list[float], n_bins: int = 10) -> float:
    """Population Stability Index (PSI) between two distributions.
    PSI < 0.1: no significant change
    PSI 0.1-0.25: moderate change
    PSI > 0.25: significant change
    """
    ref = np.array(reference, dtype=np.float64)
    cur = np.array(current, dtype=np.float64)

    if len(ref) == 0 or len(cur) == 0:
        return 0.0

    bin_edges = np.linspace(
        min(ref.min(), cur.min()),
        max(ref.max(), cur.max()) + 1e-10,
        n_bins + 1,
    )

    ref_hist, _ = np.histogram(ref, bins=bin_edges)
    cur_hist, _ = np.histogram(cur, bins=bin_edges)

    # Normalize to proportions, avoid zeros
    ref_pct = (ref_hist + 1e-10) / (ref_hist.sum() + n_bins * 1e-10)
    cur_pct = (cur_hist + 1e-10) / (cur_hist.sum() + n_bins * 1e-10)

    psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
    return max(0.0, psi)


def jensen_shannon_divergence(reference: list[float], current: list[float], n_bins: int = 10) -> float:
    """Jensen-Shannon divergence (symmetric KL divergence). Range [0, 1]."""
    ref = np.array(reference, dtype=np.float64)
    cur = np.array(current, dtype=np.float64)

    if len(ref) == 0 or len(cur) == 0:
        return 0.0

    bin_edges = np.linspace(
        min(ref.min(), cur.min()),
        max(ref.max(), cur.max()) + 1e-10,
        n_bins + 1,
    )

    ref_hist, _ = np.histogram(ref, bins=bin_edges)
    cur_hist, _ = np.histogram(cur, bins=bin_edges)

    # Normalize
    p = (ref_hist + 1e-10) / (ref_hist.sum() + n_bins * 1e-10)
    q = (cur_hist + 1e-10) / (cur_hist.sum() + n_bins * 1e-10)

    m = 0.5 * (p + q)
    kl_pm = float(np.sum(p * np.log(p / m)))
    kl_qm = float(np.sum(q * np.log(q / m)))

    return max(0.0, 0.5 * (kl_pm + kl_qm))


def disposition_distribution_shift(
    reference_counts: dict[str, int], current_counts: dict[str, int]
) -> dict[str, float]:
    """Compare disposition frequency distributions."""
    all_keys = set(reference_counts) | set(current_counts)
    ref_total = max(sum(reference_counts.values()), 1)
    cur_total = max(sum(current_counts.values()), 1)

    shifts: dict[str, float] = {}
    for key in all_keys:
        ref_pct = reference_counts.get(key, 0) / ref_total
        cur_pct = current_counts.get(key, 0) / cur_total
        shifts[key] = round(cur_pct - ref_pct, 4)

    return shifts
