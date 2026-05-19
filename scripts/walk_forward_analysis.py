"""Phase B 完成後：跨 fold robustness 分析。

掃描最近 3 個 fold 的 per_stock_best.yaml，對每檔 stock 算：
  fold1_tier, fold2_tier, fold3_tier
  robust_score: PASS 個數 + tier 加權
  label: "穩定強" / "次穩" / "lucky" / "不適合"

輸出 docs/training_log/<date>_walk_forward.md
"""
from __future__ import annotations
import os, sys, yaml
from datetime import date
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_fold_runs() -> list[tuple[str, str]]:
    """找最新 3 個 fold 的 run dir。靠 INDEX.csv 找符合 train period 的。"""
    import csv
    idx_path = os.path.join(BASE_DIR, "output", "auto_iterate", "INDEX.csv")
    if not os.path.exists(idx_path):
        return []
    with open(idx_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    fold_periods = [
        ("fold1", "2010-01-01", "2014-12-31", "2015-01-01", "2017-12-31"),
        ("fold2", "2010-01-01", "2017-12-31", "2018-01-01", "2020-12-31"),
        ("fold3", "2010-01-01", "2020-12-31", "2021-01-01", "2023-12-31"),
    ]

    out = []
    for name, ts, te, vs, ve in fold_periods:
        matched = [r for r in rows
                   if r["train_start"] == ts and r["train_end"] == te
                   and r["test_start"] == vs and r["test_end"] == ve]
        if matched:
            # 取最新一筆
            latest = sorted(matched, key=lambda r: r["started_at"], reverse=True)[0]
            out.append((name, latest["run_id"]))
    return out


def main():
    folds = find_fold_runs()
    if len(folds) < 3:
        print(f"找到 {len(folds)} 個 fold，需要 3 個，先 skip 報告")
        return

    # 載入每 fold 的 per_stock_best
    stock_results = defaultdict(dict)  # sid -> {fold_name: {tier, cagr, ...}}
    for fold_name, run_id in folds:
        psb_path = os.path.join(BASE_DIR, "output", "auto_iterate", run_id, "per_stock_best.yaml")
        if not os.path.exists(psb_path):
            continue
        with open(psb_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for sid, info in data.items():
            if isinstance(info, dict):
                stock_results[sid][fold_name] = info

    # 計算 robust_score
    TIER_SCORE = {"S":3,"A":2,"B":1,"C":0,"D":-1,"F":-3}
    classified = defaultdict(list)
    for sid, folds_data in stock_results.items():
        scores = []
        tiers = []
        for fname in ("fold1","fold2","fold3"):
            info = folds_data.get(fname, {})
            t = info.get("tier", "?")
            tiers.append(t)
            scores.append(TIER_SCORE.get(t, -5))
        total = sum(scores)
        # 分類
        sab_count = sum(1 for t in tiers if t in ("S","A","B"))
        if sab_count >= 3:
            label = "穩定強 (3 fold 都 S/A/B)"
        elif sab_count == 2:
            label = "次穩 (2 fold S/A/B)"
        elif sab_count == 1:
            label = "Lucky 警告 (僅 1 fold S/A/B)"
        else:
            label = "不適合 TA (全 C/D/F)"
        classified[label].append((sid, tiers, total, folds_data))

    # 寫 markdown
    out_path = os.path.join(BASE_DIR, "docs", "training_log",
                            f"{date.today()}_walk_forward.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    lines = []
    lines.append(f"# Walk-forward 跨 fold robustness 分析（{date.today()}）")
    lines.append("")
    lines.append("Fold 設定：")
    for fname, run_id in folds:
        lines.append(f"  - **{fname}** run_id = `{run_id}`")
    lines.append("")
    lines.append("## 個股穩定度分類")
    lines.append("")
    for label in ["穩定強 (3 fold 都 S/A/B)", "次穩 (2 fold S/A/B)",
                  "Lucky 警告 (僅 1 fold S/A/B)", "不適合 TA (全 C/D/F)"]:
        rows = classified.get(label, [])
        if not rows: continue
        lines.append(f"### {label} — {len(rows)} 檔\n")
        lines.append("| SID | fold1 | fold2 | fold3 | score |")
        lines.append("|---|---|---|---|---:|")
        rows.sort(key=lambda r: -r[2])
        for sid, tiers, total, _ in rows[:30]:
            lines.append(f"| {sid} | {tiers[0]} | {tiers[1]} | {tiers[2]} | {total} |")
        if len(rows) > 30:
            lines.append(f"\n... 還有 {len(rows)-30} 檔，詳見 CSV\n")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✓ 寫入 {out_path}")


if __name__ == "__main__":
    main()
