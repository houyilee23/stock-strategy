"""SEARCH_SPACES + sample_template_params.

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


SEARCH_SPACES = {
    "trend_pullback": _T1_SPACE,
    "donchian_breakout": {
        "donchian_entry_n": {"type": "categorical", "choices": [20, 55, 120]},
        "donchian_exit_n":  {"type": "categorical", "choices": [10, 20, 55]},
        "trend_ma":         {"type": "categorical", "choices": [50, 100, 200]},
        "atr_stop_k":       {"type": "float", "low": 1.5, "high": 4.0, "step": 0.5},
        "volume_min_ratio": {"type": "float", "low": 0.5, "high": 1.5, "step": 0.25},
    },
    "momentum_hold": {
        "mom_lookback":  {"type": "categorical", "choices": [30, 60, 120, 250]},
        "mom_entry_pct": {"type": "float", "low": 0.05, "high": 0.30, "step": 0.05},
        "mom_exit_pct":  {"type": "float", "low": -0.10, "high": 0.05, "step": 0.025},
        "trend_ma":      {"type": "categorical", "choices": [50, 100, 200]},
    },
    "chip_momentum": {
        "mom_lookback":  {"type": "categorical", "choices": [30, 60, 120]},
        "mom_entry_pct": {"type": "float", "low": 0.05, "high": 0.20, "step": 0.05},
        "chip_window":   {"type": "categorical", "choices": [20, 60, 120]},
        "trend_ma":      {"type": "categorical", "choices": [50, 100, 200]},
        "atr_stop_k":    {"type": "float", "low": 2.0, "high": 4.0, "step": 0.5},
    },
    "mean_reversion": {
        "trend_ma":        {"type": "categorical", "choices": [100, 150, 200]},
        "short_ma":        {"type": "categorical", "choices": [10, 20, 30]},
        "pullback_pct":    {"type": "float", "low": 0.02, "high": 0.10, "step": 0.01},
        "rsi_period":      {"type": "categorical", "choices": [7, 14, 21]},
        "rsi_oversold":    {"type": "int",  "low": 20, "high": 35, "step": 5},
        "rsi_overbought":  {"type": "int",  "low": 60, "high": 80, "step": 5},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.15, "step": 0.02},
        "max_hold_days":   {"type": "categorical", "choices": [30, 60, 120]},
    },
    # ── auto_iterate v2 新增模板（為 LOW_SAMPLE / 大型權值股 / 傳產設計）──
    "volume_breakout": {
        "lookback":          {"type": "categorical", "choices": [10, 20, 30, 60]},
        "vol_ratio":         {"type": "float", "low": 1.0, "high": 2.5, "step": 0.25},
        "short_ma_exit":     {"type": "categorical", "choices": [5, 10, 20]},
        "atr_stop_k":        {"type": "float", "low": 2.0, "high": 4.0, "step": 0.5},
    },
    "gap_continuation": {
        "gap_pct":           {"type": "float", "low": 0.015, "high": 0.05, "step": 0.005},
        "max_hold_days":     {"type": "categorical", "choices": [5, 10, 20, 40]},
        "stop_atr_k":        {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "trend_ma":          {"type": "categorical", "choices": [50, 100, 200]},
    },
    "low_vol_pullback": {
        "long_ma":           {"type": "categorical", "choices": [100, 150, 200]},
        "short_ma":          {"type": "categorical", "choices": [10, 20]},
        "down_days":         {"type": "int", "low": 2, "high": 5, "step": 1},
        "pb_pct":            {"type": "float", "low": 0.01, "high": 0.04, "step": 0.005},
        "take_profit_pct":   {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "max_hold_days":     {"type": "categorical", "choices": [20, 40, 60]},
    },
    "bollinger_squeeze": {
        "bb_period":         {"type": "categorical", "choices": [20, 30, 50]},
        "bb_k":              {"type": "float", "low": 1.5, "high": 2.5, "step": 0.5},
        "squeeze_lookback":  {"type": "categorical", "choices": [60, 120, 250]},
        "squeeze_pct":       {"type": "float", "low": 0.10, "high": 0.40, "step": 0.05},
        "trend_ma":          {"type": "categorical", "choices": [50, 100, 200]},
        "atr_stop_k":        {"type": "float", "low": 2.0, "high": 4.0, "step": 0.5},
    },
    # ── range-bound 大盤股 / 傳產股專用：BB 極值反轉到中軌 ─────────
    # 不同於 bollinger_squeeze（突破型），bb_extremes 是 mean-reversion：
    # close 觸 BB_lower → 預期反彈到 BB_middle → 出
    "bb_extremes": {
        "bb_period":     {"type": "categorical", "choices": [20, 30, 50]},
        "bb_std":        {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "entry_buffer":  {"type": "float", "low": 0.0, "high": 0.03, "step": 0.005},
        "long_ma":       {"type": "categorical", "choices": [100, 150, 200]},
        "max_hold_days": {"type": "categorical", "choices": [10, 20, 40, 60]},
    },
    # ── 低波動轉趨勢突破：NR4/NR7 narrow range 後 high 突破 ──────
    # 觀察「狹幅整理 → 下一日突破」pattern，適合 sideways 然後 break out 的股
    # 不同於 donchian_breakout（用固定 N 天 high）也不同於 bollinger_squeeze（BB 寬度）
    "narrow_range_breakout": {
        "nr_window":     {"type": "categorical", "choices": [4, 7, 10]},
        "trend_ma":      {"type": "categorical", "choices": [50, 100, 200]},
        "atr_stop_k":    {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.15, "step": 0.02},
        "max_hold_days": {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── 經典快慢均線黃金交叉 / 死亡交叉 ────────────────────────
    # 同時在 sideways 與 trending 都能捕到部分訊號，適合多種股性
    "golden_cross": {
        "fast_n":          {"type": "categorical", "choices": [5, 10, 20]},
        "slow_n":          {"type": "categorical", "choices": [30, 50, 100, 150]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.20, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [30, 60, 120]},
    },
    # ── 3 日連跌反彈 ── 大盤股拉回 capitulation
    "three_day_reversal": {
        "drop_days":       {"type": "int", "low": 3, "high": 5, "step": 1},
        "min_drop_pct":    {"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── RSI 極端超賣 + 量能放大 ──
    "rsi_oversold_volume": {
        "rsi_period":      {"type": "categorical", "choices": [7, 14, 21]},
        "rsi_threshold":   {"type": "int", "low": 20, "high": 35, "step": 5},
        "volume_ratio":    {"type": "float", "low": 1.2, "high": 2.5, "step": 0.25},
        "volume_period":   {"type": "categorical", "choices": [10, 20, 30]},
        "trend_ma":        {"type": "categorical", "choices": [100, 150, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.15, "step": 0.025},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── 歷史支撐位反彈 ── 找 N 天內最低點，price 接近該位 → 反彈 buy
    "support_bounce": {
        "lookback":        {"type": "categorical", "choices": [60, 120, 250]},
        "support_buffer":  {"type": "float", "low": 0.005, "high": 0.04, "step": 0.005},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.15, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 60]},
    },
    # ── CCI 超漲超跌反轉 ──
    "cci_extremes": {
        "cci_period":      {"type": "categorical", "choices": [14, 20, 30]},
        "cci_oversold":    {"type": "int", "low": -250, "high": -100, "step": 25},
        "cci_overbought":  {"type": "int", "low": 100, "high": 250, "step": 25},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── 高量 doji/hammer pattern 反轉 ── ATR 量化「長下影線 + 上影線小」
    "hammer_revert": {
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "shadow_ratio":    {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "min_drop_pct":    {"type": "float", "low": 0.01, "high": 0.05, "step": 0.005},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 2.5, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── MACD 訊號線交叉 + histogram 增強
    "macd_cross": {
        "fast_n":          {"type": "categorical", "choices": [8, 12, 16]},
        "slow_n":          {"type": "categorical", "choices": [21, 26, 35]},
        "signal_n":        {"type": "categorical", "choices": [7, 9, 12]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.20, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80]},
    },
    # ── KD (Stochastic) 超賣 + golden cross
    "kd_oversold_cross": {
        "k_period":        {"type": "categorical", "choices": [9, 14, 21]},
        "k_oversold":      {"type": "int", "low": 15, "high": 30, "step": 5},
        "k_overbought":    {"type": "int", "low": 70, "high": 85, "step": 5},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── ADX trending + entry on pullback
    "adx_trending_pullback": {
        "adx_period":      {"type": "categorical", "choices": [14, 20]},
        "adx_threshold":   {"type": "int", "low": 20, "high": 35, "step": 5},
        "pullback_pct":    {"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.15, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80]},
    },
    # ── VWAP 偏離反轉
    "vwap_revert": {
        "vwap_period":     {"type": "categorical", "choices": [20, 50, 100]},
        "deviation_pct":   {"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── 52 週新高突破（年度高）
    "yearly_high_break": {
        "lookback":        {"type": "categorical", "choices": [120, 200, 250]},
        "break_buffer":    {"type": "float", "low": 0.0, "high": 0.02, "step": 0.005},
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.20, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 2.0, "high": 4.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [30, 60, 120]},
    },
    # ── Keltner channel 突破
    "keltner_breakout": {
        "kc_period":       {"type": "categorical", "choices": [20, 30, 50]},
        "kc_multiplier":   {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.15, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80]},
    },
    # ── MFI (Money Flow Index) 量價超賣反轉
    "mfi_oversold": {
        "mfi_period":      {"type": "categorical", "choices": [10, 14, 20]},
        "mfi_threshold":   {"type": "int", "low": 20, "high": 35, "step": 5},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── ROC (Rate of Change) 極端反轉
    "roc_reversal": {
        "roc_period":      {"type": "categorical", "choices": [10, 14, 21]},
        "roc_threshold":   {"type": "float", "low": -0.20, "high": -0.05, "step": 0.025},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.15, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── Williams %R 極端反轉
    "williams_r_extreme": {
        "wr_period":       {"type": "categorical", "choices": [10, 14, 21]},
        "wr_oversold":     {"type": "int", "low": -95, "high": -80, "step": 5},
        "wr_overbought":   {"type": "int", "low": -25, "high": -10, "step": 5},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── EMA cross (vs SMA cross)
    "ema_cross": {
        "fast_n":          {"type": "categorical", "choices": [5, 8, 12, 20]},
        "slow_n":          {"type": "categorical", "choices": [21, 34, 55, 100]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.20, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80, 120]},
    },
    # ── Gap-down 反轉
    "gap_down_revert": {
        "gap_pct":         {"type": "float", "low": 0.01, "high": 0.04, "step": 0.005},
        "require_close_up":{"type": "categorical", "choices": [True, False]},
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [5, 10, 20]},
    },
    # ── PSAR 反轉
    "psar_flip": {
        "step":            {"type": "float", "low": 0.01, "high": 0.04, "step": 0.005},
        "max_step":        {"type": "float", "low": 0.1, "high": 0.3, "step": 0.05},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.15, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80]},
    },
    # ── 低波動長均線小回檔 (專為 ETF/中華電/中鋼類)
    "slow_trend_pullback": {
        "long_ma":         {"type": "categorical", "choices": [200, 252, 504]},
        "short_ma":        {"type": "categorical", "choices": [20, 30, 50]},
        "pullback_pct":    {"type": "float", "low": 0.005, "high": 0.03, "step": 0.0025},
        "take_profit_pct": {"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [40, 80, 120, 252]},
    },
    # ── Stochastic RSI extremes (more sensitive than plain RSI)
    "stoch_rsi": {
        "rsi_period":      {"type": "categorical", "choices": [7, 14, 21]},
        "stoch_period":    {"type": "categorical", "choices": [7, 14, 21]},
        "oversold":        {"type": "int", "low": 10, "high": 25, "step": 5},
        "overbought":      {"type": "int", "low": 75, "high": 90, "step": 5},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── Awesome Oscillator zero-line cross
    "ao_zero_cross": {
        "short_n":         {"type": "categorical", "choices": [5, 9, 14]},
        "long_n":          {"type": "categorical", "choices": [21, 34, 55]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.15, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80]},
    },
    # ── 52-week LOW counter-trend bounce (vs yearly_high_break)
    "yearly_low_revert": {
        "lookback":        {"type": "categorical", "choices": [200, 250, 504]},
        "low_buffer":      {"type": "float", "low": 0.0, "high": 0.02, "step": 0.005},
        "trend_ma":        {"type": "categorical", "choices": [200, 252, 504]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.20, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [30, 60, 120]},
    },
    # ── ATR-band channel breakout
    "atr_band_breakout": {
        "ma_period":       {"type": "categorical", "choices": [20, 50, 100]},
        "atr_period":      {"type": "categorical", "choices": [10, 14, 20]},
        "atr_mult":        {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.20, "step": 0.025},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80]},
    },
    # ── 2 successive pullbacks (deeper pullback than single)
    "double_pullback": {
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "pullback_window": {"type": "categorical", "choices": [10, 20, 30]},
        "min_pullback_pct":{"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80]},
    },
    # ── Linear regression slope reversal
    "linreg_slope_revert": {
        "lr_period":       {"type": "categorical", "choices": [20, 50, 100]},
        "slope_threshold": {"type": "float", "low": -0.005, "high": -0.001, "step": 0.0005},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── Coppock curve buy signal (long-term momentum)
    "coppock_buy": {
        "roc1_n":          {"type": "categorical", "choices": [11, 14, 21]},
        "roc2_n":          {"type": "categorical", "choices": [14, 21, 30]},
        "wma_n":           {"type": "categorical", "choices": [7, 10, 14]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.20, "step": 0.025},
        "max_hold_days":   {"type": "categorical", "choices": [30, 60, 120]},
    },
    # ── Ultimate oscillator
    "ultimate_oscillator": {
        "uo_short":        {"type": "categorical", "choices": [5, 7]},
        "uo_mid":          {"type": "categorical", "choices": [10, 14]},
        "uo_long":         {"type": "categorical", "choices": [21, 28]},
        "uo_oversold":     {"type": "int", "low": 25, "high": 40, "step": 5},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── Inside-day breakout (T 日 HL 完全在 T-1 HL 內) + 下一日 high 突破
    "inside_day_breakout": {
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.15, "step": 0.025},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── 3 white soldiers (3 連紅 K 紅 K 在 oversold)
    "three_white_soldiers": {
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "min_drop_pct":    {"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "rsi_period":      {"type": "categorical", "choices": [7, 14]},
        "rsi_threshold":   {"type": "int", "low": 30, "high": 50, "step": 5},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── Outside day reversal (engulfing pattern)
    "outside_day_engulf": {
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "min_prev_drop":   {"type": "float", "low": 0.01, "high": 0.04, "step": 0.005},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [5, 10, 20]},
    },
    # ── Failed breakdown (跌破 N 日低後當日收回)
    "failed_breakdown": {
        "lookback":        {"type": "categorical", "choices": [20, 50, 100]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── Volume spike reverse (大量黑K後反彈)
    "volume_spike_reverse": {
        "vol_period":      {"type": "categorical", "choices": [10, 20, 50]},
        "vol_ratio":       {"type": "float", "low": 1.8, "high": 4.0, "step": 0.5},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.10, "step": 0.02},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [5, 10, 20]},
    },
    # ── 連 N 日 OBV 上升 (累積買盤)
    "obv_uptrend": {
        "obv_period":      {"type": "categorical", "choices": [5, 10, 20]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.15, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80]},
    },
    # ── Pivot point breakout (classic floor pivots)
    "pivot_break": {
        "pivot_lookback":  {"type": "categorical", "choices": [5, 10, 20]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── 短期動能 (5-day return high vs N-day high)
    "short_momentum": {
        "ret_period":      {"type": "categorical", "choices": [3, 5, 8, 13]},
        "min_return":      {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.15, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── 兩日連續放量 (back-to-back high volume)
    "double_volume": {
        "vol_period":      {"type": "categorical", "choices": [10, 20]},
        "vol_ratio":       {"type": "float", "low": 1.3, "high": 2.5, "step": 0.25},
        "trend_ma":        {"type": "categorical", "choices": [50, 100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [5, 10, 20]},
    },
    # ── 簡單跌深買 + 固定持有 (for 低波動藍籌)
    "simple_dip_buy": {
        "ma_period":       {"type": "categorical", "choices": [50, 100, 200]},
        "dip_pct":         {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.10, "step": 0.01},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 80, 120]},
    },
    # ── 月初效應 (month-start buy)
    "monthly_anchor": {
        "month_day":       {"type": "int", "low": 1, "high": 7, "step": 1},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 30]},
    },
    # ── 大跌長持 (deep drawdown + long hold) for 大型股
    "deep_dip_long_hold": {
        "lookback":        {"type": "categorical", "choices": [60, 120, 250]},
        "drawdown_pct":    {"type": "float", "low": 0.08, "high": 0.25, "step": 0.03},
        "take_profit_pct": {"type": "float", "low": 0.08, "high": 0.25, "step": 0.025},
        "max_hold_days":   {"type": "categorical", "choices": [60, 120, 200]},
    },
    # ── 周線最低買 (週低買法)
    "weekly_low_buy": {
        "lookback_weeks":  {"type": "categorical", "choices": [4, 8, 13]},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "max_hold_days":   {"type": "categorical", "choices": [20, 40, 60]},
    },
    # ── Trend-confirmation hold (MA50 > MA200 + price > MA50)
    "trend_confirm_hold": {
        "fast_ma":         {"type": "categorical", "choices": [30, 50, 80]},
        "slow_ma":         {"type": "categorical", "choices": [100, 150, 200]},
        "take_profit_pct": {"type": "float", "low": 0.05, "high": 0.25, "step": 0.025},
        "atr_stop_k":      {"type": "float", "low": 2.0, "high": 4.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [60, 120, 200]},
    },
    # ── 量縮反彈 (低量盤整後反彈)
    "low_volume_reversal": {
        "vol_period":      {"type": "categorical", "choices": [10, 20]},
        "vol_low_ratio":   {"type": "float", "low": 0.5, "high": 0.9, "step": 0.1},
        "trend_ma":        {"type": "categorical", "choices": [100, 200]},
        "take_profit_pct": {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "atr_stop_k":      {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "max_hold_days":   {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── 三大法人連續買超模板（chip persistence alpha）──────────────
    # 不同於 chip_momentum（單日 net-buy 觸發），chip_streak 強調「連續性」：
    # 法人持續加碼 N 天 + 累積買超達 avg_volume 的 X% 後進場。
    "chip_streak": {
        "actor":         {"type": "categorical", "choices": ["foreign", "trust", "either"]},
        "streak_days":   {"type": "int", "low": 3, "high": 10, "step": 1},
        "cum_pct_min":   {"type": "float", "low": 0.5, "high": 5.0, "step": 0.5},
        "trend_filter":  {"type": "categorical", "choices": [True, False]},
        "ma_period":     {"type": "categorical", "choices": [20, 30, 50, 60, 100]},
        "regime_filter": {"type": "categorical", "choices": ["any", "BULL", "BULL_or_NEUTRAL"]},
        "atr_mult":      {"type": "float", "low": 1.5, "high": 5.0, "step": 0.5},
        "max_hold_days": {"type": "int", "low": 10, "high": 60, "step": 5},
    },
    # ── 台灣市場特殊事件：每月 10 號前公布上月營收 ──
    # 強勢營收 YoY → 公告日 gap-up + 收紅 → T+1 開盤進場
    "monthly_revenue_event": {
        "revenue_yoy_min":     {"type": "float", "low": 0.10, "high": 0.50, "step": 0.05},
        "gap_pct":             {"type": "float", "low": 0.005, "high": 0.03, "step": 0.005},
        "require_green_close": {"type": "categorical", "choices": [True, False]},
        "max_hold_days":       {"type": "int", "low": 5, "high": 30, "step": 5},
        "atr_mult":            {"type": "float", "low": 1.5, "high": 4.0, "step": 0.5},
        "regime_filter":       {"type": "categorical",
                                "choices": ["any", "BULL", "BULL_or_NEUTRAL"]},
        "volume_filter":       {"type": "categorical", "choices": [True, False]},
        "volume_avg_period":   {"type": "int", "low": 5, "high": 30, "step": 5},
    },
    # ── Ensemble / composite strategies (5/16) ──────────────────────
    "ensemble_dip_vote": {
        "rsi_period":        {"type": "categorical", "choices": [7, 14, 21]},
        "rsi_thresh":        {"type": "int", "low": 25, "high": 40, "step": 5},
        "ma_period":         {"type": "categorical", "choices": [20, 50, 100, 200]},
        "dip_pct":           {"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "low_lookback":      {"type": "categorical", "choices": [10, 20, 60, 120]},
        "take_profit_pct":   {"type": "float", "low": 0.03, "high": 0.15, "step": 0.02},
        "max_hold_days":     {"type": "categorical", "choices": [10, 20, 40, 60]},
    },
    "ensemble_breakout_vote": {
        "donchian_n":        {"type": "categorical", "choices": [20, 55, 120]},
        "ma_period":         {"type": "categorical", "choices": [50, 100, 200]},
        "breakout_pct":      {"type": "float", "low": 0.0, "high": 0.05, "step": 0.01},
        "vol_period":        {"type": "categorical", "choices": [10, 20, 60]},
        "vol_ratio":         {"type": "float", "low": 1.0, "high": 2.5, "step": 0.25},
        "atr_stop_k":        {"type": "float", "low": 1.5, "high": 4.0, "step": 0.5},
        "take_profit_pct":   {"type": "float", "low": 0.04, "high": 0.20, "step": 0.02},
        "max_hold_days":     {"type": "categorical", "choices": [10, 20, 40, 80]},
    },
    "ensemble_oversold_vote": {
        "rsi_period":        {"type": "categorical", "choices": [7, 14, 21]},
        "rsi_thresh":        {"type": "int", "low": 25, "high": 40, "step": 5},
        "roc_period":        {"type": "categorical", "choices": [5, 10, 20]},
        "roc_thresh":        {"type": "float", "low": -0.12, "high": -0.03, "step": 0.02},
        "bb_period":         {"type": "categorical", "choices": [20, 30, 50]},
        "bb_std":            {"type": "float", "low": 1.5, "high": 3.0, "step": 0.5},
        "take_profit_pct":   {"type": "float", "low": 0.03, "high": 0.12, "step": 0.02},
        "max_hold_days":     {"type": "categorical", "choices": [10, 20, 40]},
    },
    "ensemble_trend_confirm": {
        "trend_long_ma":     {"type": "categorical", "choices": [100, 150, 200]},
        "trend_short_ma":    {"type": "categorical", "choices": [20, 30, 50]},
        "rsi_period":        {"type": "categorical", "choices": [7, 14]},
        "rsi_low":           {"type": "int", "low": 25, "high": 40, "step": 5},
        "rsi_recover":       {"type": "int", "low": 40, "high": 55, "step": 5},
        "vol_period":        {"type": "categorical", "choices": [10, 20, 60]},
        "vol_ratio":         {"type": "float", "low": 1.0, "high": 2.0, "step": 0.25},
        "atr_stop_k":        {"type": "float", "low": 1.5, "high": 4.0, "step": 0.5},
        "take_profit_pct":   {"type": "float", "low": 0.04, "high": 0.15, "step": 0.02},
        "max_hold_days":     {"type": "categorical", "choices": [20, 40, 80]},
    },
    "ensemble_dip_or_bounce": {
        "rsi_period":        {"type": "categorical", "choices": [7, 14, 21]},
        "rsi_thresh":        {"type": "int", "low": 30, "high": 45, "step": 5},
        "trend_ma":          {"type": "categorical", "choices": [50, 100, 200]},
        "decline_days":      {"type": "int", "low": 2, "high": 5, "step": 1},
        "take_profit_pct":   {"type": "float", "low": 0.04, "high": 0.12, "step": 0.02},
        "stop_pct":          {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "max_hold_days":     {"type": "categorical", "choices": [10, 20, 40]},
    },
    # ── Phase 2 ensembles (5/17, regime-aware) ──────────────
    "ensemble_regime_dip": {
        "rsi_period":        {"type": "categorical", "choices": [7, 14, 21]},
        "rsi_thresh":        {"type": "int", "low": 25, "high": 40, "step": 5},
        "ma_period":         {"type": "categorical", "choices": [20, 50, 100]},
        "dip_pct":           {"type": "float", "low": 0.02, "high": 0.08, "step": 0.01},
        "allow_neutral":     {"type": "categorical", "choices": [True, False]},
        "take_profit_pct":   {"type": "float", "low": 0.03, "high": 0.15, "step": 0.02},
        "max_hold_days":     {"type": "categorical", "choices": [10, 20, 40, 80]},
    },
    "ensemble_breakout_pullback": {
        "ma_breakout":       {"type": "categorical", "choices": [50, 100, 200]},
        "breakout_threshold": {"type": "float", "low": 0.03, "high": 0.15, "step": 0.02},
        "lookback_window":   {"type": "categorical", "choices": [20, 40, 60]},
        "pullback_range":    {"type": "float", "low": 0.01, "high": 0.05, "step": 0.005},
        "atr_stop_k":        {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "take_profit_pct":   {"type": "float", "low": 0.05, "high": 0.20, "step": 0.025},
        "max_hold_days":     {"type": "categorical", "choices": [20, 40, 80]},
    },
    "ensemble_dual_momentum": {
        "roc_period":        {"type": "categorical", "choices": [20, 60, 120]},
        "roc_thresh":        {"type": "float", "low": 0.0, "high": 0.15, "step": 0.025},
        "ma_period":         {"type": "categorical", "choices": [50, 100, 200]},
        "take_profit_pct":   {"type": "float", "low": 0.05, "high": 0.20, "step": 0.025},
        "stop_pct":          {"type": "float", "low": 0.03, "high": 0.10, "step": 0.01},
        "max_hold_days":     {"type": "categorical", "choices": [20, 40, 80, 160]},
    },
    "ensemble_triple_confirm": {
        "trend_ma":          {"type": "categorical", "choices": [50, 100, 200]},
        "rsi_period":        {"type": "categorical", "choices": [7, 14, 21]},
        "rsi_min":           {"type": "int", "low": 45, "high": 55, "step": 5},
        "rsi_lookback":      {"type": "int", "low": 3, "high": 10, "step": 1},
        "vol_period":        {"type": "categorical", "choices": [10, 20, 60]},
        "vol_ratio":         {"type": "float", "low": 1.0, "high": 2.0, "step": 0.25},
        "atr_stop_k":        {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "take_profit_pct":   {"type": "float", "low": 0.04, "high": 0.15, "step": 0.02},
        "max_hold_days":     {"type": "categorical", "choices": [20, 40, 80]},
        "stop_buffer":       {"type": "float", "low": 0.90, "high": 0.98, "step": 0.02},
    },
    "ensemble_bullish_divergence": {
        "rsi_period":        {"type": "categorical", "choices": [7, 14, 21]},
        "lookback_window":   {"type": "categorical", "choices": [10, 20, 40, 60]},
        "tolerance":         {"type": "float", "low": 0.0, "high": 0.03, "step": 0.005},
        "div_threshold":     {"type": "int", "low": 5, "high": 20, "step": 5},
        "rsi_max":           {"type": "int", "low": 35, "high": 50, "step": 5},
        "atr_stop_k":        {"type": "float", "low": 1.5, "high": 3.5, "step": 0.5},
        "take_profit_pct":   {"type": "float", "low": 0.04, "high": 0.15, "step": 0.02},
        "max_hold_days":     {"type": "categorical", "choices": [10, 20, 40]},
    },
}

TEMPLATE_NAMES = list(SEARCH_SPACES.keys())


def sample_template_params(template_name: str, trial) -> dict:
    """Sample one parameter set for a given template from an optuna trial."""
    space = SEARCH_SPACES[template_name]
    params = {}
    for k, spec in space.items():
        t = spec["type"]
        if t == "categorical":
            params[k] = trial.suggest_categorical(k, spec["choices"])
        elif t == "int":
            params[k] = trial.suggest_int(k, spec["low"], spec["high"],
                                           step=spec.get("step", 1))
        elif t == "float":
            params[k] = trial.suggest_float(k, spec["low"], spec["high"],
                                             step=spec.get("step"))
    return params


# ── Template generators ──────────────────────────────────────────


def sample_template_params(template_name: str, trial) -> dict:
    """Sample one parameter set for a given template from an optuna trial."""
    space = SEARCH_SPACES[template_name]
    params = {}
    for k, spec in space.items():
        t = spec["type"]
        if t == "categorical":
            params[k] = trial.suggest_categorical(k, spec["choices"])
        elif t == "int":
            params[k] = trial.suggest_int(k, spec["low"], spec["high"],
                                           step=spec.get("step", 1))
        elif t == "float":
            params[k] = trial.suggest_float(k, spec["low"], spec["high"],
                                             step=spec.get("step"))
    return params


# ── Template generators ──────────────────────────────────────────
