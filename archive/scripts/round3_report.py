"""
Round 3 回測報告：Takeshi + Katie 組合（含 P0-6/7/8 修正）
用法：python scripts/round3_report.py
"""
import os, sys, math, yaml, pandas as pd
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.signals.regime import detect_regime
from src.strategy.signals.style1_pullback import generate_signals
from src.strategy.eval.portfolio import calc_portfolio_metrics
from src.strategy.portfolio.allocator import make_monthly_portfolio_sizing

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "config", "strategy.yaml"), encoding="utf-8") as f:
    CFG = yaml.safe_load(f)
with open(os.path.join(BASE, "config", "watchlists.yaml"), encoding="utf-8") as f:
    WL = yaml.safe_load(f)


def load_stock(sid):
    path = os.path.join(BASE, "data", "raw", f"{sid}.csv")
    if not os.path.exists(path): return None
    df = pd.read_csv(path, dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values("date").set_index("date")
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns: return None
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def fmt_pct(v):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))): return "N/A"
    return f"{v:.2%}"


# ── 共用資源 ─────────────────────────────────────────────────
df_0050 = load_stock("0050")
if df_0050 is None:
    print("[錯誤] 找不到 data/raw/0050.csv"); sys.exit(1)
regime = detect_regime(df_0050, CFG["regime"]["ma_long"])
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
        df = load_stock(str(sid))
        if df is None or len(df) < 50: continue
        sr = regime.reindex(df.index, method="ffill").fillna("BEAR")
        dfs[str(sid)] = df
        signals_dict[str(sid)] = generate_signals(df, sr, params_s1)
    return dfs, signals_dict


def run_portfolio(name, ids):
    print(f"\n{'='*65}")
    print(f"  [{name}] 組合回測  2017-01-01 ~ today")
    print(f"{'='*65}")

    dfs, signals_dict = build_dfs_signals(ids)
    if not dfs:
        print("  無可用股票資料"); return None

    from src.strategy.runner import _calc_benchmark_cagr
    try:
        bh_cagr = _calc_benchmark_cagr(df_0050, BT_CFG, CFG)
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

    print(f"  初始資金:      {init:>12,.0f}")
    print(f"  最終 equity:   {final:>12,.0f}  ({fmt_pct(total_ret)} total)")
    print(f"  CAGR:          {fmt_pct(pm['cagr'])}")
    print(f"  MaxDD:         {fmt_pct(pm['max_drawdown'])}")
    print(f"  Sharpe:        {pm['sharpe']:.2f}" if not math.isnan(pm['sharpe']) else "  Sharpe:        N/A")
    print(f"  Alpha vs 0050: {fmt_pct(pm['alpha'])}  (0050={fmt_pct(bh_cagr)})")
    print(f"  資金利用率:    {fmt_pct(pm['in_market_pct'])}")

    # Regime 統計
    if len(eq) > 0:
        regime_rng = regime.reindex(eq.index, method="ffill").fillna("BEAR")
        bull_r = (regime_rng == "BULL").mean()
        bear_r = (regime_rng == "BEAR").mean()
        print(f"\n  Regime 統計：BULL {bull_r:.1%} / BEAR {bear_r:.1%}")
        bear_mask = (regime_rng == "BEAR")
        if bear_mask.sum() > 0 and not math.isnan(init) and init > 0:
            bear_eq_ratio = (eq[bear_mask] / init).mean()
            print(f"  BEAR 期間 equity 均值/初始 = {bear_eq_ratio:.2%}"
                  f"（接近 1.0 = 成功清倉；遠高於 1.0 = 熊市仍有獲利持倉）")

    return pm, result


if __name__ == "__main__":
    print("\n" + "="*65)
    print("  Round 3 回測報告（P0-6/7/8 修正後）")
    print(f"  產出日期: {date.today()}")
    print("="*65)
    print(f"\n  0050.csv: {len(df_0050)} 列  "
          f"（{df_0050.index[0].date()} ~ {df_0050.index[-1].date()}）")

    takeshi_ids = [str(s) for s in WL.get("Takeshi", [])]
    katie_ids   = [str(s) for s in WL.get("Katie",   [])]

    tk = run_portfolio("Takeshi", takeshi_ids)
    kt = run_portfolio("Katie",   katie_ids)

    # 對照表
    print(f"\n{'='*65}")
    print(f"  Round 2 vs Round 3 對照（組合模式）")
    print(f"{'='*65}")
    print(f"  {'指標':<12}  {'Takeshi R2':>12}  {'Takeshi R3':>12}  {'Katie R2':>10}  {'Katie R3':>10}")
    print(f"  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*10}")

    def row(label, r2_tk, r3_tk, r2_kt, r3_kt):
        print(f"  {label:<12}  {r2_tk:>12}  {r3_tk:>12}  {r2_kt:>10}  {r3_kt:>10}")

    row("CAGR", "14.44%", fmt_pct(tk[0]['cagr']) if tk else "N/A",
        "-0.62%", fmt_pct(kt[0]['cagr']) if kt else "N/A")
    row("MaxDD", "-41.47%", fmt_pct(tk[0]['max_drawdown']) if tk else "N/A",
        "-63.28%", fmt_pct(kt[0]['max_drawdown']) if kt else "N/A")
    row("Sharpe", "0.54",
        f"{tk[0]['sharpe']:.2f}" if tk and not math.isnan(tk[0]['sharpe']) else "N/A",
        "0.19",
        f"{kt[0]['sharpe']:.2f}" if kt and not math.isnan(kt[0]['sharpe']) else "N/A")
    row("Alpha", "+12.60%", fmt_pct(tk[0]['alpha']) if tk else "N/A",
        "-2.46%", fmt_pct(kt[0]['alpha']) if kt else "N/A")

    print(f"\n{'='*65}")
    print("  報告結束")
    print(f"{'='*65}\n")
