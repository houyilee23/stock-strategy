"""
Widened search-space variant of templates.py for F-tier rescue experiments.

Each numeric (int/float) range is expanded ~3×: lower × 0.4, upper × 2.5,
step scaled to keep granularity reasonable.

Categorical / boolean params are kept identical.

Templates widened:
    trend_pullback, donchian_breakout, momentum_hold, chip_momentum,
    mean_reversion, gap_continuation, low_vol_pullback, bollinger_squeeze

volume_breakout is intentionally NOT widened (produced 0 winners in baseline,
likely structurally weak — widening won't help).

Usage:
    from src.strategy.auto_iterate.templates_wide import (
        SEARCH_SPACES_WIDE, sample_template_params_wide,
    )

The TEMPLATE_GENERATORS map is re-exported unchanged from templates.py
(generators don't change — only the parameter ranges Optuna samples from).
"""
import copy
import warnings

# Optuna emits UserWarning each trial when a step doesn't evenly divide
# (high - low). Even after our snap-fix, suppress them defensively so the
# log stays readable across ~12,000 trials.
warnings.filterwarnings(
    "ignore",
    message="The distribution is specified by .* and step=.* but the range",
    category=UserWarning,
)

from src.strategy.auto_iterate.templates import (
    SEARCH_SPACES as _SEARCH_SPACES_BASE,
    TEMPLATE_GENERATORS,
    TEMPLATE_NAMES,
)


# ── Templates that get a widened search space ───────────────────────
WIDEN_TARGETS = {
    "trend_pullback",
    "donchian_breakout",
    "momentum_hold",
    "chip_momentum",
    "mean_reversion",
    "gap_continuation",
    "low_vol_pullback",
    "bollinger_squeeze",
    # volume_breakout intentionally excluded — kept at base ranges
}


def _widen_categorical(choices: list, kind: str = "numeric") -> list:
    """Widen a categorical numeric list by extending both ends.

    Strategy: keep all original choices, prepend a value ~0.4× the min and
    append a value ~2.5× the max (only if the type is numeric).
    Strings/booleans are returned unchanged.
    """
    if not choices or not all(isinstance(c, (int, float)) for c in choices):
        return list(choices)

    sorted_choices = sorted(set(choices))
    lo = sorted_choices[0]
    hi = sorted_choices[-1]

    # All-int case → keep ints
    is_int = all(isinstance(c, int) for c in sorted_choices)

    new_lo = max(1, int(round(lo * 0.4))) if is_int else round(lo * 0.4, 4)
    new_hi = int(round(hi * 2.5)) if is_int else round(hi * 2.5, 4)

    extended = []
    if new_lo < lo:
        extended.append(new_lo)
    extended.extend(sorted_choices)
    if new_hi > hi:
        extended.append(new_hi)

    # de-dup keep order
    seen = set()
    out = []
    for v in extended:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _widen_int(spec: dict, name: str = "") -> dict:
    lo   = spec["low"]
    hi   = spec["high"]
    step = spec.get("step", 1)
    new_lo = max(1, int(round(lo * 0.4)))
    new_hi = int(round(hi * 2.5))
    # Scale step (~3× wider span so step can grow ~1.5× to avoid trial explosion).
    new_step = max(1, int(round(step * 1.5)))

    # Domain-clamp RSI thresholds — RSI is bounded [0,100], values outside
    # waste trials (Optuna would learn to avoid them but slowly).
    if "rsi" in name.lower() and ("oversold" in name.lower()
                                   or "overbought" in name.lower()):
        new_lo = max(5, new_lo)
        new_hi = min(95, new_hi)

    # Snap (high - low) to a multiple of step so Optuna doesn't warn /
    # silently shrink the range. We round high DOWN to the nearest step.
    span = new_hi - new_lo
    if span < new_step:
        new_step = max(1, span)
    rem = span % new_step
    if rem != 0:
        new_hi = new_hi - rem  # shrink upper bound to keep grid clean

    out = dict(spec)
    out["low"]  = new_lo
    out["high"] = new_hi
    out["step"] = new_step
    return out


def _widen_float(spec: dict) -> dict:
    """Widen a float range. Drop the step entirely so Optuna samples
    continuously over the wider range — that's actually the point of a
    wide-search experiment, and it sidesteps the float-divisibility
    UserWarning storm Optuna emits otherwise.
    """
    lo = spec["low"]
    hi = spec["high"]
    new_lo = round(lo * 0.4, 4)
    new_hi = round(hi * 2.5, 4)
    out = {"type": "float", "low": new_lo, "high": new_hi}
    return out


def _widen_space(space: dict) -> dict:
    new_space = {}
    for k, spec in space.items():
        t = spec["type"]
        if t == "categorical":
            new_space[k] = {
                "type": "categorical",
                "choices": _widen_categorical(spec["choices"]),
            }
        elif t == "int":
            new_space[k] = _widen_int(spec, name=k)
        elif t == "float":
            new_space[k] = _widen_float(spec)
        else:
            new_space[k] = copy.deepcopy(spec)
    return new_space


# ── Build the widened spaces ─────────────────────────────────────────
SEARCH_SPACES_WIDE: dict = {}
for _name, _space in _SEARCH_SPACES_BASE.items():
    if _name in WIDEN_TARGETS:
        SEARCH_SPACES_WIDE[_name] = _widen_space(_space)
    else:
        SEARCH_SPACES_WIDE[_name] = copy.deepcopy(_space)


def sample_template_params_wide(template_name: str, trial) -> dict:
    """Optuna sampler using the WIDE search space variant.

    Drop-in replacement for templates.sample_template_params.
    """
    space = SEARCH_SPACES_WIDE[template_name]
    params = {}
    for k, spec in space.items():
        t = spec["type"]
        if t == "categorical":
            params[k] = trial.suggest_categorical(k, spec["choices"])
        elif t == "int":
            params[k] = trial.suggest_int(
                k, spec["low"], spec["high"], step=spec.get("step", 1)
            )
        elif t == "float":
            params[k] = trial.suggest_float(
                k, spec["low"], spec["high"], step=spec.get("step")
            )
    return params


# Re-export so callers can pull both ranges & generators from one module.
__all__ = [
    "SEARCH_SPACES_WIDE",
    "TEMPLATE_GENERATORS",
    "TEMPLATE_NAMES",
    "WIDEN_TARGETS",
    "sample_template_params_wide",
]
