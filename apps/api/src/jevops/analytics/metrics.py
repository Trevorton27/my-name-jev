"""Pure functions for calibration and evaluation metrics."""

from __future__ import annotations

import numpy as np


def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    """Brier score: mean squared error between predicted probabilities and binary outcomes.
    Lower is better. Range [0, 1]."""
    p = np.array(probabilities, dtype=np.float64)
    o = np.array(outcomes, dtype=np.float64)
    if len(p) == 0:
        return 0.0
    return float(np.mean((p - o) ** 2))


def expected_calibration_error(probabilities: list[float], outcomes: list[int], n_bins: int = 10) -> float:
    """Expected Calibration Error (ECE): weighted average of per-bin calibration gaps."""
    p = np.array(probabilities, dtype=np.float64)
    o = np.array(outcomes, dtype=np.float64)
    n = len(p)
    if n == 0:
        return 0.0

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (p >= bin_edges[i]) & (p < bin_edges[i + 1])
        if i == n_bins - 1:
            mask = (p >= bin_edges[i]) & (p <= bin_edges[i + 1])
        bin_count = int(mask.sum())
        if bin_count == 0:
            continue
        avg_confidence = float(p[mask].mean())
        avg_accuracy = float(o[mask].mean())
        ece += (bin_count / n) * abs(avg_accuracy - avg_confidence)
    return float(ece)


def calibration_curve(probabilities: list[float], outcomes: list[int], n_bins: int = 10) -> list[dict[str, float]]:
    """Compute reliability diagram bins."""
    p = np.array(probabilities, dtype=np.float64)
    o = np.array(outcomes, dtype=np.float64)
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins = []

    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (p >= lo) & (p <= hi)
        else:
            mask = (p >= lo) & (p < hi)
        count = int(mask.sum())
        if count == 0:
            bins.append(
                {
                    "bin_start": float(lo),
                    "bin_end": float(hi),
                    "avg_confidence": float((lo + hi) / 2),
                    "avg_accuracy": 0.0,
                    "count": 0,
                }
            )
        else:
            bins.append(
                {
                    "bin_start": float(lo),
                    "bin_end": float(hi),
                    "avg_confidence": float(p[mask].mean()),
                    "avg_accuracy": float(o[mask].mean()),
                    "count": count,
                }
            )
    return bins


def confusion_matrix(predictions: list[str], actuals: list[str], labels: list[str]) -> dict[str, dict[str, int]]:
    """Compute confusion matrix as nested dict."""
    matrix: dict[str, dict[str, int]] = {pred: {act: 0 for act in labels} for pred in labels}
    for pred, act in zip(predictions, actuals):
        if pred in matrix and act in matrix[pred]:
            matrix[pred][act] += 1
    return matrix


def accuracy(predictions: list[str], actuals: list[str]) -> float:
    if not predictions:
        return 0.0
    correct = sum(1 for p, a in zip(predictions, actuals) if p == a)
    return correct / len(predictions)


def precision_recall_f1(predictions: list[str], actuals: list[str], positive_label: str) -> dict[str, float]:
    tp = sum(1 for p, a in zip(predictions, actuals) if p == positive_label and a == positive_label)
    fp = sum(1 for p, a in zip(predictions, actuals) if p == positive_label and a != positive_label)
    fn = sum(1 for p, a in zip(predictions, actuals) if p != positive_label and a == positive_label)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def false_allow_rate(predictions: list[str], actuals: list[str]) -> float:
    """Fraction of 'allow' predictions that should have been blocked/reviewed."""
    allow_predictions = [(p, a) for p, a in zip(predictions, actuals) if p == "allow"]
    if not allow_predictions:
        return 0.0
    false_allows = sum(1 for p, a in allow_predictions if a != "allow")
    return false_allows / len(allow_predictions)


def false_block_rate(predictions: list[str], actuals: list[str]) -> float:
    """Fraction of 'block' predictions that should have been allowed."""
    block_predictions = [(p, a) for p, a in zip(predictions, actuals) if p == "block"]
    if not block_predictions:
        return 0.0
    false_blocks = sum(1 for p, a in block_predictions if a == "allow")
    return false_blocks / len(block_predictions)


def override_rate(original_dispositions: list[str], final_dispositions: list[str]) -> float:
    """Fraction of decisions where the final disposition differs from original."""
    if not original_dispositions:
        return 0.0
    overrides = sum(1 for o, f in zip(original_dispositions, final_dispositions) if o != f)
    return overrides / len(original_dispositions)


def recommended_threshold(
    probabilities: list[float],
    outcomes: list[int],
    false_allow_cost: float = 10.0,
    false_block_cost: float = 1.0,
) -> float:
    """Find the threshold that minimizes expected asymmetric cost."""
    p = np.array(probabilities, dtype=np.float64)
    o = np.array(outcomes, dtype=np.float64)
    if len(p) == 0:
        return 0.5

    best_threshold = 0.5
    best_cost = float("inf")

    for threshold in np.arange(0.05, 0.96, 0.05):
        predictions = (p >= threshold).astype(int)
        false_allows = int(((predictions == 1) & (o == 0)).sum())
        false_blocks = int(((predictions == 0) & (o == 1)).sum())
        cost = false_allows * false_allow_cost + false_blocks * false_block_cost
        if cost < best_cost:
            best_cost = cost
            best_threshold = float(threshold)

    return round(best_threshold, 2)
