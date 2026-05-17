"""Auto-iterate runner: per-stock per-template optuna optimisation + hold-out validation.

v3: regime-independent objective (expectancy + PF).
    0050 CAGR computed as informational benchmark only.
"""
import os
import time
import yaml
import math
import numpy as np
import pandas as pd
from datetime import datetime

import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

TEMPLATE_NAMES = [
    "trend_pullback",
    "donchian_breakout",
    "momentum_hold",
    "chip_momentum",
    "mean_reversion",
    # auto_iterate v2 新增（為 LOW_SAMPLE / 大型權值股 / 傳產設計）
    "volume_breakout",
    "gap_continuation",
    "low_vol_pullback",
    "bollinger_squeeze",
    # auto_iterate v3 新增（台股法人連續買超 alpha）
    "chip_streak",
    # auto_iterate v4 新增（台股月營收公告事件 alpha）
    "monthly_revenue_event",
]


# ── Borderline helpers ────────────────────────────────────────────

def is_borderline_dd(test_metrics: dict) -> bool:
    """True if DD just exceeds 30% (30% < DD <= 35%) but all other PASS criteria met."""
    n   = test_metrics.get("n_trades", 0)
    if n < 5:
        return False
    dd_abs  = abs(test_metrics.get("max_drawdown", 0) or 0)
    if not (0.30 < dd_abs <= 0.35):
        return False
    pf  = test_metrics.get("profit_factor", float("nan"))
    exp = test_metrics.get("expectancy",    float("nan"))
    if isinstance(pf,  float) and (math.isnan(pf)  or math.isinf(pf)):  return False
    if isinstance(exp, float) and math.isnan(exp):                       return False
    return pf >= 1.5 and exp >= 0.05


def is_borderline_low_n(test_metrics: dict) -> bool:
    """True if 3 <= n < 5 and would otherwise PASS (exp>=5%, pf>=1.5, dd<=30%, PF finite)."""
    n = test_metrics.get("n_trades", 0)
    if not (3 <= n < 5):
        return False
    dd_abs  = abs(test_metrics.get("max_drawdown", 0) or 0)
    if dd_abs > 0.30:
        return False
    pf  = test_metrics.get("profit_factor", float("nan"))
    exp = test_metrics.get("expectancy",    float("nan"))
    if isinstance(pf,  float) and (math.isnan(pf) or math.isinf(pf)):  return False
    if isinstance(exp, float) and math.isnan(exp):                      return False
    return pf >= 1.5 and exp >= 0.05


# ── Data loaders ─────────────────────────────────────────────────

def _load_ohlcv(sid: str):
    from src.strategy.runner import _load_adj_ohlcv
    return _load_adj_ohlcv(sid)


def _load_regime(mkt_sid: str = "0050") -> pd.Series:
    from src.strategy.signals.regime import detect_regime
    df = _load_ohlcv(mkt_sid)
    if df is None:
        return pd.Series(dtype=str)
    return detect_regime(df)


def _load_cfg() -> dict:
    path = os.path.join(BASE_DIR, "config", "strategy.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _bnh_cagr(df: pd.DataFrame, start: str, end: str) -> float:
    """Buy-and-hold CAGR for df["close"] between start and end dates."""
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    sl = df[(df.index >= s) & (df.index <= e)]["close"].dropna()
    if len(sl) < 2 or sl.iloc[0] <= 0:
        return float("nan")
    yrs = (sl.index[-1] - sl.index[0]).days / 365
    if yrs <= 0:
        return float("nan")
    return (sl.iloc[-1] / sl.iloc[0]) ** (1 / yrs) - 1


# ── Serialisation helpers ─────────────────────────────────────────

def _safe(v):
    """Convert NaN/Inf/numpy scalars to Python native for YAML/CSV."""
    if isinstance(v, (np.floating, np.integer)):
        v = v.item()
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _fmt(m: dict) -> dict:
    # P1：trades_pnl_pct 是內部用列表，不寫進 yaml（節省檔案大小）
    return {k: _safe(v) for k, v in m.items() if k != "trades_pnl_pct"}


# ── Output writers ────────────────────────────────────────────────

def _write_template_yaml(out_dir, template, sids, all_results,
                         train_start, train_end, test_start, test_end,
                         bm0050_train, bm0050_test):
    doc = {
        "template":     template,
        "generated_at": datetime.now().isoformat(),
        "train_period": f"{train_start}~{train_end}",
        "test_period":  f"{test_start}~{test_end}",
        "benchmark_0050": {
            "train_cagr": _safe(bm0050_train),
            "test_cagr":  _safe(bm0050_test),
        },
        "per_stock": {},
    }
    for sid in sids:
        r = all_results.get(sid, {}).get(template)
        if r is None:
            continue
        train = r.get("train", {})
        test  = r.get("test",  {})
        # Compute informational fields for test
        test_cagr = test.get("cagr", float("nan"))
        bnh_cagr  = test.get("bnh_cagr", float("nan"))
        alpha_bnh = ((test_cagr - bnh_cagr)
                     if not (isinstance(test_cagr, float) and math.isnan(test_cagr))
                     and not (isinstance(bnh_cagr, float) and math.isnan(bnh_cagr))
                     else float("nan"))
        alpha_0050 = ((test_cagr - bm0050_test)
                      if not (isinstance(test_cagr, float) and math.isnan(test_cagr))
                      and not (isinstance(bm0050_test, float) and math.isnan(bm0050_test))
                      else float("nan"))

        test_out = _fmt(test)
        test_out["alpha_vs_0050"] = _safe(alpha_0050)
        test_out["alpha_vs_bnh"]  = _safe(alpha_bnh)

        doc["per_stock"][sid] = {
            "best_params": r.get("best_params", {}),
            "train":   _fmt(train),
            "test":    test_out,
            "verdict": r.get("verdict", "FAIL"),
        }
    path = os.path.join(out_dir, f"{template}.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _write_comparison_csv(out_dir, sids, all_results, templates, bm0050_test):
    rows = []
    for sid in sids:
        row = {"stock_id": sid, "benchmark_0050_test_cagr": _safe(bm0050_test)}

        # bnh from test period (same across templates)
        bnh = float("nan")
        for t in templates:
            r = all_results.get(sid, {}).get(t)
            if r:
                bnh = r.get("test", {}).get("bnh_cagr", float("nan"))
                if not (isinstance(bnh, float) and math.isnan(bnh)):
                    break
        row["bh_test_cagr"] = _safe(bnh)

        best_expectancy = float("-inf")
        best_t_name     = "NONE"

        for idx, t in enumerate(templates, 1):
            r    = all_results.get(sid, {}).get(t)
            pfx  = f"T{idx}"
            if r is None:
                for k in ("verdict", "n_trades", "pf", "expectancy",
                          "avg_win", "avg_loss", "dd", "cagr", "alpha_vs_0050"):
                    row[f"{pfx}_{k}"] = None
                continue

            test    = r.get("test", {})
            verdict = r.get("verdict", "N/A")
            n       = test.get("n_trades", 0)
            pf      = test.get("profit_factor", float("nan"))
            exp     = test.get("expectancy",    float("nan"))
            aw      = test.get("avg_win",       float("nan"))
            al      = test.get("avg_loss",      float("nan"))
            dd      = test.get("max_drawdown",  float("nan"))
            cagr    = test.get("cagr",          float("nan"))
            bh_t    = test.get("bnh_cagr",      float("nan"))
            a0050   = ((cagr - bm0050_test)
                       if not any(isinstance(x, float) and math.isnan(x)
                                  for x in [cagr, bm0050_test])
                       else float("nan"))

            row[f"{pfx}_verdict"]       = verdict
            row[f"{pfx}_n_trades"]      = n
            row[f"{pfx}_pf"]            = _safe(round(pf,   3)) if not (isinstance(pf,   float) and math.isnan(pf))   else None
            row[f"{pfx}_expectancy"]    = _safe(round(exp,  4)) if not (isinstance(exp,  float) and math.isnan(exp))  else None
            row[f"{pfx}_avg_win"]       = _safe(round(aw,   4)) if not (isinstance(aw,   float) and math.isnan(aw))   else None
            row[f"{pfx}_avg_loss"]      = _safe(round(al,   4)) if not (isinstance(al,   float) and math.isnan(al))   else None
            row[f"{pfx}_dd"]            = _safe(round(dd,   4)) if not (isinstance(dd,   float) and math.isnan(dd))   else None
            row[f"{pfx}_cagr"]          = _safe(round(cagr, 4)) if not (isinstance(cagr, float) and math.isnan(cagr)) else None
            row[f"{pfx}_alpha_vs_0050"] = _safe(round(a0050,4)) if not (isinstance(a0050,float) and math.isnan(a0050))else None

            # best_template: PASS first, then WEAK, sorted by expectancy
            if verdict in ("PASS", "WEAK"):
                if verdict == "PASS" and best_t_name not in [t2 for t2 in templates
                                                              if all_results.get(sid, {}).get(t2, {}).get("verdict") == "PASS"]:
                    pass  # will be resolved below
                exp_val = exp if not (isinstance(exp, float) and math.isnan(exp)) else float("-inf")
                if verdict == "PASS":
                    if (best_t_name == "NONE" or
                            all_results.get(sid, {}).get(best_t_name, {}).get("verdict") != "PASS" or
                            exp_val > best_expectancy):
                        best_expectancy = exp_val
                        best_t_name     = t
                elif verdict == "WEAK" and best_t_name == "NONE":
                    if exp_val > best_expectancy:
                        best_expectancy = exp_val
                        best_t_name     = t

        row["best_template"]    = best_t_name
        row["best_expectancy"]  = _safe(round(best_expectancy, 4)) if best_expectancy > float("-inf") else None
        rows.append(row)

    pd.DataFrame(rows).to_csv(
        os.path.join(out_dir, "comparison.csv"),
        index=False, encoding="utf-8-sig",
    )
    return rows


def _write_per_stock_best(out_dir, sids, all_results, templates, rows, bm0050_test):
    """P1 改：best_template 改用 tier 排序（S>A>B>C>F），同 tier 內取 expectancy 最高。
    多寫 tier / position_pct_recommended / bootstrap / holdouts 欄位。
    """
    doc = {"benchmark_0050_test_cagr": _safe(bm0050_test)}

    tier_order = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}

    for sid in sids:
        # 用 tier 而非 verdict 選 best_template
        candidates = []
        for t in templates:
            r = all_results.get(sid, {}).get(t)
            if r is None:
                continue
            tier = r.get("tier", "F")
            exp  = r.get("test", {}).get("expectancy", float("nan"))
            exp_v = exp if not (isinstance(exp, float) and math.isnan(exp)) else float("-inf")
            candidates.append((tier_order.get(tier, 0), exp_v, t, tier))
        candidates.sort(reverse=True)

        if candidates and candidates[0][0] >= tier_order["F"]:
            _, _, best_t, best_tier = candidates[0]
            r    = all_results.get(sid, {}).get(best_t, {})
            test = r.get("test", {})
            exp  = test.get("expectancy",   float("nan"))
            pf   = test.get("profit_factor",float("nan"))
            n    = test.get("n_trades",     0)
            dd   = test.get("max_drawdown", float("nan"))
            cagr = test.get("cagr",         float("nan"))
            a0050 = ((cagr - bm0050_test)
                     if not any(isinstance(x, float) and math.isnan(x)
                                for x in [cagr, bm0050_test])
                     else float("nan"))
            verdict = r.get("verdict", "FAIL")
            boot = r.get("bootstrap", {})
            holdouts = r.get("holdouts", {})

            entry = {
                "best_template":      best_t,
                "verdict":            verdict,
                "tier":               best_tier,
                "tier_reason":        r.get("tier_reason", ""),
                "position_pct_recommended": _safe(r.get("position_pct_recommended", 0.0)),
                "test_expectancy":    _safe(round(exp,  4)) if not (isinstance(exp,  float) and math.isnan(exp))  else None,
                "test_pf":            _safe(round(pf,   3)) if not (isinstance(pf,   float) and math.isnan(pf))   else None,
                "test_n_trades":      n,
                "test_max_dd":        _safe(round(dd,   4)) if not (isinstance(dd,   float) and math.isnan(dd))   else None,
                "test_cagr":          _safe(round(cagr, 4)) if not (isinstance(cagr, float) and math.isnan(cagr)) else None,
                "test_alpha_vs_0050": _safe(round(a0050,4)) if not (isinstance(a0050,float) and math.isnan(a0050))else None,
                "bootstrap": {
                    "pf_mean":  _safe(round(boot.get("pf_mean",  float("nan")), 3))
                                if boot else None,
                    "pf_lower": _safe(round(boot.get("pf_lower", float("nan")), 3))
                                if boot else None,
                    "pf_upper": _safe(round(boot.get("pf_upper", float("nan")), 3))
                                if boot else None,
                    "n_iterations": boot.get("n_iterations") if boot else None,
                    "n_original":   boot.get("n_original")   if boot else None,
                },
                "holdouts": {
                    # tri-state: True (PASS) / False (FAIL) / None (NA, not yet listed)
                    "A_new": holdouts.get("A_new"),
                    "B":     holdouts.get("B"),
                    "C":     holdouts.get("C"),
                },
                "params_ref":         f"{best_t}.yaml#per_stock.{sid}",
            }
            if best_tier == "F":
                entry["recommendation"] = (
                    "FAIL：所有模板 tier=F，訊號模式不適用，建議走組合模式或直接買 0050"
                )
            elif verdict == "WEAK":
                entry["recommendation"] = "可用，但建議縮小部位（expectancy 未達 5% 門檻）"
        else:
            # 完全沒結果（全部 exception）
            entry = {
                "best_template":  "NONE",
                "verdict":        "NO_RESULT",
                "tier":           "F",
                "position_pct_recommended": 0.0,
                "recommendation": "無結果",
            }
        doc[sid] = entry

    # ── Borderline candidates ─────────────────────────────────────
    borderline_dd   = []
    borderline_low_n = []
    for sid in sids:
        for t in templates:
            r = all_results.get(sid, {}).get(t)
            if r is None:
                continue
            test = r.get("test", {})
            if is_borderline_dd(test):
                borderline_dd.append({
                    "stock": sid, "template": t,
                    "expectancy":    _safe(round(test.get("expectancy", float("nan")), 4)),
                    "pf":            _safe(round(test.get("profit_factor", float("nan")), 3)),
                    "n_trades":      test.get("n_trades", 0),
                    "max_dd":        _safe(round(test.get("max_drawdown", float("nan")), 4)),
                    "note":          "DD 30-35% 超標，其餘達 PASS 標準",
                })
            if is_borderline_low_n(test):
                borderline_low_n.append({
                    "stock": sid, "template": t,
                    "expectancy":    _safe(round(test.get("expectancy", float("nan")), 4)),
                    "pf":            _safe(round(test.get("profit_factor", float("nan")), 3)),
                    "n_trades":      test.get("n_trades", 0),
                    "max_dd":        _safe(round(test.get("max_drawdown", float("nan")), 4)),
                    "note":          "n=3-4 樣本不足，但方向性佳（exp>=5%, pf>=1.5, dd<=30%）",
                })

    if borderline_dd or borderline_low_n:
        doc["borderline_candidates"] = {
            "note": "以下個股未達 PASS 門檻，但具備觀察價值",
            "borderline_dd":    borderline_dd    or [],
            "borderline_low_n": borderline_low_n or [],
        }

    with open(os.path.join(out_dir, "per_stock_best.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _collect_borderlines(sids, all_results, templates):
    """Return (borderline_dd_list, borderline_low_n_list) sorted by expectancy desc."""
    bdd, bln = [], []
    for sid in sids:
        for t in templates:
            r = all_results.get(sid, {}).get(t)
            if r is None:
                continue
            test = r.get("test", {})
            exp  = test.get("expectancy", float("nan"))
            exp_v = exp if not (isinstance(exp, float) and math.isnan(exp)) else float("-inf")
            if is_borderline_dd(test):
                bdd.append((exp_v, sid, t, test.get("profit_factor", float("nan")),
                            test.get("n_trades", 0), test.get("max_drawdown", float("nan"))))
            if is_borderline_low_n(test):
                bln.append((exp_v, sid, t, test.get("profit_factor", float("nan")),
                            test.get("n_trades", 0), test.get("max_drawdown", float("nan"))))
    bdd.sort(reverse=True)
    bln.sort(reverse=True)
    return bdd, bln


def _write_summary_md(out_dir, run_id, sids, all_results, templates, rows, elapsed_secs, bm0050_train, bm0050_test):
    from collections import Counter, defaultdict

    elapsed_min   = elapsed_secs / 60
    total_pairs   = len(sids) * len(templates)
    verdict_counts = Counter()
    template_pass  = defaultdict(list)
    top_exp        = []

    for sid in sids:
        for t in templates:
            r = all_results.get(sid, {}).get(t)
            v = r.get("verdict", "N/A") if r else "N/A"
            verdict_counts[v] += 1
            if v == "PASS":
                template_pass[t].append(sid)
            if r:
                exp = r.get("test", {}).get("expectancy", float("nan"))
                if not (isinstance(exp, float) and math.isnan(exp)):
                    top_exp.append((exp, sid, t, v))

    top_exp.sort(reverse=True)
    row_map     = {r["stock_id"]: r for r in rows}
    no_pass_sids = [s for s in sids if row_map.get(s, {}).get("best_template", "NONE") == "NONE"]
    pass_counts  = {t: len(v) for t, v in template_pass.items()}
    best_t       = max(pass_counts, key=pass_counts.get) if pass_counts else "N/A"
    pass_pct     = sum(1 for s in sids if row_map.get(s, {}).get("best_template", "NONE") != "NONE")

    lines = [
        "# Auto-Iterate Summary (v3)",
        "",
        "## 1. Run Metadata",
        f"- **run_id**: {run_id}",
        f"- **耗時**: {elapsed_min:.1f} 分鐘",
        f"- **跑了**: {total_pairs} 個 (stock, template) 對",
        f"- **Universe**: {len(sids)} 檔 x {len(templates)} 模板",
        f"- **Train**: 2017-01-01 ~ 2023-12-31",
        f"- **Test** : 2024-01-01 ~ 2026-04-22",
        f"- **0050 benchmark (informational)**: train CAGR={bm0050_train:+.1%}, test CAGR={bm0050_test:+.1%}" if not math.isnan(bm0050_train) else "",
        "",
        "## 2. Verdict 分布",
        "",
        "| Verdict | 數量 |",
        "|---------|------|",
    ]
    for v in ("PASS", "SUSPICIOUS_PERFECT", "WEAK", "FAIL", "DD_BREACH", "INSUFFICIENT"):
        lines.append(f"| {v} | {verdict_counts.get(v, 0)} |")

    lines += [
        "",
        "## 3. 各模板 PASS 個股",
        "",
    ]
    for t in templates:
        plist = template_pass.get(t, [])
        lines.append(f"- **{t}**: {', '.join(plist) if plist else '（無）'}")

    lines += [
        "",
        "## 4. 無任何模板 PASS 的個股",
        "",
        f"{'，'.join(no_pass_sids) if no_pass_sids else '（無）'}",
        "",
        "## 5. Top 10 Expectancy 個股（不分模板）",
        "",
        "| Stock | Template | Expectancy | Verdict |",
        "|-------|----------|-----------|---------|",
    ]
    for exp, sid, t, v in top_exp[:10]:
        lines.append(f"| {sid} | {t} | {exp:+.1%} | {v} |")

    # Borderline sections
    bdd_list, bln_list = _collect_borderlines(sids, all_results, templates)

    lines += [
        "",
        "## 6. BORDERLINE_DD 候選（DD 30-35%，其餘達 PASS）",
        "",
        "| Stock | Template | Exp | PF | n | DD | 備註 |",
        "|-------|----------|-----|----|---|----|------|",
    ]
    if bdd_list:
        for exp_v, sid, t, pf_v, n_v, dd_v in bdd_list:
            exp_s = f"{exp_v:+.1%}" if exp_v > float("-inf") else "N/A"
            pf_s  = f"{pf_v:.2f}"   if not (isinstance(pf_v, float) and (math.isnan(pf_v) or math.isinf(pf_v))) else "inf"
            dd_s  = f"{abs(dd_v):.1%}" if not (isinstance(dd_v, float) and math.isnan(dd_v)) else "N/A"
            lines.append(f"| {sid} | {t} | {exp_s} | {pf_s} | {n_v} | -{dd_s} | DD 超標，觀察用 |")
    else:
        lines.append("| （無） | — | — | — | — | — | — |")

    lines += [
        "",
        "## 7. BORDERLINE_LOW_N 候選（n=3-4，其餘達 PASS）",
        "",
        "| Stock | Template | Exp | PF | n | DD | 備註 |",
        "|-------|----------|-----|----|---|----|------|",
    ]
    if bln_list:
        for exp_v, sid, t, pf_v, n_v, dd_v in bln_list:
            exp_s = f"{exp_v:+.1%}" if exp_v > float("-inf") else "N/A"
            pf_s  = f"{pf_v:.2f}"   if not (isinstance(pf_v, float) and (math.isnan(pf_v) or math.isinf(pf_v))) else "inf"
            dd_s  = f"{abs(dd_v):.1%}" if not (isinstance(dd_v, float) and math.isnan(dd_v)) else "N/A"
            lines.append(f"| {sid} | {t} | {exp_s} | {pf_s} | {n_v} | -{dd_s} | 低樣本數，方向性佳 |")
    else:
        lines.append("| （無） | — | — | — | — | — | — |")

    lines += [
        "",
        "## 8. 關鍵發現",
        "",
        f"- **覆蓋最廣模板**: {best_t}（{pass_counts.get(best_t, 0)} 股 PASS）",
        f"- **Watchlist PASS 率**: {pass_pct}/{len(sids)} = {pass_pct/max(len(sids),1):.0%}",
        f"- **PASS+WEAK 合計**: {verdict_counts.get('PASS',0) + verdict_counts.get('WEAK',0)} / {total_pairs}",
        f"- **BORDERLINE_DD**: {len(bdd_list)} 個對（DD 30-35%，其餘達標）",
        f"- **BORDERLINE_LOW_N**: {len(bln_list)} 個對（n=3-4，方向性佳）",
        f"- **0050 test CAGR (benchmark)**: {bm0050_test:+.1%}" if not math.isnan(bm0050_test) else "",
        "",
    ]

    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_tiering_report(out_dir, run_id, sids, all_results, templates):
    """產生 docs/TIERING_REPORT.md（也輸出一份到 run 目錄方便對照）。

    內容：
    - 每個 tier 的個股清單（best_template 視角）
    - 統計摘要（S/A/B/C/F 數量、可操作 = S+A+B+C）
    - 對照舊 run（20260423_151107，舊 verdict 制）的差異
    """
    from src.strategy.auto_iterate.tiering import TIER_RULES

    tier_order = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "F": 1}

    # 收集每檔的 best (tier, template, metrics)
    per_stock_best = {}
    for sid in sids:
        cands = []
        for t in templates:
            r = all_results.get(sid, {}).get(t)
            if r is None:
                continue
            tier = r.get("tier", "F")
            exp  = r.get("test", {}).get("expectancy", float("nan"))
            exp_v = exp if not (isinstance(exp, float) and math.isnan(exp)) else float("-inf")
            cands.append((tier_order.get(tier, 0), exp_v, t, tier, r))
        cands.sort(reverse=True)
        if cands:
            _, _, t, tier, r = cands[0]
            per_stock_best[sid] = {"template": t, "tier": tier, "result": r}

    # 統計
    from collections import Counter, defaultdict
    tier_counts = Counter(v["tier"] for v in per_stock_best.values())
    by_tier = defaultdict(list)
    for sid, info in per_stock_best.items():
        by_tier[info["tier"]].append((sid, info))
    operable = (tier_counts.get("S", 0) + tier_counts.get("A", 0)
                + tier_counts.get("B", 0) + tier_counts.get("C", 0))

    lines = [
        f"# TIERING REPORT — {run_id}",
        "",
        "## 1. 統計摘要",
        "",
        "| Tier | 數量 | 部位上限 | 描述 |",
        "|------|------|----------|------|",
    ]
    for tier in ("S", "A", "B", "C", "F"):
        rule = TIER_RULES[tier]
        cnt = tier_counts.get(tier, 0)
        pos_max_pct = f"{int(rule['pos_max']*100)}%"
        lines.append(f"| {tier} | {cnt} | {pos_max_pct} | {rule['label']} |")

    lines += [
        "",
        f"**可操作標的合計（S+A+B+C）= {operable} / {len(sids)}**  "
        f"（目標 ≥ 20）",
        "",
        "## 2. 各 Tier 個股清單",
        "",
    ]

    for tier in ("S", "A", "B", "C", "F"):
        bucket = by_tier.get(tier, [])
        rule = TIER_RULES[tier]
        lines.append(f"### Tier {tier} — 部位上限 {int(rule['pos_max']*100)}% （共 {len(bucket)} 檔）")
        lines.append("")
        if not bucket:
            lines.append("（無）")
            lines.append("")
            continue
        lines.append("| Stock | Template | Exp | PF | n | DD | PF_lower | A_new | B | C | Reason |")
        lines.append("|-------|----------|-----|----|---|----|----------|-------|---|---|--------|")
        # 同 tier 按 expectancy 降序
        bucket_sorted = sorted(
            bucket,
            key=lambda x: x[1]["result"].get("test", {}).get("expectancy", float("-inf"))
            if not (isinstance(x[1]["result"].get("test", {}).get("expectancy", 0), float)
                    and math.isnan(x[1]["result"].get("test", {}).get("expectancy", 0)))
            else float("-inf"),
            reverse=True,
        )
        for sid, info in bucket_sorted:
            r = info["result"]
            test = r.get("test", {})
            exp = test.get("expectancy", float("nan"))
            pf  = test.get("profit_factor", float("nan"))
            n   = test.get("n_trades", 0)
            dd  = test.get("max_drawdown", float("nan"))
            boot = r.get("bootstrap", {})
            pflo = boot.get("pf_lower", float("nan"))
            holdouts = r.get("holdouts", {})
            reason = r.get("tier_reason", "")

            exp_s = f"{exp:+.1%}" if not (isinstance(exp, float) and math.isnan(exp)) else "N/A"
            pf_s  = (f"{pf:.2f}" if not (isinstance(pf, float) and (math.isnan(pf) or math.isinf(pf)))
                     else ("inf" if isinstance(pf, float) and math.isinf(pf) else "N/A"))
            dd_s  = f"{abs(dd):.1%}" if not (isinstance(dd, float) and math.isnan(dd)) else "N/A"
            pflo_s = (f"{pflo:.2f}" if not (isinstance(pflo, float) and math.isnan(pflo))
                      else "N/A")
            a_s = "O" if holdouts.get("A_new") else "X"
            b_s = "O" if holdouts.get("B") else "X"
            c_s = "O" if holdouts.get("C") else "X"
            lines.append(f"| {sid} | {info['template']} | {exp_s} | {pf_s} | {n} | "
                         f"-{dd_s} | {pflo_s} | {a_s} | {b_s} | {c_s} | {reason} |")
        lines.append("")

    # 與舊 run 對比
    old_yaml_path = os.path.join(BASE_DIR, "output", "auto_iterate",
                                 "20260423_151107", "per_stock_best.yaml")
    if os.path.exists(old_yaml_path):
        try:
            with open(old_yaml_path, encoding="utf-8") as f:
                old_doc = yaml.safe_load(f) or {}
        except Exception:
            old_doc = {}

        # 舊 run 是 verdict 制：PASS / WEAK → 對應一個粗略 tier
        # 為了對比，把舊 verdict 映射到 tier-like：
        #   PASS → A（強）, WEAK → C, NONE/FAIL → F
        old_tier = {}
        for sid in sids:
            old_entry = old_doc.get(sid, {})
            ov = old_entry.get("verdict", "FAIL")
            if old_entry.get("best_template", "NONE") == "NONE":
                old_tier[sid] = "F"
            elif ov == "PASS":
                old_tier[sid] = "A_old"   # 舊 PASS 標記
            elif ov == "WEAK":
                old_tier[sid] = "C_old"
            else:
                old_tier[sid] = "F"

        diffs = []
        for sid in sids:
            new_t = per_stock_best.get(sid, {}).get("tier", "F")
            old_t = old_tier.get(sid, "F")
            old_score = {"A_old": 4, "C_old": 2, "F": 1}.get(old_t, 0)
            new_score = tier_order.get(new_t, 0)
            delta = new_score - old_score
            diffs.append((delta, sid, old_t, new_t))

        # 取變化最大的 5 檔（升 + 降）
        ups = [d for d in diffs if d[0] > 0]
        downs = [d for d in diffs if d[0] < 0]
        ups.sort(reverse=True)
        downs.sort()

        lines += [
            "## 3. 對照舊 run（20260423_151107）",
            "",
            f"舊 run verdict 制（PASS/WEAK/NONE）映射為粗略 tier：",
            f"PASS→A_old, WEAK→C_old, 其他→F。",
            "",
            f"**升級個股**（共 {len(ups)} 檔，前 5）：",
            "",
            "| Stock | 舊 | 新 | Δ |",
            "|-------|----|----|---|",
        ]
        for delta, sid, old_t, new_t in ups[:5]:
            lines.append(f"| {sid} | {old_t} | {new_t} | +{delta} |")
        if not ups:
            lines.append("| （無） | — | — | — |")
        lines += [
            "",
            f"**降級個股**（共 {len(downs)} 檔，前 5）：",
            "",
            "| Stock | 舊 | 新 | Δ |",
            "|-------|----|----|---|",
        ]
        for delta, sid, old_t, new_t in downs[:5]:
            lines.append(f"| {sid} | {old_t} | {new_t} | {delta} |")
        if not downs:
            lines.append("| （無） | — | — | — |")
        lines.append("")

    # 寫到 run 目錄
    run_path = os.path.join(out_dir, "TIERING_REPORT.md")
    with open(run_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # 也覆寫 docs/TIERING_REPORT.md
    docs_path = os.path.join(BASE_DIR, "docs", "TIERING_REPORT.md")
    try:
        with open(docs_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as e:
        print(f"  [WARN] 無法寫 docs/TIERING_REPORT.md: {e}")


def _print_phase_complete(run_id, out_dir, elapsed_secs, all_results, templates, sids):
    from collections import Counter
    counts = Counter()
    for sid in sids:
        for t in templates:
            r = all_results.get(sid, {}).get(t)
            v = r.get("verdict", "N/A") if r else "N/A"
            counts[v] += 1

    total = len(sids) * len(templates)
    print(f"\n{'='*72}")
    print(f"  Phase A SMOKE TEST 完成")
    print(f"{'='*72}")
    print(f"  run_id: {run_id}")
    print(f"  耗時: {elapsed_secs/60:.1f} 分鐘")
    print(f"  {total} 對結果: "
          f"PASS={counts.get('PASS',0)}, "
          f"SUSPICIOUS_PERFECT={counts.get('SUSPICIOUS_PERFECT',0)}, "
          f"WEAK={counts.get('WEAK',0)}, "
          f"FAIL={counts.get('FAIL',0)}, "
          f"DD_BREACH={counts.get('DD_BREACH',0)}, "
          f"INSUFFICIENT={counts.get('INSUFFICIENT',0)}")
    print(f"")
    print(f"  輸出檔案:")
    print(f"    - {out_dir}\\comparison.csv")
    print(f"    - {out_dir}\\per_stock_best.yaml")
    print(f"    - {out_dir}\\summary.md")
    for t in templates:
        print(f"    - {out_dir}\\{t}.yaml")
    print(f"")
    print(f"  請使用者 review 上述檔案。確認 OK 後，執行：")
    print(f"    python main.py auto_iterate --resume {run_id} --universe all")
    print(f"{'='*72}\n")


# ── Main entry point ─────────────────────────────────────────────

def run_auto_iterate(
    universe: list,
    n_trials: int = 80,
    timeout_per_pair: int = 300,
    train_start: str = "2017-01-01",
    train_end: str = "2023-12-31",
    test_start: str = "2024-01-01",
    test_end: str = "2026-04-22",
    templates_to_run: list = None,
    resume_run_id: str = None,
    bootstrap_iterations: int = 1000,
    wide_search: bool = False,
) -> str:
    """Run per-stock per-template optimisation. Returns run_id string.

    wide_search: if True, swap sample_template_params → sample_template_params_wide
    (≈3× wider numeric ranges) for the F-tier rescue experiment. Generators and
    every other code path remain unchanged.
    """
    if wide_search:
        from src.strategy.auto_iterate.templates_wide import (
            sample_template_params_wide as sample_template_params,
        )
        print("  [WIDE-SEARCH] using widened search space (templates_wide.py)")
    else:
        from src.strategy.auto_iterate.templates import sample_template_params
    from src.strategy.auto_iterate.backtest_one import backtest_one, score_single, classify
    from src.strategy.auto_iterate.chip_fetcher import fetch_chip_data
    from src.strategy.auto_iterate.bootstrap import bootstrap_pf_ci
    from src.strategy.auto_iterate.tiering import (
        assign_tier, passes_holdout, HOLDOUT_PERIODS, TIER_RULES,
    )
    from src.strategy.backtest.engine import BacktestConfig

    if templates_to_run is None:
        templates_to_run = TEMPLATE_NAMES

    # run_id 用秒精度 + 原子嘗試。多 process 同秒啟動時用 mkdir(exist_ok=False)
    # 來避免 race condition：若該 dir 已被別人建立 → 立刻加 PID 後綴重試。
    if resume_run_id:
        run_id = resume_run_id
        out_dir = os.path.join(BASE_DIR, "output", "auto_iterate", run_id)
        os.makedirs(out_dir, exist_ok=True)
    else:
        base = datetime.now().strftime("%Y%m%d_%H%M%S")
        for attempt in [base, f"{base}_{os.getpid()}"]:
            try:
                out_dir = os.path.join(BASE_DIR, "output", "auto_iterate", attempt)
                os.makedirs(out_dir, exist_ok=False)
                run_id = attempt
                break
            except FileExistsError:
                continue
        else:
            # Both attempts failed (extremely rare) → fall back to allowing existing
            run_id = f"{base}_{os.getpid()}_{int(time.time()*1000) % 1000}"
            out_dir = os.path.join(BASE_DIR, "output", "auto_iterate", run_id)
            os.makedirs(out_dir, exist_ok=True)

    start_time = time.time()

    # ── 0050 benchmark (informational only) ──────────────────────
    print(f"\n  載入 0050 benchmark CAGR (informational)...")
    mkt_df = _load_ohlcv("0050")
    if mkt_df is not None:
        bm0050_train = _bnh_cagr(mkt_df, train_start, train_end)
        bm0050_test  = _bnh_cagr(mkt_df, test_start,  test_end)
        print(f"  0050: train={bm0050_train:+.1%}  test={bm0050_test:+.1%}")
    else:
        bm0050_train = bm0050_test = float("nan")
        print(f"  [WARN] 0050 資料不存在，alpha_vs_0050 欄位將為 null")

    # ── Load stock OHLCV ─────────────────────────────────────────
    print(f"\n  載入 OHLCV 資料（{len(universe)} 檔）...")
    universe_data: dict = {}
    skipped = []
    for sid in universe:
        df = _load_ohlcv(sid)
        if df is None or len(df) < 250:
            skipped.append(sid)
            continue
        universe_data[sid] = df
    if skipped:
        print(f"  [SKIP] 資料不足：{', '.join(skipped)}")
    print(f"  可用：{len(universe_data)} 檔")

    # ── Market regime (for T1) ────────────────────────────────────
    print(f"  載入大盤 regime (0050)...")
    regime = _load_regime()

    # ── Chip data (for chip_momentum / chip_streak) ───────────────
    chip_cache: dict = {}
    chip_templates = {"chip_momentum", "chip_streak"}
    if any(t in chip_templates for t in templates_to_run):
        print(f"  抓籌碼資料 (chip_*)，共 {len(universe_data)} 檔...")
        for sid in universe_data:
            try:
                chip_df = fetch_chip_data(sid)
                chip_cache[sid] = chip_df
                print(f"  [OK] {sid} 籌碼")
                time.sleep(1.2)
            except Exception as e:
                print(f"  [WARN] {sid} 籌碼失敗：{e}")
                chip_cache[sid] = pd.DataFrame()

    # ── Revenue data (for monthly_revenue_event) ──────────────────
    revenue_cache: dict = {}
    if "monthly_revenue_event" in templates_to_run:
        from src.strategy.auto_iterate.revenue_fetcher import load_revenue_data
        print(f"  載入月營收資料 (monthly_revenue_event)，共 {len(universe_data)} 檔...")
        miss = []
        for sid in universe_data:
            rev_df = load_revenue_data(sid)
            revenue_cache[sid] = rev_df
            if rev_df.empty:
                miss.append(sid)
        if miss:
            print(f"  [WARN] {len(miss)} 檔缺月營收 cache，將 HOLD-only：{','.join(miss[:10])}"
                  + ("..." if len(miss) > 10 else ""))
            print(f"        執行 'python main.py fetch-revenue --all' 補抓")

    # ── BacktestConfig ────────────────────────────────────────────
    cfg  = _load_cfg()
    fees = cfg["fees"]
    train_bt = BacktestConfig(fees=fees, start_date=train_start, end_date=train_end,
                              initial_capital=100_000, max_position_pct=1.0)
    test_bt  = BacktestConfig(fees=fees, start_date=test_start,  end_date=test_end,
                              initial_capital=100_000, max_position_pct=1.0)

    # ── P1: Holdout configs (A_new / B / C) ───────────────────────
    # warmup 從前 1 年起算（讓 SMA200 等指標暖機），但只算 segment 區間 trades
    # 簡化做法：直接用 segment 區間 backtest（不另設 warmup），
    # 因為 OHLCV 載入時已含完整歷史；engine 會 filter dates，
    # signals generator 會用 df 全段算指標 → warmup 自然有
    # ※ engine.run_per_stock 內 _filter_dates 只裁掉 backtest 區間，
    #   但 signals 已在外面用全段 df 算好（templates.py），所以指標不會缺暖機
    holdout_bt_cfgs = {}
    for seg, periods in HOLDOUT_PERIODS.items():
        holdout_bt_cfgs[seg] = BacktestConfig(
            fees=fees,
            start_date=periods["start"],
            end_date=periods["end"],
            initial_capital=100_000,
            max_position_pct=1.0,
        )

    # ── Main loop ─────────────────────────────────────────────────
    all_results: dict = {}
    total_pairs = len(universe_data) * len(templates_to_run)
    done = 0

    for sid in universe_data:
        df_full     = universe_data[sid]
        chip_data   = chip_cache.get(sid, pd.DataFrame())
        revenue_data = revenue_cache.get(sid, pd.DataFrame())
        regime_alnd = regime.reindex(df_full.index, method="ffill").fillna("BEAR")
        all_results[sid] = {}

        for template in templates_to_run:
            t0 = time.time()

            db_path     = os.path.join(out_dir, f"{template}.db")
            storage_url = "sqlite:///" + db_path.replace(os.sep, "/")
            study_name  = f"{template}_{sid}"

            study = optuna.create_study(
                study_name=study_name,
                storage=storage_url,
                direction="maximize",
                load_if_exists=True,
                sampler=optuna.samplers.TPESampler(
                    n_startup_trials=min(20, max(n_trials // 4, 5)),
                    seed=42,
                ),
            )

            completed = sum(1 for t in study.trials if t.state.name == "COMPLETE")
            remaining = max(0, n_trials - completed)

            if remaining > 0:
                def _make_obj(s, df, tmpl, cd, rd, ra, bt):
                    def _obj(trial):
                        try:
                            p = sample_template_params(tmpl, trial)
                            m = backtest_one(s, df, tmpl, p, bt,
                                             regime=ra, chip_data=cd,
                                             revenue_data=rd)
                            return score_single(m)
                        except Exception:
                            return -10.0
                    return _obj

                study.optimize(
                    _make_obj(sid, df_full, template, chip_data,
                              revenue_data, regime_alnd, train_bt),
                    n_trials=remaining,
                    timeout=timeout_per_pair,
                )

            # Hold-out validation with best params
            try:
                best_params = study.best_params
                train_m = backtest_one(sid, df_full, template, best_params,
                                       train_bt, regime=regime_alnd,
                                       chip_data=chip_data, revenue_data=revenue_data)
                test_m  = backtest_one(sid, df_full, template, best_params,
                                       test_bt,  regime=regime_alnd,
                                       chip_data=chip_data, revenue_data=revenue_data)
                verdict    = classify(test_m)
                best_score = study.best_value
            except Exception as e:
                best_params = {}
                _nan = float("nan")
                train_m = test_m = {
                    "n_trades": 0, "profit_factor": _nan, "max_drawdown": _nan,
                    "win_rate": _nan, "expectancy": _nan, "avg_win": _nan,
                    "avg_loss": _nan, "cagr": _nan, "bnh_cagr": _nan,
                    "trades_pnl_pct": [],
                }
                verdict    = "FAIL"
                best_score = float("nan")

            # ── P1: Bootstrap PF + 三段 holdout + tier 評估 ─────────
            test_trades_pnl = test_m.get("trades_pnl_pct", []) or []
            boot = bootstrap_pf_ci(test_trades_pnl,
                                   n_iterations=bootstrap_iterations, seed=42)

            holdout_metrics = {}      # {seg: metrics dict or None}
            holdout_passes  = {}      # {seg: bool}

            if best_params:
                df_first_date = df_full.index[0] if len(df_full) > 0 else None
                for seg, bt_cfg_seg in holdout_bt_cfgs.items():
                    seg_start_ts = pd.Timestamp(HOLDOUT_PERIODS[seg]["start"])
                    # 若股票上市晚於 segment 起點 → N/A（None 中性，不算 fail）
                    if df_first_date is None or df_first_date > seg_start_ts:
                        holdout_metrics[seg] = None
                        holdout_passes[seg]  = None
                        continue
                    try:
                        h_m = backtest_one(sid, df_full, template, best_params,
                                           bt_cfg_seg, regime=regime_alnd,
                                           chip_data=chip_data,
                                           revenue_data=revenue_data)
                        holdout_metrics[seg] = h_m
                        # passes_holdout v2 回傳 True/False/None
                        holdout_passes[seg]  = passes_holdout(h_m, seg)
                    except Exception as e:
                        from src.utils import log_error
                        log_error("auto_iterate.holdout", sid,
                                  f"{template} {seg} 失敗: {e}")
                        holdout_metrics[seg] = None
                        holdout_passes[seg]  = None
            else:
                for seg in holdout_bt_cfgs:
                    holdout_metrics[seg] = None
                    holdout_passes[seg]  = None

            tier, tier_reason = assign_tier(test_m, boot, holdout_passes)
            position_pct = TIER_RULES.get(tier, {}).get("pos_max", 0.0)

            elapsed = time.time() - t0
            done   += 1

            exp_v  = test_m.get("expectancy", float("nan"))
            pf_v   = test_m.get("profit_factor", float("nan"))
            n_v    = test_m.get("n_trades", 0)
            dd_v   = test_m.get("max_drawdown", float("nan"))
            exp_s  = f"{exp_v:+.1%}" if not (isinstance(exp_v, float) and math.isnan(exp_v)) else "N/A"
            pf_s   = f"{pf_v:.2f}"   if not (isinstance(pf_v,  float) and (math.isnan(pf_v) or math.isinf(pf_v))) else "inf"
            dd_s   = f"{dd_v:.0%}"   if not (isinstance(dd_v,  float) and math.isnan(dd_v)) else "N/A"
            sc_s   = f"{best_score:.2f}" if not (isinstance(best_score, float) and math.isnan(best_score)) else "N/A"

            pflo = boot.get("pf_lower", float("nan"))
            pflo_s = (f"{pflo:.2f}"
                      if not (isinstance(pflo, float) and math.isnan(pflo))
                      else " nan")
            ho_s = "".join(["O" if holdout_passes.get(s, False) else "X"
                            for s in ("A_new", "B", "C")])

            print(f"  [{done:>3}/{total_pairs}] {sid} x {template:<20}: "
                  f"score={sc_s:>5}  exp={exp_s:>6}  pf={pf_s:>5}  "
                  f"n={n_v:>2}  dd={dd_s:>5}  pflo={pflo_s:>4}  "
                  f"ho={ho_s}  tier={tier}  ({elapsed:.0f}s)")

            all_results[sid][template] = {
                "best_params": best_params,
                "train":       train_m,
                "test":        test_m,
                "verdict":     verdict,
                # P1 新增欄位
                "bootstrap":   boot,
                "holdouts":    {seg: holdout_passes[seg] for seg in holdout_passes},
                "holdout_metrics": holdout_metrics,
                "tier":        tier,
                "tier_reason": tier_reason,
                "position_pct_recommended": position_pct,
            }

    # ── Write output files ────────────────────────────────────────
    elapsed_total = time.time() - start_time
    valid_sids    = list(universe_data.keys())

    print(f"\n  寫出結果檔案...")
    for t in templates_to_run:
        _write_template_yaml(out_dir, t, valid_sids, all_results,
                             train_start, train_end, test_start, test_end,
                             bm0050_train, bm0050_test)

    rows = _write_comparison_csv(out_dir, valid_sids, all_results,
                                 templates_to_run, bm0050_test)
    _write_per_stock_best(out_dir, valid_sids, all_results,
                          templates_to_run, rows, bm0050_test)
    _write_summary_md(out_dir, run_id, valid_sids, all_results,
                      templates_to_run, rows, elapsed_total,
                      bm0050_train, bm0050_test)
    # P1: tiering report
    _write_tiering_report(out_dir, run_id, valid_sids, all_results,
                          templates_to_run)

    _print_phase_complete(run_id, out_dir, elapsed_total,
                          all_results, templates_to_run, valid_sids)
    return run_id
