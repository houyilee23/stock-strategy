"""Apply per-stock tier upgrades from new auto_iterate retrain dirs into
config/per_stock_recommendations.yaml.

Use case: after running 1+ single-template retrains targeting F-tier stocks,
compare each retrain's per_stock_best.yaml against the current recommendations
and upgrade any stock whose new tier is strictly higher.

Usage:
  python scripts/apply_retrain_upgrades.py <run_dir_1> [run_dir_2 ...]

The run_dirs are short ids under output/auto_iterate/ (e.g. 20260514_133546).
This script:
  - Reads each run_dir/per_stock_best.yaml
  - For each stock that improves tier, replaces the entire entry in
    config/per_stock_recommendations.yaml with the new per_stock_best.yaml row
    (verbose tradeable format). Drops BNH fields since the stock is no longer F.
  - Prints a summary of upgrades.

After running this, the user should run:
  python main.py signals --list Takeshi/Katie/universe
  python scripts/build_per_stock_reports.py
  python scripts/update_readme.py
  python scripts/build_html.py
"""
from __future__ import annotations
import os
import sys
import yaml
from typing import Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECS_PATH = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")
AUTO_ITER_DIR = os.path.join(BASE_DIR, "output", "auto_iterate")

TIER_ORDER = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


def load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def best_candidate(sid: str, runs: List[Tuple[str, dict]]) -> Tuple[str, dict] | None:
    """Pick the highest-tier entry for sid across all run dirs."""
    best = None
    best_score = -1
    for run_id, psb in runs:
        e = psb.get(sid)
        if not isinstance(e, dict) or "tier" not in e:
            continue
        score = TIER_ORDER.get(e.get("tier", "F"), 0)
        # Tie-break by test_pf, then test_expectancy
        pf = e.get("test_pf") or 0
        exp = e.get("test_expectancy") or 0
        tup = (score, pf, exp)
        if best is None or tup > best_score:
            best = (run_id, e)
            best_score = tup
    return best


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run_ids = sys.argv[1:]
    runs: List[Tuple[str, dict]] = []
    for rid in run_ids:
        psb_path = os.path.join(AUTO_ITER_DIR, rid, "per_stock_best.yaml")
        psb = load_yaml(psb_path)
        runs.append((rid, psb))
        print(f"  Loaded {rid}: {len([k for k,v in psb.items() if isinstance(v,dict)])} stocks")

    recs = load_yaml(RECS_PATH)

    upgrades = []
    no_change = []
    downgrades_skipped = []

    # All sids present in any run
    candidate_sids = set()
    for _, psb in runs:
        for k, v in psb.items():
            if isinstance(v, dict):
                candidate_sids.add(str(k))

    for sid in sorted(candidate_sids):
        cur = recs.get(sid, {})
        cur_tier = cur.get("tier", "F") if isinstance(cur, dict) else "F"
        cur_score = TIER_ORDER.get(cur_tier, 0)

        best = best_candidate(sid, runs)
        if best is None:
            continue
        run_id, new_entry = best
        new_tier = new_entry.get("tier", "F")
        new_score = TIER_ORDER.get(new_tier, 0)

        if new_score > cur_score:
            # Upgrade — replace entry with new (tradeable shape)
            template = new_entry.get("best_template") or new_entry.get("template")
            new_full = dict(new_entry)
            new_full["template"] = template
            new_full["position_pct_max"] = new_entry.get("position_pct_recommended", 0.0)
            new_full["tradeable"] = new_tier in ("S", "A", "B", "C")
            new_full["params_ref"] = new_entry.get("params_ref") or f"{template}.yaml#per_stock.{sid}"
            # Keep name if previously present
            if isinstance(cur, dict) and "name" in cur:
                new_full["name"] = cur["name"]
            recs[sid] = new_full
            upgrades.append((sid, cur_tier, new_tier, template, run_id))
        elif new_score < cur_score:
            downgrades_skipped.append((sid, cur_tier, new_tier))
        else:
            no_change.append((sid, cur_tier))

    if not upgrades:
        print("\n  [i] No upgrades found.")
    else:
        print(f"\n  Upgrades ({len(upgrades)}):")
        print(f"  {'sid':<8} {'old':<3} -> {'new':<3} {'template':<24} {'run_id':<20}")
        print("  " + "-"*65)
        for sid, ot, nt, tmpl, rid in upgrades:
            print(f"  {sid:<8} {ot:<3} -> {nt:<3} {tmpl:<24} {rid:<20}")

        # Write back
        # Preserve header comment if exists
        header = ""
        if os.path.exists(RECS_PATH):
            with open(RECS_PATH, encoding="utf-8") as f:
                lines = []
                for line in f:
                    if line.startswith("#"):
                        lines.append(line)
                    else:
                        break
                header = "".join(lines)

        # Replace first comment line with phase tag
        phase_tag = f"# Applied retrain upgrades from: {', '.join(run_ids)}\n"
        if header:
            header_lines = header.split("\n")
            header_lines[0] = phase_tag.rstrip()
            header = "\n".join(header_lines)
            if not header.endswith("\n"):
                header += "\n"
        else:
            header = phase_tag

        with open(RECS_PATH, "w", encoding="utf-8") as f:
            f.write(header)
            yaml.dump(recs, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
        print(f"\n  Wrote {RECS_PATH}")

    # Show final tier dist
    tier_counts = {}
    for sid, r in recs.items():
        if isinstance(r, dict):
            t = r.get("tier", "None")
            tier_counts[t] = tier_counts.get(t, 0) + 1
    total = sum(tier_counts.values())
    print(f"\n  Final tier dist ({total} stocks):")
    for t in ["S","A","B","C","D","F","None"]:
        if t in tier_counts:
            print(f"    {t}: {tier_counts[t]} ({tier_counts[t]/total*100:.1f}%)")


if __name__ == "__main__":
    main()
