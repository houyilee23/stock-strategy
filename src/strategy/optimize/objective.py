"""Optuna objective function：一組 params → 績效分數。"""
import copy
import numpy as np
import pandas as pd

from src.strategy.optimize.search_space import sample_params, SEARCH_SPACE
from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.signals.style1_pullback import generate_signals


def _make_bt_cfg(fees: dict, start_date: str, end_date: str,
                 initial_capital: float = 100_000) -> BacktestConfig:
    return BacktestConfig(
        fees=fees,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        max_position_pct=1.0,   # 單股模式：全倉（只看相對績效）
        execution_lag_days=1,
    )


def run_backtests_for_params(
    params: dict,
    universe_data: dict,       # {sid: df_adj (全期)}
    regime: pd.Series,         # 全期 regime
    bt_cfg: BacktestConfig,
) -> pd.DataFrame:
    """給定一組 params，對全 universe 跑回測，回傳 per-stock 績效 DataFrame。"""
    from src.utils import log_error
    rows = []
    for sid, df_adj in universe_data.items():
        try:
            stock_regime = regime.reindex(df_adj.index, method="ffill").fillna("BEAR")
            signals = generate_signals(df_adj, stock_regime, params)
            bt = Backtester(bt_cfg)
            result = bt.run_per_stock(sid, df_adj, signals)
            rows.append({
                "stock_id":     sid,
                "n_trades":     result.n_trades,
                "profit_factor": result.profit_factor,
                "max_drawdown": result.max_drawdown,
                "win_rate":     result.win_rate,
            })
        except Exception as e:
            log_error("optimize", sid, str(e))
            rows.append({
                "stock_id": sid, "n_trades": 0,
                "profit_factor": np.nan, "max_drawdown": np.nan, "win_rate": np.nan,
            })
    return pd.DataFrame(rows)


def score_results(df: pd.DataFrame, universe_size: int,
                  min_trades: int = 3, min_active_ratio: float = 0.3) -> float:
    """計算績效分數（最大化目標）。"""
    if df.empty:
        return -10.0

    n_active = (df["n_trades"] >= min_trades).sum()
    if n_active < universe_size * min_active_ratio:
        return -10.0

    active_mask = df["n_trades"] >= min_trades
    pf_vals = (
        df.loc[active_mask, "profit_factor"]
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    if len(pf_vals) == 0:
        return -10.0

    median_pf = float(pf_vals.median())
    median_dd = float(df["max_drawdown"].abs().median())

    dd_penalty = max(0.0, median_dd - 0.30) * 5.0
    return median_pf - dd_penalty


def make_objective(
    universe_data: dict,
    regime: pd.Series,
    bt_cfg: BacktestConfig,
    min_trades: int = 3,
    min_active_ratio: float = 0.3,
):
    """建立 optuna objective 的 closure。"""
    universe_size = len(universe_data)

    def objective(trial):
        params = sample_params(trial, SEARCH_SPACE)
        df_results = run_backtests_for_params(params, universe_data, regime, bt_cfg)
        return score_results(df_results, universe_size, min_trades, min_active_ratio)

    return objective
