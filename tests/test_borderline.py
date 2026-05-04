"""Tests for is_borderline_dd, is_borderline_low_n, and classify SUSPICIOUS_PERFECT."""
import sys
import os
import math
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.auto_iterate.runner import is_borderline_dd, is_borderline_low_n
from src.strategy.auto_iterate.backtest_one import classify


# ── is_borderline_dd ──────────────────────────────────────────────

class TestIsBorderlineDD:
    def _m(self, n=6, dd=-0.32, pf=2.0, exp=0.07):
        return {"n_trades": n, "max_drawdown": dd, "profit_factor": pf, "expectancy": exp}

    def test_true_when_dd_between_30_35_and_pass_criteria_met(self):
        assert is_borderline_dd(self._m(dd=-0.32)) is True

    def test_true_at_dd_exactly_35(self):
        assert is_borderline_dd(self._m(dd=-0.35)) is True

    def test_false_when_dd_exactly_30(self):
        # DD exactly 30% is not a DD_BREACH, so it's a real PASS — not borderline
        assert is_borderline_dd(self._m(dd=-0.30)) is False

    def test_false_when_dd_above_35(self):
        assert is_borderline_dd(self._m(dd=-0.40)) is False

    def test_false_when_dd_below_30(self):
        assert is_borderline_dd(self._m(dd=-0.25)) is False

    def test_false_when_n_below_5(self):
        assert is_borderline_dd(self._m(n=4, dd=-0.32)) is False

    def test_false_when_pf_below_1_5(self):
        assert is_borderline_dd(self._m(pf=1.4)) is False

    def test_false_when_exp_below_5pct(self):
        assert is_borderline_dd(self._m(exp=0.04)) is False

    def test_false_when_pf_inf(self):
        assert is_borderline_dd(self._m(pf=float("inf"))) is False

    def test_false_when_pf_nan(self):
        assert is_borderline_dd(self._m(pf=float("nan"))) is False

    def test_false_when_exp_nan(self):
        assert is_borderline_dd(self._m(exp=float("nan"))) is False

    def test_true_at_dd_just_above_30(self):
        assert is_borderline_dd(self._m(dd=-0.301)) is True


# ── is_borderline_low_n ───────────────────────────────────────────

class TestIsBorderlineLowN:
    def _m(self, n=3, dd=-0.20, pf=2.0, exp=0.10):
        return {"n_trades": n, "max_drawdown": dd, "profit_factor": pf, "expectancy": exp}

    def test_true_when_n_3_and_pass_criteria_met(self):
        assert is_borderline_low_n(self._m(n=3)) is True

    def test_true_when_n_4_and_pass_criteria_met(self):
        assert is_borderline_low_n(self._m(n=4)) is True

    def test_false_when_n_5(self):
        # n=5 is sufficient — classified by regular PASS/FAIL, not borderline
        assert is_borderline_low_n(self._m(n=5)) is False

    def test_false_when_n_2(self):
        assert is_borderline_low_n(self._m(n=2)) is False

    def test_false_when_dd_exceeds_30(self):
        assert is_borderline_low_n(self._m(dd=-0.31)) is False

    def test_false_when_pf_below_1_5(self):
        assert is_borderline_low_n(self._m(pf=1.4)) is False

    def test_false_when_exp_below_5pct(self):
        assert is_borderline_low_n(self._m(exp=0.04)) is False

    def test_false_when_pf_inf(self):
        # PF=inf suggests a single winning trade — exclude to avoid spurious signals
        assert is_borderline_low_n(self._m(pf=float("inf"))) is False

    def test_false_when_pf_nan(self):
        assert is_borderline_low_n(self._m(pf=float("nan"))) is False

    def test_false_when_exp_nan(self):
        assert is_borderline_low_n(self._m(exp=float("nan"))) is False

    def test_true_at_dd_exactly_30(self):
        assert is_borderline_low_n(self._m(dd=-0.30)) is True


# ── classify SUSPICIOUS_PERFECT ──────────────────────────────────

class TestClassifySuspiciousPerfect:
    def _m(self, n=6, pf=4.0, exp=0.08, dd=-0.20, avg_loss=-0.04):
        return {"n_trades": n, "profit_factor": pf, "expectancy": exp,
                "max_drawdown": dd, "avg_loss": avg_loss}

    def test_suspicious_when_avg_loss_zero(self):
        # avg_loss=0 means no losing trades — even if PF is None (was inf in yaml)
        assert classify(self._m(pf=None, avg_loss=0.0)) == "SUSPICIOUS_PERFECT"

    def test_suspicious_when_pf_inf(self):
        assert classify(self._m(pf=float("inf"), avg_loss=0.0)) == "SUSPICIOUS_PERFECT"

    def test_suspicious_when_pf_above_10(self):
        assert classify(self._m(pf=10.1, avg_loss=-0.01)) == "SUSPICIOUS_PERFECT"

    def test_suspicious_at_pf_exactly_10_boundary(self):
        # pf > 10.0 triggers suspicious; pf == 10.0 does not
        assert classify(self._m(pf=10.0, avg_loss=-0.01)) == "PASS"

    def test_normal_pass_not_suspicious(self):
        assert classify(self._m(pf=4.82, avg_loss=-0.09)) == "PASS"

    def test_insufficient_before_suspicious(self):
        # n<5 always wins
        assert classify(self._m(n=4, pf=float("inf"), avg_loss=0.0)) == "INSUFFICIENT"

    def test_dd_breach_before_suspicious(self):
        assert classify(self._m(dd=-0.35, pf=float("inf"), avg_loss=0.0)) == "DD_BREACH"

    def test_suspicious_requires_exp_above_1pct(self):
        # expectancy < 1% → FAIL, not SUSPICIOUS_PERFECT
        assert classify(self._m(avg_loss=0.0, exp=0.005)) == "FAIL"

    def test_real_2360_case(self):
        # Replicates the 2360×donchian case: pf=None (was inf), avg_loss=0
        m = {"n_trades": 5, "profit_factor": None, "max_drawdown": -0.191,
             "win_rate": 1.0, "expectancy": 0.205, "avg_win": 0.205, "avg_loss": 0.0}
        assert classify(m) == "SUSPICIOUS_PERFECT"

    def test_real_1560_case(self):
        # Replicates 1560×mean_reversion: pf=248, avg_loss=0
        m = {"n_trades": 5, "profit_factor": 248.634, "max_drawdown": -0.12,
             "win_rate": 1.0, "expectancy": 0.128, "avg_win": 0.128, "avg_loss": 0.0}
        assert classify(m) == "SUSPICIOUS_PERFECT"
