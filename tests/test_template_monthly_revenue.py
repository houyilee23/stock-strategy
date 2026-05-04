"""Tests for monthly_revenue_event template (Taiwan-specific calendar event).

Covers:
  - HOLD-only fallback when revenue_data is None / empty
  - Strong YoY revenue + gap-up + green-close → BUY signal triggers
  - Weak YoY → no entry
  - Anti-lookahead: signal at T uses only revenue announced ≤ T
  - Real backtest_one integration on 2330 (skipped if cache missing)
  - Template registered in TEMPLATE_NAMES / TEMPLATE_GENERATORS / SEARCH_SPACES
"""
import os
import numpy as np
import pandas as pd
import pytest

from src.strategy.auto_iterate.templates import (
    TEMPLATE_NAMES, TEMPLATE_GENERATORS, SEARCH_SPACES,
    generate_signals_monthly_revenue_event,
)


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def synth_price_df():
    """24 months of trading data; flat price baseline so we can plant
    a controlled gap-up event around announcement dates."""
    np.random.seed(0)
    dates = pd.date_range("2022-01-03", "2024-01-03", freq="B")
    n = len(dates)
    close = pd.Series(100.0 + np.random.normal(0, 0.5, n), index=dates)
    open_ = close.shift(1).fillna(close.iloc[0])  # flat opens
    high  = close + 0.5
    low   = close - 0.5
    vol   = pd.Series(1_000_000.0, index=dates)
    return pd.DataFrame({
        "open": open_, "high": high, "low": low,
        "close": close, "volume": vol,
    }, index=dates)


def _make_revenue(announcements: list[tuple[str, float]]) -> pd.DataFrame:
    """announcements: list of (announcement_date_str, yoy_pct)."""
    rows = []
    for ad, yoy in announcements:
        ad_ts = pd.Timestamp(ad)
        rows.append({
            "date":                    ad_ts - pd.Timedelta(days=10),
            "revenue_year":            ad_ts.year,
            "revenue_month":           ((ad_ts.month - 2) % 12) + 1,
            "revenue":                 1e10,
            "announcement_date":       ad_ts,
            "revenue_growth_yoy_pct":  yoy,
        })
    return pd.DataFrame(rows)


# ── Tests ───────────────────────────────────────────────────────────

def test_template_registered():
    """monthly_revenue_event in NAMES / GENERATORS / SEARCH_SPACES."""
    assert "monthly_revenue_event" in TEMPLATE_NAMES
    assert "monthly_revenue_event" in TEMPLATE_GENERATORS
    assert "monthly_revenue_event" in SEARCH_SPACES
    space = SEARCH_SPACES["monthly_revenue_event"]
    for k in ("revenue_yoy_min", "gap_pct", "require_green_close",
              "max_hold_days", "atr_mult", "regime_filter",
              "volume_filter", "volume_avg_period"):
        assert k in space, f"{k} missing from monthly_revenue_event SEARCH_SPACE"


def test_no_revenue_data_all_hold(synth_price_df):
    """revenue_data=None → all HOLD, no errors."""
    p = {"revenue_yoy_min": 0.20, "gap_pct": 0.01, "require_green_close": True,
         "max_hold_days": 10, "atr_mult": 3.0, "regime_filter": "any",
         "volume_filter": False, "volume_avg_period": 20}
    r = generate_signals_monthly_revenue_event(synth_price_df, p, revenue_data=None)
    assert "action" in r.columns
    assert (r["action"] == "HOLD").all()

    # also empty DataFrame
    r2 = generate_signals_monthly_revenue_event(
        synth_price_df, p, revenue_data=pd.DataFrame())
    assert (r2["action"] == "HOLD").all()


def test_strong_yoy_with_gap_triggers_buy(synth_price_df):
    """Plant strong YoY + gap-up + green close → expect at least 1 BUY."""
    df = synth_price_df.copy()
    # Plant gap-up + green close on 2023-02-13 (a Monday after weekend).
    # Use a date well inside the data with surrounding context.
    ann_dt = pd.Timestamp("2023-02-13")
    if ann_dt not in df.index:
        # fallback: pick first index after announcement
        idx = df.index[df.index >= ann_dt][0]
    else:
        idx = ann_dt
    pos = df.index.get_loc(idx)
    # Set previous close, then gap-up open and green close on `idx`
    df.iloc[pos - 1, df.columns.get_loc("close")] = 100.0
    df.iloc[pos,     df.columns.get_loc("open")]  = 105.0   # +5% gap
    df.iloc[pos,     df.columns.get_loc("close")] = 108.0   # green
    df.iloc[pos,     df.columns.get_loc("high")]  = 109.0
    df.iloc[pos,     df.columns.get_loc("low")]   = 104.5
    # high vol on this day too
    df.iloc[pos,     df.columns.get_loc("volume")] = 5_000_000

    rev = _make_revenue([(idx.strftime("%Y-%m-%d"), 0.40)])  # +40% YoY

    p = {"revenue_yoy_min": 0.20, "gap_pct": 0.01, "require_green_close": True,
         "max_hold_days": 10, "atr_mult": 3.0, "regime_filter": "any",
         "volume_filter": False, "volume_avg_period": 20}
    r = generate_signals_monthly_revenue_event(df, p, revenue_data=rev)
    # Should have at least 1 BUY at idx
    assert r.loc[idx, "action"] == "BUY", (
        f"Expected BUY at {idx}, got {r.loc[idx, 'action']}; "
        f"actions around: {r.iloc[max(0,pos-2):pos+3]['action'].tolist()}"
    )
    # At least 1 SELL afterwards (max_hold_days=10 forces exit)
    assert (r["action"] == "SELL").sum() >= 1


def test_weak_yoy_no_entry(synth_price_df):
    """Same gap setup but YoY only 5% → no BUY."""
    df = synth_price_df.copy()
    ann_dt = pd.Timestamp("2023-02-13")
    idx = df.index[df.index >= ann_dt][0]
    pos = df.index.get_loc(idx)
    df.iloc[pos - 1, df.columns.get_loc("close")] = 100.0
    df.iloc[pos,     df.columns.get_loc("open")]  = 105.0
    df.iloc[pos,     df.columns.get_loc("close")] = 108.0
    df.iloc[pos,     df.columns.get_loc("high")]  = 109.0
    df.iloc[pos,     df.columns.get_loc("low")]   = 104.5

    rev = _make_revenue([(idx.strftime("%Y-%m-%d"), 0.05)])  # only +5% YoY

    p = {"revenue_yoy_min": 0.20, "gap_pct": 0.01, "require_green_close": True,
         "max_hold_days": 10, "atr_mult": 3.0, "regime_filter": "any",
         "volume_filter": False, "volume_avg_period": 20}
    r = generate_signals_monthly_revenue_event(df, p, revenue_data=rev)
    assert (r["action"] == "BUY").sum() == 0


def test_strong_yoy_but_no_gap_no_entry(synth_price_df):
    """Strong YoY but no gap → no BUY (gap filter must hold)."""
    df = synth_price_df.copy()
    ann_dt = pd.Timestamp("2023-02-13")
    idx = df.index[df.index >= ann_dt][0]
    pos = df.index.get_loc(idx)
    # Tiny price move (no gap)
    df.iloc[pos - 1, df.columns.get_loc("close")] = 100.0
    df.iloc[pos,     df.columns.get_loc("open")]  = 100.0
    df.iloc[pos,     df.columns.get_loc("close")] = 100.5
    df.iloc[pos,     df.columns.get_loc("high")]  = 100.8

    rev = _make_revenue([(idx.strftime("%Y-%m-%d"), 0.40)])
    p = {"revenue_yoy_min": 0.20, "gap_pct": 0.02, "require_green_close": True,
         "max_hold_days": 10, "atr_mult": 3.0, "regime_filter": "any",
         "volume_filter": False, "volume_avg_period": 20}
    r = generate_signals_monthly_revenue_event(df, p, revenue_data=rev)
    assert (r["action"] == "BUY").sum() == 0


def test_no_lookahead_truncation(synth_price_df):
    """Truncating the price df after the announcement should NOT affect
    earlier signals (no future-data leakage)."""
    df = synth_price_df.copy()
    ann_dt = pd.Timestamp("2023-02-13")
    idx = df.index[df.index >= ann_dt][0]
    pos = df.index.get_loc(idx)
    df.iloc[pos - 1, df.columns.get_loc("close")] = 100.0
    df.iloc[pos,     df.columns.get_loc("open")]  = 105.0
    df.iloc[pos,     df.columns.get_loc("close")] = 108.0

    rev = _make_revenue([(idx.strftime("%Y-%m-%d"), 0.40)])
    p = {"revenue_yoy_min": 0.20, "gap_pct": 0.01, "require_green_close": True,
         "max_hold_days": 10, "atr_mult": 3.0, "regime_filter": "any",
         "volume_filter": False, "volume_avg_period": 20}

    full = generate_signals_monthly_revenue_event(df, p, revenue_data=rev)
    cut = pos + 3  # truncate just after entry, before exit window
    truncated = generate_signals_monthly_revenue_event(
        df.iloc[:cut], p, revenue_data=rev)
    pd.testing.assert_series_equal(
        full["action"].iloc[:cut], truncated["action"], check_names=False,
    )


def test_future_revenue_not_used(synth_price_df):
    """A revenue announcement dated AFTER the price window should never
    produce a BUY (announcement_date > all df.index → no entry)."""
    df = synth_price_df.copy()
    rev = _make_revenue([("2099-01-15", 0.50)])  # far future
    p = {"revenue_yoy_min": 0.20, "gap_pct": 0.01, "require_green_close": True,
         "max_hold_days": 10, "atr_mult": 3.0, "regime_filter": "any",
         "volume_filter": False, "volume_avg_period": 20}
    r = generate_signals_monthly_revenue_event(df, p, revenue_data=rev)
    assert (r["action"] == "BUY").sum() == 0


# ── Integration ────────────────────────────────────────────────────

@pytest.mark.skipif(
    not os.path.exists(os.path.join("data", "monthly_revenue", "2330.csv")),
    reason="2330 monthly revenue cache not present; run fetch-revenue first",
)
def test_backtest_one_integration_2330():
    """Smoke: run backtest_one on 2330 with monthly_revenue_event +
    real revenue cache; should not crash and return metric dict."""
    from src.strategy.auto_iterate.backtest_one import backtest_one
    from src.strategy.backtest.engine import BacktestConfig
    from src.strategy.runner import _load_adj_ohlcv
    from src.strategy.auto_iterate.revenue_fetcher import load_revenue_data

    df = _load_adj_ohlcv("2330")
    assert df is not None and len(df) > 250
    rev = load_revenue_data("2330")
    assert not rev.empty

    import yaml
    cfg_yaml = yaml.safe_load(
        open(os.path.join("config", "strategy.yaml"), encoding="utf-8"))
    cfg = BacktestConfig(
        fees=cfg_yaml["fees"],
        start_date="2017-01-01", end_date="2024-12-31",
        initial_capital=100_000, max_position_pct=1.0,
    )
    p = {"revenue_yoy_min": 0.30, "gap_pct": 0.01, "require_green_close": True,
         "max_hold_days": 10, "atr_mult": 3.0, "regime_filter": "any",
         "volume_filter": False, "volume_avg_period": 20}
    m = backtest_one("2330", df, "monthly_revenue_event", p, cfg,
                     regime=None, chip_data=None, revenue_data=rev)
    # Sanity
    assert "n_trades" in m
    assert m["n_trades"] >= 0
    assert isinstance(m.get("trades_pnl_pct", []), list)
