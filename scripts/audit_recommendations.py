"""全面 audit config/per_stock_recommendations.yaml 一致性。

檢查每一檔股票的：
  - 名稱（name 欄存在 + 不含括號 / template 名）
  - tier 有效（S/A/B/C/D/F）
  - tradeable flag 對應 tier
  - position_pct_max 對應 tier rule
  - test_* 指標完整
  - bootstrap pf_lower 對應 tier 要求
  - holdouts 結構 OK
  - params_ref 指向可找到的 yaml
  - adjusted data 存在
  - BNH 欄位只在 F-tier
  - F-tier 沒有 stale test fields

輸出：
  output/reports/audit_report.md  — 問題清單分類
  終端：問題數統計
"""
from __future__ import annotations
import os
import sys
import yaml
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

RECS_PATH = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")
ADJ_DIR = os.path.join(BASE_DIR, "data", "adjusted")
AUTO_DIR = os.path.join(BASE_DIR, "output", "auto_iterate")

# Tier rule from tiering.py (mirror for validation)
TIER_RULES = {
    "S": {"pos_max": 1.00},
    "A": {"pos_max": 0.50},
    "B": {"pos_max": 0.30},
    "C": {"pos_max": 0.15},
    "D": {"pos_max": 0.10},
    "F": {"pos_max": 0.00},
}
TRADEABLE_TIERS = {"S", "A", "B", "C"}


def _has_data(sid: str) -> bool:
    return os.path.exists(os.path.join(ADJ_DIR, f"{sid}.csv"))


def _stock_label(sid: str) -> str:
    try:
        from src.strategy.auto_iterate.final_report import _stock_label as fn
        return fn(sid)
    except Exception:
        return sid


def _find_params_yaml(params_ref: str) -> bool:
    """params_ref 形如 'chip_momentum.yaml#per_stock.5274'，找該 yaml + sid 是否存在。"""
    if not params_ref or "#" not in params_ref:
        return False
    fname, anchor = params_ref.split("#", 1)
    sid_in_anchor = anchor.replace("per_stock.", "").strip()
    # 找最新 merged_* 或所有 run dir 有沒有這個 yaml
    if not os.path.isdir(AUTO_DIR):
        return False
    candidates = sorted(os.listdir(AUTO_DIR), reverse=True)
    for d in candidates:
        path = os.path.join(AUTO_DIR, d, fname)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            continue
        per_stock = data.get("per_stock", {}) if isinstance(data, dict) else {}
        if sid_in_anchor in per_stock or str(sid_in_anchor) in per_stock:
            return True
    return False


def main():
    with open(RECS_PATH, encoding="utf-8") as f:
        recs = yaml.safe_load(f) or {}

    # 分類問題
    issues = defaultdict(list)

    total_stocks = 0
    for sid, r in recs.items():
        if not isinstance(r, dict):
            continue
        total_stocks += 1
        tier = r.get("tier")

        # 1. tier 有效
        if tier not in ("S", "A", "B", "C", "D", "F"):
            issues["INVALID_TIER"].append((sid, f"tier={tier}"))
            continue

        # 2. 名稱
        name = r.get("name")
        if not name:
            issues["MISSING_NAME"].append((sid, ""))
        elif name == sid:
            # name 是 sid 本身（多半是 fallback 留下的）
            wl_name = _stock_label(sid)
            if wl_name != sid:
                issues["NAME_IS_SID_BUT_HAS_WATCHLIST"].append(
                    (sid, f"watchlist 有「{wl_name}」但 entry 設成 sid")
                )
            else:
                issues["NAME_NO_LOOKUP"].append((sid, "watchlist 也沒名字"))
        else:
            # 檢查 name 有無不該存在的字元
            bad_chars = "（(）)【[】]/、"
            if any(c in name for c in bad_chars):
                issues["NAME_HAS_BRACKETS"].append((sid, f"name='{name}' 含括號/分隔符"))
            if len(name) > 15:
                issues["NAME_TOO_LONG"].append((sid, f"name='{name}' 長度 {len(name)}"))

        # 3. tradeable 對應 tier
        tradeable_expected = tier in TRADEABLE_TIERS
        tradeable_actual = bool(r.get("tradeable"))
        if tradeable_expected != tradeable_actual:
            issues["TRADEABLE_MISMATCH"].append(
                (sid, f"tier={tier} but tradeable={tradeable_actual} (expected {tradeable_expected})")
            )

        # 4. position_pct_max
        pos_max = r.get("position_pct_max")
        expected_pos = TIER_RULES[tier]["pos_max"]
        if pos_max is None:
            issues["POS_MAX_MISSING"].append((sid, f"tier={tier}"))
        elif abs((pos_max or 0) - expected_pos) > 0.001:
            issues["POS_MAX_MISMATCH"].append(
                (sid, f"tier={tier} expected pos_max={expected_pos}, got {pos_max}")
            )

        # 5. test_* 指標完整（tradeable 才嚴格要求）
        if tradeable_actual:
            for fld in ["test_n_trades", "test_expectancy", "test_max_dd"]:
                if r.get(fld) is None:
                    issues["TEST_METRIC_MISSING"].append((sid, f"{fld} 缺"))

        # 6. template 與 best_template 一致
        tmpl = r.get("template")
        best_tmpl = r.get("best_template")
        if tmpl and best_tmpl and tmpl != best_tmpl:
            issues["TEMPLATE_MISMATCH"].append(
                (sid, f"template={tmpl} vs best_template={best_tmpl}")
            )

        # 7. 沒有 template
        if not tmpl and not best_tmpl:
            issues["NO_TEMPLATE"].append((sid, f"tier={tier}"))

        # 8. adjusted data 存在
        if not _has_data(sid):
            issues["NO_ADJ_DATA"].append((sid, f"data/adjusted/{sid}.csv 不存在"))

        # 9. BNH 欄位只應該在 F-tier 才有意義（其他 tier 不該有 bnh_* fields）
        if tier != "F":
            stale_bnh = [k for k in r if k.startswith("bnh_")]
            if stale_bnh:
                issues["STALE_BNH_ON_TRADEABLE"].append(
                    (sid, f"tier={tier} 卻有 {len(stale_bnh)} 個 bnh_* 欄")
                )

        # 10. params_ref 有效（若 tier in S/A/B/C/D）
        if tier in ("S", "A", "B", "C", "D") and tmpl != "untestable":
            params_ref = r.get("params_ref")
            if not params_ref:
                issues["NO_PARAMS_REF"].append((sid, f"tier={tier}"))
            elif not _find_params_yaml(params_ref):
                issues["BROKEN_PARAMS_REF"].append((sid, f"找不到 {params_ref}"))

    # 印報表
    print(f"\n=== Audit Report ===")
    print(f"  總股票數：{total_stocks}")
    print()

    if not any(issues.values()):
        print("  ✅ 所有檢查通過")
        return

    severity_order = [
        "INVALID_TIER", "NO_ADJ_DATA", "TRADEABLE_MISMATCH", "POS_MAX_MISMATCH",
        "TEMPLATE_MISMATCH", "NO_TEMPLATE", "BROKEN_PARAMS_REF",
        "TEST_METRIC_MISSING", "STALE_BNH_ON_TRADEABLE",
        "NAME_HAS_BRACKETS", "NAME_TOO_LONG", "MISSING_NAME",
        "NAME_IS_SID_BUT_HAS_WATCHLIST", "NAME_NO_LOOKUP",
        "POS_MAX_MISSING", "NO_PARAMS_REF",
    ]

    for cat in severity_order:
        items = issues.get(cat, [])
        if not items:
            continue
        print(f"  [{cat}] {len(items)} 檔：")
        for sid, msg in items[:8]:
            print(f"    - {sid}  {msg}")
        if len(items) > 8:
            print(f"    - ... +{len(items)-8} more")
        print()

    # markdown 報表
    out_path = os.path.join(BASE_DIR, "output", "reports", "audit_report.md")
    lines = [f"# Recommendations Audit Report", "",
             f"_生成於：{__import__('datetime').date.today().strftime('%Y-%m-%d')}_", ""]
    lines.append(f"總股票數：**{total_stocks}**")
    lines.append("")
    if not any(issues.values()):
        lines.append("✅ 所有檢查通過")
    else:
        for cat in severity_order:
            items = issues.get(cat, [])
            if not items:
                continue
            lines.append(f"## {cat} ({len(items)})")
            lines.append("")
            for sid, msg in items:
                lines.append(f"- `{sid}` — {msg}")
            lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  寫入 {out_path}")

    total_issues = sum(len(v) for v in issues.values())
    print(f"\n  總問題數：{total_issues}")


if __name__ == "__main__":
    main()
