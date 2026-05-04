import numpy as np
import pandas as pd
from src.strategy.backtest.result import PortfolioResult


def calc_portfolio_metrics(result: PortfolioResult) -> dict:
    """計算組合層指標（SPEC §4.2）"""
    return {
        "cagr": result.cagr,
        "max_drawdown": result.max_drawdown,
        "sharpe": result.sharpe,
        "benchmark_cagr": result.benchmark_cagr,
        "alpha": result.alpha,
        "in_market_pct": result.in_market_pct,
        "in_market_cagr": result.in_market_cagr,  # P0-13
    }
