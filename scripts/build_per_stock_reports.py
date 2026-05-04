"""對 watchlist 每檔生成個股回測 markdown 報告。

用途：
- 每日 daily_update.bat 跑完 signals 後執行
- 對每檔產出 output/reports/per_stock/{stock_id}.md
- README 與 latest signals 報告中的個股代號可超連結到此頁

用法：
  python scripts/build_per_stock_reports.py
  python scripts/build_per_stock_reports.py --stocks 2360 2317
"""
import os
import sys
import math
import yaml
import argparse
import pandas as pd
import numpy as np
from datetime import date

# 強制 stdout UTF-8（Windows cp950 不支援 ✓/✗ 等 unicode）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.strategy.runner import (
    _load_strategy_cfg, _load_adj_ohlcv, _load_ohlcv,
    _load_recommendations,
)
from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.auto_iterate.templates import TEMPLATE_GENERATORS

OUT_DIR = os.path.join(BASE_DIR, "output", "reports", "per_stock")


def load_per_stock_params(stock_id: str, template: str) -> dict | None:
    """從 merged auto_iterate 結果讀該檔 best_params。"""
    merged_dir = os.path.join(BASE_DIR, "output", "auto_iterate", "merged_20260426_120034")
    yaml_path = os.path.join(merged_dir, f"{template}.yaml")
    if not os.path.exists(yaml_path):
        return None
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # YAML 結構：top-level → per_stock → {stock_id} → best_params
    per_stock = data.get("per_stock", {}) if isinstance(data, dict) else {}
    rec = per_stock.get(stock_id)
    if not isinstance(rec, dict):
        return None
    return rec.get("best_params")


def run_backtest_one(stock_id: str, template: str, params: dict,
                      start_date: str, end_date: str,
                      max_position_pct: float) -> dict:
    """執行單檔回測，回傳指標與每筆交易。

    全部用 adj_close 跑（含限價單機制下的 OCO 比較）：
      - 與 BNH / 0050 同期 CAGR 比較公平（都含複利）
      - 限價單 target 算出來與 adj 的 high/low 直接可比
    """
    df_adj = _load_adj_ohlcv(stock_id)
    if df_adj is None or len(df_adj) < 50:
        return None

    gen_fn = TEMPLATE_GENERATORS.get(template)
    if gen_fn is None:
        return None
    sig_df = gen_fn(df_adj, params)

    cfg = _load_strategy_cfg()
    bt_cfg = BacktestConfig(
        fees=cfg["fees"],
        start_date=start_date,
        end_date=end_date,
        initial_capital=1_000_000,
        max_position_pct=max_position_pct,
    )
    bt = Backtester(bt_cfg)
    res = bt.run_per_stock(stock_id, df_adj, sig_df)

    # 同期 BNH 對照
    hold = df_adj[df_adj.index >= pd.Timestamp(start_date)]
    if len(hold) > 1:
        bnh_total = hold["close"].iloc[-1] / hold["close"].iloc[0] - 1
        years = (hold.index[-1] - hold.index[0]).days / 365
        bnh_cagr = (hold["close"].iloc[-1] / hold["close"].iloc[0]) ** (1 / max(years, 0.1)) - 1
    else:
        bnh_total = float("nan")
        bnh_cagr = float("nan")

    return {
        "result": res,
        "bnh_total": bnh_total,
        "bnh_cagr": bnh_cagr,
        "params": params,
    }


def write_report(stock_id: str, name: str, rec: dict, bt: dict | None) -> str:
    """寫入單檔 markdown 報告。"""
    today = date.today().strftime("%Y-%m-%d")
    path = os.path.join(OUT_DIR, f"{stock_id}.md")
    os.makedirs(OUT_DIR, exist_ok=True)

    L = []
    L.append(f"# {stock_id} {name}")
    L.append("")
    L.append(f"_最後更新：{today}_")
    L.append("")
    L.append("## 策略推薦")
    L.append("")
    L.append("| 項目 | 值 |")
    L.append("|---|---|")
    L.append(f"| Tier | **{rec.get('tier', '—')}** |")
    L.append(f"| 倉位上限 | {(rec.get('position_pct_max', 0) or 0)*100:.0f}% |")
    L.append(f"| Template | `{rec.get('template', '—')}` |")
    L.append(f"| 可交易 | {'✅' if rec.get('tradeable') else '⚠️ 不建議'} |")
    if rec.get("bnh_tier"):
        L.append(f"| BNH 長持 Tier | {rec['bnh_tier']} (倉位上限 {(rec.get('bnh_position_pct_max', 0) or 0)*100:.0f}%) |")
    if rec.get("bnh_cagr") is not None:
        L.append(f"| BNH 長持 CAGR | {rec['bnh_cagr']*100:+.1f}% |")
    L.append("")

    # auto_iterate test 統計
    L.append("## 回測表現（auto_iterate test 階段）")
    L.append("")
    L.append("| 指標 | 值 |")
    L.append("|---|---|")
    L.append(f"| 交易次數 | {rec.get('test_n_trades', '—')} |")
    pf = rec.get("test_pf")
    L.append(f"| Profit Factor | {pf:.2f} |" if pf else "| Profit Factor | — |")
    exp = rec.get("test_expectancy")
    L.append(f"| Expectancy（每筆） | {exp*100:+.2f}% |" if exp is not None else "| Expectancy | — |")
    dd = rec.get("test_max_dd")
    L.append(f"| 最大回撤 | {dd*100:+.1f}% |" if dd is not None else "| 最大回撤 | — |")
    L.append("")

    if bt is None or bt.get("result") is None:
        L.append("_本地完整回測：資料不足或 template 未支援，跳過。_")
    else:
        res = bt["result"]
        L.append("## 本地完整回測（同模板 + 同參數，adjusted 資料 + 限價單機制）")
        L.append("")
        L.append("| 指標 | 值 |")
        L.append("|---|---|")
        L.append(f"| 交易次數 | {res.n_trades} |")
        L.append(f"| 勝率 | {res.win_rate*100:.1f}% |" if res.n_trades > 0 else "| 勝率 | — |")
        if res.n_trades > 0:
            L.append(f"| 平均勝幅 | {res.avg_win*100:+.2f}% |")
            L.append(f"| 平均虧損 | {res.avg_loss*100:+.2f}% |")
            L.append(f"| Expectancy（每筆） | {res.expectancy*100:+.2f}% |")
            pf = res.profit_factor
            pf_str = f"{pf:.2f}" if not (math.isinf(pf) or math.isnan(pf)) else "∞"
            L.append(f"| Profit Factor | {pf_str} |")
            mdd = res.max_drawdown
            if not math.isnan(mdd):
                L.append(f"| 最大回撤 | {mdd*100:.1f}% |")
            imc = res.in_market_cagr
            if not math.isnan(imc):
                L.append(f"| 持倉期 CAGR | {imc*100:.1f}% |")
            L.append(f"| 平均持有天數 | {res.avg_hold_days:.1f} |")
        bnh_cagr = bt.get("bnh_cagr")
        if bnh_cagr is not None and not math.isnan(bnh_cagr):
            L.append(f"| 同期 BNH CAGR | {bnh_cagr*100:.1f}% |")
        # 限價單成交率（v0.1 新機制）
        if hasattr(res, "fill_rate") and not math.isnan(res.fill_rate):
            L.append(f"| 限價單成交率 | {res.fill_rate*100:.0f}% "
                      f"({res.buy_filled_count}/{res.buy_signals_count}) |")
        L.append("")

        # 年度分布
        if res.trades:
            L.append("## 年度交易分布")
            L.append("")
            L.append("| 年份 | 筆數 | 勝率 | 平均/筆 | 累積 |")
            L.append("|---|---|---|---|---|")
            df_t = pd.DataFrame([{
                "year": t.entry_date.year,
                "pnl_pct": t.pnl_pct * 100,
            } for t in res.trades])
            grp = df_t.groupby("year")
            for yr, g in grp:
                L.append(f"| {yr} | {len(g)} | {(g['pnl_pct']>0).mean()*100:.0f}% | "
                          f"{g['pnl_pct'].mean():+.2f}% | {g['pnl_pct'].sum():+.1f}% |")
            L.append("")

        # 最近 10 筆
        if res.trades:
            recent = res.trades[-10:]
            L.append(f"## 最近交易（最後 {len(recent)} 筆）")
            L.append("")
            L.append("| 進場 | 進場價 | 出場 | 出場價 | 報酬 | 持有 |")
            L.append("|---|---|---|---|---|---|")
            for t in recent:
                L.append(f"| {t.entry_date.strftime('%Y-%m-%d')} | {t.entry_price:.1f} | "
                          f"{t.exit_date.strftime('%Y-%m-%d')} | {t.exit_price:.1f} | "
                          f"{t.pnl_pct*100:+.2f}% | {t.hold_days}d |")
            L.append("")

    # 參數
    if bt and bt.get("params"):
        L.append("## 策略參數")
        L.append("")
        L.append("```yaml")
        L.append(yaml.dump(bt["params"], default_flow_style=False, allow_unicode=True).rstrip())
        L.append("```")
        L.append("")

    L.append("---")
    L.append("[← 回主頁](../../../README.md)")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stocks", nargs="*", default=None,
                    help="指定股票代號；省略則對 watchlists.yaml 所有清單去重後處理")
    args = ap.parse_args()

    cfg = _load_strategy_cfg()
    bt_start = cfg["backtest"]["start_date"]
    bt_end = cfg["backtest"]["end_date"]

    # 收集要處理的股票
    if args.stocks:
        stock_ids = args.stocks
    else:
        wl_path = os.path.join(BASE_DIR, "config", "watchlists.yaml")
        if not os.path.exists(wl_path):
            print(f"[錯誤] 找不到 {wl_path}")
            return
        with open(wl_path, encoding="utf-8") as f:
            wl = yaml.safe_load(f) or {}
        ids = set()
        for key, lst in wl.items():
            if key == "exception":
                continue
            for sid in (lst or []):
                ids.add(str(sid))
        stock_ids = sorted(ids)

    rec_all = _load_recommendations()
    print(f"準備生成 {len(stock_ids)} 檔個股回測報告 → {OUT_DIR}")

    success, failed = 0, []
    for sid in stock_ids:
        rec = rec_all.get(sid, {})
        if not rec:
            rec = {"name": sid, "tier": "—", "template": "—",
                    "position_pct_max": 0.0, "tradeable": False}

        name = rec.get("name", sid)
        template = rec.get("template", "")
        pos_max = rec.get("position_pct_max", 0.0) or 0.0

        bt = None
        if template and rec.get("tradeable"):
            params = load_per_stock_params(sid, template)
            if params:
                try:
                    bt = run_backtest_one(sid, template, params,
                                          bt_start, bt_end, pos_max)
                except Exception as e:
                    print(f"  [{sid}] 回測失敗：{e}")

        try:
            path = write_report(sid, name, rec, bt)
            print(f"  ✓ {sid} {name}")
            success += 1
        except Exception as e:
            print(f"  ✗ {sid} 失敗：{e}")
            failed.append(sid)

    print(f"\n完成：{success} 檔成功，{len(failed)} 檔失敗")
    if failed:
        print(f"失敗清單：{failed}")


if __name__ == "__main__":
    main()
