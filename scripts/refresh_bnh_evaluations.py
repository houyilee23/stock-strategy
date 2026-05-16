"""Refresh BNH (buy-and-hold) evaluation for all F-tier stocks in recommendations.

For each F-tier stock, compute current BNH metrics (CAGR, MaxDD, dividend yield)
and assign BNH tier (BNH_S / BNH_A / BNH_B / F). Updates the entry in
config/per_stock_recommendations.yaml in place — adds bnh_* fields.

Use case: when new stocks are added and only their active-trading metrics are
stored, this script back-fills BNH alternative evaluation so the recommendations
show "if active doesn't work, here's BNH option" properly.

Usage:
  python scripts/refresh_bnh_evaluations.py
"""
from __future__ import annotations
import os
import sys
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.strategy.auto_iterate.bnh import (  # noqa: E402
    compute_bnh_for_stock,
    compute_market_bnh,
    estimate_dividend_yield,
)
from src.strategy.auto_iterate.tiering import assign_bnh_tier, BNH_TIER_RULES  # noqa: E402

RECS_PATH = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")


def main():
    header_lines = []
    with open(RECS_PATH, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                header_lines.append(line)
            else:
                break
    with open(RECS_PATH, encoding="utf-8") as f:
        recs = yaml.safe_load(f) or {}

    print("  Computing market (0050) BNH baseline...")
    mkt_bnh = compute_market_bnh()
    print(f"  0050 BNH: CAGR={mkt_bnh.get('cagr', 0)*100:.1f}%, "
          f"MaxDD={mkt_bnh.get('max_dd', 0)*100:.1f}%")

    f_tier = [sid for sid, r in recs.items()
              if isinstance(r, dict) and r.get("tier") == "F"]
    print(f"  F-tier stocks: {len(f_tier)}")

    rescued = []
    for sid in sorted(f_tier):
        try:
            m = compute_bnh_for_stock(sid)
            dy = estimate_dividend_yield(sid)
            bnh_tier, bnh_reason = assign_bnh_tier(sid, m, mkt_bnh, dy)
        except Exception as e:
            print(f"  [!] {sid}: BNH compute error: {e}")
            continue

        bnh_pos = BNH_TIER_RULES.get(bnh_tier, {}).get("pos_max", 0.0)
        recs[sid]["bnh_tier"] = bnh_tier
        recs[sid]["bnh_position_pct_max"] = bnh_pos if bnh_tier in BNH_TIER_RULES else 0.0
        if m:
            recs[sid]["bnh_cagr"] = m.get("cagr")
            recs[sid]["bnh_max_dd"] = m.get("max_dd")
        recs[sid]["bnh_div_yield"] = dy
        recs[sid]["bnh_holdable"] = bnh_tier in ("BNH_S", "BNH_A", "BNH_B")

        marker = "★" if bnh_tier in BNH_TIER_RULES else " "
        cagr_s = f"{(m or {}).get('cagr', 0)*100:+.1f}%" if m else "N/A"
        dd_s = f"{(m or {}).get('max_dd', 0)*100:.1f}%" if m else "N/A"
        dy_s = f"{dy*100:.1f}%" if dy else "N/A"
        print(f"  {marker} {sid}: {bnh_tier} | CAGR={cagr_s:>7} DD={dd_s:>6} div={dy_s:>5}")
        if bnh_tier in BNH_TIER_RULES:
            rescued.append((sid, bnh_tier))

    print(f"\n  BNH rescued: {len(rescued)} / {len(f_tier)}")
    for sid, t in rescued:
        print(f"    {sid}: {t} ({BNH_TIER_RULES[t]['pos_max']*100:.0f}% pos)")

    # Write back
    with open(RECS_PATH, "w", encoding="utf-8") as f:
        f.writelines(header_lines)
        yaml.dump(recs, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
    print(f"\n  Wrote {RECS_PATH}")


if __name__ == "__main__":
    main()
