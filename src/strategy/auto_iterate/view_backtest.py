"""View per-stock backtest details from the latest auto_iterate run.

Usage:
    python -m src.strategy.auto_iterate.view_backtest <stock_id> [--run-id <id>]
    python -m src.strategy.auto_iterate.view_backtest --all-tradeable
    python -m src.strategy.auto_iterate.view_backtest --tier S
    python -m src.strategy.auto_iterate.view_backtest --tier A,B

Output (per stock):
    - Stock name + tier + best template + Optuna params
    - Train metrics (CAGR, expectancy, PF, n_trades, max_dd)
    - Test metrics (CAGR, expectancy, PF, n_trades, max_dd, alpha vs 0050)
    - Bootstrap CI (PF lower / mean / upper)
    - Holdout pass/fail (A_new / B / C)
    - Tier reason
    - BNH alternative (if F-tier)

For Takeshi/Katie: gives an at-a-glance "should I trade this?" answer.
"""
from __future__ import annotations
import os
import sys
import yaml
import argparse
from typing import Optional, List

# Force UTF-8 stdout on Windows (default cp950 chokes on ≥, ∈, etc.).
# Safe no-op on POSIX. Has to happen before any print().
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


def _stock_label(sid: str) -> str:
    """Inline name lookup — kept in sync with final_report._stock_label."""
    from src.strategy.auto_iterate.final_report import _stock_label as _lbl
    return _lbl(sid)


def _find_latest_merged_run() -> Optional[str]:
    """Return the latest merged_* dir (preferred) or fallback to latest dir."""
    auto_iter = os.path.join(BASE_DIR, "output", "auto_iterate")
    if not os.path.isdir(auto_iter):
        return None
    dirs = [d for d in os.listdir(auto_iter)
            if os.path.isdir(os.path.join(auto_iter, d))
            and os.path.exists(os.path.join(auto_iter, d, "per_stock_best.yaml"))]
    merged = sorted([d for d in dirs if d.startswith("merged_")])
    if merged:
        return merged[-1]
    if dirs:
        return sorted(dirs)[-1]
    return None


def _load_per_stock_best(run_id: str) -> dict:
    path = os.path.join(BASE_DIR, "output", "auto_iterate", run_id, "per_stock_best.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_template_params(run_id: str, template: str, sid: str) -> dict:
    """Load best Optuna params for one (template, stock) pair."""
    path = os.path.join(BASE_DIR, "output", "auto_iterate", run_id, f"{template}.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        d = yaml.safe_load(f) or {}
    ps = (d or {}).get("per_stock", {}) or {}
    entry = ps.get(sid) or ps.get(str(sid)) or {}
    return entry.get("best_params", entry.get("params", {}))


def _load_recommendations() -> dict:
    path = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _fmt(x, fmt: str = ".2%", default: str = "—") -> str:
    if x is None:
        return default
    if isinstance(x, float):
        if x != x:  # NaN
            return default
        if x == float("inf"):
            return "inf"
        if x == float("-inf"):
            return "-inf"
    try:
        return format(x, fmt)
    except (TypeError, ValueError):
        return str(x)


def view_stock(sid: str, run_id: str, recs: Optional[dict] = None) -> None:
    """Print full backtest details for one stock."""
    sid = str(sid)
    if recs is None:
        recs = _load_recommendations()
    psb = _load_per_stock_best(run_id)
    e = psb.get(sid) or psb.get(int(sid)) if sid.isdigit() else psb.get(sid)
    if not isinstance(e, dict) or "best_template" not in e:
        print(f"\n[!] {sid}: 找不到回測資料於 run_id={run_id}")
        return

    label = _stock_label(sid)
    template = e.get("best_template", "?")
    tier = e.get("tier", "?")
    pos_max = e.get("position_pct_recommended", 0.0)
    rec = recs.get(sid, {}) or {}
    bnh_tier = rec.get("bnh_tier")
    bnh_pos = rec.get("bnh_position_pct_max", 0)
    bnh_cagr = rec.get("bnh_cagr")
    bnh_div = rec.get("bnh_div_yield")

    print(f"\n{'='*72}")
    print(f"  {sid} {label}")
    print(f"{'='*72}")
    print(f"  Tier:       {tier}   建議部位上限: {pos_max*100:.0f}%")
    print(f"  Template:   {template}")
    if bnh_tier in ("BNH_S", "BNH_A", "BNH_B"):
        print(f"  BNH 替代:   {bnh_tier} ({bnh_pos*100:.0f}% 部位)  "
              f"CAGR {_fmt(bnh_cagr, '.1%')}  "
              f"殖利率 {_fmt(bnh_div, '.1%')}")

    # Test metrics
    print(f"\n  Test 期間指標 (2024-2026)")
    print(f"  -----------------------------------")
    print(f"  Expectancy:    {_fmt(e.get('test_expectancy'), '+.2%'):>10}    每筆平均報酬")
    print(f"  PF:            {_fmt(e.get('test_pf'), '.2f'):>10}    Profit Factor")
    print(f"  N trades:      {str(e.get('test_n_trades', 0)):>10}    成交筆數")
    print(f"  Max DD:        {_fmt(e.get('test_max_dd'), '.1%'):>10}    最大回撤")
    print(f"  CAGR:          {_fmt(e.get('test_cagr'), '+.1%'):>10}    年化報酬")
    print(f"  Alpha vs 0050: {_fmt(e.get('test_alpha_vs_0050'), '+.1%'):>10}    超額報酬")

    # Bootstrap
    bs = e.get("bootstrap", {}) or {}
    if bs.get("pf_mean") is not None:
        print(f"\n  Bootstrap PF 95% 信賴區間 (n_iter={bs.get('n_iterations', '?')})")
        print(f"  -----------------------------------")
        print(f"  PF lower:      {_fmt(bs.get('pf_lower'), '.2f'):>10}    保守下界")
        print(f"  PF mean:       {_fmt(bs.get('pf_mean'), '.2f'):>10}    平均")
        print(f"  PF upper:      {_fmt(bs.get('pf_upper'), '.2f'):>10}    上界")

    # Holdouts
    ho = e.get("holdouts", {}) or {}
    print(f"\n  Holdout 段")
    print(f"  -----------------------------------")
    for seg, label in (("A_new", "2010-2016"), ("B", "2018"), ("C", "2022")):
        v = ho.get(seg)
        if v is True:
            mark = "PASS"
        elif v is False:
            mark = "FAIL"
        else:
            mark = "N/A (樣本不足或上市晚)"
        print(f"  {seg} ({label}):  {mark}")

    # Tier reason
    print(f"\n  Tier 判定原因")
    print(f"  -----------------------------------")
    print(f"  {e.get('tier_reason', '?')}")

    # Best Optuna params
    params = _load_template_params(run_id, template, sid)
    if params:
        print(f"\n  Optuna 最佳參數（template={template}）")
        print(f"  -----------------------------------")
        for k, v in sorted(params.items()):
            if isinstance(v, float):
                vs = f"{v:.4f}"
            else:
                vs = str(v)
            print(f"  {k:<24} = {vs}")

    print(f"\n  Recommendation:  {e.get('recommendation', '—')}\n")


def view_filter(run_id: str, tiers: List[str] = None) -> None:
    """Print summary table for all stocks matching tier filter."""
    psb = _load_per_stock_best(run_id)
    recs = _load_recommendations()

    rows = []
    for sid, e in psb.items():
        if not isinstance(e, dict) or "best_template" not in e:
            continue
        tier = e.get("tier", "F")
        if tiers and tier not in tiers:
            continue
        rows.append((sid, e))
    rows.sort(key=lambda x: ({"S":6,"A":5,"B":4,"C":3,"D":2,"F":1}.get(x[1].get("tier","F"),0),
                              x[1].get("test_expectancy") or 0),
              reverse=True)

    if not rows:
        print(f"\n[i] 無符合 tier={tiers} 的個股")
        return

    print(f"\n{'='*92}")
    title = f"Tier ∈ {','.join(tiers)}" if tiers else "All stocks"
    print(f"  {title}  (run_id={run_id})  共 {len(rows)} 檔")
    print(f"{'='*92}")
    print(f"  {'股票':<8} {'名稱':<14} {'Tier':<5} {'Template':<22} {'Exp':>7} {'PF':>7} {'n':>3} {'DD':>6} {'倉位':>5}")
    print(f"  {'-'*88}")
    for sid, e in rows:
        label = _stock_label(sid)
        tier = e.get("tier", "?")
        tmpl = e.get("best_template", "?")
        exp = _fmt(e.get("test_expectancy"), "+.1%")
        pf = _fmt(e.get("test_pf"), ".2f")
        n = str(e.get("test_n_trades", 0))
        dd = _fmt(e.get("test_max_dd"), ".0%")
        pos = e.get("position_pct_recommended", 0.0)
        pos_s = f"{pos*100:.0f}%" if pos > 0 else "—"
        print(f"  {sid:<8} {label:<14} {tier:<5} {tmpl:<22} {exp:>7} {pf:>7} {n:>3} {dd:>6} {pos_s:>5}")
    print(f"{'='*92}\n")


def main():
    p = argparse.ArgumentParser(
        description="View per-stock backtest details from auto_iterate output")
    p.add_argument("stock_id", nargs="?", help="個股代號（如 2330）")
    p.add_argument("--run-id", default=None,
                   help="指定 run_id；未指定則用最新 merged_* dir")
    p.add_argument("--all-tradeable", action="store_true",
                   help="列出所有 tradeable (S/A/B/C) 個股摘要")
    p.add_argument("--tier", default=None,
                   help="只列指定 tier（可逗號分隔，如 S,A,B）")
    args = p.parse_args()

    run_id = args.run_id or _find_latest_merged_run()
    if not run_id:
        print("[!] 找不到任何 auto_iterate run dir。先跑 auto-iterate 再用此工具。")
        sys.exit(1)
    print(f"\n  使用 run_id: {run_id}")

    if args.all_tradeable:
        view_filter(run_id, tiers=["S", "A", "B", "C"])
        return

    if args.tier:
        tiers = [t.strip().upper() for t in args.tier.split(",") if t.strip()]
        view_filter(run_id, tiers=tiers)
        return

    if args.stock_id:
        view_stock(args.stock_id, run_id)
        return

    # No args → show all-tradeable as default
    print("\n  (未指定 stock_id，預設顯示所有 tradeable 個股)")
    view_filter(run_id, tiers=["S", "A", "B", "C"])
    print("  輸入 `python -m src.strategy.auto_iterate.view_backtest <stock_id>` 看單檔細節")


if __name__ == "__main__":
    main()
