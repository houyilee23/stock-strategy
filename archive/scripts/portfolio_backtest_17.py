"""Portfolio backtest of the 17 tradeable stocks (2017-01-01 → 2026-04-22).

Inputs:
  - config/per_stock_recommendations.yaml (filter tradeable: true)
  - output/auto_iterate/20260424_220634/<template>.yaml (per_stock.<sid>.best_params)

Workflow:
  1. For each tradeable stock, load OHLCV (adjusted) and run signal generator
     (templates.TEMPLATE_GENERATORS[template]) with optimized params.
  2. Pre-compute per-day per-stock entry/exit decisions (BUY=enter, SELL=exit).
  3. Walk a single portfolio timeline:
       - On each date, T-1 BUY signals turn into T-open buys (subject to
         position_pct_max × current equity, and available cash).
       - T-1 SELL signals turn into T-open sells.
  4. Cost model from config/strategy.yaml (slippage 0.3% × 2 + commission
     0.001425 × 2 + sell tax 0.003 → ~1.185% round-trip). Reuses
     src.strategy.backtest.fees helpers.
  5. Compute portfolio CAGR / MaxDD / Sharpe / total_return / n_trades / win_rate.
  6. Compare to 0050 buy-and-hold over the same window.

Outputs:
  - docs/PORTFOLIO_BACKTEST_17.md
  - output/portfolio_backtest_17.csv (date, equity, drawdown)
  - output/errors/portfolio_backtest_{date}.csv (skipped/errored stocks)
"""
import os
import sys
import math
import yaml
import numpy as np
import pandas as pd
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.strategy.runner import _load_adj_ohlcv  # noqa
from src.strategy.signals.regime import detect_regime  # noqa
from src.strategy.auto_iterate.templates import TEMPLATE_GENERATORS  # noqa
from src.strategy.auto_iterate.chip_fetcher import fetch_chip_data  # noqa
from src.strategy.backtest.fees import calc_buy_cost, calc_sell_proceeds  # noqa
from src.utils import log_error  # noqa


REC_PATH    = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")
RUN_DIR     = os.path.join(BASE_DIR, "output", "auto_iterate", "20260424_220634")
CFG_PATH    = os.path.join(BASE_DIR, "config", "strategy.yaml")
OUT_CSV     = os.path.join(BASE_DIR, "output", "portfolio_backtest_17.csv")
OUT_MD      = os.path.join(BASE_DIR, "docs", "PORTFOLIO_BACKTEST_17.md")

START_DATE = "2017-01-01"
END_DATE   = "2026-04-22"
INITIAL_CAPITAL = 10_000_000


def _load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_template_params(template: str, sid: str) -> dict:
    path = os.path.join(RUN_DIR, f"{template}.yaml")
    doc  = _load_yaml(path)
    per_stock = doc.get("per_stock", {}) or {}
    return per_stock.get(sid, {}).get("best_params", {})


def _build_signals(sid: str, template: str, params: dict, df: pd.DataFrame,
                   regime: pd.Series, chip_cache: dict):
    gen_fn = TEMPLATE_GENERATORS[template]
    chip_data = chip_cache.get(sid)
    regime_alnd = regime.reindex(df.index, method="ffill").fillna("BEAR") if regime is not None else None
    sig = gen_fn(df, params, regime=regime_alnd, chip_data=chip_data)
    return sig


def _bnh_metrics(df: pd.DataFrame, start: str, end: str, init_cap: float):
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    sl = df[(df.index >= s) & (df.index <= e)][["close"]].dropna().copy()
    if len(sl) < 2:
        return None
    p0 = sl["close"].iloc[0]
    sl["equity"] = init_cap * (sl["close"] / p0)
    sl["dd"] = (sl["equity"] - sl["equity"].cummax()) / sl["equity"].cummax()
    yrs = (sl.index[-1] - sl.index[0]).days / 365
    cagr = (sl["equity"].iloc[-1] / sl["equity"].iloc[0]) ** (1 / yrs) - 1 if yrs > 0 else float("nan")
    daily_ret = sl["equity"].pct_change().dropna()
    sharpe = (daily_ret.mean() / daily_ret.std() * (252 ** 0.5)
              if daily_ret.std() > 0 else float("nan"))
    return {
        "equity": sl["equity"],
        "dd": sl["dd"],
        "cagr": cagr,
        "max_dd": sl["dd"].min(),
        "sharpe": sharpe,
        "total_return": sl["equity"].iloc[-1] / sl["equity"].iloc[0] - 1,
    }


def main():
    print("=" * 72)
    print("Portfolio backtest of 17 tradeable stocks")
    print(f"Period: {START_DATE} → {END_DATE}, Initial: {INITIAL_CAPITAL:,.0f} TWD")
    print("=" * 72)

    rec_doc = _load_yaml(REC_PATH)
    cfg     = _load_yaml(CFG_PATH)
    fees    = cfg["fees"]

    # ── 1) Filter tradeable stocks ────────────────────────────
    tradeable = []
    for sid, info in rec_doc.items():
        if not isinstance(info, dict):
            continue
        if info.get("tradeable", False):
            tradeable.append({
                "sid": sid,
                "name": info.get("name", ""),
                "template": info["template"],
                "tier":     info.get("tier", "?"),
                "position_pct_max": float(info["position_pct_max"]),
            })
    print(f"\n  Tradeable: {len(tradeable)} stocks")
    for t in tradeable:
        print(f"    {t['sid']:<5} {t['name']:<8} {t['template']:<22} "
              f"tier={t['tier']}  pos≤{t['position_pct_max']:.0%}")

    # ── 2) Load OHLCV + regime + chip cache ───────────────────
    print("\n  Loading OHLCV…")
    ohlcv = {}
    skipped = []
    for t in tradeable:
        sid = t["sid"]
        df = _load_adj_ohlcv(sid)
        if df is None or len(df) < 250:
            skipped.append({"sid": sid, "reason": "data missing or insufficient"})
            log_error("portfolio_backtest_17", sid, "資料不足或不存在")
            continue
        ohlcv[sid] = df

    print(f"  OHLCV ready: {len(ohlcv)}  skipped: {len(skipped)}")

    print("  Loading 0050 regime…")
    mkt_df = _load_adj_ohlcv("0050")
    regime = detect_regime(mkt_df) if mkt_df is not None else None

    chip_cache = {}
    for t in tradeable:
        sid = t["sid"]
        if t["template"] == "chip_momentum" and sid in ohlcv:
            try:
                chip_cache[sid] = fetch_chip_data(sid)
            except Exception as e:
                log_error("portfolio_backtest_17", sid, f"chip 載入失敗: {e}")
                chip_cache[sid] = pd.DataFrame()

    # ── 3) Generate per-stock signals ─────────────────────────
    print("\n  Generating per-stock signals…")
    signals = {}
    sid_to_meta = {t["sid"]: t for t in tradeable}
    for t in tradeable:
        sid = t["sid"]
        if sid not in ohlcv:
            continue
        try:
            params = _load_template_params(t["template"], sid)
            if not params:
                log_error("portfolio_backtest_17", sid,
                          f"找不到 best_params: {t['template']}")
                skipped.append({"sid": sid, "reason": "missing best_params"})
                continue
            sig = _build_signals(sid, t["template"], params,
                                 ohlcv[sid], regime, chip_cache)
            signals[sid] = sig
            n_buy  = int((sig["action"] == "BUY").sum())
            n_sell = int((sig["action"] == "SELL").sum())
            print(f"    {sid} {t['template']:<22}: BUY={n_buy:>3}  SELL={n_sell:>3}")
        except Exception as e:
            log_error("portfolio_backtest_17", sid, f"signal 失敗: {e}")
            skipped.append({"sid": sid, "reason": f"signal exception: {e}"})

    # ── 4) Build portfolio timeline ───────────────────────────
    print("\n  Walking portfolio timeline…")
    start_ts = pd.Timestamp(START_DATE)
    end_ts   = pd.Timestamp(END_DATE)

    all_dates = sorted({d for sid, df in ohlcv.items()
                        for d in df.index
                        if start_ts <= d <= end_ts})

    cash = float(INITIAL_CAPITAL)
    holdings = {}                 # {sid: shares}
    entry_info = {}               # {sid: {"date":, "price":, "shares":, "cost_basis":}}
    trades = []                   # list of dicts
    equity_vals = []
    equity_idx  = []

    for i, today in enumerate(all_dates):
        # Mark-to-market equity at open of today (used for sizing of new buys today)
        # Use prev close holdings for equity_at_open estimate.
        portfolio_close_yday = cash
        for sid, sh in holdings.items():
            df = ohlcv[sid]
            sub = df[df.index < today]
            if len(sub) > 0:
                portfolio_close_yday += sh * float(sub["close"].iloc[-1])

        # T+1 execution: read signals at index of yesterday for each stock
        # We use each stock's previous trading day in *that stock's* index
        # (so non-trading days don't shift signals).
        # For each stock with available data today, look up the signal at its
        # most recent trading day strictly before today.
        for sid, df in ohlcv.items():
            if today not in df.index:
                continue
            sig = signals.get(sid)
            if sig is None:
                continue
            prior_idx = df.index[df.index < today]
            if len(prior_idx) == 0:
                continue
            t_signal_date = prior_idx[-1]
            if t_signal_date not in sig.index:
                continue
            action = sig.loc[t_signal_date, "action"]

            open_today = float(df.loc[today, "open"])
            current_sh = holdings.get(sid, 0)

            # ── SELL ────────────────────────────────────
            if action == "SELL" and current_sh > 0:
                proceeds = calc_sell_proceeds(open_today, current_sh, fees)
                cash += proceeds
                e = entry_info.pop(sid, None)
                if e is not None:
                    pnl = proceeds - e["cost_basis"]
                    pnl_pct = pnl / e["cost_basis"] if e["cost_basis"] > 0 else 0.0
                    trades.append({
                        "stock_id":   sid,
                        "entry_date": e["date"],
                        "exit_date":  today,
                        "entry_price": e["price"],
                        "exit_price":  open_today,
                        "shares":      current_sh,
                        "pnl":         pnl,
                        "pnl_pct":     pnl_pct,
                        "hold_days":   (today - e["date"]).days,
                    })
                holdings.pop(sid, None)

            # ── BUY ─────────────────────────────────────
            elif action == "BUY" and current_sh == 0:
                meta = sid_to_meta[sid]
                pos_max = meta["position_pct_max"]
                # Sizing: min(position_pct_max × portfolio_at_open, available_cash)
                max_alloc_by_pct = pos_max * portfolio_close_yday
                budget = min(max_alloc_by_pct, cash)
                if budget <= 0 or open_today <= 0:
                    continue
                # estimate shares from exec_price + commission
                slip = fees["slippage_rate"]
                exec_price_est = open_today * (1 + slip)
                cost_per_share_est = exec_price_est * (1 + fees["buy_commission_rate"])
                shares_to_buy = max(0, int(budget / cost_per_share_est))
                while shares_to_buy > 0 and calc_buy_cost(open_today, shares_to_buy, fees) > min(budget, cash):
                    shares_to_buy -= 1
                if shares_to_buy <= 0:
                    continue
                cost = calc_buy_cost(open_today, shares_to_buy, fees)
                if cost > cash:
                    continue
                cash -= cost
                holdings[sid] = shares_to_buy
                entry_info[sid] = {
                    "date": today,
                    "price": open_today,
                    "shares": shares_to_buy,
                    "cost_basis": cost,
                }

        # End-of-day equity using close prices
        portfolio_value = cash
        for sid, sh in holdings.items():
            df = ohlcv[sid]
            if today in df.index:
                portfolio_value += sh * float(df.loc[today, "close"])
            else:
                sub = df[df.index < today]
                if len(sub) > 0:
                    portfolio_value += sh * float(sub["close"].iloc[-1])
        equity_vals.append(portfolio_value)
        equity_idx.append(today)

    # ── 5) Force close at end ─────────────────────────────────
    last_date = equity_idx[-1] if equity_idx else end_ts
    for sid, sh in list(holdings.items()):
        df = ohlcv[sid]
        sub = df[df.index <= last_date]
        if len(sub) == 0:
            continue
        last_close = float(sub["close"].iloc[-1])
        proceeds = calc_sell_proceeds(last_close, sh, fees)
        cash += proceeds
        e = entry_info.pop(sid, None)
        if e is not None:
            pnl = proceeds - e["cost_basis"]
            pnl_pct = pnl / e["cost_basis"] if e["cost_basis"] > 0 else 0.0
            trades.append({
                "stock_id":   sid,
                "entry_date": e["date"],
                "exit_date":  last_date,
                "entry_price": e["price"],
                "exit_price":  last_close,
                "shares":      sh,
                "pnl":         pnl,
                "pnl_pct":     pnl_pct,
                "hold_days":   (last_date - e["date"]).days,
                "force_close": True,
            })
    # Re-stamp final equity to use the post-flush cash (equity at last day)
    if equity_vals:
        equity_vals[-1] = cash  # everything liquidated

    equity = pd.Series(equity_vals, index=equity_idx, name="equity")
    dd = (equity - equity.cummax()) / equity.cummax()

    # ── 6) Metrics ────────────────────────────────────────────
    yrs = (equity.index[-1] - equity.index[0]).days / 365
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / yrs) - 1 if yrs > 0 else float("nan")
    daily_ret = equity.pct_change().dropna()
    sharpe = (daily_ret.mean() / daily_ret.std() * (252 ** 0.5)
              if daily_ret.std() > 0 else float("nan"))
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    max_dd = float(dd.min())
    n_trades = len(trades)
    n_wins = sum(1 for t in trades if t["pnl"] > 0)
    win_rate = n_wins / n_trades if n_trades > 0 else float("nan")

    # ── 7) 0050 Buy-and-Hold ──────────────────────────────────
    bh = _bnh_metrics(mkt_df, START_DATE, END_DATE, INITIAL_CAPITAL) if mkt_df is not None else None

    # tracking error: align dates and compute std of (port_ret - bh_ret) * sqrt(252)
    track_err = float("nan")
    if bh is not None:
        bh_eq_aligned = bh["equity"].reindex(equity.index, method="ffill")
        port_ret = equity.pct_change().dropna()
        bh_ret   = bh_eq_aligned.pct_change().dropna()
        common = port_ret.index.intersection(bh_ret.index)
        if len(common) > 30:
            diff = port_ret.loc[common] - bh_ret.loc[common]
            track_err = float(diff.std() * (252 ** 0.5))

    # ── 8) Per-stock contribution ─────────────────────────────
    contrib_rows = []
    by_sid = {}
    for tr in trades:
        by_sid.setdefault(tr["stock_id"], []).append(tr)
    for t in tradeable:
        sid = t["sid"]
        sub = by_sid.get(sid, [])
        n   = len(sub)
        pnl_total = sum(x["pnl"] for x in sub)
        wins = sum(1 for x in sub if x["pnl"] > 0)
        wr   = wins / n if n > 0 else float("nan")
        avg_pnl_pct = (sum(x["pnl_pct"] for x in sub) / n) if n > 0 else float("nan")
        # contribution to total portfolio return (% of initial capital)
        contrib_pct = pnl_total / INITIAL_CAPITAL
        contrib_rows.append({
            "sid": sid,
            "name": t["name"],
            "template": t["template"],
            "tier": t["tier"],
            "pos_max": t["position_pct_max"],
            "n_trades": n,
            "win_rate": wr,
            "avg_pnl_pct": avg_pnl_pct,
            "total_pnl_twd": pnl_total,
            "contrib_pct": contrib_pct,
        })

    # ── 9) Save daily CSV ─────────────────────────────────────
    out_df = pd.DataFrame({
        "date":     equity.index.strftime("%Y-%m-%d"),
        "equity":   equity.values.round(2),
        "drawdown": dd.values.round(6),
    })
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n  Daily CSV: {OUT_CSV}")

    # ── 10) Markdown report ───────────────────────────────────
    alpha = (cagr - bh["cagr"]) if bh is not None and not math.isnan(bh["cagr"]) else float("nan")

    # equity curve description
    peak_idx = equity.idxmax()
    peak_val = equity.max()
    trough_idx = equity.idxmin()
    trough_val = equity.min()
    max_dd_idx = dd.idxmin()
    # Recovery time after worst DD: first date after max_dd_idx where equity >= prior cummax
    prev_peak = float(equity.loc[:max_dd_idx].cummax().iloc[-1])
    after = equity.loc[max_dd_idx:]
    rec_idx = after[after >= prev_peak].index
    if len(rec_idx) > 0:
        rec_date_str = rec_idx[0].strftime("%Y-%m-%d")
        rec_days = (rec_idx[0] - max_dd_idx).days
        rec_text = f"{rec_date_str}（{rec_days} 天）"
    else:
        rec_text = "回測結束時尚未恢復"

    sorted_contrib = sorted(contrib_rows, key=lambda r: r["contrib_pct"], reverse=True)

    lines = []
    lines.append("# 17 檔 tradeable 個股組合回測（2017-01-01 → 2026-04-22）\n")
    lines.append(f"_run dir_: `output/auto_iterate/20260424_220634/`\n")
    lines.append(f"_initial capital_: NT$ {INITIAL_CAPITAL:,.0f}\n")
    lines.append(f"_signal universe_: 17 檔 tier S/A/B/C（已排除 tier F）\n")
    lines.append("")
    lines.append("## 1. 整體績效對比\n")
    lines.append("| 指標 | 17 檔組合 | 0050 Buy & Hold | Δ |")
    lines.append("|------|----------:|----------------:|---:|")
    lines.append(f"| CAGR | {cagr:+.2%} | {bh['cagr']:+.2%} | {alpha:+.2%} |")
    lines.append(f"| Total Return | {total_return:+.1%} | {bh['total_return']:+.1%} | {(total_return - bh['total_return']):+.1%} |")
    lines.append(f"| Max Drawdown | {max_dd:.2%} | {bh['max_dd']:.2%} | {(max_dd - bh['max_dd']):+.2%} |")
    lines.append(f"| Sharpe (rf=0) | {sharpe:.2f} | {bh['sharpe']:.2f} | {(sharpe - bh['sharpe']):+.2f} |")
    lines.append(f"| 期末淨值 (TWD) | {equity.iloc[-1]:,.0f} | {bh['equity'].iloc[-1]:,.0f} | {(equity.iloc[-1] - bh['equity'].iloc[-1]):+,.0f} |")
    lines.append(f"| 總交易筆數 | {n_trades} | 1 | — |")
    lines.append(f"| 勝率 | {win_rate:.1%} | — | — |")
    lines.append(f"| Tracking error (年化) | {track_err:.2%} | — | — |")
    lines.append("")
    verdict = "**打贏 0050**" if alpha > 0 else "**輸給 0050**"
    lines.append(f"### Verdict: {verdict}（alpha={alpha:+.2%} CAGR）\n")

    lines.append("## 2. 個股貢獻表（依貢獻度排序）\n")
    lines.append("| Stock | Name | Template | Tier | pos≤ | Trades | WR | AvgPnL | TotalPnL (TWD) | 貢獻 (%初始資金) |")
    lines.append("|-------|------|----------|------|------|-------:|----|-------:|---------------:|------------------:|")
    for r in sorted_contrib:
        wr_s = f"{r['win_rate']:.0%}" if not math.isnan(r['win_rate']) else "—"
        ap_s = f"{r['avg_pnl_pct']:+.1%}" if not math.isnan(r['avg_pnl_pct']) else "—"
        lines.append(
            f"| {r['sid']} | {r['name']} | {r['template']} | {r['tier']} | "
            f"{r['pos_max']:.0%} | {r['n_trades']} | {wr_s} | {ap_s} | "
            f"{r['total_pnl_twd']:+,.0f} | {r['contrib_pct']*100:+.2f}% |"
        )
    lines.append("")

    lines.append("## 3. Equity Curve 描述\n")
    lines.append(f"- **起點 ({equity.index[0].date()})**: NT$ {equity.iloc[0]:,.0f}")
    lines.append(f"- **歷史最高點 ({peak_idx.date()})**: NT$ {peak_val:,.0f}")
    lines.append(f"- **歷史最低點 ({trough_idx.date()})**: NT$ {trough_val:,.0f}")
    lines.append(f"- **最大回檔 ({max_dd_idx.date()})**: {max_dd:.2%}")
    lines.append(f"- **恢復前高**: {rec_text}")
    lines.append(f"- **終點 ({equity.index[-1].date()})**: NT$ {equity.iloc[-1]:,.0f}")
    lines.append("")

    # year-by-year returns
    yearly = equity.resample("Y").last().pct_change().dropna()
    lines.append("### 年度報酬\n")
    lines.append("| 年度 | 組合 | 0050 |")
    lines.append("|------|------:|------:|")
    bh_yearly = bh["equity"].resample("Y").last().pct_change().dropna()
    for y in yearly.index:
        y_str = str(y.year)
        port_y = yearly.loc[y]
        bh_y   = bh_yearly.loc[y] if y in bh_yearly.index else float("nan")
        bh_s   = f"{bh_y:+.1%}" if not math.isnan(bh_y) else "—"
        lines.append(f"| {y_str} | {port_y:+.1%} | {bh_s} |")
    lines.append("")

    if skipped:
        lines.append("## 4. 跳過 / 失敗的個股\n")
        for s in skipped:
            lines.append(f"- {s['sid']}: {s['reason']}")
        lines.append("")

    lines.append("## 5. Caveats（需要在解讀前看的警告）\n")
    lines.append("- **樣本數小**: 多數個股 9 年只有 2~10 筆交易（test 期更只 1~5 筆），個股期望值的統計信賴度有限。")
    lines.append("- **參數選擇偏差 (selection bias)**: 17 檔 tradeable 名單是 auto_iterate 用 train (2017-2023) + test (2024-2026) 篩出來的；同一段資料既被用來篩股、也被用來算這個回測的整體績效。**這不是純 out-of-sample 結果，會高估 alpha**。")
    lines.append("- **參數穩定性**: 每檔的 best_params 是 optuna 在 train 期間搜出來的；雖然 test 期間有過 verdict 篩選，仍可能是過擬合。")
    lines.append("- **資金利用率**: 由於分散度有限 + tier 限制，組合許多時間是現金為主；equity curve 平滑但 alpha 來自少數幾次大波段。")
    lines.append("- **無重新 rebalance**: 一檔股票在持倉期間不再加碼，BUY 訊號重複觸發時被忽略（已持倉）；SELL 出場後若再 BUY 才會重新進場。")
    lines.append("- **流動性 / 滑價**: 1000 萬規模對中小型股（如 1809 中釉、1560 中砂）可能難以在開盤價成交，實際滑價會比 0.3% 高。")
    lines.append("- **chip 資料時效**: 2383/3711 走 chip_momentum，回測用的是緩存的籌碼資料，未含最新時點外的修正。")
    lines.append("- **強制平倉**: 回測末日（{}）剩餘持倉以收盤價強制出清，視為一筆交易。".format(END_DATE))
    lines.append("")

    md_text = "\n".join(lines)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"  Report:    {OUT_MD}")

    # ── 11) Print summary ─────────────────────────────────────
    print("\n" + "=" * 72)
    print("PORTFOLIO METRICS")
    print("=" * 72)
    print(f"  CAGR:         {cagr:+.2%}")
    print(f"  Total Return: {total_return:+.1%}")
    print(f"  Max DD:       {max_dd:.2%}")
    print(f"  Sharpe:       {sharpe:.2f}")
    print(f"  Trades:       {n_trades}  (win_rate={win_rate:.1%})")
    print(f"  Final:        NT$ {equity.iloc[-1]:,.0f}")
    if bh is not None:
        print()
        print("0050 BUY-AND-HOLD")
        print(f"  CAGR:         {bh['cagr']:+.2%}")
        print(f"  Total Return: {bh['total_return']:+.1%}")
        print(f"  Max DD:       {bh['max_dd']:.2%}")
        print(f"  Sharpe:       {bh['sharpe']:.2f}")
        print(f"  Final:        NT$ {bh['equity'].iloc[-1]:,.0f}")
        print()
        print(f"  Alpha (CAGR): {alpha:+.2%}")
        print(f"  Tracking err: {track_err:.2%}")

    print("\nTop 5 contributors:")
    for r in sorted_contrib[:5]:
        print(f"  {r['sid']} {r['name']:<6} contrib={r['contrib_pct']*100:+.2f}%  trades={r['n_trades']}")
    print("\nBottom 5 contributors:")
    for r in sorted_contrib[-5:]:
        print(f"  {r['sid']} {r['name']:<6} contrib={r['contrib_pct']*100:+.2f}%  trades={r['n_trades']}")


if __name__ == "__main__":
    main()
