"""Merge multiple auto_iterate runs into a single unified run dir.

Use case: when universe is split across multiple runs (e.g. baseline 39 stocks
+ research_todo 32 stocks), merge them so final_report.py can produce a single
unified report covering all stocks.

Outputs a NEW run_id `merged_<timestamp>` containing:
  - per_stock_best.yaml          merged across all source runs (stocks must be disjoint)
  - <template>.yaml              copied from source runs (per_stock keys merged)
  - comparison.csv               concatenated across runs
  - summary.md                   short marker note
  - benchmark_0050_test_cagr     taken from the FIRST run_id (assumed same period)

Usage:
  python -m src.strategy.auto_iterate.merge_runs <run_id_1> <run_id_2> [run_id_3 ...]

Constraint:
  Source runs must use the SAME train/test window so metrics are comparable.
  The merger does not check this — it's the caller's responsibility.
"""
from __future__ import annotations
import os
import sys
import shutil
import yaml
from datetime import datetime
from typing import List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


def _load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _dump_yaml(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=True)


def merge_runs(run_ids: List[str]) -> str:
    """Merge given run_ids; return new merged run_id."""
    if not run_ids:
        raise ValueError("merge_runs requires at least one run_id")

    auto_iter_dir = os.path.join(BASE_DIR, "output", "auto_iterate")
    src_dirs = [os.path.join(auto_iter_dir, rid) for rid in run_ids]
    for d in src_dirs:
        if not os.path.isdir(d):
            raise FileNotFoundError(f"Run dir not found: {d}")

    new_run_id = "merged_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    new_dir = os.path.join(auto_iter_dir, new_run_id)
    os.makedirs(new_dir, exist_ok=True)

    # ── per_stock_best.yaml: merge by stock_id ───────────────────
    merged_best: dict = {}
    benchmark_cagr = None
    for src_dir, rid in zip(src_dirs, run_ids):
        psb_path = os.path.join(src_dir, "per_stock_best.yaml")
        if not os.path.exists(psb_path):
            print(f"  [WARN] {rid}: no per_stock_best.yaml, skipping")
            continue
        d = _load_yaml(psb_path)
        # Take benchmark from the first run that has it
        if benchmark_cagr is None and "benchmark_0050_test_cagr" in d:
            benchmark_cagr = d["benchmark_0050_test_cagr"]
        for k, v in d.items():
            if k in ("benchmark_0050_test_cagr", "borderline_candidates"):
                continue
            if k in merged_best:
                print(f"  [WARN] stock {k} duplicated across runs; keeping {rid}")
            merged_best[k] = v
    if benchmark_cagr is not None:
        merged_best["benchmark_0050_test_cagr"] = benchmark_cagr
    _dump_yaml(os.path.join(new_dir, "per_stock_best.yaml"), merged_best)

    # ── <template>.yaml: merge per_stock keys across runs ────────
    template_data: dict = {}  # template_name -> { 'per_stock': {...}, ... }
    for src_dir, rid in zip(src_dirs, run_ids):
        for fn in os.listdir(src_dir):
            if not fn.endswith(".yaml") or fn == "per_stock_best.yaml":
                continue
            tmpl = fn[:-5]  # strip .yaml
            d = _load_yaml(os.path.join(src_dir, fn))
            if tmpl not in template_data:
                template_data[tmpl] = d
                continue
            # merge per_stock dicts
            existing = template_data[tmpl]
            new_ps = (d or {}).get("per_stock", {})
            existing_ps = existing.setdefault("per_stock", {})
            for sid, sd in new_ps.items():
                if sid in existing_ps:
                    print(f"  [WARN] {tmpl} per_stock.{sid} duplicated; keeping {rid}")
                existing_ps[sid] = sd
    for tmpl, d in template_data.items():
        _dump_yaml(os.path.join(new_dir, f"{tmpl}.yaml"), d)

    # ── comparison.csv: concatenate ──────────────────────────────
    comp_lines = []
    header_done = False
    for src_dir in src_dirs:
        cpath = os.path.join(src_dir, "comparison.csv")
        if not os.path.exists(cpath):
            continue
        with open(cpath, encoding="utf-8-sig") as f:
            for i, line in enumerate(f):
                if i == 0:
                    if not header_done:
                        comp_lines.append(line.rstrip("\n"))
                        header_done = True
                    continue
                comp_lines.append(line.rstrip("\n"))
    if comp_lines:
        with open(os.path.join(new_dir, "comparison.csv"), "w", encoding="utf-8-sig") as f:
            f.write("\n".join(comp_lines) + "\n")

    # ── summary.md: short marker note ────────────────────────────
    summary_md = (
        f"# MERGED RUN — {new_run_id}\n\n"
        f"Sources: " + ", ".join(run_ids) + "\n\n"
        f"Total stocks: {sum(1 for k in merged_best if k not in ('benchmark_0050_test_cagr',))}\n\n"
        f"Generated by `src/strategy/auto_iterate/merge_runs.py`. "
        f"Run `python -m src.strategy.auto_iterate.final_report {new_run_id}` to "
        f"produce the user-facing report.\n"
    )
    with open(os.path.join(new_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"\n  Merged {len(run_ids)} runs into {new_run_id}")
    print(f"  Run dir: {new_dir}")
    print(f"  Stock count: {sum(1 for k in merged_best if k not in ('benchmark_0050_test_cagr',))}")
    print(f"  Templates merged: {sorted(template_data.keys())}")
    print(f"\n  Next step:")
    print(f"    python -m src.strategy.auto_iterate.final_report {new_run_id}")

    return new_run_id


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.strategy.auto_iterate.merge_runs <run_id_1> [run_id_2 ...]")
        sys.exit(1)
    merge_runs(sys.argv[1:])
