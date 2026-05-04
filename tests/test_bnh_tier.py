"""Tests for the BNH (Buy-and-Hold) parallel tier evaluation.

BNH is a supplementary track for F-tier stocks where active timing fails but
pure long-term holding still beats (or matches) 0050.

Covers ``tiering.assign_bnh_tier`` and ``bnh.compute_bnh_metrics`` smoke.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest

from src.strategy.auto_iterate.tiering import (
    assign_bnh_tier,
    assign_tier,
    BNH_TIER_RULES,
)
from src.strategy.auto_iterate.bnh import compute_bnh_metrics


# ── Fixtures ─────────────────────────────────────────────────────

# Realistic 0050-ish baseline used across BNH tests
MKT_BASELINE = {"cagr": 0.15, "max_dd": -0.30, "sharpe": 0.95}


# ── BNH_S: clearly beats 0050 + risk in check ─────────────────

def test_bnh_S_clearly_beats_market_with_low_dd():
    """CAGR=22% (vs 15% market, +7%), MaxDD=25% (≤40%) → BNH_S, pos_max=50%"""
    bnh = {"cagr": 0.22, "max_dd": -0.25, "sharpe": 1.10}
    tier, reason = assign_bnh_tier("9999", bnh, MKT_BASELINE, div_yield=0.02)
    assert tier == "BNH_S"
    assert "BNH_S" in reason
    assert BNH_TIER_RULES["BNH_S"]["pos_max"] == 0.50


# ── BNH_A: ties / slightly beats market, modest DD ────────────

def test_bnh_A_marginal_winner_over_market():
    """CAGR=16% (vs 15%, +1%), MaxDD=45% (≤50%) → BNH_A, pos_max=30%"""
    bnh = {"cagr": 0.16, "max_dd": -0.45, "sharpe": 0.70}
    tier, reason = assign_bnh_tier("8888", bnh, MKT_BASELINE, div_yield=0.01)
    assert tier == "BNH_A"
    assert BNH_TIER_RULES["BNH_A"]["pos_max"] == 0.30


# ── BNH_B: defensive dividend stock just below market ─────────

def test_bnh_B_defensive_dividend_stock():
    """CAGR=13% (vs 15%, -2%, ≥-3%), div_yield=4.5% → BNH_B, pos_max=20%

    DD constraint is None for BNH_B (defensive cash-flow logic — yield buffers).
    """
    bnh = {"cagr": 0.13, "max_dd": -0.42, "sharpe": 0.55}
    tier, reason = assign_bnh_tier("7777", bnh, MKT_BASELINE, div_yield=0.045)
    assert tier == "BNH_B"
    assert BNH_TIER_RULES["BNH_B"]["pos_max"] == 0.20


# ── F: dog stock that fails all tiers ─────────────────────────

def test_bnh_F_underperformer_no_dividend():
    """CAGR=-5% (vs 15%, -20%), low yield → F (no BNH rescue)"""
    bnh = {"cagr": -0.05, "max_dd": -0.50, "sharpe": -0.20}
    tier, reason = assign_bnh_tier("6666", bnh, MKT_BASELINE, div_yield=0.02)
    assert tier == "F"
    assert "BNH 不合格" in reason


def test_bnh_F_when_metrics_missing():
    """No BNH metrics (e.g. data file missing) → F."""
    tier, reason = assign_bnh_tier("0000", None, MKT_BASELINE, div_yield=None)
    assert tier == "F"
    assert "資料不足" in reason


# ── Tradeable stocks must NOT be downgraded by BNH track ──────

def test_bnh_does_not_affect_tradeable_stock():
    """Active-timing assign_tier (e.g. 2317-like B-tier) is independent of BNH.

    BNH evaluation is a *parallel* track — it only adds guidance for F-tier.
    Calling assign_tier with the same metrics must still return the active tier.
    """
    # 2317-like profile: PF_lower=1.2, exp=2.5%, n=6 → B
    test_m = {"n_trades": 6, "expectancy": 0.025}
    boot = {"pf_lower": 1.2}
    holdouts = {"A_new": False, "B": False, "C": False}
    active_tier, _ = assign_tier(test_m, boot, holdouts)
    assert active_tier == "B", "Sanity: active timing tier should remain B"

    # BNH metrics (even very strong ones) must NOT affect active tier — they're
    # consumed in a separate code path (assign_bnh_tier). Verify both tracks
    # coexist without interference: the BNH call returns its own tier without
    # mutating anything.
    bnh = {"cagr": 0.30, "max_dd": -0.20, "sharpe": 1.30}
    bnh_tier, _ = assign_bnh_tier("2317", bnh, MKT_BASELINE, div_yield=0.04)
    assert bnh_tier == "BNH_S"

    # Re-running assign_tier still yields B — no coupling.
    active_tier2, _ = assign_tier(test_m, boot, holdouts)
    assert active_tier2 == "B"


# ── Smoke test of compute_bnh_metrics on a synthetic series ──

def test_compute_bnh_metrics_synthetic():
    """Synthetic +10%/year geometric series over 4 years → CAGR ≈ 10%."""
    dates = pd.date_range("2020-01-02", "2023-12-29", freq="B")
    # Daily ret to give ~10% annual: (1+r)^252 = 1.10
    daily = 0.10 ** (1 / 252) if False else (1.10) ** (1 / 252) - 1
    prices = pd.Series(
        [100 * (1 + daily) ** i for i in range(len(dates))],
        index=dates,
    )
    m = compute_bnh_metrics(prices, start="2020-01-01", end="2023-12-31",
                             entry_cost=0.0)
    assert m is not None
    # ~10% CAGR (allow tolerance — BNH math is years-fraction based)
    assert 0.08 < m["cagr"] < 0.12
    # Monotonic up → MaxDD ≈ 0
    assert m["max_dd"] >= -0.001
    assert m["n_days"] == len(dates)


def test_compute_bnh_metrics_returns_none_for_short_window():
    """< 100 days window → None."""
    dates = pd.date_range("2024-01-02", periods=50, freq="B")
    prices = pd.Series(np.linspace(100, 110, 50), index=dates)
    assert compute_bnh_metrics(prices, start="2024-01-01", end="2024-12-31") is None


# ── Edge: market metrics None → fallback to absolute CAGR ─────

def test_bnh_S_when_market_baseline_unavailable():
    """If 0050 baseline missing, treat market as 0% — strong stock still BNH_S."""
    bnh = {"cagr": 0.20, "max_dd": -0.30, "sharpe": 1.0}
    tier, _ = assign_bnh_tier("9999", bnh, None, div_yield=0.0)
    # diff = 0.20 - 0 = 0.20 ≥ 0.05, dd 30% ≤ 40% → BNH_S
    assert tier == "BNH_S"
