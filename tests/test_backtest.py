# Phase 3 回測引擎測試
# 跑法：python.exe -m pytest tests/test_backtest.py -v
import sys
import os
import math
import numpy as np
import pandas as pd
import pytest
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.backtest.fees import calc_buy_cost, calc_sell_proceeds
from src.strategy.backtest.result import StockResult, PortfolioResult
from src.strategy.signals.regime import detect_regime
from src.strategy.signals.style1_pullback import generate_signals
from src.strategy.eval.per_stock import calc_per_stock_metrics, metrics_to_df
from src.strategy.eval.portfolio import calc_portfolio_metrics

_cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "strategy.yaml")
with open(_cfg_path, encoding="utf-8") as f:
    _STRATEGY = yaml.safe_load(f)

FEES = _STRATEGY["fees"]
BT_CFG = BacktestConfig(
    fees=FEES,
    start_date="2015-01-01",
    end_date="2025-12-31",
    initial_capital=100_000,
    max_position_pct=0.25,
)


def make_ohlcv(n: int = 600, drift: float = 0.0003, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ret = rng.normal(drift, 0.012, n)
    close = 100.0 * np.cumprod(1 + ret)
    high = close * (1 + rng.uniform(0.002, 0.015, n))
    low = close * (1 - rng.uniform(0.002, 0.015, n))
    open_ = close * (1 + rng.normal(0, 0.005, n))
    volume = rng.integers(500_000, 5_000_000, n).astype(float)
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


def make_all_hold_signals(n: int = 600) -> pd.DataFrame:
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.DataFrame({"action": ["HOLD"] * n}, index=idx)


# ── 手續費正確性 ──────────────────────────────────────────────

def test_fee_formula_buy():
    """買入手續費公式驗證"""
    price, shares = 100.0, 1000
    cost = calc_buy_cost(price, shares, FEES)
    slip = FEES["slippage_rate"]
    comm_rate = FEES["buy_commission_rate"]
    min_comm = FEES["min_commission"]
    exec_price = price * (1 + slip)
    amount = exec_price * shares
    commission = max(min_comm, amount * comm_rate)
    expected = amount + commission
    assert abs(cost - expected) < 1e-6


def test_fee_formula_sell():
    """賣出手續費 + 證交稅公式驗證"""
    price, shares = 100.0, 1000
    proceeds = calc_sell_proceeds(price, shares, FEES)
    slip = FEES["slippage_rate"]
    comm_rate = FEES["sell_commission_rate"]
    tax_rate = FEES["sell_tax_rate"]
    min_comm = FEES["min_commission"]
    exec_price = price * (1 - slip)
    amount = exec_price * shares
    commission = max(min_comm, amount * comm_rate)
    tax = amount * tax_rate
    expected = amount - commission - tax
    assert abs(proceeds - expected) < 1e-6


def test_fee_min_commission():
    """極小交易應套用最低手續費"""
    price, shares = 10.0, 1  # NT$10，手續費 < NT$20
    cost = calc_buy_cost(price, shares, FEES)
    exec_price = price * (1 + FEES["slippage_rate"])
    amount = exec_price * shares
    assert cost == pytest.approx(amount + FEES["min_commission"])


# ── 1. 零訊號測試 ─────────────────────────────────────────────

def test_all_hold_equity_flat():
    """全 HOLD 訊號 → equity curve 應為平線（初始資金不變）"""
    df = make_ohlcv(300)
    signals = make_all_hold_signals(300)
    bt = Backtester(BT_CFG)
    result = bt.run_per_stock("TEST", df, signals)
    eq = result.equity_curve
    assert len(eq) > 0, "equity_curve 為空"
    assert eq.iloc[0] == pytest.approx(BT_CFG.initial_capital)
    assert (eq == eq.iloc[0]).all(), "全 HOLD 時 equity 不應變動"


# ── 2. Buy-and-hold 測試 ──────────────────────────────────────

def test_buy_hold_cagr_positive():
    """上漲趨勢 buy-and-hold CAGR 應為正。
    T+1 成交：BUY 在 day 0，SELL 在 day n-2（day n-1 開盤成交）。
    """
    df = make_ohlcv(2520, drift=0.0004, seed=1)
    actions = ["HOLD"] * len(df)
    actions[0] = "BUY"
    actions[-2] = "SELL"  # 倒數第二日發訊，倒數第一日開盤成交
    signals = pd.DataFrame({"action": actions}, index=df.index)
    bt = Backtester(BT_CFG)
    result = bt.run_per_stock("BH", df, signals)
    assert result.n_trades == 1, f"期望 1 筆交易，實際 {result.n_trades}"
    pnl_pct = result.trades[0].pnl_pct
    assert pnl_pct > 0, f"上漲趨勢 buy-and-hold 應獲利，實際 {pnl_pct:.1%}"


def test_buy_hold_reasonable_cagr():
    """長期輕度上漲（drift=0.0003/日），10年 CAGR 應在合理範圍"""
    n = 2520
    df = make_ohlcv(n, drift=0.0003, seed=5)
    actions = ["HOLD"] * n
    actions[0] = "BUY"
    actions[-2] = "SELL"
    signals = pd.DataFrame({"action": actions}, index=df.index)
    bt = Backtester(BT_CFG)
    result = bt.run_per_stock("BH", df, signals)
    assert result.n_trades == 1, f"期望 1 筆交易，實際 {result.n_trades}"
    pnl_pct = result.trades[0].pnl_pct
    hold_d = result.trades[0].hold_days
    cagr = (1 + pnl_pct) ** (252 / max(hold_d, 1)) - 1
    assert 0.03 < cagr < 0.35, f"buy-and-hold CAGR {cagr:.1%} 超出合理範圍"


# ── 3. 時間防穿越測試 ────────────────────────────────────────

def test_no_lookahead():
    """在訊號最後一日之後插入未來漲跌，結果不應改變"""
    df = make_ohlcv(300, drift=0.0003, seed=7)
    regime = detect_regime(df)
    signals = generate_signals(df, regime, _STRATEGY["style1_pullback"])

    bt = Backtester(BT_CFG)
    result1 = bt.run_per_stock("LA", df, signals)

    # 在最後 50 日 close 改為 999999（不影響訊號，只影響 equity 估值，但不影響已實現交易）
    df2 = df.copy()
    df2.loc[df2.index[-50:], "close"] = 999999.0
    result2 = bt.run_per_stock("LA2", df2, signals)

    # 已實現交易的 pnl 應相同（因為交易都在訊號決定時點，成交用 open 價）
    pnl1 = sum(t.pnl for t in result1.trades)
    pnl2 = sum(t.pnl for t in result2.trades)
    assert abs(pnl1 - pnl2) < 1e-3, f"修改未來價格影響了已實現交易 pnl：{pnl1:.2f} vs {pnl2:.2f}"


# ── 4. 組合回測測試 ──────────────────────────────────────────

def test_portfolio_no_nan_equity():
    """組合回測 equity curve 不應含 NaN"""
    n = 600
    dfs = {str(i): make_ohlcv(n, seed=i) for i in range(3)}
    regimes = {sid: detect_regime(df) for sid, df in dfs.items()}
    signals_dict = {
        sid: generate_signals(dfs[sid], regimes[sid], _STRATEGY["style1_pullback"])
        for sid in dfs
    }

    def dummy_sizing(date, signals_dict, cash, ohlcv_dict, holdings):
        return {}

    bt = Backtester(BT_CFG)
    result = bt.run_portfolio(dfs, signals_dict, dummy_sizing)
    assert not result.equity_curve.isna().any(), "組合 equity curve 含 NaN"


def test_portfolio_csv_output():
    """對 Takeshi watchlist 跑組合回測，CSV 應產出"""
    import yaml
    wl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "config", "watchlists.yaml")
    with open(wl_path, encoding="utf-8") as f:
        wl = yaml.safe_load(f)
    takeshi_ids = [str(s) for s in wl.get("Takeshi", [])]

    n = 600
    dfs = {sid: make_ohlcv(n, seed=hash(sid) % 100) for sid in takeshi_ids}
    regimes = {sid: detect_regime(df) for sid, df in dfs.items()}
    signals_dict = {
        sid: generate_signals(dfs[sid], regimes[sid], _STRATEGY["style1_pullback"])
        for sid in dfs
    }

    def dummy_sizing(date, signals_dict, cash, ohlcv_dict, holdings):
        return {}

    bt = Backtester(BT_CFG)
    result = bt.run_portfolio(dfs, signals_dict, dummy_sizing)

    from src.strategy.eval.reporter import save_portfolio_csv
    run_id = "portfolio_phase3_check"
    path = save_portfolio_csv(result, run_id)
    assert os.path.exists(path), f"portfolio CSV 未產出：{path}"

    out_dir = os.path.dirname(path)
    equity_path = os.path.join(out_dir, f"equity_{run_id}.csv")
    assert os.path.exists(equity_path), "equity curve CSV 未產出"


# ── 5. 指標計算測試 ──────────────────────────────────────────

def test_profit_factor_inf_when_no_loss():
    """無虧損交易時 profit_factor 應為 inf"""
    from src.strategy.backtest.result import TradeRecord
    sr = StockResult(stock_id="X")
    sr.trades = [
        TradeRecord("X", pd.Timestamp("2020-01-01"), pd.Timestamp("2020-02-01"),
                    100.0, 110.0, 100, 1000.0, 0.1, 20),
    ]
    assert math.isinf(sr.profit_factor)


def test_per_stock_metrics_sufficient():
    """sufficient_trades 依 min_trades 正確計算"""
    df = make_ohlcv(2520, drift=0.0003, seed=3)
    regime = detect_regime(df)
    signals = generate_signals(df, regime, _STRATEGY["style1_pullback"])
    bt = Backtester(BT_CFG)
    result = bt.run_per_stock("M", df, signals)
    metrics = calc_per_stock_metrics(result, min_trades=10)
    assert "sufficient_trades" in metrics
    assert metrics["sufficient_trades"] == (result.n_trades >= 10)
