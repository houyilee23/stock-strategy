import os
import math
import pandas as pd
from datetime import date

from src.strategy.backtest.result import StockResult, PortfolioResult
from src.strategy.eval.per_stock import metrics_to_df
from src.strategy.eval.portfolio import calc_portfolio_metrics


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "N/A"
    return f"{v:.1%}"


def _fmt_f(v, dec=2) -> str:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "∞" if isinstance(v, float) and math.isinf(v) else "N/A"
    return f"{v:.{dec}f}"


def save_per_stock_csv(stock_results: list, run_id: str) -> str:
    out_dir = os.path.join(BASE_DIR, "output", "backtest")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"per_stock_{run_id}.csv")
    df = metrics_to_df(stock_results)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def save_portfolio_csv(result: PortfolioResult, run_id: str) -> str:
    out_dir = os.path.join(BASE_DIR, "output", "backtest")
    os.makedirs(out_dir, exist_ok=True)

    # 摘要列
    metrics = calc_portfolio_metrics(result)
    summary_path = os.path.join(out_dir, f"portfolio_{run_id}.csv")
    pd.DataFrame([metrics]).to_csv(summary_path, index=False, encoding="utf-8-sig")

    # Daily equity curve
    equity_path = os.path.join(out_dir, f"equity_{run_id}.csv")
    result.equity_curve.rename("equity").to_csv(equity_path, header=True, encoding="utf-8-sig")
    return summary_path


def save_summary_md(stock_results: list, portfolio_result: PortfolioResult,
                    run_id: str, eval_cfg: dict) -> str:
    out_dir = os.path.join(BASE_DIR, "output", "backtest")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{run_id}_summary.md")

    pm = calc_portfolio_metrics(portfolio_result)
    per_stock_df = metrics_to_df(stock_results)

    # 排序取最好/最差
    valid_df = per_stock_df[per_stock_df["sufficient_trades"]].copy()
    if not valid_df.empty and "in_market_cagr" in valid_df.columns:
        valid_df = valid_df.sort_values("in_market_cagr", ascending=False)
        top3 = valid_df.head(3)
        bot3 = valid_df.tail(3)
    else:
        top3 = pd.DataFrame()
        bot3 = pd.DataFrame()

    # 門檻檢查
    dd_thresh = eval_cfg.get("portfolio", {}).get("max_drawdown", 0.30)
    sharpe_thresh = eval_cfg.get("portfolio", {}).get("min_sharpe", 0.5)
    alpha_thresh = eval_cfg.get("portfolio", {}).get("min_alpha", 0)

    pass_dd = pm["max_drawdown"] >= -dd_thresh if not math.isnan(pm["max_drawdown"] or float("nan")) else False
    pass_sharpe = pm["sharpe"] >= sharpe_thresh if not math.isnan(pm["sharpe"] or float("nan")) else False
    pass_alpha = pm["alpha"] >= alpha_thresh if not math.isnan(pm["alpha"] or float("nan")) else False

    def chk(b): return "PASS" if b else "FAIL"

    lines = [
        f"# 回測摘要 — {run_id}",
        "",
        "## 整體結論",
        "",
        f"| 指標 | 數值 | 門檻 | 結果 |",
        f"|------|------|------|------|",
        f"| 組合 CAGR | {_fmt_pct(pm['cagr'])} | > 0050 | — |",
        f"| MaxDD | {_fmt_pct(pm['max_drawdown'])} | ≥ -{_fmt_pct(dd_thresh)} | {chk(pass_dd)} |",
        f"| Sharpe | {_fmt_f(pm['sharpe'])} | ≥ {sharpe_thresh} | {chk(pass_sharpe)} |",
        f"| Alpha vs 0050 | {_fmt_pct(pm['alpha'])} | > 0 | {chk(pass_alpha)} |",
        f"| 資金利用率 | {_fmt_pct(pm['in_market_pct'])} | — | — |",
        "",
    ]

    if not top3.empty:
        lines += ["## 表現最好 Top 3", ""]
        lines += [f"| 股票 | CAGR | PF | 勝率 | N |"]
        lines += [f"|------|------|----|----|---|"]
        for _, r in top3.iterrows():
            lines.append(f"| {r.stock_id} | {_fmt_pct(r.in_market_cagr)} | {_fmt_f(r.profit_factor)} | {_fmt_pct(r.win_rate)} | {r.n_trades} |")
        lines += [""]

    if not bot3.empty:
        lines += ["## 表現最差 Bottom 3", ""]
        lines += [f"| 股票 | CAGR | PF | 勝率 | N |"]
        lines += [f"|------|------|----|----|---|"]
        for _, r in bot3.iterrows():
            lines.append(f"| {r.stock_id} | {_fmt_pct(r.in_market_cagr)} | {_fmt_f(r.profit_factor)} | {_fmt_pct(r.win_rate)} | {r.n_trades} |")
        lines += [""]

    lines += ["## 與 0050 同期對照", ""]
    lines += [f"- 組合 CAGR: {_fmt_pct(pm['cagr'])}"]
    lines += [f"- 0050 baseline CAGR: {_fmt_pct(pm['benchmark_cagr'])}"]
    lines += [f"- Alpha: {_fmt_pct(pm['alpha'])}"]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def save_daily_signals_md(signals_df: pd.DataFrame, account_name: str,
                           stock_names: dict = None) -> str:
    """產出每日訊號 Markdown 報表。

    儲存路徑：
      output/reports/{YYYY}/{MM}/{DD}_signals_{account}.md   ← 歷史歸檔
      output/reports/latest/signals_{account}.md             ← 永遠是最新（手機入口）
    """
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    yr, mo, dd = today.strftime("%Y"), today.strftime("%m"), today.strftime("%d")

    archive_dir = os.path.join(BASE_DIR, "output", "reports", yr, mo)
    latest_dir = os.path.join(BASE_DIR, "output", "reports", "latest")
    os.makedirs(archive_dir, exist_ok=True)
    os.makedirs(latest_dir, exist_ok=True)
    path = os.path.join(archive_dir, f"{dd}_signals_{account_name}.md")
    latest_path = os.path.join(latest_dir, f"signals_{account_name}.md")

    # P1-1 修正：趨勢拆為「個股趨勢」與「市場Regime」兩欄
    # 2026-04 擴充：新增 Tier / 倉位上限 / Template 三欄（per_stock_recommendations）
    # 2026-05 新增：限價單機制 → 「掛單目標」欄；整合真實持倉 → 「在倉」欄
    lines = [
        f"# 今日訊號 — {account_name} ({today_str})",
        "",
        "| 股票 | 名稱 | 在倉 | 收盤 | 動作 | Tier | 倉位上限 | Template | 掛單目標 | 建議買入 | 建議停損 | RSI | 個股趨勢 | 市場Regime | 說明 |",
        "|------|------|-----|------|------|------|---------|---------|---------|---------|---------|-----|---------|-----------|------|",
    ]

    for _, row in signals_df.iterrows():
        sid = row.get("stock_id", "")
        name = (stock_names or {}).get(sid, "")
        close = row.get("close", float("nan"))
        action = row.get("action", "HOLD")
        entry_low = row.get("entry_low", float("nan"))
        entry_high = row.get("entry_high", float("nan"))
        stop = row.get("stop_loss", float("nan"))
        rsi_v = row.get("rsi_val", float("nan"))
        ma200 = row.get("ma200", float("nan"))
        ma50 = row.get("ma50", float("nan"))
        market_regime = str(row.get("market_regime", "—"))
        reason = row.get("reason", "")
        tier = str(row.get("tier", "—"))
        template = str(row.get("template", "—"))
        pos_max = row.get("position_pct_max", 0.0)

        # 倉位上限
        if isinstance(pos_max, (int, float)) and pos_max > 0:
            pos_str = f"{pos_max*100:.0f}%"
        else:
            pos_str = "—"

        # 買入區間
        if not (isinstance(entry_low, float) and math.isnan(entry_low)):
            buy_range = f"{entry_low:.1f}~{entry_high:.1f}"
        else:
            buy_range = "—"

        # 停損
        stop_str = f"{stop:.1f}" if not (isinstance(stop, float) and math.isnan(stop)) else "—"

        # RSI
        rsi_str = f"{rsi_v:.0f}" if not (isinstance(rsi_v, float) and math.isnan(rsi_v)) else "—"

        # 個股趨勢（MA50 > MA200 且 Close > MA200 才算多頭排列）
        if not (isinstance(ma200, float) and math.isnan(ma200)) and \
           not (isinstance(close, float) and math.isnan(close)) and \
           not (isinstance(ma50, float) and math.isnan(ma50)):
            stock_trend = "[多頭]" if (close > ma200 and ma50 > ma200) else "[空頭]"
        else:
            stock_trend = "—"

        # 收盤
        close_str = f"{close:.1f}" if not (isinstance(close, float) and math.isnan(close)) else "—"

        # 限價單目標（v0.1，部分 template 才有）
        target_buy = row.get("target_buy", float("nan"))
        target_tp = row.get("target_tp", float("nan"))
        target_sl = row.get("target_sl", float("nan"))
        if action == "BUY" and isinstance(target_buy, (int, float)) and not math.isnan(target_buy):
            order_str = f"買 {target_buy:.1f}"
        elif (isinstance(target_tp, (int, float)) and not math.isnan(target_tp)) or \
             (isinstance(target_sl, (int, float)) and not math.isnan(target_sl)):
            tp_s = f"{target_tp:.0f}" if isinstance(target_tp, (int, float)) and not math.isnan(target_tp) else "—"
            sl_s = f"{target_sl:.0f}" if isinstance(target_sl, (int, float)) and not math.isnan(target_sl) else "—"
            order_str = f"TP {tp_s} / SL {sl_s}"
        else:
            order_str = "—"

        # 在倉指示（從 runner 傳入的 in_position）
        in_pos = bool(row.get("in_position", False))
        in_pos_str = "✅" if in_pos else "—"
        # 若在倉，補持有資訊與「個人化 TP」（用真實 entry × tp_pct 算）到 reason
        if in_pos:
            rs_v = row.get("real_shares", 0)
            real_shares = int(rs_v) if isinstance(rs_v, (int, float)) and not math.isnan(rs_v) else 0
            real_entry = row.get("real_entry", float("nan"))
            personal_tp = row.get("personal_tp", float("nan"))
            note = f"(持{real_shares}股 @{real_entry:.2f}"
            if isinstance(personal_tp, (int, float)) and not math.isnan(personal_tp):
                note += f"，你的 TP {personal_tp:.1f}"
            note += ")"
            reason = (reason + " " if reason else "") + note

        lines.append(
            f"| {sid} | {name} | {in_pos_str} | {close_str} | {action} | {tier} | {pos_str} | "
            f"{template} | {order_str} | {buy_range} | {stop_str} | {rsi_str} | "
            f"{stock_trend} | {market_regime} | {reason} |"
        )

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    # 同步寫入 latest/，供 README 與手機入口直連
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
