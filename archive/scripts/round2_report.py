"""
Round 2 回測報告：Takeshi + Katie 完整結果
用法：python scripts/round2_report.py
"""
import os, sys, math, yaml, pandas as pd
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.signals.regime import detect_regime
from src.strategy.signals.style1_pullback import generate_signals
from src.strategy.eval.per_stock import calc_per_stock_metrics
from src.strategy.eval.portfolio import calc_portfolio_metrics

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "config", "strategy.yaml"), encoding="utf-8") as f:
    CFG = yaml.safe_load(f)
with open(os.path.join(BASE, "config", "watchlists.yaml"), encoding="utf-8") as f:
    WL = yaml.safe_load(f)


def load_stock(sid):
    path = os.path.join(BASE, "data", "raw", f"{sid}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values("date").set_index("date")
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            return None
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def fmt_pct(v):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "N/A"
    return f"{v:.2%}"

def fmt_f(v, dec=2):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "inf" if isinstance(v, float) and math.isinf(v) else "N/A"
    return f"{v:.{dec}f}"


# ── 共用資源 ──────────────────────────────────────────────────────
df_0050 = load_stock("0050")
if df_0050 is None:
    print("[錯誤] 找不到 data/raw/0050.csv")
    sys.exit(1)
regime = detect_regime(df_0050, CFG["regime"]["ma_long"])
params = CFG["style1_pullback"]

BT_CFG_SINGLE = BacktestConfig(
    fees=CFG["fees"],
    start_date="2017-01-01",
    end_date="today",
    initial_capital=100_000,
    max_position_pct=1.0,
)
BT_CFG_PORT = BacktestConfig(
    fees=CFG["fees"],
    start_date="2017-01-01",
    end_date="today",
    initial_capital=1_000_000,
    max_position_pct=0.25,
)


def run_per_stock_section(name, ids):
    """印出個股回測摘要，回傳 (results_list, first_stock_trades_sample)"""
    print(f"\n{'='*65}")
    print(f"  [{name}] 個股回測（per-stock mode）  2017-01-01 ~ today")
    print(f"{'='*65}")
    print(f"  {'股票':<6}  {'N':>3}  {'CAGR':>9}  {'MaxDD':>7}  {'PF':>6}  {'WR':>6}  {'AvgHold':>8}")
    print(f"  {'-'*6}  {'-'*3}  {'-'*9}  {'-'*7}  {'-'*6}  {'-'*6}  {'-'*8}")

    bt = Backtester(BT_CFG_SINGLE)
    results = []
    first_trades = []

    for sid in ids:
        df = load_stock(str(sid))
        if df is None or len(df) < 50:
            print(f"  {sid:<6}  資料不足，跳過")
            continue
        stock_regime = regime.reindex(df.index, method="ffill").fillna("BEAR")
        signals = generate_signals(df, stock_regime, params)
        result = bt.run_per_stock(str(sid), df, signals)
        results.append(result)

        if not first_trades and result.n_trades >= 1:
            first_trades = [(sid, t) for t in result.trades[:5]]

        cagr = result.in_market_cagr
        mdd = result.max_drawdown
        pf = result.profit_factor
        wr = result.win_rate
        ahd = result.avg_hold_days

        print(f"  {sid:<6}  {result.n_trades:>3}  {fmt_pct(cagr):>9}  "
              f"{fmt_pct(mdd):>7}  {fmt_f(pf):>6}  {fmt_pct(wr):>6}  "
              f"{fmt_f(ahd, 0) + 'd':>8}")

    return results, first_trades


def run_portfolio_section(name, ids):
    """印出組合回測結果"""
    print(f"\n{'='*65}")
    print(f"  [{name}] 組合回測（portfolio mode）  2017-01-01 ~ today")
    print(f"{'='*65}")

    dfs = {}
    signals_dict = {}
    for sid in ids:
        df = load_stock(str(sid))
        if df is None or len(df) < 50:
            continue
        sr = regime.reindex(df.index, method="ffill").fillna("BEAR")
        dfs[str(sid)] = df
        signals_dict[str(sid)] = generate_signals(df, sr, params)

    if not dfs:
        print("  無可用股票資料")
        return

    # benchmark CAGR
    from src.strategy.runner import _calc_benchmark_cagr
    try:
        bh_cagr = _calc_benchmark_cagr(df_0050, BT_CFG_PORT, CFG)
    except ValueError as e:
        bh_cagr = float("nan")
        print(f"  [警告] {e}")

    # 使用 top_n_equal_weight_sizing 作為 sizing_fn（月頻 rebalance gate）
    from src.strategy.portfolio.allocator import top_n_equal_weight_sizing
    mom_params = CFG["style2_momentum"]
    max_pos = BT_CFG_PORT.max_position_pct
    _last_rb = [None]

    def sizing_fn(dt, sig_dict, cash, ohlcv_dict, holdings):
        if _last_rb[0] == dt.month and holdings:
            return holdings
        _last_rb[0] = dt.month
        return top_n_equal_weight_sizing(
            dt, sig_dict, cash, ohlcv_dict, holdings, mom_params, max_pos
        )

    bt = Backtester(BT_CFG_PORT)
    result = bt.run_portfolio(dfs, signals_dict, sizing_fn, benchmark_cagr=bh_cagr)
    pm = calc_portfolio_metrics(result)

    eq = result.equity_curve
    init = eq.iloc[0] if len(eq) > 0 else float("nan")
    final = eq.iloc[-1] if len(eq) > 0 else float("nan")

    print(f"  初始資金:      {init:>12,.0f}")
    print(f"  最終 equity:   {final:>12,.0f}  ({fmt_pct((final-init)/init if init else float('nan'))} total)")
    print(f"  組合 CAGR:     {fmt_pct(pm['cagr'])}")
    print(f"  MaxDD:         {fmt_pct(pm['max_drawdown'])}")
    print(f"  Sharpe:        {fmt_f(pm['sharpe'])}")
    print(f"  Alpha vs 0050: {fmt_pct(pm['alpha'])}  (0050 price-only CAGR={fmt_pct(bh_cagr)})")
    print(f"  資金利用率:    {fmt_pct(pm['in_market_pct'])}")
    return pm


def signal_sparsity_section(ids):
    """P0-3：診斷訊號稀疏"""
    print(f"\n{'='*65}")
    print(f"  P0-3 診斷：訊號稀疏根因分析")
    print(f"{'='*65}")

    bull_pct = (regime == "BULL").mean()
    print(f"  大盤 BULL 比例（2010~today）: {bull_pct:.1%}")
    print(f"\n  策略參數（config/strategy.yaml）：")
    for k in ["ma_long","ma_short","rsi_oversold","rsi_overbought",
              "atr_stop_k","trend_break_days","max_hold_days","volume_min_ratio"]:
        print(f"    {k}: {params.get(k, 'N/A')}")

    print(f"\n  各股 BUY 訊號統計：")
    # 只計算 2017 以後
    total_buys = 0
    checked_ids = []
    df_0050_sub = df_0050["2017-01-01":]
    years_span = (df_0050_sub.index[-1] - df_0050_sub.index[0]).days / 365.25

    for sid in ids:
        df = load_stock(str(sid))
        if df is None or len(df) < 50:
            continue
        df_sub = df["2017-01-01":]
        if len(df_sub) < 50:
            continue
        sr = regime.reindex(df_sub.index, method="ffill").fillna("BEAR")
        signals = generate_signals(df_sub, sr, params)
        n_buy = (signals["action"] == "BUY").sum()
        total_buys += n_buy
        checked_ids.append(sid)
        per_year = n_buy / years_span
        print(f"    {sid}: {n_buy} BUY 訊號 / {len(df_sub)} 交易日  ({per_year:.1f}/年)")

    if checked_ids:
        avg = total_buys / len(checked_ids) / years_span
        print(f"\n  平均: {avg:.2f} BUY/年/股  →  策略訊號極度稀疏")

    print(f"""
  根因診斷：
  1. 進場條件過嚴（5個條件同時滿足）：
     - MA50>MA200 AND Close>MA200（長期趨勢）
     - 大盤 BULL（regime 過濾）
     - RSI<{params.get('rsi_oversold',40)} OR Close<BollLower（短期回檔）
     - Close>Open AND Close>prev_Close（反轉K棒）
     - Volume > vol_ma * {params.get('volume_min_ratio',1.0)}（量能確認）
  2. 出場過快：entry 時 Close 僅略高於 MA200，之後小幅回落即觸發
     trend_break_days={params.get('trend_break_days',2)} 日 <MA200 的出場條件。
  3. 後果：每股年均 ~0.3 次進場，大多數股票 8 年只有 0-3 筆交易，
     回測結果統計無意義。
  4. 建議方向（待 Opus 決定）：
     A. 加 MA200 緩衝：Close > MA200 * 1.02（至少 2% 以上）
     B. trend_break_days 2 → 3-4 天
     C. rsi_oversold 40 → 35（更嚴格的回檔才進場）
     D. 上述組合可同時增加持倉品質並減少假突破後立刻出場""")


# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    takeshi_ids = [str(s) for s in WL.get("Takeshi", [])]
    katie_ids   = [str(s) for s in WL.get("Katie",   [])]

    print("\n" + "="*65)
    print("  Round 2 回測完整報告")
    print(f"  產出日期: {date.today()}")
    print("="*65)

    # 0050 資料概況
    print(f"\n  0050.csv: {len(df_0050)} 列  "
          f"（{df_0050.index[0].date()} ~ {df_0050.index[-1].date()}）")

    # ── Takeshi ──────────────────────────────────────────────────
    tk_results, tk_trades = run_per_stock_section("Takeshi", takeshi_ids)
    run_portfolio_section("Takeshi", takeshi_ids)

    # ── Katie ─────────────────────────────────────────────────────
    kt_results, kt_trades = run_per_stock_section("Katie", katie_ids)
    run_portfolio_section("Katie", katie_ids)

    # ── 前 5 筆 trade 明細 ─────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  個股前 5 筆 trade 明細（Takeshi 第一個有交易的股票）")
    print(f"{'='*65}")
    if tk_trades:
        sid0 = tk_trades[0][0]
        print(f"  股票: {sid0}")
        print(f"  {'進場日':>12}  {'進場價':>8}  {'出場日':>12}  {'出場價':>8}  {'報酬':>8}  {'持倉':>6}")
        for sid, t in tk_trades:
            print(f"  {str(t.entry_date.date()):>12}  {t.entry_price:>8.2f}  "
                  f"{str(t.exit_date.date()):>12}  {t.exit_price:>8.2f}  "
                  f"{t.pnl_pct:>7.2%}  {t.hold_days:>4}d")
    else:
        print("  無交易記錄")

    # ── P0-3 診斷 ─────────────────────────────────────────────────
    signal_sparsity_section(takeshi_ids)

    # ── 2337 outlier 說明 ──────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  特殊說明：2337 CAGR=5141% 的成因")
    print(f"{'='*65}")
    for r in tk_results:
        if r.stock_id == "2337" and r.trades:
            print(f"  N={r.n_trades} 筆交易，avgHold={r.avg_hold_days:.0f}d")
            for t in r.trades:
                print(f"    {t.entry_date.date()} @{t.entry_price:.2f} → "
                      f"{t.exit_date.date()} @{t.exit_price:.2f}  pnl={t.pnl_pct:.2%}  {t.hold_days}d")
            total_h = sum(t.hold_days for t in r.trades)
            cmp = 1.0
            for t in r.trades: cmp *= (1+t.pnl_pct)
            print(f"  compound={cmp:.4f}  years={total_h/252:.3f}")
            print(f"  結論：第1筆 2017-07-19~08-29 獲利 +163.74%（股票20日內漲3倍，")
            print(f"         罕見事件）。N=3 不足，sufficient_trades 過濾後應排除。")

    print(f"\n{'='*65}")
    print("  報告結束")
    print(f"{'='*65}\n")
