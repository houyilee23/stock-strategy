"""Tests for per-stock template dispatch in run_signals.

Verifies that:
- Tradeable stocks dispatch to their assigned template (not style1_pullback)
- F-tier / absent stocks fallback to style1_pullback
- The cache helpers correctly load recommendations + params
"""
import os
import sys
import yaml
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy import runner as runner_mod
from src.strategy.runner import (
    _generate_for_stock,
    _load_recommendations,
    _resolve_params_ref,
)


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def synth_df():
    """600 trading days of synthetic OHLCV with mild uptrend."""
    np.random.seed(7)
    n = 600
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    close = 100 * np.exp(np.cumsum(np.random.normal(0.0006, 0.013, n)))
    high = close * (1 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.005, n)))
    open_ = close + np.random.normal(0, 0.5, n)
    vol = np.random.uniform(1e6, 5e6, n)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": vol},
        index=dates,
    )


@pytest.fixture
def bull_regime(synth_df):
    return pd.Series("BULL", index=synth_df.index)


@pytest.fixture
def fallback_params():
    """Load real strategy.yaml's style1_pullback params (used by fallback path)."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base, "config", "strategy.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)["style1_pullback"]


@pytest.fixture
def temp_recommendations_setup(tmp_path, monkeypatch):
    """Create a temp run_id dir with template params YAMLs and inject as
    'latest auto_iterate dir' so _resolve_params_ref finds them."""
    run_dir = tmp_path / "20260101_000000"
    run_dir.mkdir()

    # Donchian params for stock 'TEST_TRADE'
    donchian_yaml = {
        "template": "donchian_breakout",
        "per_stock": {
            "TEST_TRADE": {
                "best_params": {
                    "donchian_entry_n": 20,
                    "donchian_exit_n": 10,
                    "trend_ma": 50,
                    "atr_stop_k": 3.0,
                    "volume_min_ratio": 1.0,
                }
            }
        },
    }
    with open(run_dir / "donchian_breakout.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(donchian_yaml, f)

    # mean_reversion params for another tradeable stock
    mr_yaml = {
        "template": "mean_reversion",
        "per_stock": {
            "TEST_MR": {
                "best_params": {
                    "trend_ma": 200,
                    "short_ma": 20,
                    "pullback_pct": 0.05,
                    "rsi_period": 14,
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "take_profit_pct": 0.08,
                    "max_hold_days": 60,
                }
            }
        },
    }
    with open(run_dir / "mean_reversion.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(mr_yaml, f)

    # Patch the latest-dir resolver and clear template-params cache
    monkeypatch.setattr(runner_mod, "_find_latest_auto_iterate_dir",
                        lambda: str(run_dir))
    runner_mod._TEMPLATE_PARAMS_CACHE.clear()
    return str(run_dir)


# ── Test 1: tradeable stock dispatches to its assigned template ──


def test_tradeable_dispatches_to_assigned_template(
        synth_df, bull_regime, fallback_params, temp_recommendations_setup):
    """A tradeable stock with template=donchian_breakout should NOT
    use style1_pullback's signal generator."""
    recommendations = {
        "TEST_TRADE": {
            "tier": "A",
            "template": "donchian_breakout",
            "params_ref": "donchian_breakout.yaml#per_stock.TEST_TRADE",
            "position_pct_max": 0.5,
            "tradeable": True,
        }
    }

    signals, template_used, tier, pos_max, tradeable = _generate_for_stock(
        "TEST_TRADE", synth_df, bull_regime, recommendations, fallback_params)

    assert template_used == "donchian_breakout", \
        f"Expected donchian_breakout dispatch, got {template_used}"
    assert tier == "A"
    assert pos_max == 0.5
    assert tradeable is True
    assert "action" in signals.columns
    # Donchian generator does NOT produce 'entry_low' / 'rsi_val' /
    # 'ma200' columns — style1_pullback does. So presence of just
    # 'action' is also a structural marker.
    assert "entry_low" not in signals.columns, \
        "donchian_breakout should not emit entry_low (that's style1's column)"
    assert set(signals["action"].unique()).issubset({"BUY", "SELL", "HOLD"})


# ── Test 2: F-tier / absent stocks fallback to style1_pullback ──


def test_ftier_falls_back_to_style1(
        synth_df, bull_regime, fallback_params, temp_recommendations_setup):
    """A stock with tradeable=false (F-tier) should use style1_pullback."""
    recommendations = {
        "TEST_FTIER": {
            "tier": "F",
            "template": "donchian_breakout",
            "params_ref": "donchian_breakout.yaml#per_stock.TEST_FTIER",
            "position_pct_max": 0.0,
            "tradeable": False,
        }
    }

    signals, template_used, tier, pos_max, tradeable = _generate_for_stock(
        "TEST_FTIER", synth_df, bull_regime, recommendations, fallback_params)

    assert template_used == "style1_pullback", \
        f"Expected fallback to style1_pullback for F-tier, got {template_used}"
    assert tier == "F"
    assert pos_max == 0.0
    assert tradeable is False
    # style1_pullback emits these columns; serves as structural signature
    for col in ("entry_low", "entry_high", "stop_loss", "rsi_val", "ma200"):
        assert col in signals.columns, \
            f"style1 fallback should emit {col} column"


def test_absent_stock_falls_back_to_style1(
        synth_df, bull_regime, fallback_params, temp_recommendations_setup):
    """A stock not in recommendations at all should fallback to style1."""
    signals, template_used, tier, pos_max, tradeable = _generate_for_stock(
        "UNKNOWN_SID", synth_df, bull_regime, {}, fallback_params)

    assert template_used == "style1_pullback"
    assert tradeable is False
    assert "entry_low" in signals.columns


# ── Test 3: helpers load YAML correctly ──


def test_load_recommendations_from_real_config():
    """Real config/per_stock_recommendations.yaml should load
    with expected keys (auto-generated; presence sanity check)."""
    runner_mod._RECOMMENDATIONS_CACHE = None  # reset cache
    recs = _load_recommendations()
    if not recs:
        pytest.skip("per_stock_recommendations.yaml not present in this env")
    # Pick any sample row and verify required fields exist
    sid, rec = next(iter(recs.items()))
    assert "template" in rec
    assert "tradeable" in rec
    assert "tier" in rec
    assert "position_pct_max" in rec


def test_resolve_params_ref(temp_recommendations_setup):
    """_resolve_params_ref should locate per_stock.<sid>.best_params
    given a 'file.yaml#per_stock.SID' string."""
    params = _resolve_params_ref("donchian_breakout.yaml#per_stock.TEST_TRADE")
    assert params.get("donchian_entry_n") == 20
    assert params.get("trend_ma") == 50

    # Bogus ref → empty dict (no exception)
    assert _resolve_params_ref("nonexistent.yaml#per_stock.X") == {}
    assert _resolve_params_ref("") == {}
    assert _resolve_params_ref("noref") == {}
