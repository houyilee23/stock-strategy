"""Re-apply current tiering rules to config/per_stock_recommendations.yaml.

Use after editing src/strategy/auto_iterate/tiering.py to back-fill new rule
changes onto previously computed results — much faster than full re-retrain.

This script reads each stock's stored test metrics + bootstrap + holdouts and
re-runs `assign_tier()`. If the new tier differs, the entry is updated. F-tier
stocks getting upgraded keep their BNH fields stripped; tradeable stocks
getting their tier changed keep all other fields untouched.

Usage:
  python scripts/retier_recommendations.py

After running:
  python main.py signals --list Takeshi/Katie/universe
  python scripts/build_per_stock_reports.py
  python scripts/update_readme.py
  python scripts/build_html.py
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

RECS_PATH = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")

TIER_ORDER = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


def main():
    with open(RECS_PATH, encoding="utf-8") as f:
        # Preserve header
        header_lines = []
        for line in f:
            if line.startswith("#"):
                header_lines.append(line)
            else:
                break
    with open(RECS_PATH, encoding="utf-8") as f:
        recs = yaml.safe_load(f) or {}

    changes = []  # (sid, old, new, reason)
    skipped = []  # entries without enough data

    for sid, r in recs.items():
        if not isinstance(r, dict):
            continue
        # Need test metrics
        n = r.get("test_n_trades")
        exp = r.get("test_expectancy")
        pf = r.get("test_pf")
        dd = r.get("test_max_dd")
        boot = r.get("bootstrap")
        holdouts = r.get("holdouts")
        if n is None or exp is None:
            skipped.append((sid, r.get("tier", "?"), "missing test metrics"))
            continue
        # CRITICAL: skip entries without bootstrap data (older entries that
        # used the simplified write_recommendations format only have
        # tier/template/test_*; no bootstrap means we'd compute pf_lower=0
        # and downgrade them spuriously). Their stored tier is the source of
        # truth from when they were originally tiered.
        if not isinstance(boot, dict) or boot.get("pf_lower") is None:
            skipped.append((sid, r.get("tier", "?"), "no bootstrap in entry"))
            continue
        if not isinstance(holdouts, dict):
            holdouts = {}

        test_metrics = {
            "n_trades": n,
            "expectancy": exp,
            "profit_factor": pf,
            "max_drawdown": dd,
        }
        new_tier, new_reason = assign_tier(test_metrics, boot, holdouts)
        old_tier = r.get("tier", "F")

        if new_tier != old_tier:
            changes.append((sid, old_tier, new_tier, new_reason))
            # Update the entry
            r["tier"] = new_tier
            r["tier_reason"] = new_reason
            r["position_pct_max"] = TIER_RULES.get(new_tier, {}).get("pos_max", 0.0)
            r["position_pct_recommended"] = TIER_RULES.get(new_tier, {}).get("pos_max", 0.0)
            r["tradeable"] = new_tier in ("S", "A", "B", "C")

    # Print summary
    print(f"  Total stocks reviewed: {sum(1 for v in recs.values() if isinstance(v,dict))}")
    print(f"  Tier changes: {len(changes)}")
    print(f"  Skipped (missing data): {len(skipped)}")
    print()

    if changes:
        upgrades = [(s,o,n,r) for s,o,n,r in changes
                    if TIER_ORDER.get(n,0) > TIER_ORDER.get(o,0)]
        downgrades = [(s,o,n,r) for s,o,n,r in changes
                      if TIER_ORDER.get(n,0) < TIER_ORDER.get(o,0)]
        print(f"  Upgrades ({len(upgrades)}):")
        for sid, ot, nt, reason in upgrades:
            print(f"    {sid}: {ot} -> {nt}  // {reason[:80]}")
        print()
        if downgrades:
            print(f"  Downgrades ({len(downgrades)}):")
            for sid, ot, nt, reason in downgrades:
                print(f"    {sid}: {ot} -> {nt}  // {reason[:80]}")

    # Write back
    if changes:
        # Update header
        phase_tag = "# Re-tiered after tiering.py rules update\n"
        if header_lines:
            header_lines[0] = phase_tag
        else:
            header_lines = [phase_tag]
        with open(RECS_PATH, "w", encoding="utf-8") as f:
            f.writelines(header_lines)
            yaml.dump(recs, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
        print(f"\n  Wrote {RECS_PATH}")

    # Final tier dist
    tier_counts = {}
    for sid, r in recs.items():
        if isinstance(r, dict):
            t = r.get("tier", "None")
            tier_counts[t] = tier_counts.get(t, 0) + 1
    total = sum(tier_counts.values())
    print(f"\n  Tier dist ({total} stocks):")
    for t in ["S","A","B","C","D","F","None"]:
        if t in tier_counts:
            print(f"    {t}: {tier_counts[t]} ({tier_counts[t]/total*100:.1f}%)")


if __name__ == "__main__":
    main()
