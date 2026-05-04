"""Tests for tiering.assign_tier (v2 — bootstrap-first, NA-tolerant)."""
import pytest

from src.strategy.auto_iterate.tiering import assign_tier, passes_holdout, TIER_RULES


# ── assign_tier happy paths ──────────────────────────────────────

def test_tier_S_via_holdout_pass():
    """PF_lower≥2.0 + Exp≥5% + n≥8 + 至少一段 holdout PASS → S"""
    test_m = {"n_trades": 10, "expectancy": 0.08}
    boot = {"pf_lower": 2.5}
    holdouts = {"A_new": True, "B": False, "C": None}
    tier, reason = assign_tier(test_m, boot, holdouts)
    assert tier == "S"
    assert "PF_lower=2.50" in reason


def test_tier_S_via_pf_lower_only():
    """PF_lower≥3.0 + Exp≥5% + n≥8 + 全部 holdout NA → S（自動晉升）"""
    test_m = {"n_trades": 10, "expectancy": 0.08}
    boot = {"pf_lower": 3.5}
    holdouts = {"A_new": None, "B": None, "C": None}
    tier, reason = assign_tier(test_m, boot, holdouts)
    assert tier == "S"
    assert "自動晉升" in reason


def test_tier_A_via_holdout_pass():
    """PF_lower≥1.5 + Exp≥3% + n≥6 + 至少一段 holdout PASS → A"""
    test_m = {"n_trades": 8, "expectancy": 0.04}
    boot = {"pf_lower": 1.6}
    holdouts = {"A_new": False, "B": True, "C": None}
    tier, reason = assign_tier(test_m, boot, holdouts)
    assert tier == "A"


def test_tier_A_via_pf_lower_only():
    """PF_lower≥2.0 + Exp≥3% + n≥6 + 全部 holdout NA → A（自動晉升）"""
    test_m = {"n_trades": 8, "expectancy": 0.04}
    boot = {"pf_lower": 2.0}
    holdouts = {"A_new": None, "B": None, "C": None}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "A"


def test_tier_B():
    """PF_lower≥1.0 + Exp≥2% + n≥5 → B（不需 holdout）"""
    test_m = {"n_trades": 6, "expectancy": 0.025}
    boot = {"pf_lower": 1.05}
    holdouts = {"A_new": False, "B": False, "C": False}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "B"


def test_tier_C():
    """PF_lower≥0.7 + Exp≥1% + n≥5 → C（仍可給 15%）"""
    test_m = {"n_trades": 7, "expectancy": 0.015}
    boot = {"pf_lower": 0.75}
    holdouts = {"A_new": False, "B": False, "C": False}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "C"


def test_tier_F_low_n():
    """n<5 + 無 raw_PF → F（即使 holdouts 都過）

    注意：raw_pf 缺失時 LOW_N_RESCUE 不啟用，回到 F 路徑。
    """
    test_m = {"n_trades": 3, "expectancy": 0.10}  # 沒有 profit_factor
    boot = {"pf_lower": 2.5}
    holdouts = {"A_new": True, "B": True, "C": True}
    tier, reason = assign_tier(test_m, boot, holdouts)
    assert tier == "F"
    assert "n_trades=3" in reason


# ── Q5b-lite LOW_N_RESCUE：n=3-4 但訊號品質強 → C ──────────────

def test_tier_C_low_n_rescue_basic():
    """n=4 + raw_PF=5 + Exp 8% + DD 20% + holdout 全 NA → C (LOW_N_RESCUE)"""
    test_m = {"n_trades": 4, "expectancy": 0.08, "profit_factor": 5.0,
              "max_drawdown": -0.20}
    boot = {"pf_lower": float("nan")}  # bootstrap 不可靠
    holdouts = {"A_new": None, "B": None, "C": None}
    tier, reason = assign_tier(test_m, boot, holdouts)
    assert tier == "C"
    assert "LOW_N_RESCUE" in reason


def test_tier_C_low_n_rescue_with_inf_pf():
    """n=3 + raw_PF=inf（無虧損）+ Exp 6% + DD 15% → C"""
    test_m = {"n_trades": 3, "expectancy": 0.06, "profit_factor": float("inf"),
              "max_drawdown": -0.15}
    boot = {"pf_lower": float("nan")}
    holdouts = {"A_new": None, "B": True, "C": None}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "C"


def test_tier_F_low_n_rescue_blocked_by_holdout_fail():
    """n=4 + 強 PF/exp 但有 holdout FAIL → 不救 → F"""
    test_m = {"n_trades": 4, "expectancy": 0.08, "profit_factor": 5.0,
              "max_drawdown": -0.20}
    boot = {"pf_lower": float("nan")}
    holdouts = {"A_new": None, "B": False, "C": None}  # B 段 fail
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "F"


def test_tier_F_low_n_rescue_blocked_by_dd():
    """n=4 + raw_PF=5 + Exp 8% 但 DD=-30%（>25%）→ 不救 → F"""
    test_m = {"n_trades": 4, "expectancy": 0.08, "profit_factor": 5.0,
              "max_drawdown": -0.30}
    boot = {"pf_lower": float("nan")}
    holdouts = {"A_new": None, "B": None, "C": None}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "F"


def test_tier_F_low_n_rescue_blocked_by_low_exp():
    """n=4 + raw_PF=5 但 exp 只有 3%（<5%）→ 不救 → F"""
    test_m = {"n_trades": 4, "expectancy": 0.03, "profit_factor": 5.0,
              "max_drawdown": -0.20}
    boot = {"pf_lower": float("nan")}
    holdouts = {"A_new": None, "B": None, "C": None}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "F"


def test_tier_F_negative_expectancy():
    """expectancy < 0 → F"""
    test_m = {"n_trades": 8, "expectancy": -0.02}
    boot = {"pf_lower": 1.5}
    holdouts = {"A_new": True, "B": True, "C": True}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "F"


def test_tier_S_demoted_to_A_when_no_holdout_and_low_pf():
    """PF_lower=2.5 (有達到 S 的 PF) + Exp 8% + n=10 + 全部 holdout=NA →
    沒有 holdout PASS 且 PF_lower<3.0 → 不能 S；PF_lower≥2.0 → A 自動晉升"""
    test_m = {"n_trades": 10, "expectancy": 0.08}
    boot = {"pf_lower": 2.5}
    holdouts = {"A_new": None, "B": None, "C": None}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "A"


def test_tier_S_demoted_to_B_when_n_too_low():
    """n=5（夠 B 但不夠 S 的 8）→ B"""
    test_m = {"n_trades": 5, "expectancy": 0.08}
    boot = {"pf_lower": 2.5}
    holdouts = {"A_new": True, "B": True, "C": True}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "B"  # n<6 不能 A，但 PF/exp/n>=5 夠 B


def test_tier_F_when_pf_lower_too_low():
    """PF_lower 0.5 + Exp 0.5% → 不夠 C → F"""
    test_m = {"n_trades": 8, "expectancy": 0.005}
    boot = {"pf_lower": 0.5}
    holdouts = {"A_new": False, "B": False, "C": False}
    tier, _ = assign_tier(test_m, boot, holdouts)
    assert tier == "F"


def test_tier_nan_pf_lower_treated_as_zero():
    """bootstrap pf_lower nan → 視為 0，無法達到任何 C 以上"""
    test_m = {"n_trades": 8, "expectancy": 0.10}
    boot = {"pf_lower": float("nan")}
    holdouts = {"A_new": True, "B": True, "C": True}
    tier, _ = assign_tier(test_m, boot, holdouts)
    # PF_lower=0 < 0.7 → 無法過 C → F
    assert tier == "F"


# ── passes_holdout v2 三態 ───────────────────────────────────────

def test_passes_holdout_A_new_pass():
    m = {"n_trades": 5, "profit_factor": 1.5, "expectancy": 0.03,
         "max_drawdown": -0.20}
    assert passes_holdout(m, "A_new") is True


def test_passes_holdout_A_new_fail_low_pf():
    m = {"n_trades": 5, "profit_factor": 0.6, "expectancy": 0.03}
    assert passes_holdout(m, "A_new") is False


def test_passes_holdout_B_dd_breach():
    m = {"n_trades": 4, "profit_factor": 1.5, "max_drawdown": -0.50}
    assert passes_holdout(m, "B") is False


def test_passes_holdout_None_metrics_returns_None():
    """None metrics（晚上市等）→ None（中性 NA）"""
    assert passes_holdout(None, "A_new") is None


def test_passes_holdout_low_n_returns_None():
    """樣本數低於 n_min → None（不算 fail）"""
    m = {"n_trades": 0, "profit_factor": float("nan"), "expectancy": float("nan")}
    assert passes_holdout(m, "A_new") is None


def test_tier_rules_pos_max_consistent():
    """sanity：S→1.0, A→0.5, B→0.3, C→0.15, F→0.0"""
    assert TIER_RULES["S"]["pos_max"] == 1.00
    assert TIER_RULES["A"]["pos_max"] == 0.50
    assert TIER_RULES["B"]["pos_max"] == 0.30
    assert TIER_RULES["C"]["pos_max"] == 0.15
    assert TIER_RULES["F"]["pos_max"] == 0.00
