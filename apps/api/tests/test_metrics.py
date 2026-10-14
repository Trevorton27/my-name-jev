from jevops.analytics.metrics import (
    accuracy,
    brier_score,
    calibration_curve,
    confusion_matrix,
    expected_calibration_error,
    false_allow_rate,
    false_block_rate,
    override_rate,
    precision_recall_f1,
    recommended_threshold,
)


class TestBrierScore:
    def test_perfect_predictions(self):
        assert brier_score([1.0, 0.0, 1.0], [1, 0, 1]) == 0.0

    def test_worst_predictions(self):
        assert brier_score([0.0, 1.0], [1, 0]) == 1.0

    def test_intermediate(self):
        score = brier_score([0.7, 0.3], [1, 0])
        assert 0.0 < score < 1.0

    def test_empty(self):
        assert brier_score([], []) == 0.0


class TestECE:
    def test_perfectly_calibrated(self):
        # When predicted probabilities match empirical frequencies, ECE ~ 0
        probs = [0.1] * 10 + [0.9] * 10
        outcomes = [0] * 9 + [1] * 1 + [1] * 9 + [0] * 1
        ece = expected_calibration_error(probs, outcomes, n_bins=10)
        assert ece < 0.15

    def test_empty(self):
        assert expected_calibration_error([], []) == 0.0

    def test_ece_range(self):
        probs = [0.5] * 100
        outcomes = [1] * 50 + [0] * 50
        ece = expected_calibration_error(probs, outcomes)
        assert 0.0 <= ece <= 1.0


class TestCalibrationCurve:
    def test_returns_correct_bins(self):
        bins = calibration_curve([0.1, 0.5, 0.9], [0, 1, 1], n_bins=5)
        assert len(bins) == 5

    def test_empty_bins(self):
        bins = calibration_curve([], [], n_bins=5)
        assert len(bins) == 5
        assert all(b["count"] == 0 for b in bins)


class TestConfusionMatrix:
    def test_basic(self):
        preds = ["allow", "block", "allow", "block"]
        actual = ["allow", "allow", "block", "block"]
        labels = ["allow", "block"]
        cm = confusion_matrix(preds, actual, labels)
        assert cm["allow"]["allow"] == 1
        assert cm["allow"]["block"] == 1
        assert cm["block"]["allow"] == 1
        assert cm["block"]["block"] == 1


class TestAccuracy:
    def test_perfect(self):
        assert accuracy(["a", "b"], ["a", "b"]) == 1.0

    def test_zero(self):
        assert accuracy(["a", "b"], ["b", "a"]) == 0.0

    def test_empty(self):
        assert accuracy([], []) == 0.0


class TestPrecisionRecallF1:
    def test_perfect(self):
        result = precision_recall_f1(["allow", "block"], ["allow", "block"], "allow")
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_no_positive_predictions(self):
        result = precision_recall_f1(["block", "block"], ["allow", "block"], "allow")
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0


class TestRates:
    def test_false_allow_rate(self):
        preds = ["allow", "allow", "block", "allow"]
        actual = ["allow", "block", "block", "allow"]
        rate = false_allow_rate(preds, actual)
        assert abs(rate - 1 / 3) < 0.01

    def test_false_block_rate(self):
        preds = ["block", "block", "allow"]
        actual = ["allow", "block", "allow"]
        rate = false_block_rate(preds, actual)
        assert rate == 0.5

    def test_override_rate(self):
        original = ["allow", "block", "human_review"]
        final = ["allow", "allow", "human_review"]
        rate = override_rate(original, final)
        assert abs(rate - 1 / 3) < 0.01


class TestRecommendedThreshold:
    def test_returns_valid_threshold(self):
        probs = [0.1, 0.3, 0.5, 0.7, 0.9]
        outcomes = [0, 0, 0, 1, 1]
        t = recommended_threshold(probs, outcomes)
        assert 0.0 < t < 1.0

    def test_empty(self):
        assert recommended_threshold([], []) == 0.5

    def test_asymmetric_costs(self):
        probs = [0.3, 0.4, 0.5, 0.6, 0.7]
        outcomes = [0, 0, 1, 1, 1]
        t_high_allow_cost = recommended_threshold(probs, outcomes, false_allow_cost=100.0, false_block_cost=1.0)
        t_high_block_cost = recommended_threshold(probs, outcomes, false_allow_cost=1.0, false_block_cost=100.0)
        # Higher false-allow cost should push threshold higher
        assert t_high_allow_cost >= t_high_block_cost
