"""Rebuild per_stock_best.yaml from per-template yamls in an auto_iterate run dir.

Use case: when multiple auto_iterate processes shared a single run dir (due to
the 1-second precision in run_id timestamps), the LAST process to finalize
will have overwritten per_stock_best.yaml with only its own template's data.
This script re-scans all template yamls in the dir and rebuilds a unified
per_stock_best.yaml that contains the BEST template per stock across all
templates present.

Usage:
  python scripts/rebuild_per_stock_best.py <run_dir_1> [run_dir_2 ...]

Where run_dir_N is a short id under output/auto_iterate/.
"""
from __future__ import annotations
import os
import sys
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTO_ITER_DIR = os.path.join(BASE_DIR, "output", "auto_iterate")

TIER_ORDER = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


def load_template_yaml(path: str) -> dict:
    """Load a single template yaml → {sid: result_dict}"""
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f) or {}
    return d.get("per_stock", {}) or {}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for run_id in sys.argv[1:]:
        run_path = os.path.join(AUTO_ITER_DIR, run_id)
        if not os.path.isdir(run_path):
            print(f"  [!] {run_id}: dir not found")
            continue

        template_files = [
            fn for fn in os.listdir(run_path)
            if fn.endswith(".yaml") and fn != "per_stock_best.yaml"
        ]
        print(f"\n== {run_id} ==")
        print(f"  Found {len(template_files)} template yamls: {template_files}")

        # For each (sid, template), capture the result; track best per sid.
        per_sid: dict = {}  # sid -> (template_name, result_dict)
        for fn in template_files:
            template = fn[:-5]
            data = load_template_yaml(os.path.join(run_path, fn))
            for sid, e in data.items():
                if not isinstance(e, dict):
                    continue
                tier = e.get("tier", "F")
                pf = e.get("test_pf") or 0
                exp = e.get("test_expectancy") or 0
                score = (TIER_ORDER.get(tier, 0), pf, exp)
                cur = per_sid.get(sid)
                if cur is None or score > cur[0]:
                    per_sid[sid] = (score, template, e)

        # Read the existing per_stock_best.yaml to get benchmark_0050_test_cagr etc.
        psb_path = os.path.join(run_path, "per_stock_best.yaml")
        existing = {}
        if os.path.exists(psb_path):
            with open(psb_path, encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}

        # Build new per_stock_best dict
        out = {}
        # Preserve benchmark key if present
        if "benchmark_0050_test_cagr" in existing:
            out["benchmark_0050_test_cagr"] = existing["benchmark_0050_test_cagr"]

        for sid, (score, template, e) in per_sid.items():
            # Match the structure expected by apply_retrain_upgrades / final_report
            entry = dict(e)
            entry["best_template"] = template
            # Preserve other fields as-is
            out[sid] = entry

        # Write back
        with open(psb_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(out, f, allow_unicode=True, sort_keys=True)

        tier_dist = {}
        for sid, e in out.items():
            if isinstance(e, dict) and "tier" in e:
                t = e["tier"]
                tier_dist[t] = tier_dist.get(t, 0) + 1
        total = sum(tier_dist.values())
        print(f"  Wrote {psb_path}: {total} stocks, tiers={dict(sorted(tier_dist.items()))}")


if __name__ == "__main__":
    main()
