"""Buy-and-Hold (BNH) metrics for F-tier rescue evaluation.

For F-tier stocks where active timing strategies fail (insufficient signals,
negative expectancy), evaluate whether *pure holding* would have outperformed
0050 over the long-run train+test span (default 2017-2024, 8 years).

Rationale:
    Some defensive / blue-chip stocks (e.g. 2412 中華電 dividend, 1101 台泥)
    are simply not amenable to short-term timing — strategies don't trigger
    enough or whipsaw too much. For these, an honest "buy and hold" answer
    is more useful than a misleading low-confidence trade signal.

Outputs are consumed by ``tiering.assign_bnh_tier()`` and reported in the
final report under section 7 (BNH 候選).

Cost model:
    BNH assumes a single buy now and hold forever (no sell). Slip + commission
    on entry only:  slippage_rate (0.3%) + buy_commission_rate (0.1425%) ≈ 0.4275%
    This is applied as a one-time haircut on the initial price (entry slightly
    above quoted close).
"""
from __future__ import annotations
import os
import math
from typing import Optional

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


# Default span — matches train (2017-2022) + test (2023-2024) used by auto_iterate
BNH_START = "2017-01-01"
BNH_END = "2024-12-31"

# Buy-side cost only (no sell): slip 0.3% + commission 0.1425%
BNH_ENTRY_COST = 0.003 + 0.001425  # 0.004425 (~0.4275%)

TRADING_DAYS_PER_YEAR = 252


def _load_adj_close(stock_id: str) -> Optional[pd.Series]:
    """Load adjusted close prices from data/adjusted/{sid}.csv.

    Returns a date-indexed pd.Series of close_adj, or None if file missing /
    corrupt.
    """
    path = os.path.join(BASE_DIR, "data", "adjusted", f"{stock_id}.csv")
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path, dtype={"date": str})
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").set_index("date")
        if "close_adj" not in df.columns:
            return None
        s = df["close_adj"].astype(float).dropna()
        return s if len(s) else None
    except Exception:
        return None


def compute_bnh_metrics(
    prices: pd.Series,
    start: str = BNH_START,
    end: str = BNH_END,
    entry_cost: float = BNH_ENTRY_COST,
) -> Optional[dict]:
    """Compute BNH CAGR / MaxDD / Sharpe over [start, end].

    Args:
        prices: date-indexed Series of adjusted close.
        start, end: ISO date strings (inclusive).
        entry_cost: fractional cost on entry (default 0.4275%).

    Returns:
        Dict with keys: ``cagr``, ``max_dd`` (negative), ``sharpe`` (annualised),
        ``years``, ``start_date``, ``end_date``, ``n_days``.
        Returns ``None`` if window has < 100 trading days (insufficient data).
    """
    if prices is None or len(prices) == 0:
        return None
    sub = prices.loc[(prices.index >= start) & (prices.index <= end)].dropna()
    if len(sub) < 100:
        return None

    entry_px = sub.iloc[0] * (1.0 + entry_cost)
    exit_px = sub.iloc[-1]

    years = max((sub.index[-1] - sub.index[0]).days / 365.25, 1e-6)
    total_ret = exit_px / entry_px
    if total_ret <= 0:
        cagr = -1.0
    else:
        cagr = total_ret ** (1.0 / years) - 1.0

    # Drawdown from cumulative price path (incl. entry cost effect)
    px_path = sub.copy()
    px_path.iloc[0] = entry_px  # adjust starting point for cost
    rets = px_path.pct_change().fillna(0.0)
    cum = (1.0 + rets).cumprod()
    peak = cum.cummax()
    dd_series = cum / peak - 1.0
    max_dd = float(dd_series.min())

    std = float(rets.std())
    sharpe = float(rets.mean() / std * math.sqrt(TRADING_DAYS_PER_YEAR)) if std > 0 else 0.0

    return {
        "cagr": float(cagr),
        "max_dd": max_dd,
        "sharpe": sharpe,
        "years": float(years),
        "start_date": str(sub.index[0].date()),
        "end_date": str(sub.index[-1].date()),
        "n_days": int(len(sub)),
    }


def compute_bnh_for_stock(
    stock_id: str,
    start: str = BNH_START,
    end: str = BNH_END,
) -> Optional[dict]:
    """Convenience: load + compute. Returns None if data missing."""
    prices = _load_adj_close(stock_id)
    if prices is None:
        return None
    return compute_bnh_metrics(prices, start=start, end=end)


def compute_market_bnh(
    market_proxy: str = "0050",
    start: str = BNH_START,
    end: str = BNH_END,
) -> Optional[dict]:
    """Baseline BNH metrics for the market proxy (default 0050)."""
    return compute_bnh_for_stock(market_proxy, start=start, end=end)


def estimate_dividend_yield(
    stock_id: str,
    start_year: int = 2020,
    end_year: int = 2024,
) -> Optional[float]:
    """Rough trailing 5-year average cash dividend yield estimate.

    Uses ``data/dividends/{sid}.csv`` (FinMind dividend distribution table) to
    sum CashEarningsDistribution per year, average across years, and divide by
    average raw close price over the same span.

    Returns None if dividend file missing or no data in window.
    """
    div_path = os.path.join(BASE_DIR, "data", "dividends", f"{stock_id}.csv")
    px_path = os.path.join(BASE_DIR, "data", "adjusted", f"{stock_id}.csv")
    if not (os.path.exists(div_path) and os.path.exists(px_path)):
        return None
    try:
        d = pd.read_csv(div_path)
    except UnicodeDecodeError:
        d = pd.read_csv(div_path, encoding="utf-8-sig")
    except Exception:
        return None
    if "date" not in d.columns or "CashEarningsDistribution" not in d.columns:
        return None
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"])
    span = d[(d["date"].dt.year >= start_year) & (d["date"].dt.year <= end_year)]
    if len(span) == 0:
        return 0.0
    n_years = max(end_year - start_year + 1, 1)
    cash_per_year = float(span["CashEarningsDistribution"].sum()) / n_years

    try:
        p = pd.read_csv(px_path, dtype={"date": str})
    except Exception:
        return None
    p["date"] = pd.to_datetime(p["date"], format="%Y%m%d", errors="coerce")
    p = p.dropna(subset=["date"])
    pmask = (p["date"].dt.year >= start_year) & (p["date"].dt.year <= end_year)
    avg_px = float(p.loc[pmask, "close"].mean()) if pmask.any() else 0.0
    if avg_px <= 0:
        return None
    return cash_per_year / avg_px
