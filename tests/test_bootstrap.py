"""Tests for bootstrap_pf_ci."""
import math

import pytest

from src.strategy.auto_iterate.bootstrap import bootstrap_pf_ci


def test_stable_with_seed():
    """同 seed 同輸入 → 結果應完全一致（reproducibility）"""
    trades = [0.10, -0.05, 0.20, -0.08, 0.15, -0.03, 0.25, -0.10, 0.05, 0.12]
    r1 = bootstrap_pf_ci(trades, n_iterations=500, seed=42)
    r2 = bootstrap_pf_ci(trades, n_iterations=500, seed=42)
    assert r1["pf_lower"] == r2["pf_lower"]
    assert r1["pf_mean"] == r2["pf_mean"]
    # 真實 PF gross 0.87 / 0.26 ≈ 3.35；bootstrap lower 應 > 0、< mean
    assert r1["pf_lower"] > 0.0
    assert r1["pf_lower"] < r1["pf_mean"]
    assert r1["pf_lower"] < r1["pf_upper"]


def test_zero_loss_capped_at_5():
    """全贏（無虧損）→ PF 應 cap 在 5.0"""
    trades = [0.10, 0.05, 0.20, 0.15, 0.08, 0.12]  # 全 > 0
    r = bootstrap_pf_ci(trades, n_iterations=500, seed=42)
    # 任何重抽都不會出現虧損，所有 PF 應為 5.0
    assert r["pf_lower"] == pytest.approx(5.0)
    assert r["pf_upper"] == pytest.approx(5.0)
    assert r["pf_mean"] == pytest.approx(5.0)


def test_too_few_trades_returns_nan():
    """< 5 筆 → 全部欄位 nan"""
    trades = [0.10, -0.05, 0.20, -0.08]  # 4 筆
    r = bootstrap_pf_ci(trades, n_iterations=500, seed=42)
    assert math.isnan(r["pf_lower"])
    assert math.isnan(r["pf_upper"])
    assert math.isnan(r["pf_mean"])
    assert r["n_original"] == 4


def test_pf_lower_pct_default_0_025():
    """confidence=0.95 → pf_lower_pct = 0.025"""
    trades = [0.10, -0.05, 0.20, -0.08, 0.15]
    r = bootstrap_pf_ci(trades, n_iterations=200, confidence=0.95, seed=42)
    assert r["pf_lower_pct"] == pytest.approx(0.025)
    assert r["n_iterations"] == 200


def test_lower_below_upper():
    """sanity：lower 應 ≤ upper"""
    trades = [0.10, -0.05, 0.20, -0.08, 0.15, -0.03, 0.25, -0.10]
    r = bootstrap_pf_ci(trades, n_iterations=1000, seed=42)
    assert r["pf_lower"] <= r["pf_upper"]
    assert r["pf_lower"] <= r["pf_mean"] <= r["pf_upper"] or \
           abs(r["pf_mean"] - r["pf_upper"]) < 0.01  # 邊界容忍
