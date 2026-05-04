"""比對兩份 per_stock_recommendations.yaml — 例如 retrain 前後

用法：
  python scripts/compare_recommendations.py
    → 預設比對 archive/per_stock_recommendations_2017train.yaml vs config/per_stock_recommendations.yaml

  python scripts/compare_recommendations.py <old.yaml> <new.yaml>

輸出：
  - 終端 summary
  - output/recommendations_diff_{YYYY-MM-DD}.md
"""
import os
import sys
import yaml
import argparse
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_OLD = os.path.join(BASE_DIR, "archive", "per_stock_recommendations_2017train.yaml")
DEFAULT_NEW = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")

TIER_ORDER = ["S", "A", "B", "C", "D", "F"]


def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return {}
    return {sid: rec for sid, rec in data.items() if isinstance(rec, dict)}


def tier_delta(old: str | None, new: str | None) -> str:
    if old == new:
        return "—"
    if old is None:
        return f"NEW→{new}"
    if new is None:
        return f"{old}→DROP"
    try:
        oi = TIER_ORDER.index(old)
        ni = TIER_ORDER.index(new)
        arrow = "↑" if ni < oi else "↓"
        return f"{old}{arrow}{new}"
    except ValueError:
        return f"{old}→{new}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old", nargs="?", default=DEFAULT_OLD)
    ap.add_argument("new", nargs="?", default=DEFAULT_NEW)
    args = ap.parse_args()

    if not os.path.exists(args.old):
        print(f"[錯誤] 找不到 OLD：{args.old}")
        return
    if not os.path.exists(args.new):
        print(f"[錯誤] 找不到 NEW：{args.new}")
        return

    old = load_yaml(args.old)
    new = load_yaml(args.new)

    sids_all = sorted(set(old.keys()) | set(new.keys()))
    sids_only_old = sorted(set(old.keys()) - set(new.keys()))
    sids_only_new = sorted(set(new.keys()) - set(old.keys()))
    sids_both = sorted(set(old.keys()) & set(new.keys()))

    tier_changes = []
    template_changes = []
    tradeable_changes = []
    bnh_changes = []

    for sid in sids_both:
        o, n = old[sid], new[sid]
        if o.get("tier") != n.get("tier"):
            tier_changes.append((sid, o.get("name", sid), o.get("tier"), n.get("tier")))
        if o.get("template") != n.get("template"):
            template_changes.append((sid, o.get("name", sid), o.get("template"), n.get("template")))
        if bool(o.get("tradeable")) != bool(n.get("tradeable")):
            tradeable_changes.append((sid, o.get("name", sid), o.get("tradeable"), n.get("tradeable")))
        if o.get("bnh_tier") != n.get("bnh_tier"):
            bnh_changes.append((sid, o.get("name", sid), o.get("bnh_tier"), n.get("bnh_tier")))

    # Tier 分佈
    def tier_dist(d):
        from collections import Counter
        return Counter(rec.get("tier", "—") for rec in d.values())
    old_dist = tier_dist(old)
    new_dist = tier_dist(new)

    # 寫 markdown
    today = date.today().strftime("%Y-%m-%d")
    L = []
    L.append(f"# Recommendations Diff — {today}")
    L.append("")
    L.append(f"OLD: `{os.path.relpath(args.old, BASE_DIR)}`")
    L.append(f"NEW: `{os.path.relpath(args.new, BASE_DIR)}`")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(f"- 總股票：OLD {len(old)} / NEW {len(new)} / 共 {len(sids_both)} 檔出現在兩邊")
    L.append(f"- 只在 OLD：{len(sids_only_old)}")
    L.append(f"- 只在 NEW：{len(sids_only_new)}")
    L.append(f"- **Tier 改變**：{len(tier_changes)} 檔")
    L.append(f"- **Template 改變**：{len(template_changes)} 檔")
    L.append(f"- **Tradeable 翻轉**：{len(tradeable_changes)} 檔")
    L.append(f"- **BNH Tier 改變**：{len(bnh_changes)} 檔")
    L.append("")

    L.append("## Tier 分佈")
    L.append("")
    L.append("| Tier | OLD | NEW | Δ |")
    L.append("|---|---|---|---|")
    for t in TIER_ORDER + ["—"]:
        o = old_dist.get(t, 0)
        n = new_dist.get(t, 0)
        if o or n:
            d = n - o
            sign = f"+{d}" if d > 0 else (f"{d}" if d < 0 else "—")
            L.append(f"| {t} | {o} | {n} | {sign} |")
    L.append("")

    if tier_changes:
        L.append("## Tier 變動清單")
        L.append("")
        L.append("| 股票 | 名稱 | OLD Tier | NEW Tier | 方向 |")
        L.append("|---|---|---|---|---|")
        # Sort: 升級在前，降級在後
        def tier_idx(t):
            try:
                return TIER_ORDER.index(t)
            except (ValueError, TypeError):
                return 99
        tier_changes.sort(key=lambda x: tier_idx(x[3]) - tier_idx(x[2]))
        for sid, name, ot, nt in tier_changes:
            L.append(f"| {sid} | {name} | {ot or '—'} | {nt or '—'} | {tier_delta(ot, nt)} |")
        L.append("")

    if template_changes:
        L.append("## Template 變動清單")
        L.append("")
        L.append("| 股票 | 名稱 | OLD Template | NEW Template |")
        L.append("|---|---|---|---|")
        for sid, name, ot, nt in sorted(template_changes):
            L.append(f"| {sid} | {name} | {ot or '—'} | {nt or '—'} |")
        L.append("")

    if tradeable_changes:
        L.append("## Tradeable 翻轉")
        L.append("")
        L.append("| 股票 | 名稱 | OLD | NEW |")
        L.append("|---|---|---|---|")
        for sid, name, ot, nt in sorted(tradeable_changes):
            L.append(f"| {sid} | {name} | {ot} | {nt} |")
        L.append("")

    if sids_only_new:
        L.append("## 只在 NEW（新增）")
        L.append("")
        L.append(", ".join(sids_only_new))
        L.append("")
    if sids_only_old:
        L.append("## 只在 OLD（消失）")
        L.append("")
        L.append(", ".join(sids_only_old))
        L.append("")

    out_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"recommendations_diff_{today}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # 終端輸出
    print("=" * 60)
    print(f"OLD: {os.path.relpath(args.old, BASE_DIR)}")
    print(f"NEW: {os.path.relpath(args.new, BASE_DIR)}")
    print("=" * 60)
    print(f"Tier 改變      ：{len(tier_changes)} 檔")
    print(f"Template 改變  ：{len(template_changes)} 檔")
    print(f"Tradeable 翻轉 ：{len(tradeable_changes)} 檔")
    print(f"BNH Tier 改變  ：{len(bnh_changes)} 檔")
    print(f"只在 OLD       ：{len(sids_only_old)}")
    print(f"只在 NEW       ：{len(sids_only_new)}")
    print()
    print(f"Tier 分佈：")
    for t in TIER_ORDER + ["—"]:
        o = old_dist.get(t, 0)
        n = new_dist.get(t, 0)
        if o or n:
            d = n - o
            sign = f"+{d}" if d > 0 else (f"{d}" if d < 0 else " ")
            print(f"  {t}: {o:>3} → {n:>3}  ({sign})")
    print()
    print(f"完整報告寫入：{out_path}")


if __name__ == "__main__":
    main()
