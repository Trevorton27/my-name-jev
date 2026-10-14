# Calibration & Evaluation

## Metrics

- **Brier Score**: Mean squared error between predicted probabilities and outcomes. Lower is better.
- **ECE (Expected Calibration Error)**: Weighted average of per-bin calibration gaps.
- **Accuracy, Precision, Recall, F1**: Standard classification metrics.
- **False-Allow Rate**: Fraction of ALLOW predictions that were actually unsafe.
- **False-Block Rate**: Fraction of BLOCK predictions that were actually safe.
- **Override Rate**: Fraction of decisions where human review changed the disposition.

## Asymmetric Risk

Policies can define error costs:
```yaml
error_costs:
  false_allow: 10.0   # Cost of letting a bad action through
  false_block: 1.0    # Cost of blocking a good action
```

The threshold optimizer minimizes expected cost given calibration data.

## Drift Detection

- **PSI (Population Stability Index)**: Detects distribution shifts in confidence/probability values.
- **Jensen-Shannon Divergence**: Symmetric measure of distribution difference.
- **Disposition Distribution Shift**: Tracks changes in ALLOW/BLOCK/REVIEW/RETRY proportions.

## Replay

Re-evaluate historical decisions with different policies or thresholds without executing external actions. Replay uses stored Jev responses by default.
