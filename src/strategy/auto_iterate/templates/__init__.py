"""Public API for the auto_iterate templates package.

Imports from this package keep backward compatibility with the old
`src.strategy.auto_iterate.templates` module path. Specifically:
  - SEARCH_SPACES, TEMPLATE_NAMES, TEMPLATE_GENERATORS
  - sample_template_params(template_name, trial)
  - All generate_* functions (used by tests + runner)

Categorization (see each sub-module for details):
  core_t1_t9         — T1..T9 (original 9 templates)
  reversal_dips      — mean-reversion / dip / oversold (~23 templates)
  trend_breakouts    — trend-following / breakout / momentum (~21 templates)
  composite_advanced — chip-data / revenue-event driven (2 templates)
  ensembles          — 10 composite-vote ensemble strategies
"""

from .search_spaces import SEARCH_SPACES, TEMPLATE_NAMES, sample_template_params

from .core_t1_t9 import (
    generate_T1,
    generate_T2,
    generate_T3,
    generate_T4,
    generate_T5,
    generate_T6,
    generate_T7,
    generate_T8,
    generate_T9,
)

from .composite_advanced import (
    generate_signals_chip_streak,
    generate_signals_monthly_revenue_event,
)

from .reversal_dips import (
    generate_bb_extremes,
    generate_three_day_reversal,
    generate_rsi_oversold_volume,
    generate_support_bounce,
    generate_cci_extremes,
    generate_hammer_revert,
    generate_kd_oversold_cross,
    generate_mfi_oversold,
    generate_roc_reversal,
    generate_williams_r_extreme,
    generate_gap_down_revert,
    generate_low_volume_reversal,
    generate_deep_dip_long_hold,
    generate_weekly_low_buy,
    generate_simple_dip_buy,
    generate_yearly_low_revert,
    generate_linreg_slope_revert,
    generate_coppock_buy,
    generate_ultimate_oscillator,
    generate_stoch_rsi,
    generate_ao_zero_cross,
    generate_vwap_revert,
    generate_double_pullback,
)

from .trend_breakouts import (
    generate_narrow_range_breakout,
    generate_golden_cross,
    generate_ema_cross,
    generate_macd_cross,
    generate_adx_trending_pullback,
    generate_yearly_high_break,
    generate_keltner_breakout,
    generate_trend_confirm_hold,
    generate_monthly_anchor,
    generate_pivot_break,
    generate_short_momentum,
    generate_double_volume,
    generate_failed_breakdown,
    generate_volume_spike_reverse,
    generate_obv_uptrend,
    generate_inside_day_breakout,
    generate_three_white_soldiers,
    generate_outside_day_engulf,
    generate_atr_band_breakout,
    generate_slow_trend_pullback,
    generate_psar_flip,
)

from .ensembles import (
    generate_ensemble_dip_vote,
    generate_ensemble_breakout_vote,
    generate_ensemble_oversold_vote,
    generate_ensemble_trend_confirm,
    generate_ensemble_dip_or_bounce,
    generate_ensemble_regime_dip,
    generate_ensemble_breakout_pullback,
    generate_ensemble_triple_confirm,
    generate_ensemble_bullish_divergence,
    generate_ensemble_dual_momentum,
)


# ── TEMPLATE_GENERATORS registry ────────────────────────
# Maps user-facing template name → generator function. Used by runner
# and tests to dispatch the right generator at backtest time.
TEMPLATE_GENERATORS = {
    "trend_pullback": generate_T1,
    "donchian_breakout": generate_T2,
    "momentum_hold": generate_T3,
    "chip_momentum": generate_T4,
    "mean_reversion": generate_T5,
    "volume_breakout": generate_T6,
    "gap_continuation": generate_T7,
    "low_vol_pullback": generate_T8,
    "bollinger_squeeze": generate_T9,
    "bb_extremes": generate_bb_extremes,
    "narrow_range_breakout": generate_narrow_range_breakout,
    "golden_cross": generate_golden_cross,
    "three_day_reversal": generate_three_day_reversal,
    "rsi_oversold_volume": generate_rsi_oversold_volume,
    "support_bounce": generate_support_bounce,
    "cci_extremes": generate_cci_extremes,
    "hammer_revert": generate_hammer_revert,
    "macd_cross": generate_macd_cross,
    "kd_oversold_cross": generate_kd_oversold_cross,
    "adx_trending_pullback": generate_adx_trending_pullback,
    "vwap_revert": generate_vwap_revert,
    "yearly_high_break": generate_yearly_high_break,
    "keltner_breakout": generate_keltner_breakout,
    "mfi_oversold": generate_mfi_oversold,
    "roc_reversal": generate_roc_reversal,
    "williams_r_extreme": generate_williams_r_extreme,
    "ema_cross": generate_ema_cross,
    "gap_down_revert": generate_gap_down_revert,
    "psar_flip": generate_psar_flip,
    "slow_trend_pullback": generate_slow_trend_pullback,
    "stoch_rsi": generate_stoch_rsi,
    "ao_zero_cross": generate_ao_zero_cross,
    "yearly_low_revert": generate_yearly_low_revert,
    "atr_band_breakout": generate_atr_band_breakout,
    "double_pullback": generate_double_pullback,
    "linreg_slope_revert": generate_linreg_slope_revert,
    "coppock_buy": generate_coppock_buy,
    "ultimate_oscillator": generate_ultimate_oscillator,
    "inside_day_breakout": generate_inside_day_breakout,
    "three_white_soldiers": generate_three_white_soldiers,
    "outside_day_engulf": generate_outside_day_engulf,
    "failed_breakdown": generate_failed_breakdown,
    "volume_spike_reverse": generate_volume_spike_reverse,
    "obv_uptrend": generate_obv_uptrend,
    "pivot_break": generate_pivot_break,
    "short_momentum": generate_short_momentum,
    "double_volume": generate_double_volume,
    "simple_dip_buy": generate_simple_dip_buy,
    "monthly_anchor": generate_monthly_anchor,
    "deep_dip_long_hold": generate_deep_dip_long_hold,
    "weekly_low_buy": generate_weekly_low_buy,
    "trend_confirm_hold": generate_trend_confirm_hold,
    "low_volume_reversal": generate_low_volume_reversal,
    "chip_streak": generate_signals_chip_streak,
    "monthly_revenue_event": generate_signals_monthly_revenue_event,
    "ensemble_dip_vote": generate_ensemble_dip_vote,
    "ensemble_breakout_vote": generate_ensemble_breakout_vote,
    "ensemble_oversold_vote": generate_ensemble_oversold_vote,
    "ensemble_trend_confirm": generate_ensemble_trend_confirm,
    "ensemble_dip_or_bounce": generate_ensemble_dip_or_bounce,
    "ensemble_regime_dip": generate_ensemble_regime_dip,
    "ensemble_breakout_pullback": generate_ensemble_breakout_pullback,
    "ensemble_dual_momentum": generate_ensemble_dual_momentum,
    "ensemble_triple_confirm": generate_ensemble_triple_confirm,
    "ensemble_bullish_divergence": generate_ensemble_bullish_divergence,
}

# Sanity check: every TEMPLATE_GENERATORS key must have a SEARCH_SPACES entry
assert set(TEMPLATE_GENERATORS) == set(SEARCH_SPACES), (
    'Mismatch between TEMPLATE_GENERATORS and SEARCH_SPACES keys'
)
