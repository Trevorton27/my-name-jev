from jevops.analytics.drift import (
    disposition_distribution_shift,
    jensen_shannon_divergence,
    population_stability_index,
)


class TestPSI:
    def test_identical_distributions(self):
        data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        psi = population_stability_index(data, data)
        assert psi < 0.01

    def test_different_distributions(self):
        ref = [0.1, 0.2, 0.3, 0.4, 0.5] * 20
        cur = [0.6, 0.7, 0.8, 0.9, 1.0] * 20
        psi = population_stability_index(ref, cur)
        assert psi > 0.1

    def test_empty(self):
        assert population_stability_index([], []) == 0.0
        assert population_stability_index([0.5], []) == 0.0


class TestJSD:
    def test_identical_distributions(self):
        data = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        jsd = jensen_shannon_divergence(data, data)
        assert jsd < 0.01

    def test_different_distributions(self):
        ref = [0.1, 0.2, 0.3] * 30
        cur = [0.7, 0.8, 0.9] * 30
        jsd = jensen_shannon_divergence(ref, cur)
        assert jsd > 0.1

    def test_non_negative(self):
        jsd = jensen_shannon_divergence([0.5], [0.5])
        assert jsd >= 0.0


class TestDispositionShift:
    def test_no_shift(self):
        ref = {"allow": 50, "block": 50}
        cur = {"allow": 50, "block": 50}
        shifts = disposition_distribution_shift(ref, cur)
        assert all(abs(v) < 0.01 for v in shifts.values())

    def test_shift_detected(self):
        ref = {"allow": 80, "block": 20}
        cur = {"allow": 40, "block": 60}
        shifts = disposition_distribution_shift(ref, cur)
        assert shifts["allow"] < 0
        assert shifts["block"] > 0

    def test_new_category(self):
        ref = {"allow": 100}
        cur = {"allow": 80, "block": 20}
        shifts = disposition_distribution_shift(ref, cur)
        assert "block" in shifts
