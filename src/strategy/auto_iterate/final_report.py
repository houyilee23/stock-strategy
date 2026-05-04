"""Generate AUTO_ITERATE_FINAL_REPORT.md from a completed run.

Reads:
  output/auto_iterate/{run_id}/per_stock_best.yaml
  output/auto_iterate/{run_id}/comparison.csv (for new-template contribution)
  config/watchlists.yaml (for grouping by Takeshi/Katie/Research)

Writes:
  docs/AUTO_ITERATE_FINAL_REPORT.md           — narrative, user-facing
  config/per_stock_recommendations.yaml        — machine-readable for signals/optimize

Usage:
  python -m src.strategy.auto_iterate.final_report 20260424_220634
"""
from __future__ import annotations
import os
import sys
import yaml
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional

from src.strategy.auto_iterate.bnh import (
    compute_bnh_for_stock,
    compute_market_bnh,
    estimate_dividend_yield,
    BNH_START,
    BNH_END,
)
from src.strategy.auto_iterate.tiering import assign_bnh_tier, BNH_TIER_RULES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))


# ── Helpers ──────────────────────────────────────────────────────

def _load_per_stock_best(run_id: str) -> dict:
    path = os.path.join(BASE_DIR, "output", "auto_iterate", run_id, "per_stock_best.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_watchlists() -> Dict[str, List[str]]:
    """All groups except `exception` (data-broken stocks).

    Includes `research_todo` so the unified report can show coverage on
    the expanded 32-stock universe added in 2026-04 (auto_iterate v3+).
    """
    path = os.path.join(BASE_DIR, "config", "watchlists.yaml")
    with open(path, encoding="utf-8") as f:
        wl = yaml.safe_load(f) or {}
    return {k: list(v) for k, v in wl.items() if k != "exception"}


def _stock_label(sid: str) -> str:
    """Lookup short label from watchlist comments — fallback to sid."""
    # Inline names for the 71 stocks (39 original + 32 research_todo).
    names = {
        # ── Original 39 (Takeshi/Katie/research) ──
        "0050": "元大台灣50",
        "1227": "佳格", "1301": "台塑", "1303": "南亞", "1326": "台化",
        "1560": "中砂", "1802": "台玻", "1809": "中釉",
        "2002": "中鋼", "2303": "聯電", "2308": "台達電", "2317": "鴻海",
        "2324": "仁寶", "2327": "國巨", "2330": "台積電", "2337": "旺宏",
        "2344": "華邦電", "2345": "智邦", "2360": "致茂", "2379": "瑞昱",
        "2382": "廣達", "2383": "台光電", "2408": "南亞科", "2412": "中華電",
        "2426": "鼎元", "2454": "聯發科", "3008": "大立光", "3017": "奇鋐",
        "3034": "聯詠", "3037": "欣興", "3231": "緯創", "3711": "日月光投控",
        "4938": "和碩", "4958": "臻鼎-KY", "6271": "同欣電", "6505": "台塑化",
        "6515": "穎崴", "6669": "緯穎", "6770": "力積電", "9940": "信義",
        # ── research_todo (32) added 2026-04-26 ──
        # 半導體 / 電子權值
        "2474": "可成", "2376": "技嘉", "2356": "英業達", "2353": "宏碁",
        "5347": "世界先進", "6488": "環球晶", "3661": "世芯-KY",
        # 金融 / 保險
        "2881": "富邦金", "2882": "國泰金", "2884": "玉山金", "2885": "元大金",
        "2886": "兆豐金", "2891": "中信金", "2892": "第一金", "2883": "開發金",
        "5880": "合庫金", "5871": "中租-KY",
        # 電信
        "3045": "台灣大", "4904": "遠傳",
        # 傳產 / 食品 / 民生
        "1216": "統一", "1101": "台泥", "1102": "亞泥",
        "2207": "和泰車", "2105": "正新", "9921": "巨大", "9914": "美利達",
        "2912": "統一超", "1402": "遠東新", "1605": "華新", "2027": "大成鋼",
        # 航運 / 航空
        "2603": "長榮", "2615": "萬海", "2618": "長榮航",
        # ETF
        "0056": "元大高股息", "006208": "富邦台50",
        "00878": "國泰永續高股息", "00919": "群益台灣精選高息",
        "00940": "元大台灣價值高息",
    }
    return names.get(sid, sid)


def _fmt_pct(x: Optional[float], plus: bool = False) -> str:
    if x is None:
        return "N/A"
    s = f"{x*100:.1f}%"
    if plus and x > 0:
        s = "+" + s
    return s


def _fmt_pf(x: Optional[float]) -> str:
    if x is None:
        return "N/A"
    return f"{x:.2f}"


def _fmt_holdout(d: dict) -> str:
    parts = []
    for seg in ("A_new", "B", "C"):
        v = d.get(seg)
        if v is True:
            parts.append(f"{seg}=O")
        elif v is False:
            parts.append(f"{seg}=X")
        else:
            parts.append(f"{seg}=NA")
    return " ".join(parts)


# ── Main report writer ───────────────────────────────────────────

def write_final_report(run_id: str) -> None:
    doc = _load_per_stock_best(run_id)
    benchmark = doc.pop("benchmark_0050_test_cagr", None)
    borderline = doc.pop("borderline_candidates", {})

    # Filter to pure stock entries
    stock_entries = {sid: e for sid, e in doc.items()
                     if isinstance(e, dict) and "best_template" in e}

    # Tier groupings
    tier_buckets: Dict[str, List[Tuple[str, dict]]] = defaultdict(list)
    for sid, e in stock_entries.items():
        tier_buckets[e.get("tier", "F")].append((sid, e))
    for tier in tier_buckets:
        tier_buckets[tier].sort(
            key=lambda x: (x[1].get("test_expectancy") or 0),
            reverse=True,
        )

    # Watchlist coverage
    wl = _load_watchlists()
    wl_coverage: Dict[str, Dict[str, List[Tuple[str, dict]]]] = {}
    for list_name, sids in wl.items():
        bucket = {"tradeable": [], "fail": []}
        for sid in sids:
            e = stock_entries.get(sid)
            if e is None:
                continue
            tier = e.get("tier", "F")
            if tier in ("S", "A", "B", "C"):
                bucket["tradeable"].append((sid, e))
            else:
                bucket["fail"].append((sid, e))
        bucket["tradeable"].sort(
            key=lambda x: ({"S":5,"A":4,"B":3,"C":2}.get(x[1].get("tier","F"),0),
                           x[1].get("test_expectancy") or 0),
            reverse=True,
        )
        wl_coverage[list_name] = bucket

    # Template usage among tradeable (S/A/B/C)
    template_use = Counter()
    for sid, e in stock_entries.items():
        if e.get("tier") in ("S", "A", "B", "C"):
            template_use[e.get("best_template", "?")] += 1

    # New templates added in v2 (Phase 3) and v3/v4 (Phase 6).
    new_templates = {
        # v2 (low-sample / 大型權值股 / 傳產) — Phase 3
        "volume_breakout", "gap_continuation",
        "low_vol_pullback", "bollinger_squeeze",
        # v3/v4 (台股 alpha 特化) — Phase 6
        "chip_streak", "monthly_revenue_event",
    }
    new_template_wins = sum(c for t, c in template_use.items() if t in new_templates)
    old_template_wins = sum(c for t, c in template_use.items() if t not in new_templates)

    # ── BNH evaluation for F-tier stocks ────────────────────────
    # Compute once and reuse for both markdown and YAML.
    mkt_bnh = compute_market_bnh()
    bnh_results: Dict[str, dict] = {}  # sid -> {tier, reason, metrics, div_yield}
    for sid, e in stock_entries.items():
        if e.get("tier") != "F":
            continue
        m = compute_bnh_for_stock(sid)
        dy = estimate_dividend_yield(sid)
        bnh_tier, bnh_reason = assign_bnh_tier(sid, m, mkt_bnh, dy)
        bnh_results[sid] = {
            "tier": bnh_tier,
            "reason": bnh_reason,
            "metrics": m,
            "div_yield": dy,
        }

    # ── Compose markdown ─────────────────────────────────────────

    L = []
    L.append(f"# Auto-Iterate Final Report — {run_id}")
    L.append("")
    L.append(f"**Generated**: 自動執行（Auto Mode）— Q5=(b) 激進改寫授權範圍內")
    # Universe is the actual stock count from per_stock_best.yaml; sources may
    # vary across runs (single run vs merged multi-run).
    n_total = sum(len(b) for b in tier_buckets.values())
    L.append(f"**Universe**: {n_total} 檔（涵蓋 Takeshi / Katie / Research / Research_todo 去重後合集）")
    L.append(f"**0050 test CAGR**: {_fmt_pct(benchmark, plus=True) if benchmark is not None else 'N/A'}")
    L.append("")

    # Section 1: Tier Summary
    operable = sum(len(tier_buckets.get(t, [])) for t in "SABC")
    total = sum(len(b) for b in tier_buckets.values())
    L.append("## 1. Tier 分布")
    L.append("")
    L.append("| Tier | 數量 | 部位上限 | 描述 |")
    L.append("|------|------|----------|------|")
    tier_meta = [
        ("S", "100%", "ROBUST：訊號模式直接用"),
        ("A", "50%",  "STRONG：可用，建議 50% 部位"),
        ("B", "30%",  "MODERATE：可用，30% 部位 + 嚴格 trailing stop"),
        ("C", "15%",  "WEAK：紙上交易 3 個月再啟用，最大 15%"),
        ("F", "0%",   "FAIL：移出 universe，建議走組合模式或買 0050"),
    ]
    for tier, pos, desc in tier_meta:
        cnt = len(tier_buckets.get(tier, []))
        L.append(f"| {tier} | {cnt} | {pos} | {desc} |")
    L.append("")
    L.append(f"**可操作標的（S+A+B+C）= {operable} / {total}**  （目標 ≥ 20）")
    L.append("")

    # Section 2: Watchlist coverage
    L.append("## 2. Watchlist 覆蓋率")
    L.append("")
    for list_name in ("Takeshi", "Katie", "research", "research_todo"):
        bucket = wl_coverage.get(list_name, {"tradeable": [], "fail": []})
        n_t = len(bucket["tradeable"])
        n_f = len(bucket["fail"])
        n_total = n_t + n_f
        L.append(f"### {list_name} — 可操作 {n_t} / {n_total}")
        L.append("")
        if n_t == 0:
            L.append("（無可操作）")
            L.append("")
            continue
        L.append("| Stock | 名稱 | Tier | 模板 | 部位上限 | Exp | PF | n |")
        L.append("|-------|------|------|------|----------|-----|----|---|")
        for sid, e in bucket["tradeable"]:
            L.append(
                f"| {sid} | {_stock_label(sid)} | {e.get('tier','?')} | "
                f"{e.get('best_template','?')} | "
                f"{int((e.get('position_pct_recommended') or 0)*100)}% | "
                f"{_fmt_pct(e.get('test_expectancy'), plus=True)} | "
                f"{_fmt_pf(e.get('test_pf'))} | "
                f"{e.get('test_n_trades', 0)} |"
            )
        L.append("")

    # Section 3: 新模板貢獻
    L.append("## 3. 新模板貢獻分析（Phase 3 + Phase 6 加入）")
    L.append("")
    L.append("| 模板 | 用途 | tradeable 命中數 |")
    L.append("|------|------|------------------|")
    template_purpose = {
        # Phase 3 (v2)
        "volume_breakout":        "LOW_SAMPLE 大型權值股（去 trend filter）",
        "gap_continuation":       "事件驅動跳空 + 收紅",
        "low_vol_pullback":       "傳產慢牛低波動回檔",
        "bollinger_squeeze":      "BB 壓縮後爆量突破",
        # Phase 6 (v3/v4) — 台股特化
        "chip_streak":            "三大法人連續 ≥N 天買超（台股法人持續性 alpha）",
        "monthly_revenue_event":  "月營收 YoY > X% + 公布日跳空（台股獨有日曆事件）",
    }
    for t in ("volume_breakout", "gap_continuation",
              "low_vol_pullback", "bollinger_squeeze",
              "chip_streak", "monthly_revenue_event"):
        cnt = template_use.get(t, 0)
        note = ""
        if cnt == 0:
            note = "  ⚠️ 0 命中（其他模板覆蓋更好）"
        L.append(f"| {t} | {template_purpose[t]} | {cnt}{note} |")
    L.append("")
    L.append(f"**新模板貢獻**：{new_template_wins} / {operable} tradeable "
             f"（舊模板：{old_template_wins}）")
    L.append("")
    L.append("### 新模板拯救的個股（best_template ∈ 新四模板）")
    L.append("")
    saved = []
    for sid, e in stock_entries.items():
        if e.get("tier") in ("S", "A", "B", "C") and e.get("best_template") in new_templates:
            saved.append((sid, e))
    saved.sort(key=lambda x: ({"S":5,"A":4,"B":3,"C":2}.get(x[1].get("tier","F"),0),
                              x[1].get("test_expectancy") or 0), reverse=True)
    if saved:
        L.append("| Stock | 名稱 | Tier | 模板 | Exp | PF_lower |")
        L.append("|-------|------|------|------|-----|----------|")
        for sid, e in saved:
            boot = e.get("bootstrap", {})
            L.append(
                f"| {sid} | {_stock_label(sid)} | {e.get('tier','?')} | "
                f"{e.get('best_template','?')} | "
                f"{_fmt_pct(e.get('test_expectancy'), plus=True)} | "
                f"{_fmt_pf((boot or {}).get('pf_lower'))} |"
            )
    else:
        L.append("（無）")
    L.append("")

    # Section 4: 各 Tier 完整列表
    L.append("## 4. 各 Tier 完整清單")
    L.append("")
    for tier in ("S", "A", "B", "C"):
        bucket = tier_buckets.get(tier, [])
        if not bucket:
            continue
        L.append(f"### Tier {tier} （{len(bucket)} 檔）")
        L.append("")
        L.append("| Stock | 名稱 | 模板 | Exp | PF | n | DD | PF_lower | Holdouts |")
        L.append("|-------|------|------|-----|----|---|----|----------|----------|")
        for sid, e in bucket:
            boot = e.get("bootstrap", {}) or {}
            ho   = e.get("holdouts", {}) or {}
            dd   = e.get("test_max_dd")
            L.append(
                f"| {sid} | {_stock_label(sid)} | {e.get('best_template','?')} | "
                f"{_fmt_pct(e.get('test_expectancy'), plus=True)} | "
                f"{_fmt_pf(e.get('test_pf'))} | "
                f"{e.get('test_n_trades', 0)} | "
                f"{_fmt_pct(dd) if dd is not None else 'N/A'} | "
                f"{_fmt_pf(boot.get('pf_lower'))} | "
                f"{_fmt_holdout(ho)} |"
            )
        L.append("")

    # Section 5: 行動建議
    L.append("## 5. 給 Takeshi/Katie 的行動建議")
    L.append("")
    L.append("### 立即可用（S+A）")
    sa = [(sid, e) for tier in ("S", "A") for sid, e in tier_buckets.get(tier, [])]
    if sa:
        for sid, e in sa:
            L.append(f"- **{sid} {_stock_label(sid)}** "
                     f"({e.get('best_template')}) — Tier {e.get('tier')}, "
                     f"建議部位上限 {int((e.get('position_pct_recommended') or 0)*100)}%")
    else:
        L.append("（無）")
    L.append("")
    L.append("### 條件可用（B），加嚴格 trailing stop")
    bs = [(sid, e) for sid, e in tier_buckets.get("B", [])]
    if bs:
        for sid, e in bs:
            L.append(f"- **{sid} {_stock_label(sid)}** "
                     f"({e.get('best_template')}) — Tier B, 建議部位 30%")
    else:
        L.append("（無）")
    L.append("")
    L.append("### 觀察（C），先紙上交易 3 個月")
    cs = [(sid, e) for sid, e in tier_buckets.get("C", [])]
    if cs:
        for sid, e in cs:
            L.append(f"- **{sid} {_stock_label(sid)}** "
                     f"({e.get('best_template')}) — Tier C, 最大部位 15%")
    else:
        L.append("（無）")
    L.append("")

    # Section 6: 限制與後續
    L.append("## 6. 已知限制與後續建議")
    L.append("")
    if operable < 15:
        L.append(f"- **未達目標**：tradeable={operable} < 15。下一輪建議：")
        L.append("  1. **Q5(b) 激進改寫**：考慮 multi-template ensemble（≥2 模板同意才進場）")
        L.append("  2. **擴充 universe**：watchlists_todo 共 38 檔尚未測試（金融 / 食品 / 航運）")
        L.append("  3. **Indicator-driven scaling**：重新 enable scaling，但用 ATR-based 智能規則")
    else:
        L.append(f"- **達標**：tradeable={operable} ≥ 15，可進入訊號模式生產使用")
        L.append("- **後續優化**：擴充 watchlists_todo 38 檔（金融 / 食品 / 航運）以增加 universe")
    L.append("- **F-tier 個股建議**：走組合模式（top-N）、BNH 候選（見下節）、或直接持有 0050")
    L.append("- **Holdout caveat**：A_new (2010-2016) 多數 NA — 因 universe 多為 2010 後上市；"
             "B (2018) / C (2022) 樣本常 < 5，依 v2 tri-state 邏輯不算 fail")
    L.append("")

    # Section 7: BNH 候選
    L.append("## 7. BNH 候選（不適合 timing 但適合長持）")
    L.append("")
    L.append(f"評估期間：{BNH_START} ~ {BNH_END}（≈8 年），對 F-tier 個股做平行評估。")
    L.append("")
    if mkt_bnh is None:
        L.append("（0050 baseline 無法計算，跳過 BNH 評估。）")
        L.append("")
    else:
        L.append(
            f"**0050 baseline**：CAGR={_fmt_pct(mkt_bnh['cagr'], plus=True)}，"
            f"|MaxDD|={_fmt_pct(abs(mkt_bnh['max_dd']))}，Sharpe={mkt_bnh['sharpe']:.2f}"
        )
        L.append("")
        L.append("### BNH Tier 條件")
        L.append("")
        L.append("| Tier | CAGR vs 0050 | MaxDD | div_yield | 部位上限 |")
        L.append("|------|--------------|-------|-----------|----------|")
        L.append("| BNH_S | ≥ +5% | ≤ 40% | — | 50% |")
        L.append("| BNH_A | ≥ 0% | ≤ 50% | — | 30% |")
        L.append("| BNH_B | ≥ -3% | — | ≥ 4% | 20% |")
        L.append("| F | 其他 | | | 0%（建議走 0050 / 組合模式） |")
        L.append("")

        # Group BNH results
        bnh_buckets: Dict[str, List[Tuple[str, dict]]] = defaultdict(list)
        for sid, r in bnh_results.items():
            bnh_buckets[r["tier"]].append((sid, r))
        for k in bnh_buckets:
            bnh_buckets[k].sort(
                key=lambda x: (x[1]["metrics"] or {}).get("cagr", 0),
                reverse=True,
            )

        for tier in ("BNH_S", "BNH_A", "BNH_B"):
            bucket = bnh_buckets.get(tier, [])
            if not bucket:
                continue
            L.append(f"### {tier} （{len(bucket)} 檔）")
            L.append("")
            L.append("| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | Sharpe | 股息率 | 部位上限 |")
            L.append("|-------|------|------|---------|--------|--------|--------|----------|")
            pos_max = BNH_TIER_RULES[tier]["pos_max"]
            for sid, r in bucket:
                m = r["metrics"]
                if m is None:
                    continue
                diff = m["cagr"] - mkt_bnh["cagr"]
                dy = r["div_yield"]
                L.append(
                    f"| {sid} | {_stock_label(sid)} | "
                    f"{_fmt_pct(m['cagr'], plus=True)} | "
                    f"{_fmt_pct(diff, plus=True)} | "
                    f"{_fmt_pct(abs(m['max_dd']))} | "
                    f"{m['sharpe']:.2f} | "
                    f"{(_fmt_pct(dy) if dy is not None else 'N/A')} | "
                    f"{int(pos_max*100)}% |"
                )
            L.append("")

        # F (BNH 也不合格) 的 F-tier 列表
        bnh_f = bnh_buckets.get("F", [])
        if bnh_f:
            L.append(f"### F-tier 中也不適合 BNH （{len(bnh_f)} 檔）")
            L.append("")
            L.append("這些股票既無法 timing 也輸 0050，建議改走組合模式或直接買 0050。")
            L.append("")
            L.append("| Stock | 名稱 | CAGR | vs 0050 | |MaxDD| | 股息率 |")
            L.append("|-------|------|------|---------|--------|--------|")
            for sid, r in bnh_f:
                m = r["metrics"]
                if m is None:
                    L.append(f"| {sid} | {_stock_label(sid)} | N/A | N/A | N/A | N/A |")
                    continue
                diff = m["cagr"] - mkt_bnh["cagr"]
                dy = r["div_yield"]
                L.append(
                    f"| {sid} | {_stock_label(sid)} | "
                    f"{_fmt_pct(m['cagr'], plus=True)} | "
                    f"{_fmt_pct(diff, plus=True)} | "
                    f"{_fmt_pct(abs(m['max_dd']))} | "
                    f"{(_fmt_pct(dy) if dy is not None else 'N/A')} |"
                )
            L.append("")

        n_bnh_total = sum(len(bnh_buckets.get(t, [])) for t in ("BNH_S", "BNH_A", "BNH_B"))
        L.append(
            f"**BNH 救回統計**：{n_bnh_total} / {len(bnh_results)} F-tier 個股可改走 BNH。"
        )
        L.append("")

    L.append("---")
    L.append(f"_Run dir: `output/auto_iterate/{run_id}/`_")
    L.append(f"_Detail: `TIERING_REPORT.md` / `per_stock_best.yaml` / `comparison.csv`_")

    out_path = os.path.join(BASE_DIR, "docs", "AUTO_ITERATE_FINAL_REPORT.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"  寫出 {out_path}")
    return operable, total, dict(template_use), bnh_results


# ── per_stock_recommendations.yaml ───────────────────────────────

def write_recommendations(run_id: str, bnh_results: Optional[dict] = None) -> None:
    """Generate machine-readable per-stock recommendation YAML for signals/optimize use.

    Args:
        run_id: auto_iterate run id.
        bnh_results: optional pre-computed BNH evaluations from
            ``write_final_report()``. If None, BNH is computed here on the fly
            for each F-tier stock.
    """
    doc = _load_per_stock_best(run_id)
    doc.pop("benchmark_0050_test_cagr", None)
    doc.pop("borderline_candidates", None)

    # If BNH not pre-computed, compute now (so write_recommendations is standalone-safe).
    if bnh_results is None:
        mkt_bnh = compute_market_bnh()
        bnh_results = {}
        for sid, e in doc.items():
            if not isinstance(e, dict) or "best_template" not in e:
                continue
            if e.get("tier") != "F":
                continue
            m = compute_bnh_for_stock(sid)
            dy = estimate_dividend_yield(sid)
            bnh_tier, bnh_reason = assign_bnh_tier(sid, m, mkt_bnh, dy)
            bnh_results[sid] = {
                "tier": bnh_tier,
                "reason": bnh_reason,
                "metrics": m,
                "div_yield": dy,
            }

    out: Dict[str, dict] = {}
    for sid, e in doc.items():
        if not isinstance(e, dict) or "best_template" not in e:
            continue
        tier = e.get("tier", "F")
        bnh_info = bnh_results.get(sid) if tier == "F" else None
        bnh_tier = (bnh_info or {}).get("tier")
        bnh_metrics = (bnh_info or {}).get("metrics") or {}
        bnh_pos_max = (
            BNH_TIER_RULES[bnh_tier]["pos_max"]
            if bnh_tier in BNH_TIER_RULES
            else 0.0
        )
        out[sid] = {
            "tier": tier,
            "template": e.get("best_template"),
            "position_pct_max": e.get("position_pct_recommended", 0.0),
            "test_expectancy":  e.get("test_expectancy"),
            "test_pf":          e.get("test_pf"),
            "test_n_trades":    e.get("test_n_trades"),
            "test_max_dd":      e.get("test_max_dd"),
            "tradeable":        tier in ("S", "A", "B", "C"),
            "params_ref":       e.get("params_ref"),
            "name":             _stock_label(sid),
            # BNH parallel evaluation (only set for F-tier; None otherwise)
            "bnh_tier":         bnh_tier,
            "bnh_position_pct_max": bnh_pos_max if bnh_tier else 0.0,
            "bnh_cagr":         bnh_metrics.get("cagr"),
            "bnh_max_dd":       bnh_metrics.get("max_dd"),
            "bnh_div_yield":    (bnh_info or {}).get("div_yield"),
            "bnh_holdable":     bnh_tier in ("BNH_S", "BNH_A", "BNH_B"),
        }

    out_path = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")
    header = (
        "# Auto-generated by src/strategy/auto_iterate/final_report.py\n"
        f"# Run: {run_id}\n"
        "# DO NOT EDIT MANUALLY — re-run auto_iterate to refresh.\n"
        "# tradeable=true => use position_pct_max in signals/optimize.\n"
        "# tradeable=false => skip (走組合模式 or 0050).\n\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.dump(out, f, allow_unicode=True, default_flow_style=False, sort_keys=True)
    print(f"  寫出 {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.strategy.auto_iterate.final_report <run_id>")
        sys.exit(1)
    run_id = sys.argv[1]
    operable, total, template_use, bnh_results = write_final_report(run_id)
    write_recommendations(run_id, bnh_results=bnh_results)
    n_bnh = sum(1 for r in bnh_results.values()
                if r["tier"] in ("BNH_S", "BNH_A", "BNH_B"))
    print(f"\n  Tradeable = {operable} / {total}")
    print(f"  BNH 救回 = {n_bnh} / {len(bnh_results)} F-tier")
    print(f"  Template use: {template_use}")
