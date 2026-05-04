"""Smoke tests for v2 new templates: volume_breakout, gap_continuation,
low_vol_pullback, bollinger_squeeze.

Goal: confirm signal generators don't crash, produce action column,
generate at least some BUY/SELL pairs on synthetic trending data,
and respect anti-lookahead (no future data leakage)."""
import numpy as np
import pandas as pd
import pytest

from src.strategy.auto_iterate.templates import (
    TEMPLATE_NAMES, TEMPLATE_GENERATORS, SEARCH_SPACES,
    generate_T6, generate_T7, generate_T8, generate_T9,
)


@pytest.fixture
def synth_df():
    """500 trading-day synthetic data: trending up with volatility."""
    np.random.seed(42)
    n = 500
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    close = 100 * np.exp(np.cumsum(np.random.normal(0.0008, 0.015, n)))
    high = close * (1 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.005, n)))
    open_ = close + np.random.normal(0, 0.5, n)
    vol = np.random.uniform(1e6, 5e6, n)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol},
        index=dates,
    )


def test_new_templates_registered():
    """All 4 new templates are in TEMPLATE_NAMES, GENERATORS, SEARCH_SPACES."""
    for name in ("volume_breakout", "gap_continuation",
                 "low_vol_pullback", "bollinger_squeeze"):
        assert name in TEMPLATE_NAMES, f"{name} missing from TEMPLATE_NAMES"
        assert name in TEMPLATE_GENERATORS, f"{name} missing from GENERATORS"
        assert name in SEARCH_SPACES, f"{name} missing from SEARCH_SPACES"


def test_volume_breakout_action_column(synth_df):
    p = {"lookback": 20, "vol_ratio": 1.5, "short_ma_exit": 10, "atr_stop_k": 3.0}
    r = generate_T6(synth_df, p)
    assert "action" in r.columns
    assert len(r) == len(synth_df)
    assert set(r["action"].unique()).issubset({"BUY", "SELL", "HOLD"})


def test_gap_continuation_action_column(synth_df):
    p = {"gap_pct": 0.02, "max_hold_days": 10, "stop_atr_k": 2.5, "trend_ma": 100}
    r = generate_T7(synth_df, p)
    assert "action" in r.columns
    assert len(r) == len(synth_df)
    assert set(r["action"].unique()).issubset({"BUY", "SELL", "HOLD"})


def test_low_vol_pullback_action_column(synth_df):
    p = {"long_ma": 150, "short_ma": 20, "down_days": 3, "pb_pct": 0.02,
         "take_profit_pct": 0.05, "max_hold_days": 40}
    r = generate_T8(synth_df, p)
    assert "action" in r.columns
    assert len(r) == len(synth_df)
    assert set(r["action"].unique()).issubset({"BUY", "SELL", "HOLD"})


def test_bollinger_squeeze_action_column(synth_df):
    p = {"bb_period": 20, "bb_k": 2.0, "squeeze_lookback": 120, "squeeze_pct": 0.20,
         "trend_ma": 100, "atr_stop_k": 3.0}
    r = generate_T9(synth_df, p)
    assert "action" in r.columns
    assert len(r) == len(synth_df)
    assert set(r["action"].unique()).issubset({"BUY", "SELL", "HOLD"})


def test_buy_sell_pairing(synth_df):
    """每個模板：BUY 數應 = SELL 數 ± 1（最後可能持倉未出）。"""
    fixtures = [
        ("volume_breakout", generate_T6,
         {"lookback": 20, "vol_ratio": 1.5, "short_ma_exit": 10, "atr_stop_k": 3.0}),
        ("gap_continuation", generate_T7,
         {"gap_pct": 0.02, "max_hold_days": 10, "stop_atr_k": 2.5, "trend_ma": 100}),
        ("low_vol_pullback", generate_T8,
         {"long_ma": 150, "short_ma": 20, "down_days": 3, "pb_pct": 0.02,
          "take_profit_pct": 0.05, "max_hold_days": 40}),
        ("bollinger_squeeze", generate_T9,
         {"bb_period": 20, "bb_k": 2.0, "squeeze_lookback": 120, "squeeze_pct": 0.20,
          "trend_ma": 100, "atr_stop_k": 3.0}),
    ]
    for name, fn, params in fixtures:
        r = fn(synth_df, params)
        n_buy = (r["action"] == "BUY").sum()
        n_sell = (r["action"] == "SELL").sum()
        assert abs(n_buy - n_sell) <= 1, (
            f"{name}: BUY={n_buy} SELL={n_sell} 不平衡 (>1)"
        )


def test_no_lookahead_volume_breakout(synth_df):
    """Anti-lookahead：截斷後 N 日的訊號不應改變。

    給 generate_T6 完整 500 日資料和截至 400 日的資料，
    第 1~400 日的訊號應完全相同。"""
    p = {"lookback": 20, "vol_ratio": 1.5, "short_ma_exit": 10, "atr_stop_k": 3.0}
    full = generate_T6(synth_df, p)
    truncated = generate_T6(synth_df.iloc[:400], p)
    pd.testing.assert_series_equal(
        full["action"].iloc[:400], truncated["action"], check_names=False,
    )
