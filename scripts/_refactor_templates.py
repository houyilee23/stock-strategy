"""One-shot refactor script: split templates.py into a templates/ package.

Reads src/strategy/auto_iterate/templates.py, identifies function boundaries,
categorizes each generate_* function, and writes them into category modules:

  templates/
    __init__.py            (re-exports public API)
    _common.py             (imports + helpers used everywhere)
    search_spaces.py       (SEARCH_SPACES dict + sample_template_params)
    core_t1_t9.py          (generate_T1 .. T9)
    reversal_dips.py       (~23 mean-reversion/dip templates)
    trend_breakouts.py     (~21 trend/breakout templates)
    composite_advanced.py  (chip_streak + monthly_revenue_event)
    ensembles.py           (10 ensemble templates)

After running this, templates.py is moved aside as templates.py.bak so it
can be restored if the package version has issues.
"""
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "strategy", "auto_iterate", "templates.py")
PKG = os.path.join(ROOT, "src", "strategy", "auto_iterate", "templates_pkg")

CATEGORY = {
    # T1-T9 originals
    "core_t1_t9": [
        "generate_T1", "generate_T2", "generate_T3", "generate_T4", "generate_T5",
        "generate_T6", "generate_T7", "generate_T8", "generate_T9",
    ],
    # Composite / event-driven
    "composite_advanced": [
        "generate_signals_chip_streak", "generate_signals_monthly_revenue_event",
    ],
    # Reversal / dip / mean-reversion
    "reversal_dips": [
        "generate_bb_extremes", "generate_three_day_reversal",
        "generate_rsi_oversold_volume", "generate_support_bounce",
        "generate_cci_extremes", "generate_hammer_revert",
        "generate_kd_oversold_cross", "generate_mfi_oversold",
        "generate_roc_reversal", "generate_williams_r_extreme",
        "generate_gap_down_revert", "generate_low_volume_reversal",
        "generate_deep_dip_long_hold", "generate_weekly_low_buy",
        "generate_simple_dip_buy", "generate_yearly_low_revert",
        "generate_linreg_slope_revert", "generate_coppock_buy",
        "generate_ultimate_oscillator", "generate_stoch_rsi",
        "generate_ao_zero_cross", "generate_vwap_revert",
        "generate_double_pullback",
    ],
    # Trend / breakout / momentum
    "trend_breakouts": [
        "generate_narrow_range_breakout", "generate_golden_cross",
        "generate_ema_cross", "generate_macd_cross",
        "generate_adx_trending_pullback", "generate_yearly_high_break",
        "generate_keltner_breakout", "generate_trend_confirm_hold",
        "generate_monthly_anchor", "generate_pivot_break",
        "generate_short_momentum", "generate_double_volume",
        "generate_failed_breakdown", "generate_volume_spike_reverse",
        "generate_obv_uptrend", "generate_inside_day_breakout",
        "generate_three_white_soldiers", "generate_outside_day_engulf",
        "generate_atr_band_breakout", "generate_slow_trend_pullback",
        "generate_psar_flip",
    ],
    # Ensemble / composite-vote
    "ensembles": [
        "generate_ensemble_dip_vote", "generate_ensemble_breakout_vote",
        "generate_ensemble_oversold_vote", "generate_ensemble_trend_confirm",
        "generate_ensemble_dip_or_bounce", "generate_ensemble_regime_dip",
        "generate_ensemble_breakout_pullback", "generate_ensemble_triple_confirm",
        "generate_ensemble_bullish_divergence", "generate_ensemble_dual_momentum",
    ],
}

# Sanity: total 65 functions
total = sum(len(v) for v in CATEGORY.values())
print(f"Categorized {total} functions across {len(CATEGORY)} modules")


def find_function_blocks(src_text: str) -> dict:
    """Parse src_text and return {func_name: (start_line, end_line, body_text)}.

    A function block starts at "def NAME(" at column 0 and ends just before
    the next "def NAME(" at column 0 OR the line "TEMPLATE_GENERATORS = {".
    """
    lines = src_text.split("\n")
    # Find all function-def positions
    func_positions = []  # list of (line_no, name)
    for i, line in enumerate(lines):
        m = re.match(r"^def\s+(\w+)\s*\(", line)
        if m:
            func_positions.append((i, m.group(1)))

    # Find module-end marker (start of TEMPLATE_GENERATORS or end of file).
    # NOTE: only look for TEMPLATE_GENERATORS at column 0, not TEMPLATE_NAMES,
    # because TEMPLATE_NAMES appears at line ~600 (after SEARCH_SPACES) which
    # is BEFORE any generate_* function — using it as end_line would break
    # the LAST function's block extraction.
    end_line = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("TEMPLATE_GENERATORS = {"):
            end_line = i
            break

    # For each function, find its end line (line before next def at col 0, or end_line)
    blocks = {}
    for idx, (start, name) in enumerate(func_positions):
        next_start = func_positions[idx + 1][0] if idx + 1 < len(func_positions) else end_line
        # Trim trailing blank lines
        body_lines = lines[start:next_start]
        # Remove trailing blank lines
        while body_lines and body_lines[-1].strip() == "":
            body_lines.pop()
        blocks[name] = (start, next_start, "\n".join(body_lines))
    return blocks


def extract_search_spaces(src_text: str) -> str:
    """Extract SEARCH_SPACES = {...} block + TEMPLATE_NAMES + sample_template_params."""
    lines = src_text.split("\n")
    # Find start of SEARCH_SPACES = {
    start = None
    for i, line in enumerate(lines):
        if line.startswith("SEARCH_SPACES = {"):
            start = i
            break
    if start is None:
        return ""
    # Find matching closing brace at column 0 (the next "}\n" line followed by blank or TEMPLATE_NAMES)
    depth = 0
    end = start
    for i in range(start, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
        if depth == 0 and i > start:
            end = i
            break

    # Continue capturing TEMPLATE_NAMES = ... and sample_template_params function
    j = end + 1
    while j < len(lines) and not lines[j].startswith("def generate_"):
        j += 1

    return "\n".join(lines[start:j]).rstrip() + "\n"


def main():
    with open(SRC, encoding="utf-8") as f:
        src_text = f.read()

    blocks = find_function_blocks(src_text)
    print(f"Parsed {len(blocks)} functions from templates.py")

    # Extract header (everything before first def)
    first_def = src_text.find("\ndef ")
    header = src_text[:first_def].rstrip() + "\n"

    # Extract SEARCH_SPACES section
    search_spaces_section = extract_search_spaces(src_text)

    # Find sample_template_params function (it's not generate_*)
    sample_func = blocks.get("sample_template_params")
    if sample_func:
        sample_body = sample_func[2]
    else:
        sample_body = ""

    # ── Write _common.py ─────────────────────────────────────
    common_path = os.path.join(PKG, "_common.py")
    common_content = '''"""Common imports & helpers shared by all template modules.

All template generator files start with:
    from ._common import *

This consolidates the boilerplate (pandas/numpy + the indicator functions)
into one place. If a new helper is needed across templates, add it here.
"""
import numpy as np
import pandas as pd

from src.strategy.indicators.trend import sma, ema
from src.strategy.indicators.momentum import rsi
from src.strategy.indicators.volatility import atr, bollinger
from src.strategy.indicators.volume import volume_ma
'''
    with open(common_path, "w", encoding="utf-8") as f:
        f.write(common_content)
    print(f"  Wrote {common_path}")

    # ── Write search_spaces.py ────────────────────────────────
    ss_path = os.path.join(PKG, "search_spaces.py")
    ss_content = '''"""SEARCH_SPACES + sample_template_params.

SEARCH_SPACES is a dict {template_name: param_spec_dict}. Each param_spec
describes how Optuna should sample (categorical / int / float, ranges, step).

sample_template_params(template_name, optuna_trial) returns the actual
sampled value dict from a trial, used inside the runner's objective function.

To add a new template, also add its search space here (or in the generator
file's docstring as a comment, then mirror it here).
"""
import warnings
import numpy as np
import pandas as pd

from src.strategy.optimize.search_space import SEARCH_SPACE as _T1_SPACE

# Suppress Optuna step-not-divisible warnings (we use float ranges where this
# happens; the snap-fix is acceptable for our search granularity).
warnings.filterwarnings(
    "ignore",
    message="The distribution is specified by .* and step=.* but the range",
    category=UserWarning,
)


''' + search_spaces_section + "\n"

    if sample_body:
        ss_content += "\n" + sample_body + "\n"

    with open(ss_path, "w", encoding="utf-8") as f:
        f.write(ss_content)
    print(f"  Wrote {ss_path}")

    # ── Write category modules ────────────────────────────────
    for module, funcs in CATEGORY.items():
        path = os.path.join(PKG, f"{module}.py")
        # Docstring describing the category
        docstrings = {
            "core_t1_t9": ("Original 9 templates (T1-T9) — the seed set.\n\n"
                          "T1 trend_pullback / T2 donchian_breakout / T3 momentum_hold /\n"
                          "T4 chip_momentum / T5 mean_reversion / T6 volume_breakout /\n"
                          "T7 gap_continuation / T8 low_vol_pullback / T9 bollinger_squeeze"),
            "composite_advanced": ("Event-driven / composite signals using auxiliary data.\n\n"
                          "chip_streak — institutional buy/sell streak from chip_data\n"
                          "monthly_revenue_event — revenue YoY gap continuation"),
            "reversal_dips": ("Mean-reversion / dip-buying templates (~23).\n\n"
                          "Patterns: BB extremes, RSI/MFI/Williams oversold, ROC reversal,\n"
                          "hammer, three-day reversal, gap-down revert, simple/weekly/deep dip,\n"
                          "yearly low revert, KD/stoch RSI, AO zero cross, VWAP revert, etc."),
            "trend_breakouts": ("Trend-following + breakout + momentum templates (~21).\n\n"
                          "Patterns: golden cross, EMA cross, MACD cross, narrow range break,\n"
                          "Donchian/Keltner/ATR-band breakout, monthly anchor, ADX trend pullback,\n"
                          "pivot break, three-white-soldiers, outside-day engulf, PSAR flip, etc."),
            "ensembles": ("10 ensemble strategies (5/16-5/17 — composite of multiple filters).\n\n"
                          "Vote-based: dip_vote, breakout_vote, oversold_vote, trend_confirm,\n"
                          "         dip_or_bounce\n"
                          "Regime-aware: regime_dip, breakout_pullback, dual_momentum\n"
                          "Intersection: triple_confirm, bullish_divergence\n\n"
                          "These reduce false-positives by requiring multi-filter agreement."),
        }
        doc = docstrings.get(module, "")
        content = f'"""{doc}"""\nfrom ._common import *\n\n\n'
        for fname in funcs:
            if fname not in blocks:
                print(f"  [WARN] {module}: function {fname} not found")
                continue
            content += blocks[fname][2] + "\n\n\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  Wrote {path}: {len(funcs)} functions")

    # ── Write __init__.py with public API ────────────────────
    init_path = os.path.join(PKG, "__init__.py")
    # Build import statements for each generator name → its module
    func_to_module = {}
    for module, funcs in CATEGORY.items():
        for fn in funcs:
            func_to_module[fn] = module

    # Re-export search spaces + helper
    init_lines = [
        '"""Public API for the auto_iterate templates package.',
        "",
        "Imports from this package keep backward compatibility with the old",
        "`src.strategy.auto_iterate.templates` module path. Specifically:",
        "  - SEARCH_SPACES, TEMPLATE_NAMES, TEMPLATE_GENERATORS",
        "  - sample_template_params(template_name, trial)",
        "  - All generate_* functions (used by tests + runner)",
        "",
        "Categorization (see each sub-module for details):",
        "  core_t1_t9         — T1..T9 (original 9 templates)",
        "  reversal_dips      — mean-reversion / dip / oversold (~23 templates)",
        "  trend_breakouts    — trend-following / breakout / momentum (~21 templates)",
        "  composite_advanced — chip-data / revenue-event driven (2 templates)",
        "  ensembles          — 10 composite-vote ensemble strategies",
        '"""',
        "",
        "from .search_spaces import SEARCH_SPACES, TEMPLATE_NAMES, sample_template_params",
        "",
    ]

    # Import each module's functions
    for module, funcs in CATEGORY.items():
        funcs_str = ", ".join(funcs)
        init_lines.append(f"from .{module} import (")
        for fn in funcs:
            init_lines.append(f"    {fn},")
        init_lines.append(")")
        init_lines.append("")

    # Build TEMPLATE_GENERATORS dict
    init_lines.append("")
    init_lines.append("# ── TEMPLATE_GENERATORS registry ────────────────────────")
    init_lines.append("# Maps user-facing template name → generator function. Used by runner")
    init_lines.append("# and tests to dispatch the right generator at backtest time.")
    init_lines.append("TEMPLATE_GENERATORS = {")
    # We need to recover the (name → generator) mapping. We have CATEGORY but not the
    # template-name-to-function mapping; that was in templates.py's TEMPLATE_GENERATORS dict.
    # Parse the original TEMPLATE_GENERATORS dict from templates.py.
    tg_start = src_text.find("TEMPLATE_GENERATORS = {")
    if tg_start >= 0:
        # Find matching closing brace
        depth = 0
        tg_end = tg_start
        for i in range(tg_start, len(src_text)):
            ch = src_text[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    tg_end = i
                    break
        tg_block = src_text[tg_start:tg_end + 1]
        # Parse mappings inside
        # Match lines like: "name": generate_func,
        for line in tg_block.split("\n")[1:-1]:
            m = re.match(r'\s*"([^"]+)":\s+(\w+),?\s*(#.*)?$', line)
            if m:
                tname, gname = m.group(1), m.group(2)
                init_lines.append(f'    "{tname}": {gname},')
    init_lines.append("}")
    init_lines.append("")
    init_lines.append("# Sanity check: every TEMPLATE_GENERATORS key must have a SEARCH_SPACES entry")
    init_lines.append("assert set(TEMPLATE_GENERATORS) == set(SEARCH_SPACES), (")
    init_lines.append("    'Mismatch between TEMPLATE_GENERATORS and SEARCH_SPACES keys'")
    init_lines.append(")")
    init_lines.append("")

    with open(init_path, "w", encoding="utf-8") as f:
        f.write("\n".join(init_lines))
    print(f"  Wrote {init_path}")

    print("\nDone. Next steps:")
    print("  1. Test imports: python -c 'from src.strategy.auto_iterate.templates_pkg import TEMPLATE_GENERATORS; print(len(TEMPLATE_GENERATORS))'")
    print("  2. If OK: move templates.py → templates.py.bak and rename templates_pkg → templates")


if __name__ == "__main__":
    main()
