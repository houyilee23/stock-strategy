"""
Round 4 回測報告：Takeshi + Katie 組合（P0-12 還原股價版）
對照 Round 3 raw 數據，驗證 adj_close 改善情況。
用法：python scripts/round4_report.py
"""
import os, sys, math, yaml, pandas as pd
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.signals.regime import detect_regime
from src.strategy.signals.style1_pullback import generate_signals
from src.strategy.eval.portfolio import calc_portfolio_metrics
from src.strategy.portfolio.allocator import make_monthly_portfolio_sizing
from src.strategy.runner import _load_adj_ohlcv, _load_ohlcv, _calc_benchmark_cagr

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "config", "strategy.yaml"), encoding="utf-8") as f:
    CFG = yaml.safe_load(f)
with open(os.path.join(BASE, "config", "watchlists.yaml"), encoding="utf-8") as f:
    WL = yaml.safe_load(f)


def fmt_pct(v):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "N/A"
    return f"{v:.2%}"


def fmt_f(v, fmt=".2f"):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "N/A"
    return format(v, fmt)


# ── 共用資源（改用 adjusted 0050）────────────────────────────
df_0050_adj = _load_adj_ohlcv("0050")
if df_0050_adj is None:
    print("[錯誤] 找不到 data/adjusted/0050.csv，請先執行 fetch-adjusted")
    sys.exit(1)

regime = detect_regime(df_0050_adj, CFG["regime"]["ma_long"])
params_s1 = CFG["style1_pullback"]
mom_params = CFG["style2_momentum"]

BT_CFG = BacktestConfig(
    fees=CFG["fees"],
    start_date="2017-01-01",
    end_date="today",
    initial_capital=1_000_000,
    max_position_pct=0.25,
)


def build_dfs_signals(ids):
    dfs, signals_dict = {}, {}
    for sid in ids:
        # P0-12: 訊號用 adj_close（無除權息跳空），引擎用 raw（真實成交價 / P&L）
        df_adj = _load_adj_ohlcv(str(sid))
        df_raw = _load_ohlcv(str(sid))
        if df_adj is None or len(df_adj) < 50:
            continue
        if df_raw is None or len(df_raw) < 50:
            df_raw = df_adj  # fallback
        df_raw = df_raw.reindex(df_adj.index)
        sr = regime.reindex(df_adj.index, method="ffill").fillna("BEAR")
        dfs[str(sid)] = df_raw
        signals_dict[str(sid)] = generate_signals(df_adj, sr, params_s1)
    return dfs, signals_dict


def run_portfolio(name, ids):
    print(f"\n{'='*65}")
    print(f"  [{name}] 組合回測  2017-01-01 ~ today  (adj_close)")
    print(f"{'='*65}")

    dfs, signals_dict = build_dfs_signals(ids)
    if not dfs:
        print("  無可用股票資料（adjusted）")
        return None

    try:
        bh_cagr = _calc_benchmark_cagr(df_0050_adj, BT_CFG, CFG)
    except ValueError as e:
        bh_cagr = float("nan")
        print(f"  [警告] {e}")

    sizing_fn = make_monthly_portfolio_sizing(regime, mom_params, 0.25)
    bt = Backtester(BT_CFG)
    result = bt.run_portfolio(dfs, signals_dict, sizing_fn, benchmark_cagr=bh_cagr)
    pm = calc_portfolio_metrics(result)

    eq = result.equity_curve
    init = eq.iloc[0] if len(eq) > 0 else float("nan")
    final = eq.iloc[-1] if len(eq) > 0 else float("nan")
    total_ret = (final - init) / init if init else float("nan")

    print(f"  初始資金:         {init:>12,.0f}")
    print(f"  最終 equity:      {final:>12,.0f}  ({fmt_pct(total_ret)} total)")
    print(f"  CAGR:             {fmt_pct(pm['cagr'])}")
    print(f"  MaxDD:            {fmt_pct(pm['max_drawdown'])}")
    sharpe_v = pm['sharpe']
    print(f"  Sharpe:           {fmt_f(sharpe_v)}" if not math.isnan(sharpe_v) else "  Sharpe:           N/A")
    print(f"  Alpha vs 0050:    {fmt_pct(pm['alpha'])}  (0050 adj={fmt_pct(bh_cagr)})")
    print(f"  資金利用率:       {fmt_pct(pm['in_market_pct'])}")
    imc = pm.get('in_market_cagr', float('nan'))
    print(f"  In-Market CAGR:   {fmt_pct(imc)}  ← 有持倉日年化（排除現金稀釋）")

    # Regime 統計
    if len(eq) > 0:
        regime_rng = regime.reindex(eq.index, method="ffill").fillna("BEAR")
        bull_r = (regime_rng == "BULL").mean()
        bear_r = (regime_rng == "BEAR").mean()
        print(f"\n  Regime：BULL {bull_r:.1%} / BEAR {bear_r:.1%}")
        bear_mask = (regime_rng == "BEAR")
        if bear_mask.sum() > 0 and not math.isnan(init) and init > 0:
            bear_eq_ratio = (eq[bear_mask] / init).mean()
            print(f"  BEAR 期間 equity 均值/初始 = {bear_eq_ratio:.2%}")

    return pm, result, bh_cagr


if __name__ == "__main__":
    print("\n" + "="*65)
    print("  Round 4 回測報告（P0-12 adj_close 版）")
    print(f"  產出日期: {date.today()}")
    print("="*65)
    print(f"\n  0050 adj: {len(df_0050_adj)} 列  "
          f"（{df_0050_adj.index[0].date()} ~ {df_0050_adj.index[-1].date()}）")

    takeshi_ids = [str(s) for s in WL.get("Takeshi", [])]
    katie_ids   = [str(s) for s in WL.get("Katie",   [])]

    tk = run_portfolio("Takeshi", takeshi_ids)
    kt = run_portfolio("Katie",   katie_ids)

    # Round 3 vs Round 4 對照表
    print(f"\n{'='*72}")
    print(f"  Round 3 (raw) vs Round 4 (adj) 對照")
    print(f"{'='*72}")
    print(f"  {'指標':<16}  {'Takeshi R3':>12}  {'Takeshi R4':>12}  {'Katie R3':>10}  {'Katie R4':>10}")
    print(f"  {'-'*16}  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*10}")

    def row(label, r3_tk, r4_tk, r3_kt, r4_kt):
        print(f"  {label:<16}  {r3_tk:>12}  {r4_tk:>12}  {r3_kt:>10}  {r4_kt:>10}")

    tk4_pm = tk[0] if tk else None
    kt4_pm = kt[0] if kt else None
    tk4_bh = tk[2] if tk else float("nan")

    row("CAGR",
        "2.03%",   fmt_pct(tk4_pm['cagr'])         if tk4_pm else "N/A",
        "6.77%",   fmt_pct(kt4_pm['cagr'])          if kt4_pm else "N/A")
    row("MaxDD",
        "-44.04%", fmt_pct(tk4_pm['max_drawdown'])  if tk4_pm else "N/A",
        "-31.35%", fmt_pct(kt4_pm['max_drawdown'])  if kt4_pm else "N/A")
    row("Sharpe",
        "0.20",    fmt_f(tk4_pm['sharpe'])           if tk4_pm else "N/A",
        "0.58",    fmt_f(kt4_pm['sharpe'])           if kt4_pm else "N/A")
    row("Alpha",
        "+0.19%",  fmt_pct(tk4_pm['alpha'])          if tk4_pm else "N/A",
        "+4.93%",  fmt_pct(kt4_pm['alpha'])          if kt4_pm else "N/A")
    row("0050 Baseline",
        "1.84%",   fmt_pct(tk4_bh),
        "1.84%",   fmt_pct(tk4_bh))
    row("資金利用率",
        "25.51%",  fmt_pct(tk4_pm['in_market_pct']) if tk4_pm else "N/A",
        "40.07%",  fmt_pct(kt4_pm['in_market_pct']) if kt4_pm else "N/A")
    row("In-Market CAGR",
        "N/A",     fmt_pct(tk4_pm.get('in_market_cagr', float('nan'))) if tk4_pm else "N/A",
        "N/A",     fmt_pct(kt4_pm.get('in_market_cagr', float('nan'))) if kt4_pm else "N/A")

    print(f"\n{'='*72}")
    print("  報告結束")
    print(f"{'='*72}\n")
