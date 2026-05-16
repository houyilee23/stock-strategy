"""Re-apply latest tiering rules to per_stock_best.yaml in auto_iterate run dirs.

Use case: after editing tiering.py with new rescue rules, re-tier the stored
per_stock_best.yaml entries (which have full bootstrap + holdouts data) so
apply_retrain_upgrades.py picks up the upgraded tiers.

Usage:
  python scripts/retier_run_dir.py <run_dir_1> [run_dir_2 ...]

Each per_stock_best.yaml entry is updated in place. Entries without bootstrap
or holdouts data are skipped.
"""
from __future__ import annotations
import os
import sys
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.strategy.auto_iterate.tiering import assign_tier, TIER_RULES  # noqa: E402

AUTO_ITER_DIR = os.path.join(BASE_DIR, "output", "auto_iterate")
TIER_ORDER = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for run_id in sys.argv[1:]:
        psb_path = os.path.join(AUTO_ITER_DIR, run_id, "per_stock_best.yaml")
        if not os.path.exists(psb_path):
            print(f"  [!] {run_id}: per_stock_best.yaml not found")
            continue
        with open(psb_path, encoding="utf-8") as f:
            psb = yaml.safe_load(f) or {}

        changes = []
        for sid, e in psb.items():
            if not isinstance(e, dict):
                continue
            test = e.get("test")
            if not isinstance(test, dict):
                # Some psb formats keep test_* flat
                n = e.get("test_n_trades")
                exp = e.get("test_expectancy")
                pf = e.get("test_pf")
                dd = e.get("test_max_dd")
            else:
                n = test.get("n_trades")
                exp = test.get("expectancy")
                pf = test.get("profit_factor")
                dd = test.get("max_drawdown")
            boot = e.get("bootstrap")
            holdouts = e.get("holdouts") or {}
            if n is None or exp is None:
                continue
            # pf=None typically means all winning trades (avg_loss=0 → PF=inf
            # but YAML can't serialize inf → reads back as None). Treat as inf
            # so Q5b-lite / C_HIGH_Q / D_LOW_N rescues can fire.
            if pf is None:
                import math as _math
                pf = _math.inf
            # If boot is None / missing pf_lower → use empty dict (assign_tier
            # normalizes to 0.0). Q5b-lite / C_HIGH_Q / D_LOW_N rescues use
            # raw_pf, not pf_lower, so they still work.
            if not isinstance(boot, dict):
                boot = {}
            old_tier = e.get("tier", "F")
            test_metrics = {
                "n_trades": n, "expectancy": exp,
                "profit_factor": pf, "max_drawdown": dd,
            }
            new_tier, new_reason = assign_tier(test_metrics, boot, holdouts)
            if new_tier != old_tier:
                changes.append((sid, old_tier, new_tier))
                e["tier"] = new_tier
                e["tier_reason"] = new_reason
                e["position_pct_recommended"] = TIER_RULES.get(new_tier, {}).get("pos_max", 0.0)

        if changes:
            with open(psb_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(psb, f, allow_unicode=True, sort_keys=True)
            ups = [(s,o,n) for s,o,n in changes if TIER_ORDER.get(n,0) > TIER_ORDER.get(o,0)]
            downs = [(s,o,n) for s,o,n in changes if TIER_ORDER.get(n,0) < TIER_ORDER.get(o,0)]
            print(f"  {run_id}: {len(ups)} upgrades, {len(downs)} downgrades")
            for sid, ot, nt in ups:
                print(f"    UP   {sid}: {ot} -> {nt}")
            for sid, ot, nt in downs:
                print(f"    DOWN {sid}: {ot} -> {nt}")
        else:
            print(f"  {run_id}: no changes")


if __name__ == "__main__":
    main()
