"""Single-stock backtest wrapper: generates signals → runs engine → returns metrics dict.

v3: objective = expectancy*10 + pf*0.2 - dd_penalty  (regime-independent)
    verdict   = expectancy >= 5% AND pf >= 1.5 AND dd <= 30% AND n >= 5
"""
import os
import yaml
import numpy as np
import pandas as pd
from datetime import date as _date

from src.strategy.backtest.engine import Backtester
from src.strategy.auto_iterate.templates import TEMPLATE_GENERATORS


_SCALING_CFG_CACHE = None


def _load_scaling_cfg() -> dict:
    """從 config/strategy.yaml 載入 scaling 區塊（caching 避免重複 IO）。

    若 yaml 不存在或無 scaling 區塊，回傳 {"enabled": False} 走原邏輯。
    """
    global _SCALING_CFG_CACHE
    if _SCALING_CFG_CACHE is not None:
        return _SCALING_CFG_CACHE
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
    cfg_path = os.path.join(base_dir, "config", "strategy.yaml")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        _SCALING_CFG_CACHE = cfg.get("scaling", {"enabled": False})
    except Exception:
        _SCALING_CFG_CACHE = {"enabled": False}
    return _SCALING_CFG_CACHE


def backtest_one(
    sid: str,
    df: pd.DataFrame,
    template_name: str,
    params: dict,
    bt_cfg,
    regime=None,
    chip_data=None,
    revenue_data=None,
) -> dict:
    """Run one (stock, template, params) backtest on the date range from bt_cfg.

    Returns dict with keys:
      n_trades, profit_factor, max_drawdown, win_rate,
      expectancy, avg_win, avg_loss,
      cagr, bnh_cagr

    revenue_data: 月營收 DataFrame（僅 monthly_revenue_event 模板需要）。
    為相容性，只在模板的 generator 簽章接受 revenue_data 時才傳。
    """
    gen_fn  = TEMPLATE_GENERATORS[template_name]
    # 動態判斷 generator 是否接受 revenue_data 參數（向下相容舊模板）
    import inspect
    try:
        sig_params = inspect.signature(gen_fn).parameters
        accepts_revenue = "revenue_data" in sig_params
    except (TypeError, ValueError):
        accepts_revenue = False

    if accepts_revenue:
        signals = gen_fn(df, params, regime=regime,
                         chip_data=chip_data, revenue_data=revenue_data)
    else:
        signals = gen_fn(df, params, regime=regime, chip_data=chip_data)

    # P0：把 scaling 設定傳給 Backtester；預設 enabled=false 走原邏輯
    scaling_cfg = _load_scaling_cfg()
    bt     = Backtester(bt_cfg, scaling_cfg=scaling_cfg)
    result = bt.run_per_stock(sid, df, signals)

    # CAGR from equity curve
    eq = result.equity_curve
    if len(eq) >= 2 and eq.iloc[0] > 0:
        years = (eq.index[-1] - eq.index[0]).days / 365
        cagr  = (eq.iloc[-1] / eq.iloc[0]) ** (1 / max(years, 0.5)) - 1 if years > 0 else float("nan")
    else:
        cagr = float("nan")

    # B&H CAGR over the same window as bt_cfg
    end_str  = (bt_cfg.end_date if bt_cfg.end_date != "today"
                else _date.today().strftime("%Y-%m-%d"))
    start_ts = pd.Timestamp(bt_cfg.start_date)
    end_ts   = pd.Timestamp(end_str)
    bnh_s    = df[(df.index >= start_ts) & (df.index <= end_ts)]["close"].dropna()
    if len(bnh_s) >= 2 and bnh_s.iloc[0] > 0:
        bnh_yrs  = (bnh_s.index[-1] - bnh_s.index[0]).days / 365
        bnh_cagr = (bnh_s.iloc[-1] / bnh_s.iloc[0]) ** (1 / max(bnh_yrs, 0.5)) - 1 \
                   if bnh_yrs > 0 else float("nan")
    else:
        bnh_cagr = float("nan")

    # expectancy / avg_win / avg_loss from StockResult properties
    expectancy = result.expectancy  # may be nan
    avg_win    = result.avg_win     # 0.0 if no wins
    avg_loss   = result.avg_loss    # 0.0 if no losses

    # P1：多回傳 trades_pnl_pct 列表，供 bootstrap 直接使用（避免重跑 backtest）
    trades_pnl_pct = [float(t.pnl_pct) for t in result.trades
                      if t.pnl_pct is not None]

    return {
        "n_trades":       result.n_trades,
        "profit_factor":  result.profit_factor,   # may be inf
        "max_drawdown":   result.max_drawdown,
        "win_rate":       result.win_rate,
        "expectancy":     expectancy,
        "avg_win":        avg_win,
        "avg_loss":       avg_loss,
        "cagr":           cagr,
        "bnh_cagr":       bnh_cagr,
        "trades_pnl_pct": trades_pnl_pct,
    }


def score_single(metrics: dict) -> float:
    """v3 per-stock optuna objective score (maximise).

    score = expectancy * 10 + pf * 0.2 - dd_penalty
    Completely regime-independent: no benchmark comparison.
    """
    if metrics.get("n_trades", 0) < 5:
        return -10.0

    pf = metrics.get("profit_factor", 0.0)
    if pf is None or (isinstance(pf, float) and np.isnan(pf)):
        return -5.0
    if isinstance(pf, float) and (np.isinf(pf) or pf > 5.0):
        pf = 5.0    # cap to prevent small-sample PF inflation
    if pf <= 0:
        return -5.0

    expectancy = metrics.get("expectancy", 0.0)
    if expectancy is None or (isinstance(expectancy, float) and np.isnan(expectancy)):
        expectancy = 0.0

    dd    = metrics.get("max_drawdown", float("nan"))
    dd_ab = abs(dd) if not (isinstance(dd, float) and np.isnan(dd)) else 0.0
    dd_penalty = max(0.0, dd_ab - 0.30) * 5.0

    return expectancy * 10 + pf * 0.2 - dd_penalty


def classify(test_metrics: dict) -> str:
    """v3 verdict: based purely on per-trade quality (regime-independent).

    PASS               : expectancy >= 5% AND pf >= 1.5 AND dd <= 30% AND n >= 5
    WEAK               : pf >= 1.0 AND expectancy >= 1% AND dd <= 30% AND n >= 5
    DD_BREACH          : dd > 30%
    FAIL               : pf < 1.0 OR expectancy < 1%
    INSUFFICIENT       : n < 5
    SUSPICIOUS_PERFECT : n >= 5 AND (avg_loss == 0 OR pf is inf OR pf > 10.0) — 零虧損或極端 PF，小樣本伪 PASS
    """
    n          = test_metrics.get("n_trades", 0)
    pf         = test_metrics.get("profit_factor", 0.0)
    expectancy = test_metrics.get("expectancy", 0.0)
    dd         = abs(test_metrics.get("max_drawdown", 0.0))
    avg_loss   = test_metrics.get("avg_loss", 0.0)

    if n < 5:
        return "INSUFFICIENT"
    if dd > 0.30:
        return "DD_BREACH"

    # Check expectancy first (independent of PF)
    if expectancy is None or (isinstance(expectancy, float) and np.isnan(expectancy)) \
            or expectancy < 0.01:
        return "FAIL"

    # Detect suspiciously perfect results BEFORE PF null check:
    # avg_loss==0 means no losing trades; pf may be serialised as None when originally inf
    if avg_loss == 0 or (isinstance(pf, float) and (np.isinf(pf) or pf > 10.0)):
        return "SUSPICIOUS_PERFECT"

    if pf is None or (isinstance(pf, float) and np.isnan(pf)) or pf < 1.0:
        return "FAIL"

    if expectancy >= 0.05 and pf >= 1.5:
        return "PASS"
    return "WEAK"
