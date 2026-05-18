"""Normalize per_stock_recommendations.yaml 統一兩種格式：

過去 entries 來自 2 種來源：
  (a) write_recommendations() 寫入的「舊格式」：name + tradeable + position_pct_max
  (b) apply_retrain_upgrades() 寫入的「升級格式」：直接複製 per_stock_best.yaml
      含 best_template / bootstrap / holdouts / position_pct_recommended，但
      缺 tradeable flag 和 position_pct_max

統一規則：
  - position_pct_max = position_pct_recommended (若兩者都缺則依 tier 推算)
  - tradeable = tier in (S, A, B, C)
  - template = best_template (若 template 缺)
  - name = _stock_label(sid) (若缺或 name == sid)
  - 移除 metadata key 'borderline_candidates'
"""
import os
import sys
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

RECS_PATH = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")

TIER_POS_MAX = {"S": 1.00, "A": 0.50, "B": 0.30, "C": 0.15, "D": 0.10, "F": 0.00}
TRADEABLE_TIERS = {"S", "A", "B", "C"}


def main():
    from src.strategy.auto_iterate.final_report import _stock_label

    # Preserve header
    header_lines = []
    with open(RECS_PATH, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                header_lines.append(line)
            else:
                break
    with open(RECS_PATH, encoding="utf-8") as f:
        recs = yaml.safe_load(f) or {}

    fixes = {
        "pos_max_added": 0,
        "tradeable_added": 0,
        "tradeable_corrected": 0,
        "template_synced": 0,
        "name_fixed": 0,
        "metadata_removed": 0,
    }

    # Remove metadata key
    if "borderline_candidates" in recs:
        del recs["borderline_candidates"]
        fixes["metadata_removed"] += 1

    for sid, r in recs.items():
        if not isinstance(r, dict):
            continue
        tier = r.get("tier")
        if tier not in TIER_POS_MAX:
            continue

        # 1. position_pct_max
        if r.get("position_pct_max") is None:
            pos = r.get("position_pct_recommended")
            if pos is None:
                pos = TIER_POS_MAX[tier]
            r["position_pct_max"] = pos
            fixes["pos_max_added"] += 1

        # 2. tradeable
        expected_tradeable = tier in TRADEABLE_TIERS
        if r.get("tradeable") is None:
            r["tradeable"] = expected_tradeable
            fixes["tradeable_added"] += 1
        elif r.get("tradeable") != expected_tradeable:
            r["tradeable"] = expected_tradeable
            fixes["tradeable_corrected"] += 1

        # 3. template = best_template
        if not r.get("template") and r.get("best_template"):
            r["template"] = r["best_template"]
            fixes["template_synced"] += 1

        # 4. name
        cur_name = r.get("name")
        if not cur_name or cur_name == sid:
            wl_name = _stock_label(sid)
            if wl_name and wl_name != sid:
                r["name"] = wl_name
                fixes["name_fixed"] += 1

    # Write back
    phase_tag = "# Normalized format (2026-05-18): unified tradeable + position_pct_max + name\n"
    if header_lines:
        header_lines[0] = phase_tag
    else:
        header_lines = [phase_tag]

    with open(RECS_PATH, "w", encoding="utf-8") as f:
        f.writelines(header_lines)
        yaml.dump(recs, f, allow_unicode=True, default_flow_style=False, sort_keys=True)

    print(f"  Normalized {RECS_PATH}")
    print(f"  Total stocks: {sum(1 for v in recs.values() if isinstance(v, dict))}")
    for k, v in fixes.items():
        if v > 0:
            print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
