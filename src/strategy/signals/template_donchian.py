"""Donchian breakout signal generator with optional market regime filter.

Mirrors the logic in auto_iterate/templates.py generate_T2, with one addition:
  regime_filter=True  →  entry requires 0050 close > 0050 200-day MA (bull filter).

Kept in src/strategy/signals/ so it can be used by validation scripts
without touching the auto_iterate runner or per_stock_best.yaml.
"""
import os
import numpy as np
import pandas as pd

from src.strategy.indicators.trend import sma
from src.strategy.indicators.volatility import atr
from src.strategy.indicators.volume import volume_ma

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


def _load_0050_close() -> pd.Series:
    """Load 0050 adjusted close; returns empty Series on failure."""
    path = os.path.join(_ROOT, "data", "adjusted", "0050.csv")
    if not os.path.exists(path):
        return pd.Series(dtype=float)
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    col = "close_adj" if "close_adj" in df.columns else "close"
    return df[col].sort_index()


def generate_donchian(
    df: pd.DataFrame,
    params: dict,
    regime_filter: bool = False,
    regime=None,      # unused; kept for API compatibility
    chip_data=None,   # unused; kept for API compatibility
) -> pd.DataFrame:
    """Donchian breakout signals.

    Entry conditions (all must be true):
      1. close >= previous-N-day high   (anti-lookahead: shift(1))
      2. close > trend_MA
      3. volume > volume_MA(20) * vol_ratio
      4. [if regime_filter] 0050 close > 0050 MA(200)

    Exit conditions (first hit exits):
      - close < previous-M-day low
      - close < ATR trailing stop (peak since entry − atr_k × ATR14)

    Args:
        df:            OHLCV DataFrame indexed by date.
        params:        Dict with keys: donchian_entry_n, donchian_exit_n,
                       trend_ma, atr_stop_k, volume_min_ratio.
        regime_filter: If True, adds 0050 MA(200) bull market gate to entry.

    Returns:
        DataFrame with 'action' column (BUY/SELL/HOLD), same index as df.
    """
    close = df["close"]
    high  = df["high"]
    vol   = df["volume"]

    entry_n   = int(params["donchian_entry_n"])
    exit_n    = int(params["donchian_exit_n"])
    trend_n   = int(params["trend_ma"])
    atr_k     = float(params["atr_stop_k"])
    vol_ratio = float(params["volume_min_ratio"])

    trend_ma_s = sma(close, trend_n)
    vol_ma20   = volume_ma(vol, 20)
    atr_s      = atr(df, 14)
    don_high   = close.rolling(entry_n).max().shift(1)
    don_low    = close.rolling(exit_n).min().shift(1)

    # Regime filter: 0050 close > 200-day MA
    bull_gate: pd.Series
    if regime_filter:
        bm_close = _load_0050_close()
        if bm_close.empty:
            # Fallback: allow all entries (degrades to no filter)
            bull_gate = pd.Series(True, index=df.index)
        else:
            bm_ma200  = sma(bm_close, 200)
            bull_flag = (bm_close > bm_ma200).reindex(df.index, method="ffill")
            bull_gate = bull_flag.fillna(False)
    else:
        bull_gate = pd.Series(True, index=df.index)

    n = len(df)
    action = ["HOLD"] * n
    in_pos = False
    high_since = np.nan

    for i in range(n):
        c  = close.iloc[i]
        h  = high.iloc[i]
        v  = vol.iloc[i]
        tm = trend_ma_s.iloc[i]
        vm = vol_ma20.iloc[i]
        dh = don_high.iloc[i]
        dl = don_low.iloc[i]
        ai = atr_s.iloc[i]
        bg = bull_gate.iloc[i]

        if in_pos:
            if not np.isnan(h):
                high_since = max(high_since, h) if not np.isnan(high_since) else h
            atr_stop = (high_since - atr_k * ai
                        if not np.isnan(high_since) and not np.isnan(ai) else np.nan)
            exit_cond = (not np.isnan(dl) and c < dl) or \
                        (not np.isnan(atr_stop) and c < atr_stop)
            if exit_cond:
                action[i] = "SELL"
                in_pos = False
                high_since = np.nan
        else:
            entry_ok = (
                not np.isnan(dh) and c >= dh and
                not np.isnan(tm) and c > tm and
                not np.isnan(vm) and v > vm * vol_ratio and
                bool(bg)  # regime gate (True when filter disabled)
            )
            if entry_ok:
                action[i] = "BUY"
                in_pos = True
                high_since = h

    return pd.DataFrame({"action": action}, index=df.index)
