"""S/A/B/C/F Tier 分級制度（v2 — bootstrap-first, NA-tolerant）。

把過去「PASS / WEAK / FAIL」二元結果轉成五級，
每級對應建議部位上限（部位大小取代過/不過判斷）。

判斷順序：S → A → B → C → F，第一個全部條件符合就回傳。

v2 與 v1 主要差異（2026-04-24 autonomous run）：
    1. PF_lower 為主要訊號：bootstrap PF 下界夠高 (≥2.0/3.0) 可獨立晉升。
    2. Holdout 三段允許「N/A 中性」(stock 上市晚於 segment 起點)，
       不再把 N/A 視為 fail；用 holdout_pass / holdout_total 比例判斷。
    3. n_min / pf threshold 放寬，承認小樣本 (5-12 trades) 是台股常態。
    4. F 條件保持嚴格 (n<5 或 exp<0)。

Tier 條件總覽（v2 + Q5b-lite low-N rescue）：
    S：PF_lower≥2.0 + Exp≥5% + n≥8 + (任一 holdout PASS 或 PF_lower≥3.0)  → 100%
    A：PF_lower≥1.5 + Exp≥3% + n≥6 + (任一 holdout PASS 或 PF_lower≥2.0)  → 50%
    B：PF_lower≥1.0 + Exp≥2% + n≥5                                          → 30%
    C：PF_lower≥0.7 + Exp≥1% + n≥5                                          → 15%
    C_rescue：n∈[3,4] + raw_PF≥3.0 + Exp≥5% + |DD|≤25% + 無 holdout FAIL    → 15%
              （LOW_SAMPLE 高品質訊號的紙上交易候選）
    F：其他（含 n<3 / Exp<0）                                                → 0%
"""
from __future__ import annotations

import math


# ── Tier 規則表（也提供給報表/runner 使用）─────────────────
TIER_RULES = {
    "S": dict(
        pf_lower=2.0,
        expectancy=0.05,
        n_min=8,
        holdout_required="any_pass OR PF_lower>=3.0",
        pos_max=1.00,
        label="ROBUST：訊號模式直接用，單檔上限 100%",
    ),
    "A": dict(
        pf_lower=1.5,
        expectancy=0.03,
        n_min=6,
        holdout_required="any_pass OR PF_lower>=2.0",
        pos_max=0.50,
        label="STRONG：可用，建議 50% 部位",
    ),
    "B": dict(
        pf_lower=1.0,
        expectancy=0.02,
        n_min=5,
        holdout_required="none (PF_lower 已達標)",
        pos_max=0.30,
        label="MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop",
    ),
    "C": dict(
        pf_lower=0.7,
        expectancy=0.01,
        n_min=5,
        holdout_required="none",
        pos_max=0.15,
        label="WEAK：紙上交易 3 個月再啟用，最大 15%",
    ),
    "D": dict(
        pf_lower=0.5,
        expectancy=0.0,
        n_min=5,
        holdout_required="none",
        pos_max=0.10,
        label="BORDERLINE：策略邊界，僅供紙上交易；最大 10%",
    ),
    "F": dict(
        pf_lower=0.0,
        expectancy=-1.0,
        n_min=0,
        holdout_required="none",
        pos_max=0.00,
        label="FAIL：移出 universe",
    ),
}


# ── BNH (Buy-and-Hold) Tier 規則 ────────────────────────────────
# 給 F-tier 個股的「平行評估」：active timing 失敗，但純持有仍可能贏 0050。
# 比較基準：同期 0050 的 BNH CAGR / MaxDD。
#
# 條件（assign_bnh_tier 順序判斷 BNH_S → BNH_A → BNH_B → F）：
#   BNH_S：CAGR > 0050_CAGR + 5% AND MaxDD ≤ 40%        → pos_max 50%
#   BNH_A：CAGR > 0050_CAGR + 0% AND MaxDD ≤ 50%        → pos_max 30%
#   BNH_B：CAGR ≥ 0050_CAGR - 3% AND div_yield ≥ 4%      → pos_max 20%
#         （防禦型現金流股，輸 0050 一些但有股息墊底）
#   F：    其他（不適合 timing 也不適合長持，建議組合模式或 0050）
BNH_TIER_RULES = {
    "BNH_S": dict(
        cagr_diff_min=0.05,
        max_dd_max=0.40,
        div_yield_min=None,
        pos_max=0.50,
        label="BNH ROBUST：明顯贏 0050 + 風險受控，可長持，部位上限 50%",
    ),
    "BNH_A": dict(
        cagr_diff_min=0.00,
        max_dd_max=0.50,
        div_yield_min=None,
        pos_max=0.30,
        label="BNH STRONG：略勝 0050，可長持，部位上限 30%",
    ),
    "BNH_B": dict(
        cagr_diff_min=-0.03,
        max_dd_max=None,
        div_yield_min=0.04,
        pos_max=0.20,
        label="BNH DIVIDEND：CAGR 接近 0050 + 股息 ≥ 4%，現金流型長持，上限 20%",
    ),
}


def assign_bnh_tier(
    stock_id: str,
    bnh_metrics: dict | None,
    mkt_metrics: dict | None,
    div_yield: float | None = None,
) -> tuple[str, str]:
    """根據 BNH metrics 判斷個股是否適合長期持有。

    與 ``assign_tier()`` 為平行評估：active timing F-tier 個股可能仍是好的
    BNH 候選（如高股息、藍籌權值股）。

    Args:
        stock_id: 股票代號（僅供 reason 使用）。
        bnh_metrics: ``bnh.compute_bnh_metrics()`` 回傳值，
            含 cagr / max_dd / sharpe。None 視為資料不足 → F。
        mkt_metrics: 同 ``compute_bnh_metrics()`` 但 0050 baseline。
            None 時 fallback 到 cagr_diff_min 為「絕對 CAGR」（即 0050 視為 0%）。
        div_yield: 估算年化股息率（小數，e.g. 0.04 = 4%）；
            BNH_B 判斷需要。None 視為 0。

    Returns:
        (tier_str, reason_str)，tier ∈ {"BNH_S", "BNH_A", "BNH_B", "F"}
    """
    if bnh_metrics is None:
        return "F", f"{stock_id}：BNH 資料不足（adjusted 不存在或天數 < 100）"

    cagr = float(bnh_metrics.get("cagr", float("nan")))
    dd = float(bnh_metrics.get("max_dd", float("nan")))
    if _is_nan(cagr):
        return "F", f"{stock_id}：BNH CAGR 為 NaN"
    dd_abs = abs(dd) if not _is_nan(dd) else float("inf")

    mkt_cagr = 0.0
    if mkt_metrics is not None:
        m = float(mkt_metrics.get("cagr", float("nan")))
        if not _is_nan(m):
            mkt_cagr = m
    diff = cagr - mkt_cagr

    dy = float(div_yield) if div_yield is not None else 0.0

    # BNH_S
    s = BNH_TIER_RULES["BNH_S"]
    if diff >= s["cagr_diff_min"] and dd_abs <= s["max_dd_max"]:
        return "BNH_S", (
            f"BNH_S：CAGR={cagr*100:+.1f}% (vs 0050 {mkt_cagr*100:+.1f}%, "
            f"diff={diff*100:+.1f}%) ≥ +5%；|MaxDD|={dd_abs*100:.1f}% ≤ 40%"
        )

    # BNH_A
    a = BNH_TIER_RULES["BNH_A"]
    if diff >= a["cagr_diff_min"] and dd_abs <= a["max_dd_max"]:
        return "BNH_A", (
            f"BNH_A：CAGR={cagr*100:+.1f}% (vs 0050 {mkt_cagr*100:+.1f}%, "
            f"diff={diff*100:+.1f}%) ≥ 0%；|MaxDD|={dd_abs*100:.1f}% ≤ 50%"
        )

    # BNH_B（防禦型現金流）
    b = BNH_TIER_RULES["BNH_B"]
    if diff >= b["cagr_diff_min"] and dy >= b["div_yield_min"]:
        return "BNH_B", (
            f"BNH_B：CAGR={cagr*100:+.1f}% (vs 0050 {mkt_cagr*100:+.1f}%, "
            f"diff={diff*100:+.1f}%) ≥ -3%；div_yield={dy*100:.2f}% ≥ 4%"
        )

    return "F", (
        f"F (BNH 不合格)：CAGR={cagr*100:+.1f}% (diff vs 0050={diff*100:+.1f}%), "
        f"|MaxDD|={dd_abs*100:.1f}%, div_yield={dy*100:.2f}%"
    )


# ── Holdout 段定義（與 docs/HOLDOUT_VALIDATION_V2.md 一致）──
# warmup 從 起始日 - 1 年開始，segment 起點才開始評估
HOLDOUT_PERIODS = {
    "A_new": {"warmup_start": "2009-01-01", "start": "2010-01-01", "end": "2016-12-31"},
    "B":     {"warmup_start": "2017-01-01", "start": "2018-01-01", "end": "2018-12-31"},
    "C":     {"warmup_start": "2021-01-01", "start": "2022-01-01", "end": "2022-12-31"},
}


# ── 各段過關條件（v2 放寬）─────────────────────────────────
# n_min 從 2-3 降到 1-2；PF 從 0.8-1.0 降到 0.7-0.8
HOLDOUT_PASS_CRITERIA = {
    "A_new": {"expectancy": 0.005, "pf": 0.8, "n_min": 2},
    "B":     {"pf": 0.7, "max_dd": 0.45, "n_min": 1},
    "C":     {"pf": 0.7, "max_dd": 0.45, "n_min": 1},
}


def _is_nan(x) -> bool:
    return isinstance(x, float) and math.isnan(x)


def passes_holdout(metrics: dict | None, segment: str):
    """判斷某段 holdout 是否通過。

    Returns:
        True  → PASS
        False → FAIL（有資料但不達標）
        None  → N/A（無資料 / 樣本太少 / 股票上市晚於 segment）
    """
    if metrics is None:
        return None
    crit = HOLDOUT_PASS_CRITERIA.get(segment)
    if crit is None:
        return None

    n = metrics.get("n_trades", 0) or 0
    if n < crit.get("n_min", 1):
        # 樣本太少 → N/A 中性，不算 fail
        return None

    pf = metrics.get("profit_factor", float("nan"))
    if pf is None or _is_nan(pf):
        pf_ok = False
    elif math.isinf(pf):
        pf_ok = True
    else:
        pf_ok = pf >= crit.get("pf", 0)
    if not pf_ok:
        return False

    if "expectancy" in crit:
        exp = metrics.get("expectancy", float("nan"))
        if exp is None or _is_nan(exp) or exp < crit["expectancy"]:
            return False

    if "max_dd" in crit:
        dd = metrics.get("max_drawdown", float("nan"))
        dd_abs = abs(dd) if dd is not None and not _is_nan(dd) else 0.0
        if dd_abs > crit["max_dd"]:
            return False

    return True


def _normalize_pf_lower(boot_pf_lower) -> float:
    """nan / None → 0.0，其餘照舊。"""
    if boot_pf_lower is None or _is_nan(boot_pf_lower):
        return 0.0
    return float(boot_pf_lower)


def _normalize_exp(exp) -> float:
    if exp is None or _is_nan(exp):
        return float("-inf")
    return float(exp)


def _holdout_summary(holdouts: dict) -> tuple[int, int, int, str]:
    """回傳 (pass 數, fail 數, NA 數, 顯示字串)。
    holdouts 值可為 True / False / None。"""
    p = sum(1 for v in holdouts.values() if v is True)
    f = sum(1 for v in holdouts.values() if v is False)
    na = sum(1 for v in holdouts.values() if v is None)
    parts = []
    for seg in ("A_new", "B", "C"):
        v = holdouts.get(seg)
        if v is True:
            parts.append(f"{seg}=O")
        elif v is False:
            parts.append(f"{seg}=X")
        else:
            parts.append(f"{seg}=NA")
    return p, f, na, " ".join(parts)


def assign_tier(
    test_metrics: dict,
    bootstrap_result: dict,
    holdouts: dict,
) -> tuple[str, str]:
    """根據 test 段指標 + bootstrap PF + holdout 結果決定 tier (v2 規則)。

    Args:
        test_metrics: backtest_one() 對 test 段的回傳值（含 n_trades / expectancy）
        bootstrap_result: bootstrap_pf_ci() 的回傳值（含 pf_lower）
        holdouts: {"A_new": bool|None, "B": bool|None, "C": bool|None}
                  None 代表 N/A（中性，不算 fail）

    Returns:
        (tier_letter, reason_str)
    """
    n = test_metrics.get("n_trades", 0) or 0
    exp = _normalize_exp(test_metrics.get("expectancy"))
    pf_lower = _normalize_pf_lower(bootstrap_result.get("pf_lower"))
    raw_pf = test_metrics.get("profit_factor", float("nan"))
    dd = test_metrics.get("max_drawdown", float("nan"))
    dd_abs = abs(dd) if dd is not None and not _is_nan(dd) else float("inf")

    n_pass, n_fail, n_na, ho_str = _holdout_summary(holdouts)
    any_pass = n_pass > 0

    # 負期望值直接 F（不論樣本大小）
    if exp < 0:
        return "F", f"FAIL：test expectancy={exp:+.1%} < 0（負期望值）"

    # ── Q5b-lite C 補救條款：n=3-4 但訊號品質極強的 LOW_SAMPLE 個股 ──
    # 條件：n ∈ [3, 4] AND raw_PF ≥ 3.0 AND exp ≥ 5% AND |DD| ≤ 25% AND 無 holdout FAIL
    # 目的：搶救 BORDERLINE_LOW_N（如 1326 台化、4958 臻鼎、1809 中釉）
    if n in (3, 4):
        raw_pf_ok = (
            raw_pf is not None and not _is_nan(raw_pf)
            and (math.isinf(raw_pf) or raw_pf >= 3.0)
        )
        no_holdout_fail = (n_fail == 0)  # 全 PASS / 全 NA / 混合 PASS+NA 都允許
        if raw_pf_ok and exp >= 0.05 and dd_abs <= 0.25 and no_holdout_fail:
            raw_pf_s = "inf" if math.isinf(raw_pf) else f"{raw_pf:.2f}"
            return "C", (
                f"LOW_N_RESCUE：n={n}, raw_PF={raw_pf_s} ≥ 3.0, "
                f"exp={exp:+.1%} ≥ 5%, |DD|={dd_abs:.0%} ≤ 25%, "
                f"holdout=[{ho_str}]（紙上交易 3 個月）"
            )

    # F：n<5（除非通過 Q5b-lite 補救）
    if n < 5:
        return "F", f"FAIL：test n_trades={n} < 5（樣本不足，未達 LOW_N_RESCUE）"

    pf_lower_s = f"{pf_lower:.2f}"
    exp_s = f"{exp:+.1%}"

    # S：PF_lower≥2.0 + Exp≥5% + n≥8 + (任一 holdout PASS 或 PF_lower≥3.0)
    s_rule = TIER_RULES["S"]
    if (pf_lower >= s_rule["pf_lower"]
            and exp >= s_rule["expectancy"]
            and n >= s_rule["n_min"]
            and (any_pass or pf_lower >= 3.0)):
        gate = "any holdout PASS" if any_pass else "PF_lower≥3.0 自動晉升"
        return "S", (
            f"PF_lower={pf_lower_s} ≥ 2.0, exp={exp_s} ≥ 5%, n={n}≥8, "
            f"holdout=[{ho_str}], gate={gate}"
        )

    # A：PF_lower≥1.5 + Exp≥3% + n≥6 + (任一 holdout PASS 或 PF_lower≥2.0)
    a_rule = TIER_RULES["A"]
    if (pf_lower >= a_rule["pf_lower"]
            and exp >= a_rule["expectancy"]
            and n >= a_rule["n_min"]
            and (any_pass or pf_lower >= 2.0)):
        gate = "any holdout PASS" if any_pass else "PF_lower≥2.0 自動晉升"
        return "A", (
            f"PF_lower={pf_lower_s} ≥ 1.5, exp={exp_s} ≥ 3%, n={n}≥6, "
            f"holdout=[{ho_str}], gate={gate}"
        )

    # B：PF_lower≥1.0 + Exp≥2% + n≥5
    b_rule = TIER_RULES["B"]
    if (pf_lower >= b_rule["pf_lower"]
            and exp >= b_rule["expectancy"]
            and n >= b_rule["n_min"]):
        return "B", (
            f"PF_lower={pf_lower_s} ≥ 1.0, exp={exp_s} ≥ 2%, n={n}≥5, "
            f"holdout=[{ho_str}]"
        )

    # C：PF_lower≥0.7 + Exp≥1%
    c_rule = TIER_RULES["C"]
    if (pf_lower >= c_rule["pf_lower"]
            and exp >= c_rule["expectancy"]
            and n >= c_rule["n_min"]):
        return "C", (
            f"PF_lower={pf_lower_s} ≥ 0.7, exp={exp_s} ≥ 1%, n={n}≥5, "
            f"holdout=[{ho_str}]"
        )

    # ── C_HIGH_QUALITY_RESCUE：n=5-9 高品質訊號但 bootstrap CI 偏寬 ──
    # 條件：n ∈ [5, 9]、raw_PF ≥ 3.0、exp ≥ 5%、|DD| ≤ 25%、無 holdout FAIL
    # 目的：搶救 bootstrap 因小樣本變異大而 PF_lower 不及格，但實際訊號很強的個股
    #       （補 Q5b-lite 在 n=3-4 之外的中樣本段）
    if 5 <= n <= 9:
        raw_pf_ok = (
            raw_pf is not None and not _is_nan(raw_pf)
            and (math.isinf(raw_pf) or raw_pf >= 3.0)
        )
        no_holdout_fail = (n_fail == 0)
        if raw_pf_ok and exp >= 0.05 and dd_abs <= 0.25 and no_holdout_fail:
            raw_pf_s = "inf" if math.isinf(raw_pf) else f"{raw_pf:.2f}"
            return "C", (
                f"C_HIGH_Q_RESCUE：n={n}, raw_PF={raw_pf_s} ≥ 3.0, "
                f"exp={exp_s} ≥ 5%, |DD|={dd_abs:.0%} ≤ 25%, "
                f"holdout=[{ho_str}]（小樣本高品質訊號，紙上交易 3 個月）"
            )

    # D：邊界正期望（PF_lower≥0.5 + exp>0% + n≥5）
    d_rule = TIER_RULES["D"]
    if (pf_lower >= d_rule["pf_lower"]
            and exp >= d_rule["expectancy"]
            and n >= d_rule["n_min"]):
        return "D", (
            f"BORDERLINE：PF_lower={pf_lower_s} ≥ 0.5, exp={exp_s} ≥ 0%, n={n}≥5, "
            f"holdout=[{ho_str}]（紙上交易）"
        )

    # F：其他
    return "F", (
        f"FAIL：PF_lower={pf_lower_s}, exp={exp_s}, n={n}, holdout=[{ho_str}]"
    )
