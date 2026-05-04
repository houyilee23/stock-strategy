"""Cross-period holdout validation for PASS pairs (frozen best_params, no re-optimise).

Reads per_stock_best.yaml, finds all PASS pairs, runs 3 independent backtest windows
on frozen params, and writes docs/HOLDOUT_VALIDATION.md.

Usage:
    python scripts/validate_holdout.py [--run-id 20260423_151107]
"""
import sys
import os
import math
import argparse
import time
import yaml
import requests
import pandas as pd
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.strategy.auto_iterate.templates import TEMPLATE_GENERATORS
from src.strategy.auto_iterate.chip_fetcher import fetch_chip_data, load_chip_data
from src.strategy.backtest.engine import Backtester, BacktestConfig
from src.strategy.runner import _load_adj_ohlcv

# ── Validation windows ────────────────────────────────────────────
WINDOWS = [
    {"label": "A", "warmup": "2013-01-01", "start": "2014-01-01", "end": "2016-12-31"},
    {"label": "B", "warmup": "2017-01-01", "start": "2018-01-01", "end": "2018-12-31"},
    {"label": "C", "warmup": "2021-01-01", "start": "2022-01-01", "end": "2022-12-31"},
]

# A_new: expanded segment 2010-2016 (warmup from 2009-01-01)
WINDOW_A_NEW = {"label": "A_new", "warmup": "2009-01-01", "start": "2010-01-01", "end": "2016-12-31"}

# chip_momentum FinMind data starts 2013-01-02; use this as effective start for chip stocks
CHIP_EFFECTIVE_WINDOW = {"label": "A_new", "warmup": "2012-07-01", "start": "2013-01-02", "end": "2016-12-31"}

# ── Pass thresholds per window ────────────────────────────────────
def window_pass(label: str, metrics: dict) -> bool:
    n   = metrics.get("n_trades", 0)
    pf  = metrics.get("profit_factor", 0.0) or 0.0
    exp = metrics.get("expectancy", float("nan"))
    dd  = abs(metrics.get("max_drawdown", 0.0) or 0.0)
    if math.isnan(pf) or math.isinf(pf):
        pf = 0.0
    if label == "A":
        exp_ok = (not (isinstance(exp, float) and math.isnan(exp))) and exp >= 0.01
        return n >= 3 and pf >= 1.0 and exp_ok
    else:  # B / C
        return pf >= 0.8 and dd <= 0.40


def _safe_fmt(v, fmt=".1%"):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "N/A"
    return format(v, fmt)


# ── Load config ───────────────────────────────────────────────────
def _load_fees() -> dict:
    with open(os.path.join(ROOT, "config", "strategy.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)["fees"]


# ── Run one backtest segment ──────────────────────────────────────
def run_segment(sid, df_full, template, params, win, fees, regime, chip_data):
    """Return metrics dict for one (sid, template, window)."""
    bt_cfg = BacktestConfig(
        fees=fees,
        start_date=win["start"],
        end_date=win["end"],
        initial_capital=100_000,
        max_position_pct=1.0,
    )
    try:
        signals = TEMPLATE_GENERATORS[template](
            df_full, params, regime=regime, chip_data=chip_data
        )
        result = Backtester(bt_cfg).run_per_stock(sid, df_full, signals)

        eq = result.equity_curve
        if len(eq) >= 2 and eq.iloc[0] > 0:
            yrs  = (eq.index[-1] - eq.index[0]).days / 365
            cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / max(yrs, 0.5)) - 1 if yrs > 0 else float("nan")
        else:
            cagr = float("nan")

        return {
            "n_trades":      result.n_trades,
            "win_rate":      result.win_rate,
            "profit_factor": result.profit_factor,
            "expectancy":    result.expectancy,
            "avg_win":       result.avg_win,
            "avg_loss":      result.avg_loss,
            "max_drawdown":  result.max_drawdown,
            "cagr":          cagr,
        }
    except Exception as e:
        print(f"    [ERR] {sid} x {template} window {win['label']}: {e}")
        nan = float("nan")
        return {"n_trades": 0, "win_rate": nan, "profit_factor": nan,
                "expectancy": nan, "avg_win": nan, "avg_loss": nan,
                "max_drawdown": nan, "cagr": nan}


# ── Overall verdict ───────────────────────────────────────────────
def overall_verdict(passes: dict) -> str:
    a, b, c = passes["A"], passes["B"], passes["C"]
    if a and b and c:
        return "ROBUST"
    if not a and b and c:
        return "TRAINED-FIT"
    if a and not (b and c):
        return "SURVIVES-BEAR-ONLY"
    # a passes or doesn't, but B or C fails
    if not a:
        return "TRAINED-FIT"
    return "BEAR-FRAGILE"


# ── Ensure chip data covers warmup ────────────────────────────────
def ensure_chip_coverage(sid: str, earliest_needed: str) -> pd.DataFrame:
    chip_df = load_chip_data(sid)
    if chip_df.empty:
        print(f"    [CHIP] {sid}: 無快取，從 FinMind 補抓...")
        chip_df = fetch_chip_data(sid, force=True)
        time.sleep(1.2)
        return chip_df

    earliest_date = pd.Timestamp(earliest_needed)
    if chip_df.index.min() <= earliest_date:
        return chip_df

    print(f"    [CHIP] {sid}: 快取起始 {chip_df.index.min().date()} > {earliest_needed}，重抓...")
    try:
        chip_df = fetch_chip_data(sid, force=True)
        time.sleep(1.2)
    except Exception as e:
        print(f"    [WARN] {sid} 補抓失敗：{e}，用既有快取")
    return chip_df


# ── Main ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="20260423_151107")
    args = parser.parse_args()

    run_dir = os.path.join(ROOT, "output", "auto_iterate", args.run_id)
    best_path = os.path.join(run_dir, "per_stock_best.yaml")
    docs_dir  = os.path.join(ROOT, "docs")

    print(f"\n  讀取 {best_path}")
    with open(best_path, encoding="utf-8") as f:
        best_yaml = yaml.safe_load(f)

    # Collect PASS pairs
    pairs = []
    for sid, entry in best_yaml.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("verdict") != "PASS":
            continue
        tmpl = entry.get("best_template")
        if not tmpl or tmpl == "NONE":
            continue
        # Load best_params from template yaml
        tmpl_path = os.path.join(run_dir, f"{tmpl}.yaml")
        with open(tmpl_path, encoding="utf-8") as f:
            tmpl_doc = yaml.safe_load(f)
        params = tmpl_doc.get("per_stock", {}).get(sid, {}).get("best_params", {})
        pairs.append({"sid": sid, "template": tmpl, "params": params})

    print(f"  找到 {len(pairs)} 對 PASS pairs")
    for p in pairs:
        print(f"    {p['sid']} x {p['template']}")

    fees   = _load_fees()
    regime = pd.Series(dtype=str)  # dummy; T1 uses regime but defaults to BULL if missing

    # Load regime (0050)
    try:
        from src.strategy.signals.regime import detect_regime
        mkt_df = _load_adj_ohlcv("0050")
        if mkt_df is not None:
            import yaml as _yaml
            with open(os.path.join(ROOT, "config", "strategy.yaml"), encoding="utf-8") as f:
                _cfg = _yaml.safe_load(f)
            regime = detect_regime(mkt_df, _cfg["regime"]["ma_long"])
    except Exception as e:
        print(f"  [WARN] regime 載入失敗：{e}（T1 將視為 BULL）")

    # Earliest warmup needed: 2013-01-01
    chip_earliest = "2013-01-01"

    # ── Run validation ────────────────────────────────────────────
    results = []
    total = len(pairs) * len(WINDOWS)
    done  = 0
    t0_all = time.time()

    for p in pairs:
        sid      = p["sid"]
        template = p["template"]
        params   = p["params"]

        print(f"\n  [{sid} x {template}]")

        # Load OHLCV (need data from earliest warmup)
        df_full = _load_adj_ohlcv(sid)
        if df_full is None or len(df_full) < 50:
            print(f"    [SKIP] OHLCV 不存在")
            continue

        # Load chip data if needed
        chip_data = pd.DataFrame()
        if template == "chip_momentum":
            chip_data = ensure_chip_coverage(sid, chip_earliest)

        # Align regime to df index
        regime_aligned = regime.reindex(df_full.index, method="ffill").fillna("BULL")

        seg_results = {}
        seg_passes  = {}

        for win in WINDOWS:
            t0 = time.time()
            m  = run_segment(sid, df_full, template, params, win,
                             fees, regime_aligned, chip_data)
            elapsed = time.time() - t0
            done   += 1

            passed = window_pass(win["label"], m)
            seg_results[win["label"]] = m
            seg_passes[win["label"]]  = passed

            n   = m["n_trades"]
            exp = _safe_fmt(m.get("expectancy"), ".1%")
            pf  = m.get("profit_factor", float("nan"))
            pf_s = f"{pf:.2f}" if not (isinstance(pf, float) and (math.isnan(pf) or math.isinf(pf))) else "inf"
            dd  = _safe_fmt(m.get("max_drawdown"), ".1%")
            ok  = "PASS" if passed else "FAIL"

            print(f"    Window {win['label']} ({win['start']}~{win['end']}): "
                  f"n={n} exp={exp} pf={pf_s} dd={dd} → {ok}  ({elapsed:.0f}s)")

        verdict = overall_verdict(seg_passes)
        print(f"    => {verdict}")

        results.append({
            "sid":      sid,
            "template": template,
            "passes":   seg_passes,
            "metrics":  seg_results,
            "verdict":  verdict,
        })

    elapsed_total = time.time() - t0_all
    print(f"\n  完成 {len(results)} 對，耗時 {elapsed_total/60:.1f} 分鐘")

    # ── Write HOLDOUT_VALIDATION.md ───────────────────────────────
    lines = [
        "# Holdout Validation 跨期驗證報告",
        "",
        f"**run_id**: `{args.run_id}`  ",
        f"**PASS pairs 驗證數**: {len(results)}  ",
        f"**驗證段**: A=2014-2016（資料不足 2017 前）/ B=2018 / C=2022  ",
        f"**params**: 凍結自 optuna 最佳解，不重新優化  ",
        "",
        "## 驗證標準",
        "",
        "| 段 | 通過條件 |",
        "|----|---------|",
        "| A（2014-2016，樣本稀） | expectancy >= 1% AND PF >= 1.0 AND n >= 3 |",
        "| B（2018，震盪熊市） | PF >= 0.8 AND MaxDD <= 40% |",
        "| C（2022，熊市）   | PF >= 0.8 AND MaxDD <= 40% |",
        "",
        "## 總評定義",
        "",
        "| 總評 | 說明 |",
        "|------|------|",
        "| ROBUST | A/B/C 全過 |",
        "| TRAINED-FIT | A 不過（params 對 2017-2023 訓練期過擬合）|",
        "| BEAR-FRAGILE | B 或 C 不過（熊市失效）|",
        "| SURVIVES-BEAR-ONLY | A 不過，B/C 過（熊市可用但更早期不行）|",
        "",
        "---",
        "",
        "## 完整結果表",
        "",
        "| Stock | Template | A_pass | A_exp/PF/n/DD | B_pass | B_PF/DD | C_pass | C_PF/DD | 總評 |",
        "|-------|----------|--------|--------------|--------|---------|--------|---------|------|",
    ]

    for r in results:
        sid = r["sid"]
        tmpl = r["template"]
        passes = r["passes"]
        metrics = r["metrics"]

        def _row_seg(lbl):
            m = metrics.get(lbl, {})
            n   = m.get("n_trades", 0)
            exp = _safe_fmt(m.get("expectancy"), ".1%")
            pf  = m.get("profit_factor", float("nan"))
            pf_s = f"{pf:.2f}" if pf and not (isinstance(pf, float) and (math.isnan(pf) or math.isinf(pf))) else "?"
            dd  = _safe_fmt(m.get("max_drawdown"), ".1%")
            ok  = "✓" if passes.get(lbl) else "✗"
            return ok, f"{exp}/{pf_s}/n={n}/{dd}"

        a_ok, a_detail = _row_seg("A")
        b_ok, b_detail = _row_seg("B")
        c_ok, c_detail = _row_seg("C")
        # B/C simpler: PF/DD only
        def _bc(lbl):
            m = metrics.get(lbl, {})
            pf = m.get("profit_factor", float("nan"))
            pf_s = f"{pf:.2f}" if pf and not (isinstance(pf, float) and (math.isnan(pf) or math.isinf(pf))) else "?"
            dd = _safe_fmt(m.get("max_drawdown"), ".1%")
            ok = "✓" if passes.get(lbl) else "✗"
            return ok, f"{pf_s}/{dd}"

        b_ok, b_detail = _bc("B")
        c_ok, c_detail = _bc("C")

        lines.append(
            f"| {sid} | {tmpl} | {a_ok} | {a_detail} | {b_ok} | {b_detail} | {c_ok} | {c_detail} | **{r['verdict']}** |"
        )

    # ── Grouped recommendations ───────────────────────────────────
    groups = {"ROBUST": [], "TRAINED-FIT": [], "BEAR-FRAGILE": [], "SURVIVES-BEAR-ONLY": []}
    for r in results:
        groups[r["verdict"]].append(f"{r['sid']}×{r['template']}")

    lines += [
        "",
        "---",
        "",
        "## 分組推薦",
        "",
        "### 第一線：ROBUST（A/B/C 全過，直接接訊號模式）",
        "",
    ]
    if groups["ROBUST"]:
        for item in groups["ROBUST"]:
            lines.append(f"- {item}")
    else:
        lines.append("（無）")

    lines += [
        "",
        "### 第二線：TRAINED-FIT（A 不過，但 B/C 過 → 可用，縮小部位）",
        "",
    ]
    if groups["TRAINED-FIT"]:
        for item in groups["TRAINED-FIT"]:
            lines.append(f"- {item}  ← params 可能過擬合 2017-2023，縮小至半倉")
    else:
        lines.append("（無）")

    lines += [
        "",
        "### 第三線：BEAR-FRAGILE（B 或 C 熊市失效 → 牛市可用，需手動退場機制）",
        "",
    ]
    if groups["BEAR-FRAGILE"]:
        for item in groups["BEAR-FRAGILE"]:
            lines.append(f"- {item}  ← 牛轉熊時手動退場，或設大盤 regime 過濾")
    else:
        lines.append("（無）")

    lines += [
        "",
        "### 其他：SURVIVES-BEAR-ONLY（A 不過，B/C 過）",
        "",
    ]
    if groups["SURVIVES-BEAR-ONLY"]:
        for item in groups["SURVIVES-BEAR-ONLY"]:
            lines.append(f"- {item}")
    else:
        lines.append("（無）")

    lines += [
        "",
        "---",
        "",
        f"*驗證耗時：{elapsed_total/60:.1f} 分鐘，共 {len(results)*3} 個 backtest*",
    ]

    out_path = os.path.join(docs_dir, "HOLDOUT_VALIDATION.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  報告寫出：{out_path}")

    # ── Regime filter comparison for 2308 + 2330 ─────────────────
    _run_regime_comparison(pairs, results, fees, regime, docs_dir)

    # ── V2: expanded A segment 2010-2016 ──────────────────────────
    _run_v2_comparison(pairs, results, fees, regime, docs_dir, args.run_id)


def _run_regime_comparison(pairs, baseline_results, fees, regime, docs_dir):
    """Re-run A/B/C for 2308×donchian and 2330×donchian with regime_filter=True."""
    from src.strategy.signals.template_donchian import generate_donchian

    REGIME_PAIRS = {("2308", "donchian_breakout"), ("2330", "donchian_breakout")}

    # Build lookup: (sid, template) → baseline result
    baseline = {(r["sid"], r["template"]): r for r in baseline_results}

    regime_rows = []  # list of dicts for each (sid, template, filter_on/off)

    print(f"\n{'='*60}")
    print(f"  Regime filter 對比：2308 + 2330 × donchian_breakout")
    print(f"{'='*60}")

    for p in pairs:
        sid      = p["sid"]
        template = p["template"]
        if (sid, template) not in REGIME_PAIRS:
            continue

        df_full = _load_adj_ohlcv(sid)
        if df_full is None:
            continue

        regime_aligned = regime.reindex(df_full.index, method="ffill").fillna("BULL")
        params = p["params"]

        # We already have baseline (filter=False) from the main run
        base = baseline.get((sid, template))
        if base is None:
            continue

        # Run with regime_filter=True
        print(f"\n  [{sid} x {template}] regime_filter=True")
        seg_r_on  = {}
        seg_p_on  = {}

        for win in WINDOWS:
            t0 = time.time()
            # Use generate_donchian directly (bypasses TEMPLATE_GENERATORS)
            bt_cfg = BacktestConfig(
                fees=fees,
                start_date=win["start"],
                end_date=win["end"],
                initial_capital=100_000,
                max_position_pct=1.0,
            )
            try:
                signals = generate_donchian(df_full, params, regime_filter=True)
                result  = Backtester(bt_cfg).run_per_stock(sid, df_full, signals)
                eq = result.equity_curve
                if len(eq) >= 2 and eq.iloc[0] > 0:
                    yrs  = (eq.index[-1] - eq.index[0]).days / 365
                    cagr = (eq.iloc[-1]/eq.iloc[0])**(1/max(yrs,0.5))-1 if yrs>0 else float("nan")
                else:
                    cagr = float("nan")
                m = {
                    "n_trades":      result.n_trades,
                    "win_rate":      result.win_rate,
                    "profit_factor": result.profit_factor,
                    "expectancy":    result.expectancy,
                    "avg_win":       result.avg_win,
                    "avg_loss":      result.avg_loss,
                    "max_drawdown":  result.max_drawdown,
                    "cagr":          cagr,
                }
            except Exception as e:
                print(f"    [ERR] {e}")
                nan = float("nan")
                m = {"n_trades": 0, "profit_factor": nan, "expectancy": nan,
                     "max_drawdown": nan, "win_rate": nan, "cagr": nan,
                     "avg_win": nan, "avg_loss": nan}

            passed = window_pass(win["label"], m)
            seg_r_on[win["label"]]  = m
            seg_p_on[win["label"]]  = passed
            elapsed = time.time() - t0

            n   = m["n_trades"]
            exp = _safe_fmt(m.get("expectancy"), ".1%")
            pf  = m.get("profit_factor", float("nan"))
            pf_s = f"{pf:.2f}" if not (isinstance(pf, float) and (math.isnan(pf) or math.isinf(pf))) else "inf"
            dd  = _safe_fmt(m.get("max_drawdown"), ".1%")
            ok  = "PASS" if passed else "FAIL"
            print(f"    Window {win['label']}: n={n} exp={exp} pf={pf_s} dd={dd} → {ok}  ({elapsed:.0f}s)")

        verdict_on = overall_verdict(seg_p_on)
        print(f"    => {verdict_on}")

        regime_rows.append({
            "sid": sid, "template": template,
            "base_metrics":   base["metrics"],
            "base_passes":    base["passes"],
            "base_verdict":   base["verdict"],
            "filter_metrics": seg_r_on,
            "filter_passes":  seg_p_on,
            "filter_verdict": verdict_on,
        })

    # ── Write HOLDOUT_VALIDATION_REGIME.md ───────────────────────
    def _fmt_seg(metrics, passes, lbl):
        m    = metrics.get(lbl, {})
        n    = m.get("n_trades", 0)
        exp  = _safe_fmt(m.get("expectancy"), ".1%")
        pf   = m.get("profit_factor", float("nan"))
        pf_s = f"{pf:.2f}" if pf and not (isinstance(pf, float) and (math.isnan(pf) or math.isinf(pf))) else "?"
        dd   = _safe_fmt(m.get("max_drawdown"), ".1%")
        ok   = "✓" if passes.get(lbl) else "✗"
        return ok, f"n={n} exp={exp} PF={pf_s} dd={dd}"

    lines = [
        "# Holdout Validation — Regime Filter 對比報告",
        "",
        "**對象**: 2308×donchian_breakout, 2330×donchian_breakout  ",
        "**比較**: regime_filter=False（原）vs True（0050 close > MA200）  ",
        "**params**: 凍結，不重新 tune  ",
        "",
        "## Regime Filter 說明",
        "",
        "entry 條件新增第 4 條：",
        "```",
        "0050.close > SMA(0050.close, 200)   # 大盤在 200MA 之上才允許進場",
        "```",
        "預期效果：2018/2022 熊市期間 0050 跌破 MA200，自動阻擋進場，",
        "使 B/C 段 n_trades ≈ 0（INSUFFICIENT）而非虧損進場。",
        "",
        "## A 段（2014-2016）對比",
        "",
        "**標準**：expectancy >= 1% AND PF >= 1.0 AND n >= 3  ",
        "**期望**：regime_filter=True 的 A 段通過率不應下降（2014-2016 牛市為主）",
        "",
        "| Stock | Filter | A_pass | n | exp | PF | DD |",
        "|-------|--------|--------|---|-----|----|----|",
    ]
    for row in regime_rows:
        for (fl, m_dict, p_dict) in [
            ("False", row["base_metrics"], row["base_passes"]),
            ("True",  row["filter_metrics"], row["filter_passes"]),
        ]:
            ok, detail = _fmt_seg(m_dict, p_dict, "A")
            lines.append(f"| {row['sid']} | {fl} | {ok} | {detail} |")

    lines += [
        "",
        "## B 段（2018 熊市）對比",
        "",
        "**標準**：PF >= 0.8 AND MaxDD <= 40%  ",
        "**期望**：regime_filter=True → n_trades 降低（被 MA200 過濾），PF 提升或 INSUFFICIENT",
        "",
        "| Stock | Filter | B_pass | n | exp | PF | DD |",
        "|-------|--------|--------|---|-----|----|----|",
    ]
    for row in regime_rows:
        for (fl, m_dict, p_dict) in [
            ("False", row["base_metrics"], row["base_passes"]),
            ("True",  row["filter_metrics"], row["filter_passes"]),
        ]:
            ok, detail = _fmt_seg(m_dict, p_dict, "B")
            lines.append(f"| {row['sid']} | {fl} | {ok} | {detail} |")

    lines += [
        "",
        "## C 段（2022 熊市）對比",
        "",
        "**標準**：PF >= 0.8 AND MaxDD <= 40%  ",
        "**期望**：同 B 段",
        "",
        "| Stock | Filter | C_pass | n | exp | PF | DD |",
        "|-------|--------|--------|---|-----|----|----|",
    ]
    for row in regime_rows:
        for (fl, m_dict, p_dict) in [
            ("False", row["base_metrics"], row["base_passes"]),
            ("True",  row["filter_metrics"], row["filter_passes"]),
        ]:
            ok, detail = _fmt_seg(m_dict, p_dict, "C")
            lines.append(f"| {row['sid']} | {fl} | {ok} | {detail} |")

    lines += [
        "",
        "## 總評對比",
        "",
        "| Stock | Template | Filter=False | Filter=True |",
        "|-------|----------|-------------|------------|",
    ]
    for row in regime_rows:
        lines.append(
            f"| {row['sid']} | {row['template']} "
            f"| **{row['base_verdict']}** | **{row['filter_verdict']}** |"
        )

    lines += [
        "",
        "## 結論",
        "",
    ]
    for row in regime_rows:
        sid = row["sid"]
        bv  = row["base_verdict"]
        fv  = row["filter_verdict"]
        bp  = row["base_passes"]
        fp  = row["filter_passes"]

        improved = sum(fp.values()) > sum(bp.values())
        a_intact = fp.get("A") or not bp.get("A")  # A not degraded

        if fv == "ROBUST":
            lines.append(f"- **{sid}** ✓ ROBUST with regime filter → 直接接訊號模式")
        elif improved and a_intact:
            lines.append(f"- **{sid}** 改善（{bv} → {fv}），A 段未退步 → regime filter 有效，可使用")
        elif not a_intact:
            lines.append(f"- **{sid}** A 段被 filter 破壞（{bv} → {fv}）→ filter 過於嚴格，不建議加")
        else:
            lines.append(f"- **{sid}** 無改善（{bv} → {fv}）→ regime filter 對此股無效")

    out_path = os.path.join(docs_dir, "HOLDOUT_VALIDATION_REGIME.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  報告寫出：{out_path}")


def _run_v2_comparison(pairs, baseline_results, fees, regime, docs_dir, run_id):
    """Run A_new (2010-2016) for all PASS pairs; write HOLDOUT_VALIDATION_V2.md."""

    # Build lookup: (sid, template) → baseline result (contains A_old metrics)
    baseline = {(r["sid"], r["template"]): r for r in baseline_results}

    # Late-listed stocks that have no data before 2017 → mark as N/A
    LATE_LISTED = {"3711", "6515", "6770"}

    print(f"\n{'='*60}")
    print(f"  V2 擴大驗證段 A：2010-2016（warmup 2009-01-01）")
    print(f"{'='*60}")

    v2_rows = []

    for p in pairs:
        sid      = p["sid"]
        template = p["template"]

        # Determine effective A_new window for this pair
        if sid in LATE_LISTED:
            # Stock listed after 2016 — cannot cover A_new; record as SKIP
            base = baseline.get((sid, template))
            a_old = base["metrics"].get("A", {}) if base else {}
            a_old_pass = base["passes"].get("A", False) if base else False
            v2_rows.append({
                "sid": sid, "template": template,
                "a_old_metrics": a_old, "a_old_pass": a_old_pass,
                "a_new_metrics": None, "a_new_pass": False,
                "note": f"上市日在 2017 後，無法覆蓋 2010-2016",
            })
            print(f"\n  [{sid} x {template}] SKIP（晚上市）")
            continue

        if template == "chip_momentum":
            win = CHIP_EFFECTIVE_WINDOW
            note = "chip 資料從 2013-01-02 起，有效段 2013-2016"
        else:
            win = WINDOW_A_NEW
            note = ""

        df_full = _load_adj_ohlcv(sid)
        if df_full is None or len(df_full) < 50:
            print(f"    [SKIP] {sid} OHLCV 不存在")
            continue

        # Determine actual data start
        data_start = df_full.index.min()
        effective_start = pd.Timestamp(win["start"])
        if data_start > effective_start:
            note = f"股票資料從 {data_start.date()} 起（晚於窗口起始）"
            effective_start = data_start

        chip_data = pd.DataFrame()
        if template == "chip_momentum":
            chip_data = ensure_chip_coverage(sid, win["warmup"])

        regime_aligned = regime.reindex(df_full.index, method="ffill").fillna("BULL")

        print(f"\n  [{sid} x {template}] A_new ({win['start']}~{win['end']})")
        t0 = time.time()
        m_new = run_segment(sid, df_full, template, p["params"], win,
                            fees, regime_aligned, chip_data)
        elapsed = time.time() - t0

        a_new_pass = window_pass("A", m_new)

        n   = m_new["n_trades"]
        exp = _safe_fmt(m_new.get("expectancy"), ".1%")
        pf  = m_new.get("profit_factor", float("nan"))
        pf_s = f"{pf:.2f}" if not (isinstance(pf, float) and (math.isnan(pf) or math.isinf(pf))) else "?"
        dd  = _safe_fmt(m_new.get("max_drawdown"), ".1%")
        ok  = "PASS" if a_new_pass else "FAIL"
        print(f"    n={n} exp={exp} pf={pf_s} dd={dd} → {ok}  ({elapsed:.0f}s)")

        base = baseline.get((sid, template))
        a_old = base["metrics"].get("A", {}) if base else {}
        a_old_pass = base["passes"].get("A", False) if base else False

        v2_rows.append({
            "sid": sid, "template": template,
            "a_old_metrics": a_old, "a_old_pass": a_old_pass,
            "a_new_metrics": m_new, "a_new_pass": a_new_pass,
            "note": note,
        })

    # ── Write HOLDOUT_VALIDATION_V2.md ───────────────────────────
    def _fmt_a(m, passed):
        if m is None:
            return "N/A（晚上市）"
        n   = m.get("n_trades", 0)
        exp = _safe_fmt(m.get("expectancy"), ".1%")
        pf  = m.get("profit_factor", float("nan"))
        pf_s = f"{pf:.2f}" if pf and not (isinstance(pf, float) and (math.isnan(pf) or math.isinf(pf))) else "?"
        dd  = _safe_fmt(m.get("max_drawdown"), ".1%")
        ok  = "✓" if passed else "✗"
        return f"{ok} n={n} exp={exp} PF={pf_s} dd={dd}"

    lines = [
        "# Holdout Validation V2 — 擴大 A 段（2010-2016）對比報告",
        "",
        f"**run_id**: `{run_id}`  ",
        "**A_old**: 2014-2016（warmup 2013-01-01）  ",
        "**A_new**: 2010-2016（warmup 2009-01-01；chip_momentum 有效起 2013-01-02）  ",
        "**B/C 段**: 不變（2018 / 2022）  ",
        "**params**: 凍結自 optuna 最佳解，不重新優化  ",
        "",
        "## 目的",
        "",
        "驗證段 A 從 3 年擴展到 7 年後，各對策略的表現變化：",
        "- 若 A_new 通過：策略在更長牛熊週期均可生存 → 可信度提升",
        "- 若 A_new 退步：2014 前的資料增加了難以應對的市場狀態",
        "",
        "## 說明",
        "",
        "| 情況 | 原因 |",
        "|------|------|",
        "| chip_momentum 有效段 2013-2016 | FinMind 籌碼資料從 2013-01-02 起，2010-2012 無籌碼訊號 |",
        "| 3711/6515/6770 標記 N/A | 股票上市日在 2017 年後，無法覆蓋 2010-2016 |",
        "",
        "## A 段對比結果表",
        "",
        "**通過標準**：expectancy >= 1% AND PF >= 1.0 AND n >= 3  ",
        "",
        "| Stock | Template | A_old（2014-2016） | A_new（2010-2016） | A_new_pass | 備註 |",
        "|-------|----------|-------------------|-------------------|------------|------|",
    ]

    for row in v2_rows:
        sid   = row["sid"]
        tmpl  = row["template"]
        a_old = _fmt_a(row["a_old_metrics"], row["a_old_pass"])
        a_new = _fmt_a(row["a_new_metrics"], row["a_new_pass"])
        a_new_pass = "✓" if row["a_new_pass"] else ("N/A" if row["a_new_metrics"] is None else "✗")
        note  = row.get("note", "")
        lines.append(f"| {sid} | {tmpl} | {a_old} | {a_new} | {a_new_pass} | {note} |")

    # Summary counts
    rows_with_data = [r for r in v2_rows if r["a_new_metrics"] is not None]
    a_old_pass_cnt = sum(1 for r in rows_with_data if r["a_old_pass"])
    a_new_pass_cnt = sum(1 for r in rows_with_data if r["a_new_pass"])
    both_pass      = sum(1 for r in rows_with_data if r["a_old_pass"] and r["a_new_pass"])
    old_only       = sum(1 for r in rows_with_data if r["a_old_pass"] and not r["a_new_pass"])
    new_only       = sum(1 for r in rows_with_data if not r["a_old_pass"] and r["a_new_pass"])
    both_fail      = sum(1 for r in rows_with_data if not r["a_old_pass"] and not r["a_new_pass"])

    lines += [
        "",
        "## 統計摘要",
        "",
        f"| 指標 | 值 |",
        f"|------|----|",
        f"| 有效比較對數（排除晚上市） | {len(rows_with_data)} |",
        f"| A_old 通過數 | {a_old_pass_cnt} |",
        f"| A_new 通過數 | {a_new_pass_cnt} |",
        f"| 兩者皆過 | {both_pass} |",
        f"| 僅 A_old 過（A_new 退步） | {old_only} |",
        f"| 僅 A_new 過（A_new 新增） | {new_only} |",
        f"| 兩者皆不過 | {both_fail} |",
        "",
        "## 分析",
        "",
    ]

    if old_only > 0:
        lines.append("### A_old 通過但 A_new 退步的對（2010-2013 段造成拖累）")
        lines.append("")
        for row in rows_with_data:
            if row["a_old_pass"] and not row["a_new_pass"]:
                m = row["a_new_metrics"]
                n = m.get("n_trades", 0)
                exp = _safe_fmt(m.get("expectancy"), ".1%")
                lines.append(f"- **{row['sid']}×{row['template']}**：A_new n={n} exp={exp}（2010-2013 段可能拉低整體）")
        lines.append("")

    if new_only > 0:
        lines.append("### A_new 新增通過的對（更長窗口反而更好）")
        lines.append("")
        for row in rows_with_data:
            if not row["a_old_pass"] and row["a_new_pass"]:
                m = row["a_new_metrics"]
                n = m.get("n_trades", 0)
                exp = _safe_fmt(m.get("expectancy"), ".1%")
                lines.append(f"- **{row['sid']}×{row['template']}**：A_new n={n} exp={exp}")
        lines.append("")

    if both_pass > 0:
        lines.append("### A_old 和 A_new 均通過（強健策略）")
        lines.append("")
        for row in rows_with_data:
            if row["a_old_pass"] and row["a_new_pass"]:
                lines.append(f"- **{row['sid']}×{row['template']}**")
        lines.append("")

    lines += [
        "## 結論",
        "",
        f"A 段從 2014-2016（3 年）擴展至 2010-2016（7 年）後，"
        f"A_new 通過率 {a_new_pass_cnt}/{len(rows_with_data)}（可比較對），"
        f"A_old 通過率 {a_old_pass_cnt}/{len(rows_with_data)}。",
        "",
        "- 若 A_new 通過率 ≥ A_old：擴大窗口未降低標準，策略在更長期間仍可用",
        "- 若 A_new 通過率 < A_old：2010-2013 段（全球低利率修復期）具有不同市場特性，"
        "params 不完全適應",
        "",
        "*此驗證為補充分析，B/C 段熊市驗證仍是主要判斷依據。*",
    ]

    out_path = os.path.join(docs_dir, "HOLDOUT_VALIDATION_V2.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  報告寫出：{out_path}")


if __name__ == "__main__":
    main()
