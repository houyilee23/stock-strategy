"""個人庫存進出點分析：對手上 open positions 給出進出建議。

整合：
  - data/trades_<account>.csv (從 Excel 同步而來) → open positions + cost basis
  - data/adjusted/<sid>.csv → 當前收盤價
  - config/per_stock_recommendations.yaml → 該股 tier / template / 推薦倉位
  - output/reports/latest/signals_universe.md (or 直接呼叫 runner) → 今日訊號

輸出：
  output/reports/inventory_advice_<account>.md  - markdown 報告（手機看）
  output/reports/inventory_advice_<account>.csv - 結構化資料

建議邏輯（按優先順序）：
  1. tier=F → ★REDUCE★ 該策略已證實不適合 TA，建議減碼或改 BNH 評估
  2. 損失 > 15% AND tier in {C,D} → ★STOP_LOSS★ 弱策略止損
  3. 獲利 > 30% AND tier in {C,D} → ★TAKE_PROFIT★ 弱策略過度獲利可能反轉
  4. 獲利 > 50% AND tier in {S,A,B} → ★TRIM★ 強策略也適度減碼
  5. 損失 > 25% AND tier in {S,A,B} → ★STOP_LOSS★ 強策略也要停損
  6. 倉位過大（超過 tier 推薦倉位上限的 1.5×）→ ★REDUCE★
  7. 倉位偏小 AND tier in {S,A,B,C} AND 訊號 BUY → ★ADD★
  8. 否則 → HOLD

用法：
  python scripts/inventory_analysis.py [--account Personal]
"""
from __future__ import annotations
import os
import sys
import csv
import yaml
import argparse
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

DEFAULT_ACCOUNT = "Personal"
TRADING_NAV_DEFAULT = 1_000_000  # 假設總部位（用於相對倉位計算）


def _load_recommendations() -> dict:
    """載入 per_stock_recommendations.yaml。"""
    path = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _latest_close_and_change(sid: str) -> tuple:
    """從 adjusted CSV 取最新 close + 5日漲跌幅 + 20日 high。"""
    import pandas as pd
    path = os.path.join(BASE_DIR, "data", "adjusted", f"{sid}.csv")
    if not os.path.exists(path):
        return None, None, None, None
    try:
        df = pd.read_csv(path, parse_dates=["date"])
        if len(df) < 1:
            return None, None, None, None
        latest = float(df["close"].iloc[-1])
        latest_date = df["date"].iloc[-1].strftime("%Y-%m-%d")
        change_5d = None
        if len(df) >= 6:
            change_5d = float(df["close"].iloc[-1] / df["close"].iloc[-6] - 1)
        recent_20d_high = None
        if len(df) >= 20:
            recent_20d_high = float(df["close"].tail(20).max())
        return latest, latest_date, change_5d, recent_20d_high
    except Exception:
        return None, None, None, None


def _stock_label(sid: str) -> str:
    """從 watchlists 找名稱（refactored 後共用工具）。"""
    try:
        from src.strategy.auto_iterate.final_report import _stock_label as _f
        return _f(sid)
    except Exception:
        return sid


def make_recommendation(pos: dict, latest_price: float, rec: dict,
                        recent_20d_high: float | None,
                        nav: float = TRADING_NAV_DEFAULT) -> dict:
    """產出單檔建議。pos 含 stock_id, total_shares, avg_cost, market_value, pnl_pct。"""
    tier = rec.get("tier", "?") if rec else "?"
    rec_pos_pct = rec.get("position_pct_max", 0) if rec else 0
    template = rec.get("template") or rec.get("best_template", "—") if rec else "—"

    cur_pos_pct = (pos["market_value"] / nav) if nav > 0 else 0
    pnl_pct = pos["pnl_pct"]
    distance_from_20d_high = None
    if recent_20d_high and latest_price:
        distance_from_20d_high = latest_price / recent_20d_high - 1

    # ── 決策樹（順序重要，第一個 match 即停）────────────────────
    action = "HOLD"
    reason = ""

    # 1. F-tier → REDUCE
    if tier == "F":
        bnh_holdable = rec.get("bnh_holdable", False) if rec else False
        if bnh_holdable:
            action = "BNH_HOLD"
            reason = f"Tier F 但 BNH 評估可長持 (CAGR>0050)，維持但不加碼"
        else:
            action = "REDUCE"
            reason = f"Tier F：策略已證實不適合 TA，建議減碼或改純長持"

    # 2. 嚴重虧損 + 弱策略 → 停損
    elif pnl_pct < -15 and tier in ("C", "D"):
        action = "STOP_LOSS"
        reason = f"虧損 {pnl_pct:.1f}% AND Tier {tier} 弱策略 → 停損出場"

    # 3. 嚴重虧損 + 強策略 → 緊急停損（更寬限）
    elif pnl_pct < -25 and tier in ("S", "A", "B"):
        action = "STOP_LOSS"
        reason = f"虧損 {pnl_pct:.1f}% > 25% → 即使 Tier {tier} 也應停損"

    # 4. 弱策略大獲利 → 減碼
    elif pnl_pct > 30 and tier in ("C", "D"):
        action = "TAKE_PROFIT"
        reason = f"獲利 {pnl_pct:+.1f}% AND Tier {tier} 弱策略 → 落袋為安"

    # 5. 強策略過度獲利 → 適度減碼
    elif pnl_pct > 50 and tier in ("S", "A", "B"):
        action = "TRIM"
        reason = f"獲利 {pnl_pct:+.1f}% > 50% AND Tier {tier} → 適度減碼鎖利"

    # 6. 倉位過大
    elif rec_pos_pct > 0 and cur_pos_pct > rec_pos_pct * 1.5:
        action = "REDUCE"
        reason = (f"目前倉位 {cur_pos_pct*100:.1f}% > Tier {tier} 推薦上限 "
                  f"{rec_pos_pct*100:.0f}% × 1.5")

    # 7. 倉位偏小（< 推薦倉位的 30%）+ 強策略 → ADD
    elif (tier in ("S", "A", "B") and rec_pos_pct > 0 and
          cur_pos_pct < rec_pos_pct * 0.3):
        # 進階：可參考訊號（這裡簡化為 distance from 20d high 判斷）
        if distance_from_20d_high is not None and distance_from_20d_high < -0.05:
            action = "ADD"
            reason = (f"目前倉位 {cur_pos_pct*100:.2f}% < Tier {tier} 推薦 "
                      f"{rec_pos_pct*100:.0f}% × 30%；近 20 日高 {distance_from_20d_high*100:.1f}% (拉回中)")
        else:
            action = "HOLD"
            reason = (f"目前倉位 {cur_pos_pct*100:.2f}% 偏小，但 20 日內接近高點，等回檔再加碼")

    else:
        action = "HOLD"
        if tier in ("S", "A", "B"):
            reason = f"Tier {tier}，倉位適中，繼續持有"
        else:
            reason = f"Tier {tier}，無強訊號改變，繼續持有"

    return {
        "action": action,
        "reason": reason,
        "tier": tier,
        "template": template,
        "rec_pos_pct": rec_pos_pct,
        "cur_pos_pct": cur_pos_pct,
        "distance_from_20d_high": distance_from_20d_high,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--account", default=DEFAULT_ACCOUNT,
                   help=f"帳戶名稱（預設 {DEFAULT_ACCOUNT}）")
    p.add_argument("--nav", type=float, default=None,
                   help=f"總投資資金 NAV（用於計算相對倉位，預設 {TRADING_NAV_DEFAULT:,}）")
    args = p.parse_args()

    from src.ledger import load_trades, compute_open_positions, get_account_nav
    from collections import defaultdict

    trades_df = load_trades(args.account)
    if trades_df.empty:
        print(f"[ERR] 帳戶 {args.account} 沒有任何交易紀錄。")
        print(f"      先跑：python scripts/sync_positions_from_excel.py --account {args.account}")
        return

    raw_positions = compute_open_positions(trades_df)
    if not raw_positions:
        print(f"[i] 帳戶 {args.account} 目前無持倉。")
        return

    # 同一檔股票可能有多筆 lots → aggregate by stock_id
    agg: dict = defaultdict(lambda: {"shares": 0, "cost": 0.0})
    for p in raw_positions:
        sid = p["stock_id"]
        agg[sid]["shares"] += p["shares"]
        agg[sid]["cost"] += p["open_price"] * p["shares"]

    # 計算 NAV
    try:
        nav = args.nav or get_account_nav(args.account) or TRADING_NAV_DEFAULT
    except Exception:
        nav = TRADING_NAV_DEFAULT

    recs = _load_recommendations()

    # 為每檔 enrich
    rows = []
    for sid, info in agg.items():
        shares = info["shares"]
        avg_cost = info["cost"] / shares if shares > 0 else 0
        latest, latest_date, change_5d, high_20 = _latest_close_and_change(sid)
        if latest is None:
            # 沒有股價資料
            rows.append({
                "sid": sid, "name": _stock_label(sid),
                "shares": shares, "avg_cost": avg_cost,
                "latest": None, "latest_date": None,
                "market_value": shares * avg_cost,
                "pnl": 0, "pnl_pct": 0,
                "change_5d": None, "high_20": None,
                "tier": "?", "template": "—",
                "advice": {"action": "NO_DATA", "reason": "查無股價，請執行 fetch-adjusted"},
            })
            continue
        market_value = shares * latest
        pnl = market_value - shares * avg_cost
        pnl_pct = (latest / avg_cost - 1) * 100 if avg_cost > 0 else 0
        rec = recs.get(sid, {})
        pos_for_advice = {
            "stock_id": sid, "total_shares": shares,
            "avg_cost": avg_cost, "market_value": market_value,
            "pnl_pct": pnl_pct,
        }
        advice = make_recommendation(pos_for_advice, latest, rec, high_20, nav=nav)
        rows.append({
            "sid": sid, "name": _stock_label(sid),
            "shares": shares, "avg_cost": avg_cost,
            "latest": latest, "latest_date": latest_date,
            "market_value": market_value,
            "pnl": pnl, "pnl_pct": pnl_pct,
            "change_5d": change_5d, "high_20": high_20,
            "tier": rec.get("tier", "?") if rec else "?",
            "template": rec.get("template") or rec.get("best_template", "—") if rec else "—",
            "advice": advice,
        })

    # 排序：先按 action 緊急度，再按 PnL 大小
    action_priority = {
        "STOP_LOSS": 0, "REDUCE": 1, "TAKE_PROFIT": 2, "TRIM": 3,
        "ADD": 4, "BNH_HOLD": 5, "HOLD": 6, "NO_DATA": 9,
    }
    rows.sort(key=lambda r: (action_priority.get(r["advice"]["action"], 99),
                              -abs(r["pnl_pct"] or 0)))

    total_cost = sum(r["shares"] * r["avg_cost"] for r in rows)
    total_mv = sum(r["market_value"] for r in rows if r["latest"] is not None)
    total_pnl = total_mv - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

    # ── 輸出 markdown ──────────────────────────────────────
    out_md = os.path.join(BASE_DIR, "output", "reports", f"inventory_advice_{args.account}.md")
    os.makedirs(os.path.dirname(out_md), exist_ok=True)

    lines = []
    lines.append(f"# 庫存進出建議：{args.account}")
    lines.append(f"")
    lines.append(f"_自動產出 {date.today().strftime('%Y-%m-%d')}（依 per_stock_recommendations.yaml + 最新收盤價）_")
    lines.append(f"")
    lines.append(f"## 整體")
    lines.append(f"")
    lines.append(f"- 持倉數量：**{len(rows)} 檔**")
    lines.append(f"- 總成本：{total_cost:,.0f}")
    lines.append(f"- 市值：{total_mv:,.0f}")
    lines.append(f"- 總損益：**{total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)**")
    lines.append(f"")

    # 建議分類統計
    from collections import Counter
    action_counts = Counter(r["advice"]["action"] for r in rows)
    lines.append(f"## 建議統計")
    lines.append(f"")
    for action in ["STOP_LOSS", "REDUCE", "TAKE_PROFIT", "TRIM", "ADD", "BNH_HOLD", "HOLD", "NO_DATA"]:
        if action_counts.get(action, 0) > 0:
            emoji = {
                "STOP_LOSS": "🛑", "REDUCE": "⬇️", "TAKE_PROFIT": "💰",
                "TRIM": "✂️", "ADD": "➕", "BNH_HOLD": "💎",
                "HOLD": "✋", "NO_DATA": "❓",
            }.get(action, "")
            lines.append(f"- {emoji} **{action}**: {action_counts[action]} 檔")
    lines.append(f"")

    # 詳細表
    lines.append(f"## 個股建議")
    lines.append(f"")
    lines.append(f"| 股號 | 名稱 | Tier | 股數 | 均價 | 現價 | 損益% | 建議 | 原因 |")
    lines.append(f"|---|---|---|---:|---:|---:|---:|---|---|")
    for r in rows:
        sid = r["sid"]
        name = r["name"][:8]
        tier = r["tier"]
        shares = r["shares"]
        avg = r["avg_cost"]
        latest = r["latest"]
        pnl_pct = r["pnl_pct"]
        action = r["advice"]["action"]
        reason = r["advice"]["reason"]

        latest_s = f"{latest:.2f}" if latest else "—"
        pnl_s = f"{pnl_pct:+.1f}%" if latest else "—"
        lines.append(
            f"| {sid} | {name} | {tier} | {shares} | {avg:.2f} | {latest_s} | "
            f"{pnl_s} | **{action}** | {reason} |"
        )
    lines.append(f"")
    lines.append(f"## 說明")
    lines.append(f"")
    lines.append(f"建議邏輯（按優先順序）：")
    lines.append(f"")
    lines.append(f"1. **STOP_LOSS** 🛑 — 嚴重虧損（弱策略 < -15%，強策略 < -25%）")
    lines.append(f"2. **REDUCE** ⬇️ — Tier F 或 倉位過重")
    lines.append(f"3. **TAKE_PROFIT** 💰 — 弱策略大幅獲利 > 30%（落袋為安）")
    lines.append(f"4. **TRIM** ✂️ — 強策略過度獲利 > 50%（適度減碼）")
    lines.append(f"5. **ADD** ➕ — 倉位過小且 Tier S/A/B 拉回中")
    lines.append(f"6. **BNH_HOLD** 💎 — Tier F 但 BNH 可長持")
    lines.append(f"7. **HOLD** ✋ — 維持")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  寫入 {out_md}")

    # ── 輸出 CSV ──
    out_csv = os.path.join(BASE_DIR, "output", "reports", f"inventory_advice_{args.account}.csv")
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sid", "name", "tier", "template", "shares", "avg_cost",
                          "latest_price", "latest_date", "market_value",
                          "pnl", "pnl_pct", "change_5d", "high_20d",
                          "advice", "reason"])
        for r in rows:
            writer.writerow([
                r["sid"], r["name"], r["tier"], r["template"], r["shares"],
                round(r["avg_cost"], 2), r["latest"], r["latest_date"],
                round(r["market_value"], 0) if r["latest"] else None,
                round(r["pnl"], 0) if r["latest"] else None,
                round(r["pnl_pct"], 2) if r["latest"] else None,
                round(r["change_5d"]*100, 2) if r["change_5d"] is not None else None,
                round(r["high_20"], 2) if r["high_20"] else None,
                r["advice"]["action"], r["advice"]["reason"],
            ])
    print(f"  寫入 {out_csv}")

    # 終端摘要
    print(f"\n  總損益: {total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)")
    for action in ["STOP_LOSS", "REDUCE", "TAKE_PROFIT", "TRIM", "ADD", "BNH_HOLD", "HOLD"]:
        c = action_counts.get(action, 0)
        if c > 0:
            print(f"  {action}: {c} 檔")


if __name__ == "__main__":
    main()
