"""Tests for chip_streak template — institutional persistent net-buy streak.

Coverage:
- Registration in 3 places (TEMPLATE_NAMES / TEMPLATE_GENERATORS / SEARCH_SPACES)
- Streak detection: 5 consecutive synthetic buy days → BUY signal
- Graceful degrade when chip_data is None / empty
- Exit on streak break (single sell day)
- No-lookahead: truncating future data must not change earlier signals
- Integration with backtest_one on cached real data (2317 if available)
"""
import os
import numpy as np
import pandas as pd
import pytest

from src.strategy.auto_iterate.templates import (
    TEMPLATE_NAMES,
    TEMPLATE_GENERATORS,
    SEARCH_SPACES,
    generate_signals_chip_streak,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def trending_df():
    """300 trading-day uptrending OHLCV with realistic volume."""
    np.random.seed(7)
    n = 300
    dates = pd.date_range("2022-01-03", periods=n, freq="B")
    close = 100 * np.exp(np.cumsum(np.random.normal(0.0010, 0.012, n)))
    high = close * (1 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.005, n)))
    open_ = close + np.random.normal(0, 0.3, n)
    vol = np.random.uniform(8e5, 2e6, n)  # avg ≈ 1.4M shares/day
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol},
        index=dates,
    )


def _build_chip_with_streak(df, start_idx, streak_len, daily_buy=300_000):
    """Build a chip_data DataFrame with a forced foreign-buy streak.

    Days [start_idx, start_idx+streak_len) get net buy of `daily_buy` shares;
    everything else is 0.
    """
    n = len(df)
    foreign = np.zeros(n)
    trust   = np.zeros(n)
    for k in range(streak_len):
        idx = start_idx + k
        if 0 <= idx < n:
            foreign[idx] = daily_buy
    return pd.DataFrame(
        {"foreign_net": foreign, "trust_net": trust},
        index=df.index,
    )


# ── Registration tests ───────────────────────────────────────────

def test_chip_streak_registered():
    assert "chip_streak" in TEMPLATE_NAMES
    assert "chip_streak" in TEMPLATE_GENERATORS
    assert "chip_streak" in SEARCH_SPACES
    space = SEARCH_SPACES["chip_streak"]
    # Required keys per the spec
    for k in ("actor", "streak_days", "cum_pct_min", "trend_filter",
              "ma_period", "regime_filter", "atr_mult", "max_hold_days"):
        assert k in space, f"missing search-space key: {k}"
    # actor must be the 3 documented choices
    assert set(space["actor"]["choices"]) == {"foreign", "trust", "either"}


# ── Behaviour tests ──────────────────────────────────────────────

def test_no_chip_data_returns_all_hold(trending_df):
    """When chip_data is None or empty, generator must not crash and
    must emit only HOLD."""
    p = {
        "actor": "foreign", "streak_days": 5, "cum_pct_min": 1.0,
        "trend_filter": False, "ma_period": 50,
        "regime_filter": "any", "atr_mult": 3.0, "max_hold_days": 30,
    }
    r1 = generate_signals_chip_streak(trending_df, p, chip_data=None)
    assert "action" in r1.columns
    assert (r1["action"] == "HOLD").all()

    r2 = generate_signals_chip_streak(trending_df, p, chip_data=pd.DataFrame())
    assert (r2["action"] == "HOLD").all()


def test_streak_triggers_buy(trending_df):
    """5 consecutive foreign-buy days with material size should produce a BUY."""
    # Inject streak starting on day 60 (warmup margin for SMA/ATR)
    streak_start = 60
    streak_len   = 5
    # daily_buy = 1.5M shares × 5 days = 7.5M total, far exceeds 1% × 1.4M × 5 = 70k threshold
    chip = _build_chip_with_streak(trending_df, streak_start, streak_len,
                                   daily_buy=1_500_000)
    p = {
        "actor": "foreign", "streak_days": 5, "cum_pct_min": 1.0,
        "trend_filter": False, "ma_period": 50,
        "regime_filter": "any", "atr_mult": 3.0, "max_hold_days": 30,
    }
    r = generate_signals_chip_streak(trending_df, p, chip_data=chip)
    n_buy = (r["action"] == "BUY").sum()
    assert n_buy >= 1, "expected at least one BUY signal from 5-day streak"
    # First BUY should land on day streak_start+streak_len (chip_data shifted by 1
    # → streak of length 5 ending at day t-1 visible at day t).
    first_buy_idx = (r["action"] == "BUY").to_numpy().argmax()
    # Allow a small window around streak_start + streak_len
    assert streak_start + streak_len - 1 <= first_buy_idx <= streak_start + streak_len + 2, (
        f"BUY landed at idx {first_buy_idx}, expected near {streak_start + streak_len}"
    )


def test_exit_on_streak_break(trending_df):
    """After a BUY, a single net-sell day should trigger SELL (streak break)."""
    streak_start = 60
    streak_len   = 5
    chip = _build_chip_with_streak(trending_df, streak_start, streak_len,
                                   daily_buy=1_500_000)
    # Add a clear sell day a few sessions after the streak ends
    sell_day_idx = streak_start + streak_len + 3
    chip.iloc[sell_day_idx, chip.columns.get_loc("foreign_net")] = -2_000_000

    p = {
        "actor": "foreign", "streak_days": 5, "cum_pct_min": 1.0,
        "trend_filter": False, "ma_period": 50,
        "regime_filter": "any", "atr_mult": 5.0,  # generous so ATR stop won't fire
        "max_hold_days": 60,
    }
    r = generate_signals_chip_streak(trending_df, p, chip_data=chip)

    buys  = np.where(r["action"].to_numpy() == "BUY")[0]
    sells = np.where(r["action"].to_numpy() == "SELL")[0]
    assert len(buys) >= 1 and len(sells) >= 1, (
        f"expected at least one BUY and one SELL, got BUY={len(buys)} SELL={len(sells)}"
    )
    first_buy = buys[0]
    # The sell day flow is shifted by 1 day in the generator → SELL appears at sell_day_idx + 1
    matching_sells = [s for s in sells if s > first_buy]
    assert len(matching_sells) >= 1
    first_sell = matching_sells[0]
    # SELL should be within a couple of bars of the injected break day
    assert sell_day_idx <= first_sell <= sell_day_idx + 2, (
        f"SELL at {first_sell}, expected near {sell_day_idx + 1}"
    )


def test_no_lookahead(trending_df):
    """Truncating the dataframe and chip_data after day 200 must not change
    the action sequence over days 0..199."""
    chip_full = _build_chip_with_streak(trending_df, 60, 5,
                                        daily_buy=1_500_000)
    p = {
        "actor": "foreign", "streak_days": 5, "cum_pct_min": 1.0,
        "trend_filter": False, "ma_period": 50,
        "regime_filter": "any", "atr_mult": 3.0, "max_hold_days": 30,
    }
    full = generate_signals_chip_streak(trending_df, p, chip_data=chip_full)
    truncated = generate_signals_chip_streak(
        trending_df.iloc[:200], p, chip_data=chip_full.iloc[:200],
    )
    pd.testing.assert_series_equal(
        full["action"].iloc[:200].reset_index(drop=True),
        truncated["action"].reset_index(drop=True),
        check_names=False,
    )


def test_backtest_one_integration_real_data():
    """End-to-end: run chip_streak through backtest_one on a real cached stock.

    Uses 2317 (foreign-heavy mid-cap with cached chip data). Skips if data
    isn't present locally — keeps CI green on machines without data/.
    """
    from src.strategy.auto_iterate.backtest_one import backtest_one
    from src.strategy.auto_iterate.chip_fetcher import load_chip_data
    from src.strategy.backtest.engine import BacktestConfig

    sid = "2317"
    adj_path  = os.path.join(BASE_DIR, "data", "adjusted", f"{sid}.csv")
    chip_path = os.path.join(BASE_DIR, "data", "chips",   f"{sid}.csv")
    if not (os.path.exists(adj_path) and os.path.exists(chip_path)):
        pytest.skip(f"required cached data missing for {sid}")

    from src.strategy.runner import _load_adj_ohlcv
    df   = _load_adj_ohlcv(sid)
    chip = load_chip_data(sid)
    assert df is not None and len(df) > 250
    assert not chip.empty

    # Pull real fees structure from config/strategy.yaml (avoids drift)
    import yaml
    with open(os.path.join(BASE_DIR, "config", "strategy.yaml"),
              encoding="utf-8") as f:
        fees = (yaml.safe_load(f) or {}).get("fees", {})
    bt_cfg = BacktestConfig(
        fees=fees,
        start_date="2022-01-01",
        end_date="2024-12-31",
        initial_capital=100_000,
        max_position_pct=1.0,
    )
    params = {
        "actor": "either", "streak_days": 4, "cum_pct_min": 1.0,
        "trend_filter": True, "ma_period": 50,
        "regime_filter": "any", "atr_mult": 3.0, "max_hold_days": 30,
    }
    metrics = backtest_one(sid, df, "chip_streak", params, bt_cfg,
                           chip_data=chip)
    # Just sanity — engine returned a metrics dict with expected keys, no crash
    for k in ("n_trades", "profit_factor", "max_drawdown", "win_rate",
              "expectancy", "cagr", "bnh_cagr"):
        assert k in metrics
