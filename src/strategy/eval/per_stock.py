import numpy as np
import pandas as pd
from src.strategy.backtest.result import StockResult


def calc_per_stock_metrics(result: StockResult, min_trades: int = 10) -> dict:
    """計算單股層指標（SPEC §4.1）"""
    n = result.n_trades
    metrics = {
        "stock_id": result.stock_id,
        "n_trades": n,
        "win_rate": result.win_rate,
        "avg_win_pct": result.avg_win,
        "avg_loss_pct": result.avg_loss,
        "expectancy": result.expectancy,
        "profit_factor": result.profit_factor,
        "in_market_cagr": result.in_market_cagr,
        "max_drawdown": result.max_drawdown,
        "avg_hold_days": result.avg_hold_days,
        "annual_trade_count": result.annual_trade_count,
        "sufficient_trades": n >= min_trades,
    }
    return metrics


def metrics_to_df(results: list, min_trades: int = 10) -> pd.DataFrame:
    """多個 StockResult → per_stock 指標 DataFrame"""
    rows = [calc_per_stock_metrics(r, min_trades) for r in results]
    return pd.DataFrame(rows)
