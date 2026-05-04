"""Audit：對每檔在限價單機制下跑 7 個 templates，找新機制最佳 template

5/4 限價單機制 v0.1 上線後，per_stock_recommendations.yaml 的 best_template 是
4/26 用舊機制（T+1 open）選的。新機制下「最佳 template」可能改變，此腳本驗證。

詳見 docs/TODO_AUDIT_TEMPLATES.md。

用法：
  python scripts/audit_templates.py                # 全部 tradeable stocks
  python scripts/audit_templates.py --stocks 2330 2317
  python scripts/audit_templates.py --include-non-tradeable
"""
import os
import sys
import math
import yaml
import argparse
import pandas as pd
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.strategy.runner import (
    _load_strategy_cfg, _load_adj_ohlcv, _load_recommendations,
)
from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.auto_iterate.templates import TEMPLATE_GENERATORS

# 7 個已實作限價單機制的 template（詳見 docs/LIMIT_ORDER_V0_1.md）
LIMIT_ORDER_TEMPLATES = [
    "low_vol_pullback",
    "mean_reversion",
    "donchian_breakout",
    "trend_pullback",
    "momentum_hold",
    "volume_breakout",
    "bollinger_squeeze",
]

MERGED_DIR = os.path.join(BASE_DIR, "output", "auto_iterate", "merged_20260426_120034")
OUT_DIR = os.path.join(BASE_DIR, "output", f"audit_{date.today().strftime('%Y-%m-%d')}")
DEFAULT_POS_MAX = 0.5  # 不可交易的標的，audit 用 50% 倉位試（純比較）


def load_params(stock_id: str, template: str) -> dict | None:
    """從 merged auto_iterate run 讀 (stock, template) 的 best_params。"""
    yaml_path = os.path.join(MERGED_DIR, f"{template}.yaml")
    if not os.path.exists(yaml_path):
        return None
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    per_stock = data.get("per_stock", {}) if isinstance(data, dict) else {}
    rec = per_stock.get(stock_id)
    if not isinstance(rec, dict):
        return None
    return rec.get("best_params")


def run_one(stock_id: str, template: str, params: dict,
            bt_start: str, bt_end: str, pos_max: float):
    """跑單檔單 template 限價單回測，回傳 BacktestResult 或 None。"""
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
        start_date=bt_start,
        end_date=bt_end,
        initial_capital=1_000_000,
        max_position_pct=pos_max,
    )
    return Backtester(bt_cfg).run_per_stock(stock_id, df_adj, sig_df)


def score(res) -> float:
    """Risk-adjusted score：PF × log(n_trades+1)，過濾低 fill_rate / 低 PF。"""
    if res is None or res.n_trades == 0:
        return float("-inf")
    pf = res.profit_factor
    if math.isnan(pf):
        return float("-inf")
    if math.isinf(pf):
        pf = 100.0
    if pf <= 1.0:
        return float("-inf")
    fr = getattr(res, "fill_rate", 1.0)
    if isinstance(fr, float) and math.isnan(fr):
        fr = 1.0
    if fr < 0.3:
        return float("-inf")
    return pf * math.log(res.n_trades + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stocks", nargs="*", default=None,
                    help="指定股票代號；省略則取所有 tradeable")
    ap.add_argument("--include-non-tradeable", action="store_true",
                    help="也 audit tradeable=false 的股票（用 50% 倉位試）")
    args = ap.parse_args()

    rec_all = _load_recommendations()
    cfg = _load_strategy_cfg()
    bt_start = cfg["backtest"]["start_date"]
    bt_end = cfg["backtest"]["end_date"]

    if args.stocks:
        stock_ids = args.stocks
    else:
        stock_ids = sorted([
            sid for sid, rec in rec_all.items()
            if rec.get("tradeable") or args.include_non_tradeable
        ])

    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Audit {len(stock_ids)} 檔 × {len(LIMIT_ORDER_TEMPLATES)} templates")
    print(f"  資料範圍：{bt_start} ~ {bt_end}")
    print(f"  輸出 → {OUT_DIR}\n")

    rows = []
    changes = []
    skipped = []

    for sid in stock_ids:
        rec = rec_all.get(sid, {})
        current_template = rec.get("template", "")
        pos_max = rec.get("position_pct_max") or DEFAULT_POS_MAX

        results = {}
        for tpl in LIMIT_ORDER_TEMPLATES:
            params = load_params(sid, tpl)
            if not params:
                continue
            try:
                res = run_one(sid, tpl, params, bt_start, bt_end, pos_max)
            except Exception as e:
                print(f"  [{sid} / {tpl}] 失敗：{e}")
                continue
            if res is None:
                continue
            results[tpl] = res

        if not results:
            skipped.append(sid)
            print(f"  {sid} {rec.get('name', '')[:10]:<10}  ⚠️  無可用 templates，跳過")
            continue

        scored = sorted(
            [(tpl, score(res), res) for tpl, res in results.items()],
            key=lambda x: x[1], reverse=True
        )
        best_new, best_score, _ = scored[0]

        for tpl, res in results.items():
            pf = res.profit_factor
            rows.append({
                "stock_id": sid,
                "name": rec.get("name", sid),
                "template": tpl,
                "is_current": tpl == current_template,
                "is_new_best": tpl == best_new,
                "n_trades": res.n_trades,
                "win_rate": round(res.win_rate, 4) if res.n_trades > 0 else None,
                "pf": round(pf, 3) if not (math.isinf(pf) or math.isnan(pf)) else None,
                "max_dd": round(res.max_drawdown, 4) if not math.isnan(res.max_drawdown) else None,
                "im_cagr": round(res.in_market_cagr, 4) if not math.isnan(res.in_market_cagr) else None,
                "fill_rate": round(getattr(res, "fill_rate", float("nan")), 3)
                              if not math.isnan(getattr(res, "fill_rate", float("nan"))) else None,
                "expectancy": round(res.expectancy, 4) if res.n_trades > 0 else None,
                "score": round(score(res), 3) if score(res) != float("-inf") else None,
            })

        if best_new != current_template and current_template in LIMIT_ORDER_TEMPLATES:
            curr_score = score(results.get(current_template))
            changes.append({
                "stock_id": sid,
                "name": rec.get("name", sid),
                "current": current_template,
                "current_score": curr_score if curr_score != float("-inf") else None,
                "new_best": best_new,
                "new_score": best_score,
                "improvement": (best_score - curr_score)
                                if curr_score != float("-inf") else None,
            })

        flag = "⚠️ 改變" if best_new != current_template else "✓ 不變"
        print(f"  {sid} {rec.get('name', '')[:10]:<10}  目前 {current_template:<20} → 新最佳 {best_new:<20} [{flag}]")

    # 寫入 CSV
    df = pd.DataFrame(rows)
    csv_path = os.path.join(OUT_DIR, "template_comparison.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    # 寫入 changes.md
    md_path = os.path.join(OUT_DIR, "changes.md")
    L = [
        f"# Template Audit — {date.today().strftime('%Y-%m-%d')}",
        "",
        f"審查 {len(stock_ids)} 檔 × {len(LIMIT_ORDER_TEMPLATES)} 個 limit-order templates",
        "",
        "## Summary",
        "",
        f"- 總股票數：{len(stock_ids)}",
        f"- 最佳 template **改變**的：{len(changes)} 檔（{len(changes)/max(len(stock_ids),1)*100:.0f}%）",
        f"- 跳過（無可用 templates）：{len(skipped)} 檔",
        "",
    ]

    if changes:
        L.extend([
            "## 變動清單（按改善幅度排序）",
            "",
            "| 股票 | 名稱 | 目前 | 目前 score | 新最佳 | 新 score | Δ |",
            "|---|---|---|---|---|---|---|",
        ])
        changes.sort(key=lambda x: (x["improvement"] or 0), reverse=True)
        for c in changes:
            curr_s = f"{c['current_score']:.2f}" if c['current_score'] is not None else "N/A"
            imp_s = f"+{c['improvement']:.2f}" if c.get("improvement") is not None else "—"
            L.append(f"| {c['stock_id']} | {c['name']} | {c['current']} | {curr_s} | "
                     f"**{c['new_best']}** | {c['new_score']:.2f} | {imp_s} |")
        L.append("")
        # 決策建議
        change_pct = len(changes) / max(len(stock_ids), 1) * 100
        L.extend([
            "## 決策建議",
            "",
        ])
        if change_pct < 10:
            L.extend([
                f"變動率 {change_pct:.0f}% < 10% → **暫不重訓**，繼續用 current best_params",
                "可考慮對個別變動明顯的標的手動切換 template",
            ])
        elif change_pct < 30:
            L.extend([
                f"變動率 {change_pct:.0f}%（10-30%）→ **觀察 1~2 週後再決定**",
                "若新訊號實單表現優於舊訊號，再排重訓",
            ])
        else:
            L.extend([
                f"變動率 {change_pct:.0f}% > 30% → **建議排完整重訓**",
                "詳見 docs/TODO_RETRAIN.md",
            ])
    else:
        L.extend([
            "## 結論：無顯著變動",
            "",
            "所有股票的最佳 template 在限價單機制下未改變。current best_params 仍為最佳選擇。",
        ])

    if skipped:
        L.extend([
            "",
            f"## 跳過清單（{len(skipped)} 檔）",
            "",
            "下列股票無任何 limit-order template 有可用 best_params：",
            "",
            ", ".join(skipped),
        ])

    L.extend(["", "---", f"完整 metrics：[template_comparison.csv]({os.path.basename(csv_path)})"])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"\n寫入 {csv_path}")
    print(f"寫入 {md_path}")
    print(f"\n變動：{len(changes)} 檔；不變：{len(stock_ids) - len(changes) - len(skipped)} 檔；跳過：{len(skipped)} 檔")


if __name__ == "__main__":
    main()
