"""
Five strategy template signal generators for auto_iterate.

Each generator:  generate_T*(df, params, regime=None, chip_data=None) -> DataFrame
Returns DataFrame with at least 'action' column (BUY/SELL/HOLD), index = df.index.

T1 trend_pullback   — delegates to existing style1_pullback
T2 donchian_breakout — N-day high breakout + ATR stop
T3 momentum_hold     — raw momentum entry/exit
T4 chip_momentum     — momentum + institutional chip filter (single-window)
T5 mean_reversion    — long-trend + short-MA pullback + RSI
chip_streak         — institutional persistent net-buy streak (consecutive days)
"""
import numpy as np
import pandas as pd

from src.strategy.indicators.trend import sma
from src.strategy.indicators.momentum import rsi
from src.strategy.indicators.volatility import atr, bollinger
from src.strategy.indicators.volume import volume_ma
from src.strategy.optimize.search_space import SEARCH_SPACE as _T1_SPACE


# ── Search spaces ────────────────────────────────────────────────

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

def generate_T1(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """trend_pullback: delegates to style1_pullback.generate_signals.

    限價單機制（v0.1）：把 style1 的 entry_high/stop_loss 對應成 target：
      target_buy: entry_high（buy-limit；T+1 跌進區間就買）
      target_buy_mode: 'limit'
      target_tp: NaN（無固定 TP，靠 ATR trailing/RSI overbought/max_hold 出場）
      target_sl: stop_loss（MA200 / ATR 取較高者，與 style1 一致）
    """
    from src.strategy.signals.style1_pullback import generate_signals
    if regime is None:
        regime = pd.Series("BULL", index=df.index)
    sig = generate_signals(df, regime, params)

    # 把 style1 既有欄位對應到 limit-order 介面
    n = len(sig)
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = sig["stop_loss"].values.tolist() if "stop_loss" in sig.columns else [np.nan] * n
    target_mode = [""] * n

    actions = sig["action"].values
    e_high = sig["entry_high"].values if "entry_high" in sig.columns else None

    for i, a in enumerate(actions):
        if a == "BUY" and e_high is not None and not np.isnan(e_high[i]):
            target_buy[i] = e_high[i]
            target_mode[i] = "limit"
        # 在倉時的 target_sl 已經由 style1 的 stop_loss 提供，直接沿用

    sig["target_buy"] = target_buy
    sig["target_tp"] = target_tp
    sig["target_sl"] = target_sl
    sig["target_buy_mode"] = target_mode
    return sig


def generate_T2(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """donchian_breakout: N-day high entry (stop-buy), M-day low exit, ATR trailing stop.

    限價單機制（v0.1）：
      target_buy: T+1 漲到 don_high 才買（buy-stop 模式 = 突破才買）
      target_buy_mode: 'stop'
      target_tp: NaN（trailing 出場，無固定 TP）
      target_sl: max(don_low, atr_stop)
    """
    close = df["close"]
    high  = df["high"]
    vol   = df["volume"]

    entry_n   = int(params["donchian_entry_n"])
    exit_n    = int(params["donchian_exit_n"])
    trend_n   = int(params["trend_ma"])
    atr_k     = float(params["atr_stop_k"])
    vol_ratio = float(params["volume_min_ratio"])

    trend_ma_s = sma(close, trend_n)
    vol_ma20   = volume_ma(vol, 20)
    atr_s      = atr(df, 14)
    don_high = close.rolling(entry_n).max().shift(1)
    don_low  = close.rolling(exit_n).min().shift(1)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    target_mode = [""] * n

    in_pos = False
    high_since = np.nan

    for i in range(n):
        c  = close.iloc[i]
        h  = high.iloc[i]
        v  = vol.iloc[i]
        tm = trend_ma_s.iloc[i]
        vm = vol_ma20.iloc[i]
        dh = don_high.iloc[i]
        dl = don_low.iloc[i]
        ai = atr_s.iloc[i]

        if in_pos:
            if not np.isnan(h):
                high_since = max(high_since, h) if not np.isnan(high_since) else h
            atr_stop = (high_since - atr_k * ai
                        if not np.isnan(high_since) and not np.isnan(ai) else np.nan)
            # 隔日掛單目標 SL（取 don_low 與 atr_stop 較高者保守）
            if not np.isnan(dl) and not np.isnan(atr_stop):
                target_sl[i] = max(dl, atr_stop)
            elif not np.isnan(dl):
                target_sl[i] = dl
            elif not np.isnan(atr_stop):
                target_sl[i] = atr_stop
            # T close 已破 → 隔日 market sell
            exit_cond = (not np.isnan(dl) and c < dl) or \
                        (not np.isnan(atr_stop) and c < atr_stop)
            if exit_cond:
                action[i] = "SELL"
                in_pos = False
                high_since = np.nan
                target_sl[i] = np.nan
        else:
            # 進場條件：T close 已突破 don_high 等
            if (not np.isnan(dh) and c >= dh and
                    not np.isnan(tm) and c > tm and
                    not np.isnan(vm) and v > vm * vol_ratio):
                action[i] = "BUY"
                # buy-stop：隔日漲到 dh 才買（其實 T close 已 ≥ dh，所以 T+1 開盤通常會直接成交）
                target_buy[i] = dh
                target_mode[i] = "stop"
                in_pos = True
                high_since = h

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
        "target_buy_mode": target_mode,
    }, index=df.index)


def generate_T3(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """momentum_hold: lookback-period return threshold entry/exit.

    限價單機制（v0.1）：
      target_buy: T_close（buy-limit；T+1 觸及就買）
      target_buy_mode: 'limit'
      target_tp: NaN（本策略無固定 TP，靠動量轉折出場）
      target_sl: trend_ma_at_T（趨勢線停損）
    """
    close    = df["close"]
    lookback = int(params["mom_lookback"])
    entry_p  = float(params["mom_entry_pct"])
    exit_p   = float(params["mom_exit_pct"])
    trend_n  = int(params["trend_ma"])

    trend_ma_s = sma(close, trend_n)
    mom        = close / close.shift(lookback) - 1

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    target_mode = [""] * n

    in_pos = False

    for i in range(n):
        c  = close.iloc[i]
        m  = mom.iloc[i]
        tm = trend_ma_s.iloc[i]

        if in_pos:
            if not np.isnan(tm):
                target_sl[i] = tm
            # T close 已觸發 → 隔日 market sell
            mom_break = (not np.isnan(m) and m < exit_p)
            trend_break = (not np.isnan(tm) and c < tm)
            if mom_break or trend_break:
                action[i] = "SELL"
                in_pos = False
                target_sl[i] = np.nan
        else:
            if not np.isnan(m) and m > entry_p and \
               not np.isnan(tm) and c > tm:
                action[i] = "BUY"
                target_buy[i] = c   # buy-limit at T_close
                target_mode[i] = "limit"
                in_pos = True

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
        "target_buy_mode": target_mode,
    }, index=df.index)


def generate_T4(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """chip_momentum: momentum + institutional chip cumulative filter."""
    if chip_data is None or chip_data.empty:
        return pd.DataFrame({"action": ["HOLD"] * len(df)}, index=df.index)

    close    = df["close"]
    high     = df["high"]
    lookback = int(params["mom_lookback"])
    entry_p  = float(params["mom_entry_pct"])
    chip_win = int(params["chip_window"])
    trend_n  = int(params["trend_ma"])
    atr_k    = float(params["atr_stop_k"])

    trend_ma_s = sma(close, trend_n)
    atr_s      = atr(df, 14)
    mom        = close / close.shift(lookback) - 1

    # Chip: T-1 shift (anti-lookahead) then rolling sum
    combo = (chip_data.get("foreign_net", pd.Series(0, index=chip_data.index))
             .add(chip_data.get("trust_net", pd.Series(0, index=chip_data.index)),
                  fill_value=0))
    combo_aligned = combo.reindex(df.index).fillna(0)
    chip_roll = combo_aligned.shift(1).rolling(chip_win, min_periods=chip_win).sum()

    n = len(df)
    action = ["HOLD"] * n
    in_pos = False
    high_since = np.nan

    for i in range(n):
        c  = close.iloc[i]
        h  = high.iloc[i]
        m  = mom.iloc[i]
        tm = trend_ma_s.iloc[i]
        cr = chip_roll.iloc[i]
        ai = atr_s.iloc[i]

        if in_pos:
            if not np.isnan(h):
                high_since = max(high_since, h) if not np.isnan(high_since) else h
            atr_stop = (high_since - atr_k * ai
                        if not np.isnan(high_since) and not np.isnan(ai) else np.nan)
            if (not np.isnan(cr) and cr < 0) or \
               (not np.isnan(atr_stop) and c < atr_stop):
                action[i] = "SELL"
                in_pos = False
                high_since = np.nan
        else:
            if not np.isnan(m) and m > entry_p and \
               not np.isnan(cr) and cr > 0 and \
               not np.isnan(tm) and c > tm:
                action[i] = "BUY"
                in_pos = True
                high_since = h

    return pd.DataFrame({"action": action}, index=df.index)


def generate_T5(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """mean_reversion: long-trend filter + short-MA pullback + RSI oversold entry.

    限價單機制（v0.1）：每天 T close 後，輸出隔日掛單目標價。
      target_buy : T 已滿足進場條件 → 隔日掛限價買 = T_close
      target_tp  : 在倉時 → 隔日掛限價賣 = short_ma × (1 + tp_pct)（rebound 目標）
      target_sl  : 在倉時 → 隔日停損參考 trend_ma_at_T（trend break 防線）
    """
    close        = df["close"]
    trend_n      = int(params["trend_ma"])
    short_n      = int(params["short_ma"])
    pb_pct       = float(params["pullback_pct"])
    rsi_period   = int(params["rsi_period"])
    rsi_over     = int(params["rsi_oversold"])
    rsi_under    = int(params["rsi_overbought"])
    tp_pct       = float(params["take_profit_pct"])
    max_hold     = int(params["max_hold_days"])

    trend_ma_s   = sma(close, trend_n)
    short_ma_s   = sma(close, short_n)
    rsi_s        = rsi(close, rsi_period)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n

    in_pos = False
    hold_days = 0
    entry_price = np.nan

    for i in range(n):
        c  = close.iloc[i]
        r  = rsi_s.iloc[i]
        tm = trend_ma_s.iloc[i]
        sm = short_ma_s.iloc[i]

        if in_pos:
            hold_days += 1
            # 隔日掛單目標
            if not np.isnan(sm):
                target_tp[i] = sm * (1 + tp_pct)   # 反彈到 short_ma 之上 → TP
            if not np.isnan(tm):
                target_sl[i] = tm                    # 跌破 trend_ma → SL

            # T close 已觸發 → 隔日 market sell（走 SELL action）
            tp_hit = (not np.isnan(target_tp[i])) and (c >= target_tp[i])
            sl_hit = (not np.isnan(target_sl[i])) and (c < target_sl[i])
            rsi_over_bought = (not np.isnan(r) and r > rsi_under)
            timeout = hold_days >= max_hold
            if tp_hit or sl_hit or rsi_over_bought or timeout:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                entry_price = np.nan
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if not np.isnan(tm) and c > tm and \
               not np.isnan(sm) and c < sm * (1 - pb_pct) and \
               not np.isnan(r) and r < rsi_over:
                action[i] = "BUY"
                # 限價買在「進場區間上界」= short_ma × (1 - pb_pct)
                target_buy[i] = sm * (1 - pb_pct)
                in_pos = True
                entry_price = c
                hold_days = 0

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
    }, index=df.index)


def generate_T6(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """volume_breakout: lookback-N high break + volume surge, ATR trailing exit.

    比 donchian_breakout 寬鬆：去掉 trend_ma filter，
    僅以「突破前 N 日新高 + 量能放大」為進場，適合 LOW_SAMPLE 大型權值股。

    限價單機制（v0.1）：
      target_buy: don_high（buy-stop 模式 = 突破才買）
      target_buy_mode: 'stop'
      target_tp: NaN
      target_sl: max(short_ma, atr_stop)
    """
    close = df["close"]
    high  = df["high"]
    vol   = df["volume"]

    lookback   = int(params["lookback"])
    vol_ratio  = float(params["vol_ratio"])
    short_n    = int(params["short_ma_exit"])
    atr_k      = float(params["atr_stop_k"])

    vol_ma20   = volume_ma(vol, 20)
    atr_s      = atr(df, 14)
    short_ma_s = sma(close, short_n)
    don_high   = close.rolling(lookback).max().shift(1)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    target_mode = [""] * n

    in_pos = False
    high_since = np.nan

    for i in range(n):
        c  = close.iloc[i]
        h  = high.iloc[i]
        v  = vol.iloc[i]
        vm = vol_ma20.iloc[i]
        dh = don_high.iloc[i]
        ai = atr_s.iloc[i]
        sm = short_ma_s.iloc[i]

        if in_pos:
            if not np.isnan(h):
                high_since = max(high_since, h) if not np.isnan(high_since) else h
            atr_stop = (high_since - atr_k * ai
                        if not np.isnan(high_since) and not np.isnan(ai) else np.nan)
            # 隔日 SL（兩個取較高者保護更多）
            if not np.isnan(sm) and not np.isnan(atr_stop):
                target_sl[i] = max(sm, atr_stop)
            elif not np.isnan(sm):
                target_sl[i] = sm
            elif not np.isnan(atr_stop):
                target_sl[i] = atr_stop
            if (not np.isnan(sm) and c < sm) or \
               (not np.isnan(atr_stop) and c < atr_stop):
                action[i] = "SELL"
                in_pos = False
                high_since = np.nan
                target_sl[i] = np.nan
        else:
            if (not np.isnan(dh) and c >= dh and
                    not np.isnan(vm) and v > vm * vol_ratio):
                action[i] = "BUY"
                target_buy[i] = dh
                target_mode[i] = "stop"
                in_pos = True
                high_since = h

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
        "target_buy_mode": target_mode,
    }, index=df.index)


def generate_T7(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """gap_continuation: 強勢跳空 → 持有 N 日 / ATR stop / 趨勢 break。

    進場：當日 open ≥ 昨日 close × (1 + gap_pct) 且當日 close ≥ open（跳空收紅）
    出場：max_hold_days 到 / ATR trailing / 跌破 trend_ma
    """
    close = df["close"]
    open_ = df["open"]
    high  = df["high"]

    gap_pct    = float(params["gap_pct"])
    max_hold   = int(params["max_hold_days"])
    stop_k     = float(params["stop_atr_k"])
    trend_n    = int(params["trend_ma"])

    trend_ma_s = sma(close, trend_n)
    atr_s      = atr(df, 14)
    prev_close = close.shift(1)

    n = len(df)
    action = ["HOLD"] * n
    in_pos = False
    high_since = np.nan
    hold_days = 0

    for i in range(n):
        c  = close.iloc[i]
        o  = open_.iloc[i]
        h  = high.iloc[i]
        pc = prev_close.iloc[i]
        tm = trend_ma_s.iloc[i]
        ai = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(h):
                high_since = max(high_since, h) if not np.isnan(high_since) else h
            atr_stop = (high_since - stop_k * ai
                        if not np.isnan(high_since) and not np.isnan(ai) else np.nan)
            exit_cond = (
                hold_days >= max_hold or
                (not np.isnan(atr_stop) and c < atr_stop) or
                (not np.isnan(tm) and c < tm)
            )
            if exit_cond:
                action[i] = "SELL"
                in_pos = False
                high_since = np.nan
                hold_days = 0
        else:
            if (not np.isnan(pc) and pc > 0 and
                    not np.isnan(o) and o >= pc * (1 + gap_pct) and
                    not np.isnan(c) and c >= o and
                    not np.isnan(tm) and c > tm):
                action[i] = "BUY"
                in_pos = True
                high_since = h
                hold_days = 0

    return pd.DataFrame({"action": action}, index=df.index)


def generate_T8(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """low_vol_pullback: 長期上升趨勢 + 連續 N 日小幅回檔 → 進場。

    比 mean_reversion 更寬鬆：不需要 RSI 極值，只看連續紅黑 K + 小幅跌幅。
    為傳產 / 慢牛低波動標的設計。

    限價單機制（v0.1）：每天 T close 後，輸出隔日掛單目標價。
      target_buy : T 已滿足進場條件 → 隔日掛限價買 = T_close
      target_tp  : 在倉時 → 隔日掛限價賣 = entry_price × (1 + tp_pct)
      target_sl  : 在倉時 → 隔日掛停損 = long_ma_at_T（趨勢線停損）
    """
    close   = df["close"]
    long_n  = int(params["long_ma"])
    short_n = int(params["short_ma"])
    dn_days = int(params["down_days"])
    pb_pct  = float(params["pb_pct"])
    tp_pct  = float(params["take_profit_pct"])
    max_h   = int(params["max_hold_days"])

    long_ma_s  = sma(close, long_n)
    short_ma_s = sma(close, short_n)

    down = (close.diff() < 0).astype(int)
    grp = (down != down.shift()).cumsum()
    consec_down = down.groupby(grp).cumsum()

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n

    in_pos = False
    entry_price = np.nan
    hold_days = 0

    for i in range(n):
        c  = close.iloc[i]
        lm = long_ma_s.iloc[i]
        sm = short_ma_s.iloc[i]
        cd = consec_down.iloc[i] if i < len(consec_down) else 0

        if in_pos:
            hold_days += 1
            # 隔日掛單目標
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            if not np.isnan(lm):
                target_sl[i] = lm

            # T close 已觸發 TP/SL/timeout → 隔日 market sell（走 SELL action）
            tp_hit = (not np.isnan(target_tp[i])) and (c >= target_tp[i])
            trend_break = (not np.isnan(target_sl[i])) and (c < target_sl[i])
            timeout = hold_days >= max_h
            if tp_hit or trend_break or timeout:
                action[i] = "SELL"
                in_pos = False
                entry_price = np.nan
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if (not np.isnan(lm) and c > lm and
                    not np.isnan(sm) and c < sm * (1 - pb_pct) and
                    cd >= dn_days):
                action[i] = "BUY"
                # 限價買在「進場區間上界」= short_ma × (1 - pb_pct)
                target_buy[i] = sm * (1 - pb_pct)
                in_pos = True
                entry_price = c   # generator 內部追蹤用 T_close 當假設 entry（用於 target_tp 計算）
                hold_days = 0

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
    }, index=df.index)


def generate_T9(df: pd.DataFrame, params: dict,
                regime=None, chip_data=None) -> pd.DataFrame:
    """bollinger_squeeze: 波動壓縮 → 突破帶口進場 (volatility expansion)。

    進場：BB band-width 處於 N 日 lookback 的最低 squeeze_pct 分位（壓縮中）
          且 close 突破 BB upper 且 close > trend_ma
    出場：close 跌破 BB mid 或 ATR trailing stop

    限價單機制（v0.1）：
      target_buy: bb_upper（buy-stop = 突破帶口才買）
      target_buy_mode: 'stop'
      target_tp: NaN
      target_sl: max(bb_mid, atr_stop)
    """
    close   = df["close"]
    high    = df["high"]

    bb_n    = int(params["bb_period"])
    bb_k    = float(params["bb_k"])
    sq_lb   = int(params["squeeze_lookback"])
    sq_p    = float(params["squeeze_pct"])
    trend_n = int(params["trend_ma"])
    atr_k   = float(params["atr_stop_k"])

    bb         = bollinger(close, bb_n, bb_k)
    bb_width   = (bb["upper"] - bb["lower"]) / bb["mid"]
    width_q    = bb_width.rolling(sq_lb).quantile(sq_p)
    trend_ma_s = sma(close, trend_n)
    atr_s      = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    target_mode = [""] * n

    in_pos = False
    high_since = np.nan

    for i in range(n):
        c   = close.iloc[i]
        h   = high.iloc[i]
        bw  = bb_width.iloc[i]
        wq  = width_q.iloc[i]
        bu  = bb["upper"].iloc[i]
        bm  = bb["mid"].iloc[i]
        tm  = trend_ma_s.iloc[i]
        ai  = atr_s.iloc[i]

        if in_pos:
            if not np.isnan(h):
                high_since = max(high_since, h) if not np.isnan(high_since) else h
            atr_stop = (high_since - atr_k * ai
                        if not np.isnan(high_since) and not np.isnan(ai) else np.nan)
            # 隔日 SL（取較高者保護）
            if not np.isnan(bm) and not np.isnan(atr_stop):
                target_sl[i] = max(bm, atr_stop)
            elif not np.isnan(bm):
                target_sl[i] = bm
            elif not np.isnan(atr_stop):
                target_sl[i] = atr_stop
            if (not np.isnan(bm) and c < bm) or \
               (not np.isnan(atr_stop) and c < atr_stop):
                action[i] = "SELL"
                in_pos = False
                high_since = np.nan
                target_sl[i] = np.nan
        else:
            squeezed = (not np.isnan(bw) and not np.isnan(wq) and bw <= wq)
            breakout = (not np.isnan(bu) and c > bu)
            trend_ok = (not np.isnan(tm) and c > tm)
            if squeezed and breakout and trend_ok:
                action[i] = "BUY"
                target_buy[i] = bu
                target_mode[i] = "stop"
                in_pos = True
                high_since = h

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
        "target_buy_mode": target_mode,
    }, index=df.index)


def generate_signals_chip_streak(df: pd.DataFrame, params: dict,
                                 regime=None, chip_data=None) -> pd.DataFrame:
    """chip_streak: institutional persistent net-buy streak entry.

    Hypothesis: when foreign / investment-trust funds net-buy a stock for
    streak_days consecutive sessions AND cumulative net buy ≥ cum_pct_min %
    of (avg daily volume × streak_days), this often precedes a sustained
    5–15% move within 1–2 months. Distinct from chip_momentum which only
    sums chip flows over a window — here we require persistence.

    Entry (T+1 open via engine):
      1. Streak length on chosen actor ≥ streak_days at T (using shifted chip data).
      2. Cumulative net-buy shares over the streak ≥ cum_pct_min% * avg_vol(20) * streak_days.
      3. Optional trend filter: close > SMA(ma_period).
      4. Optional regime filter: BULL or BULL/NEUTRAL.

    Exit:
      1. Streak breaks (any net-sell day on the chosen actor) → SELL.
      2. ATR(14) trailing stop: high_since - atr_mult * ATR.
      3. max_hold_days hit.

    Anti-lookahead: chip_data and price-derived signals are shifted by 1 day
    so the entry decision at index i uses only data through i-1, then the
    engine executes at T+1 open.
    """
    n = len(df)
    if chip_data is None or len(chip_data) == 0:
        return pd.DataFrame({"action": ["HOLD"] * n}, index=df.index)

    actor          = str(params.get("actor", "either"))
    streak_days    = int(params["streak_days"])
    cum_pct_min    = float(params["cum_pct_min"])
    trend_filter   = bool(params.get("trend_filter", False))
    ma_period      = int(params.get("ma_period", 50))
    regime_filter  = str(params.get("regime_filter", "any"))
    atr_mult       = float(params["atr_mult"])
    max_hold_days  = int(params["max_hold_days"])

    close   = df["close"]
    high    = df["high"]
    volume  = df["volume"]

    # Pick actor net-flow series (aligned to df.index, missing days = 0)
    foreign = chip_data.get("foreign_net",
                            pd.Series(0.0, index=chip_data.index))
    trust   = chip_data.get("trust_net",
                            pd.Series(0.0, index=chip_data.index))
    if actor == "foreign":
        flow = foreign
    elif actor == "trust":
        flow = trust
    else:  # "either" — use foreign + trust combined net
        flow = foreign.add(trust, fill_value=0)

    flow_aligned = flow.reindex(df.index).fillna(0.0)
    # T-1 shift to enforce no lookahead (decision at T uses up to T-1 data)
    flow_lag = flow_aligned.shift(1)

    # Compute per-day "is net buy" boolean and rolling streak length.
    is_buy = (flow_lag > 0).astype(int)
    # Streak length = consecutive 1s ending at i. Using groupby trick:
    grp = (is_buy != is_buy.shift()).cumsum()
    streak_len = is_buy.groupby(grp).cumsum()  # 0 when not buy, otherwise running count

    # Rolling cumulative net buy over streak_days window (lagged flow)
    cum_flow = flow_lag.rolling(streak_days, min_periods=streak_days).sum()

    # Avg volume for normalisation (20-day MA, also lagged for safety)
    vol_ma20 = volume_ma(volume, 20).shift(1)

    # Trend / ATR
    trend_ma_s = sma(close, ma_period) if trend_filter else None
    atr_s      = atr(df, 14)

    action = ["HOLD"] * n
    in_pos = False
    high_since = np.nan
    hold_days = 0

    # Pre-compute regime values aligned (defensive — engine may pass series)
    if regime is not None and not isinstance(regime, pd.Series):
        regime = None

    for i in range(n):
        c   = close.iloc[i]
        h   = high.iloc[i]
        sl  = streak_len.iloc[i] if i < len(streak_len) else 0
        cf  = cum_flow.iloc[i]
        vm  = vol_ma20.iloc[i]
        ai  = atr_s.iloc[i]
        f_today = flow_lag.iloc[i]   # net flow attributed to T-1 (decision input at T)

        if in_pos:
            hold_days += 1
            if not np.isnan(h):
                high_since = max(high_since, h) if not np.isnan(high_since) else h
            atr_stop = (high_since - atr_mult * ai
                        if not np.isnan(high_since) and not np.isnan(ai)
                        else np.nan)

            streak_break = (not np.isnan(f_today)) and f_today < 0
            stop_hit     = (not np.isnan(atr_stop)) and c < atr_stop
            time_out     = hold_days >= max_hold_days

            if streak_break or stop_hit or time_out:
                action[i] = "SELL"
                in_pos = False
                high_since = np.nan
                hold_days = 0
        else:
            # Streak length condition
            streak_ok = (not pd.isna(sl)) and sl >= streak_days
            # Cumulative buy threshold (in shares): cum_flow >= cum_pct_min/100 * vol_ma * streak_days
            cum_ok = (
                not np.isnan(cf) and not np.isnan(vm) and vm > 0
                and cf >= (cum_pct_min / 100.0) * vm * streak_days
            )
            # Trend filter
            trend_ok = True
            if trend_filter:
                tm = trend_ma_s.iloc[i] if trend_ma_s is not None else np.nan
                trend_ok = (not np.isnan(tm)) and c > tm
            # Regime filter
            regime_ok = True
            if regime_filter != "any" and regime is not None:
                try:
                    r_val = regime.iloc[i] if i < len(regime) else None
                except Exception:
                    r_val = None
                if regime_filter == "BULL":
                    regime_ok = (r_val == "BULL")
                elif regime_filter == "BULL_or_NEUTRAL":
                    regime_ok = (r_val in ("BULL", "NEUTRAL"))

            if streak_ok and cum_ok and trend_ok and regime_ok:
                action[i] = "BUY"
                in_pos = True
                high_since = h
                hold_days = 0

    return pd.DataFrame({"action": action}, index=df.index)


def generate_signals_monthly_revenue_event(
    df: pd.DataFrame, params: dict,
    regime=None, chip_data=None, revenue_data=None,
) -> pd.DataFrame:
    """monthly_revenue_event: enter on Taiwan monthly revenue announcement day
    when YoY growth is strong AND price gap-ups confirm market reaction.

    Hypothesis: 台灣上市公司依規定每月 10 號前公布上月營收，是台股獨有的
    同步資訊釋放事件。當 YoY 營收成長率 ≥ X%，且公告日當天股票跳空 (gap-up)
    並收紅，市場確認消息利多 → 隔日開盤進場往往有正期望值。

    Entry (decision at T, executes T+1 open via engine):
      1. T 必須是「營收公告日」: 對該 sid 而言，存在某筆 revenue 資料的
         announcement_date <= T 且 announcement_date 落在 T 當週（最近一筆）。
         具體：取最新 announcement_date <= T，若 T - that <= 0 → T 即公告當日。
         （我們把所有 announcement_date 都標成 cache 中的「revenue 期月次月+10 天」，
          所以「公告日」是該日。）
      2. 該筆 revenue 的 YoY ≥ revenue_yoy_min
      3. T 當日 close > open（綠 K）—— 若 require_green_close
      4. T 當日 open >= 昨收 * (1 + gap_pct)
      5. Optional: regime_filter
      6. Optional: volume_filter — T 當日成交量 > avg(volume, period)

    Exit:
      1. hold ≥ max_hold_days
      2. ATR(14) trailing stop: high_since - atr_mult * atr
      3. （隱含）下個月若再次出現「公告日 + YoY < threshold」可提早出 — 此處簡化
         為純 ATR + max_hold；若想加 revenue-deteriorate exit 可在後續 iteration 加。

    Anti-lookahead: announcement_date 已在 fetcher 加 +10 天（保守估），
    且 T 日訊號只用 announcement_date <= T 的 revenue 資料；T+1 才實際成交。
    """
    n = len(df)
    if revenue_data is None or len(revenue_data) == 0:
        return pd.DataFrame({"action": ["HOLD"] * n}, index=df.index)

    # 防呆：必要欄位
    if not {"announcement_date", "revenue_growth_yoy_pct"}.issubset(
            revenue_data.columns):
        return pd.DataFrame({"action": ["HOLD"] * n}, index=df.index)

    yoy_min       = float(params["revenue_yoy_min"])
    gap_pct       = float(params["gap_pct"])
    require_green = bool(params.get("require_green_close", True))
    max_hold      = int(params["max_hold_days"])
    atr_mult      = float(params["atr_mult"])
    regime_filter = str(params.get("regime_filter", "any"))
    volume_filter = bool(params.get("volume_filter", False))
    vol_period    = int(params.get("volume_avg_period", 20))

    close = df["close"]
    open_ = df["open"]
    high  = df["high"]
    vol   = df["volume"]
    prev_close = close.shift(1)

    atr_s    = atr(df, 14)
    vol_ma_s = volume_ma(vol, vol_period) if volume_filter else None

    # ── Build "announcement-day → yoy" map aligned to df.index ──────────
    # 每筆 revenue 的 announcement_date 對應該日的 YoY；若該日不是交易日
    # （週末/假日），向後 ffill 到第一個交易日，模擬「公告當日（含遞延到下一交易日）
    # 的訊號日」。為避免長時段重複觸發，我們只在「真正第一個有訊號的交易日」打標記。
    rev = revenue_data.copy()
    rev = rev.dropna(subset=["announcement_date", "revenue_growth_yoy_pct"])
    rev["announcement_date"] = pd.to_datetime(rev["announcement_date"])
    rev = rev.sort_values("announcement_date")

    # 對每個 revenue announcement，找 df.index 中第一個 >= announcement_date 的日期
    yoy_on_day = pd.Series(np.nan, index=df.index, dtype=float)
    idx_arr = df.index.values
    if len(idx_arr) > 0:
        for ann_dt, yoy in zip(rev["announcement_date"].values,
                               rev["revenue_growth_yoy_pct"].values):
            if pd.isna(yoy):
                continue
            # searchsorted 找第一個 >= ann_dt 的位置（左插入點）
            pos = np.searchsorted(idx_arr, ann_dt, side="left")
            if pos < len(idx_arr):
                target_day = df.index[pos]
                # 同一個交易日只記一次（取後到的會覆蓋；通常 1 個月 1 筆，無衝突）
                yoy_on_day.loc[target_day] = float(yoy)

    # Pre-compute regime values aligned (defensive)
    if regime is not None and not isinstance(regime, pd.Series):
        regime = None

    action = ["HOLD"] * n
    in_pos = False
    high_since = np.nan
    hold_days = 0

    for i in range(n):
        c  = close.iloc[i]
        o  = open_.iloc[i]
        h  = high.iloc[i]
        v  = vol.iloc[i]
        pc = prev_close.iloc[i]
        ai = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(h):
                high_since = max(high_since, h) if not np.isnan(high_since) else h
            atr_stop = (high_since - atr_mult * ai
                        if not np.isnan(high_since) and not np.isnan(ai)
                        else np.nan)
            stop_hit = (not np.isnan(atr_stop)) and c < atr_stop
            time_out = hold_days >= max_hold
            if stop_hit or time_out:
                action[i] = "SELL"
                in_pos = False
                high_since = np.nan
                hold_days = 0
        else:
            yoy = yoy_on_day.iloc[i]
            if pd.isna(yoy):
                continue
            if yoy < yoy_min:
                continue
            # gap-up
            if pd.isna(pc) or pc <= 0:
                continue
            if pd.isna(o) or o < pc * (1 + gap_pct):
                continue
            # green close
            if require_green and (pd.isna(c) or c <= o):
                continue
            # volume filter
            if volume_filter and vol_ma_s is not None:
                vm = vol_ma_s.iloc[i]
                if pd.isna(vm) or pd.isna(v) or v <= vm:
                    continue
            # regime filter
            if regime_filter != "any" and regime is not None:
                try:
                    r_val = regime.iloc[i] if i < len(regime) else None
                except Exception:
                    r_val = None
                if regime_filter == "BULL" and r_val != "BULL":
                    continue
                if regime_filter == "BULL_or_NEUTRAL" and \
                        r_val not in ("BULL", "NEUTRAL"):
                    continue

            action[i] = "BUY"
            in_pos = True
            high_since = h
            hold_days = 0

    return pd.DataFrame({"action": action}, index=df.index)


def generate_bb_extremes(df: pd.DataFrame, params: dict,
                          regime=None, chip_data=None) -> pd.DataFrame:
    """bb_extremes: Bollinger Band 極值反轉（range-bound 股票專用，5/9 新增）

    機制：
      BUY  ：close 接近 BB_lower（oversold）AND price > long_ma × 0.92（避免崩跌追刀）
      SELL ：close 回到 BB_middle（mean-revert 完成）OR 跌破 long_ma OR 持有超 max_hold

    限價單機制：
      target_buy = BB_lower × (1 + entry_buffer)  隔日掛限價買在 BB_lower 上方
      target_tp  = BB_middle                        隔日掛限價賣在中軌
      target_sl  = long_ma                          跌破長期均線 → 停損
    """
    close = df["close"]
    bb_period    = int(params["bb_period"])
    bb_std       = float(params["bb_std"])
    entry_buffer = float(params["entry_buffer"])
    long_ma_n    = int(params["long_ma"])
    max_hold     = int(params["max_hold_days"])

    bb = bollinger(close, bb_period, bb_std)
    bb_mid_s   = bb["mid"]
    bb_lower_s = bb["lower"]
    long_ma_s = sma(close, long_ma_n)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp  = [np.nan] * n
    target_sl  = [np.nan] * n

    in_pos = False
    hold_days = 0

    for i in range(n):
        c   = close.iloc[i]
        bbl = bb_lower_s.iloc[i]
        bbm = bb_mid_s.iloc[i]
        lma = long_ma_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(bbm):
                target_tp[i] = bbm
            if not np.isnan(lma):
                target_sl[i] = lma

            tp_hit = (not np.isnan(bbm)) and (c >= bbm)
            sl_hit = (not np.isnan(lma)) and (c < lma)
            timeout = hold_days >= max_hold

            if tp_hit or sl_hit or timeout:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if (not np.isnan(bbl) and not np.isnan(bbm) and not np.isnan(lma)
                and c < bbl * (1 + entry_buffer)
                and c > lma * 0.92):
                action[i] = "BUY"
                target_buy[i] = bbl * (1 + entry_buffer)
                in_pos = True
                hold_days = 0

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
    }, index=df.index)


def generate_narrow_range_breakout(df: pd.DataFrame, params: dict,
                                    regime=None, chip_data=None) -> pd.DataFrame:
    """narrow_range_breakout: NR-N 狹幅整理後高點突破 (5/9 新增)

    機制：
      identifier：T 日 H-L 是 N-day 中最小 → narrow range
      BUY：T+1 high break T's high AND price > trend_ma
      SELL：take_profit_pct 達標 OR ATR-based stop OR timeout

    限價單機制：
      target_buy = T_high (隔日掛 buy-stop)
      target_tp  = entry × (1 + take_profit_pct)
      target_sl  = T_low - ATR × atr_stop_k
    """
    high  = df["high"]
    low   = df["low"]
    close = df["close"]

    nr_window    = int(params["nr_window"])
    trend_n      = int(params["trend_ma"])
    atr_k        = float(params["atr_stop_k"])
    tp_pct       = float(params["take_profit_pct"])
    max_hold     = int(params["max_hold_days"])

    rng = (high - low)
    is_nr = rng == rng.rolling(nr_window).min()  # T 是窗內最小 range
    trend_ma_s = sma(close, trend_n)
    atr_s = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy      = [np.nan] * n
    target_tp       = [np.nan] * n
    target_sl       = [np.nan] * n
    target_buy_mode = [""] * n  # buy-stop mode for breakout

    in_pos = False
    hold_days = 0
    entry_price = np.nan
    nr_high = np.nan
    nr_low_atr = np.nan

    for i in range(n):
        c = close.iloc[i]
        h = high.iloc[i]
        l = low.iloc[i]
        tm = trend_ma_s.iloc[i]
        a = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            if not np.isnan(nr_low_atr):
                target_sl[i] = nr_low_atr

            tp_hit = (not np.isnan(target_tp[i])) and (c >= target_tp[i])
            sl_hit = (not np.isnan(nr_low_atr)) and (c < nr_low_atr)
            timeout = hold_days >= max_hold

            if tp_hit or sl_hit or timeout:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                entry_price = np.nan
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if (bool(is_nr.iloc[i]) and not np.isnan(tm) and c > tm
                and not np.isnan(a)):
                # T 是 NR-N → 隔日掛 buy-stop = T_high
                action[i] = "BUY"
                target_buy[i] = h
                target_buy_mode[i] = "stop"
                in_pos = True
                entry_price = h
                nr_high = h
                nr_low_atr = l - a * atr_k
                hold_days = 0

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
        "target_buy_mode": target_buy_mode,
    }, index=df.index)


def generate_golden_cross(df: pd.DataFrame, params: dict,
                           regime=None, chip_data=None) -> pd.DataFrame:
    """golden_cross: 快慢 MA 交叉 (5/9 新增)

    BUY  : fast MA crosses ABOVE slow MA AND price > trend_ma
    SELL : fast MA crosses BELOW slow MA OR take_profit OR atr stop OR timeout
    """
    close = df["close"]
    fast_n   = int(params["fast_n"])
    slow_n   = int(params["slow_n"])
    trend_n  = int(params["trend_ma"])
    tp_pct   = float(params["take_profit_pct"])
    atr_k    = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    if fast_n >= slow_n:
        return pd.DataFrame({"action": ["HOLD"] * len(df)}, index=df.index)

    fast_s   = sma(close, fast_n)
    slow_s   = sma(close, slow_n)
    trend_s  = sma(close, trend_n)
    atr_s    = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp  = [np.nan] * n
    target_sl  = [np.nan] * n

    in_pos = False
    hold_days = 0
    entry_price = np.nan
    sl_level = np.nan

    for i in range(1, n):
        c  = close.iloc[i]
        f0, f1 = fast_s.iloc[i-1], fast_s.iloc[i]
        s0, s1 = slow_s.iloc[i-1], slow_s.iloc[i]
        tm = trend_s.iloc[i]
        a  = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level

            tp_hit = (not np.isnan(target_tp[i])) and (c >= target_tp[i])
            sl_hit = (not np.isnan(sl_level)) and (c < sl_level)
            death_cross = (not np.isnan(f0) and not np.isnan(f1) and not np.isnan(s0) and not np.isnan(s1)
                            and f0 >= s0 and f1 < s1)
            timeout = hold_days >= max_hold

            if tp_hit or sl_hit or death_cross or timeout:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            golden = (not np.isnan(f0) and not np.isnan(f1) and not np.isnan(s0) and not np.isnan(s1)
                      and f0 <= s0 and f1 > s1)
            if golden and not np.isnan(tm) and c > tm and not np.isnan(a):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                sl_level = c - a * atr_k
                hold_days = 0

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
    }, index=df.index)


def generate_three_day_reversal(df: pd.DataFrame, params: dict,
                                 regime=None, chip_data=None) -> pd.DataFrame:
    """three_day_reversal: 連 N 日下跌且累計跌幅夠 → 反彈 (5/9 新增)"""
    close = df["close"]
    drop_days   = int(params["drop_days"])
    min_drop    = float(params["min_drop_pct"])
    trend_n     = int(params["trend_ma"])
    tp_pct      = float(params["take_profit_pct"])
    atr_k       = float(params["atr_stop_k"])
    max_hold    = int(params["max_hold_days"])

    trend_s = sma(close, trend_n)
    atr_s   = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n

    in_pos = False
    hold_days = 0
    entry_price = np.nan
    sl_level = np.nan

    for i in range(drop_days, n):
        c = close.iloc[i]
        tm = trend_s.iloc[i]
        a = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and (c >= target_tp[i])
            sl_hit = (not np.isnan(sl_level)) and (c < sl_level)
            timeout = hold_days >= max_hold
            if tp_hit or sl_hit or timeout:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            # 檢查連 drop_days 個下跌天 + 累計跌幅
            window_start = i - drop_days
            window_close_chain = close.iloc[window_start:i+1].values
            all_down = all(window_close_chain[k+1] < window_close_chain[k]
                            for k in range(len(window_close_chain)-1))
            cum_drop = (window_close_chain[0] - window_close_chain[-1]) / window_close_chain[0] if window_close_chain[0] > 0 else 0
            in_uptrend = (not np.isnan(tm)) and c > tm * 0.95
            if all_down and cum_drop >= min_drop and in_uptrend and not np.isnan(a):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                sl_level = c - a * atr_k
                hold_days = 0

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
    }, index=df.index)


def generate_rsi_oversold_volume(df: pd.DataFrame, params: dict,
                                   regime=None, chip_data=None) -> pd.DataFrame:
    """rsi_oversold_volume: RSI 極端 + 量能放大進場 (5/9 新增)"""
    close = df["close"]
    volume = df["volume"]
    rsi_period   = int(params["rsi_period"])
    rsi_thresh   = int(params["rsi_threshold"])
    vol_ratio    = float(params["volume_ratio"])
    vol_period   = int(params["volume_period"])
    trend_n      = int(params["trend_ma"])
    tp_pct       = float(params["take_profit_pct"])
    max_hold     = int(params["max_hold_days"])

    rsi_s   = rsi(close, rsi_period)
    vol_avg = volume.rolling(vol_period).mean()
    trend_s = sma(close, trend_n)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n

    in_pos = False
    hold_days = 0
    entry_price = np.nan

    for i in range(n):
        c = close.iloc[i]
        r = rsi_s.iloc[i]
        v = volume.iloc[i]
        va = vol_avg.iloc[i]
        tm = trend_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            if not np.isnan(tm):
                target_sl[i] = tm * 0.95
            tp_hit = (not np.isnan(target_tp[i])) and (c >= target_tp[i])
            sl_hit = (not np.isnan(target_sl[i])) and (c < target_sl[i])
            timeout = hold_days >= max_hold
            if tp_hit or sl_hit or timeout:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if (not np.isnan(r) and r < rsi_thresh and
                not np.isnan(va) and va > 0 and v / va >= vol_ratio and
                not np.isnan(tm) and c > tm * 0.85):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                hold_days = 0

    return pd.DataFrame({
        "action": action,
        "target_buy": target_buy,
        "target_tp": target_tp,
        "target_sl": target_sl,
    }, index=df.index)


def generate_support_bounce(df: pd.DataFrame, params: dict,
                              regime=None, chip_data=None) -> pd.DataFrame:
    """support_bounce: N 天內歷史最低點附近反彈 (5/9 新增)"""
    close = df["close"]; low = df["low"]
    lookback   = int(params["lookback"])
    buf        = float(params["support_buffer"])
    trend_n    = int(params["trend_ma"])
    tp_pct     = float(params["take_profit_pct"])
    atr_k      = float(params["atr_stop_k"])
    max_hold   = int(params["max_hold_days"])

    rolling_low = low.rolling(lookback).min()
    trend_s = sma(close, trend_n)
    atr_s = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp  = [np.nan] * n
    target_sl  = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan

    for i in range(n):
        c = close.iloc[i]; l = low.iloc[i]; rl = rolling_low.iloc[i]
        tm = trend_s.iloc[i]; a = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and (c >= target_tp[i])
            sl_hit = (not np.isnan(sl_level)) and (c < sl_level)
            timeout = hold_days >= max_hold
            if tp_hit or sl_hit or timeout:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            if (not np.isnan(rl) and rl > 0
                and l <= rl * (1 + buf)
                and not np.isnan(tm) and c > tm * 0.85
                and not np.isnan(a)):
                action[i] = "BUY"
                target_buy[i] = rl * (1 + buf)
                in_pos = True; entry_price = c
                sl_level = rl - a * atr_k
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_cci_extremes(df: pd.DataFrame, params: dict,
                           regime=None, chip_data=None) -> pd.DataFrame:
    """cci_extremes: CCI 極值反轉 (5/9 新增)"""
    high  = df["high"]; low = df["low"]; close = df["close"]
    cci_period = int(params["cci_period"])
    cci_os     = int(params["cci_oversold"])
    cci_ob     = int(params["cci_overbought"])
    trend_n    = int(params["trend_ma"])
    tp_pct     = float(params["take_profit_pct"])
    max_hold   = int(params["max_hold_days"])

    tp = (high + low + close) / 3
    ma_tp = tp.rolling(cci_period).mean()
    md = (tp - ma_tp).abs().rolling(cci_period).mean()
    cci = (tp - ma_tp) / (0.015 * md.replace(0, np.nan))
    trend_s = sma(close, trend_n)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan

    for i in range(n):
        c = close.iloc[i]; cc = cci.iloc[i]; tm = trend_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            if not np.isnan(tm):
                target_sl[i] = tm * 0.92
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(target_sl[i])) and c < target_sl[i]
            cci_overbought = (not np.isnan(cc)) and cc > cci_ob
            timeout = hold_days >= max_hold
            if tp_hit or sl_hit or cci_overbought or timeout:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            if (not np.isnan(cc) and cc < cci_os and
                not np.isnan(tm) and c > tm * 0.85):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_hammer_revert(df: pd.DataFrame, params: dict,
                            regime=None, chip_data=None) -> pd.DataFrame:
    """hammer_revert: hammer/長下影線 candle 反轉 (5/9 新增)"""
    open_  = df["open"]; high = df["high"]; low = df["low"]; close = df["close"]
    trend_n      = int(params["trend_ma"])
    shadow_ratio = float(params["shadow_ratio"])
    min_drop     = float(params["min_drop_pct"])
    tp_pct       = float(params["take_profit_pct"])
    atr_k        = float(params["atr_stop_k"])
    max_hold     = int(params["max_hold_days"])

    trend_s = sma(close, trend_n)
    atr_s   = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan

    for i in range(1, n):
        o = open_.iloc[i]; h = high.iloc[i]; l = low.iloc[i]; c = close.iloc[i]
        prev_c = close.iloc[i-1]
        body = abs(c - o)
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)
        tm = trend_s.iloc[i]; a = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            timeout = hold_days >= max_hold
            if tp_hit or sl_hit or timeout:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            is_hammer = (body > 0 and lower_shadow > body * shadow_ratio
                          and upper_shadow < body * 0.5
                          and prev_c > 0 and (prev_c - l) / prev_c >= min_drop)
            in_uptrend = (not np.isnan(tm)) and c > tm * 0.92
            if is_hammer and in_uptrend and not np.isnan(a):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c
                sl_level = l - a * atr_k * 0.5
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_macd_cross(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """MACD line cross above signal line"""
    close = df["close"]
    fast_n   = int(params["fast_n"])
    slow_n   = int(params["slow_n"])
    signal_n = int(params["signal_n"])
    trend_n  = int(params["trend_ma"])
    tp_pct   = float(params["take_profit_pct"])
    atr_k    = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    if fast_n >= slow_n:
        return pd.DataFrame({"action": ["HOLD"] * len(df)}, index=df.index)

    ema_fast = close.ewm(span=fast_n, adjust=False).mean()
    ema_slow = close.ewm(span=slow_n, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal_n, adjust=False).mean()
    trend_s = sma(close, trend_n)
    atr_s = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan

    for i in range(1, n):
        c = close.iloc[i]
        m0, m1 = macd.iloc[i-1], macd.iloc[i]
        s0, s1 = signal_line.iloc[i-1], signal_line.iloc[i]
        tm = trend_s.iloc[i]; a = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            death = (not np.isnan(m0) and not np.isnan(m1) and not np.isnan(s0) and not np.isnan(s1)
                     and m0 >= s0 and m1 < s1)
            if tp_hit or sl_hit or death or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            golden = (not np.isnan(m0) and not np.isnan(m1) and not np.isnan(s0) and not np.isnan(s1)
                      and m0 <= s0 and m1 > s1)
            if golden and not np.isnan(tm) and c > tm and not np.isnan(a):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c
                sl_level = c - a * atr_k; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_kd_oversold_cross(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """KD oversold + %K crossing above %D"""
    high = df["high"]; low = df["low"]; close = df["close"]
    k_period   = int(params["k_period"])
    k_os       = int(params["k_oversold"])
    k_ob       = int(params["k_overbought"])
    trend_n    = int(params["trend_ma"])
    tp_pct     = float(params["take_profit_pct"])
    max_hold   = int(params["max_hold_days"])

    ll = low.rolling(k_period).min()
    hh = high.rolling(k_period).max()
    k = 100 * (close - ll) / (hh - ll).replace(0, np.nan)
    d = k.rolling(3).mean()
    trend_s = sma(close, trend_n)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan

    for i in range(1, n):
        c = close.iloc[i]
        k0, k1 = k.iloc[i-1], k.iloc[i]
        d0, d1 = d.iloc[i-1], d.iloc[i]
        tm = trend_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            if not np.isnan(tm):
                target_sl[i] = tm * 0.92
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(target_sl[i])) and c < target_sl[i]
            kd_overbought = (not np.isnan(k1)) and k1 > k_ob
            if tp_hit or sl_hit or kd_overbought or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            kd_oversold_cross = (not np.isnan(k0) and not np.isnan(k1) and not np.isnan(d0) and not np.isnan(d1)
                                  and k1 < k_os + 10 and k0 <= d0 and k1 > d1)
            if kd_oversold_cross and not np.isnan(tm) and c > tm * 0.85:
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_adx_trending_pullback(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """ADX > threshold + pullback to short MA + bounce"""
    high = df["high"]; low = df["low"]; close = df["close"]
    adx_p     = int(params["adx_period"])
    adx_th    = int(params["adx_threshold"])
    pb_pct    = float(params["pullback_pct"])
    trend_n   = int(params["trend_ma"])
    tp_pct    = float(params["take_profit_pct"])
    atr_k     = float(params["atr_stop_k"])
    max_hold  = int(params["max_hold_days"])

    # Simple ADX approx via ATR & directional movement
    plus_dm = (high - high.shift()).where(lambda x: x > 0, 0)
    minus_dm = (low.shift() - low).where(lambda x: x > 0, 0)
    tr = pd.concat([(high - low).abs(),
                    (high - close.shift()).abs(),
                    (low - close.shift()).abs()], axis=1).max(axis=1)
    atr_x = tr.ewm(span=adx_p, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(span=adx_p, adjust=False).mean() / atr_x.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(span=adx_p, adjust=False).mean() / atr_x.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_s = dx.ewm(span=adx_p, adjust=False).mean()

    short_ma_s = sma(close, 10)
    trend_s = sma(close, trend_n)
    atr_s = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan

    for i in range(n):
        c = close.iloc[i]
        ax = adx_s.iloc[i]
        sm = short_ma_s.iloc[i]
        tm = trend_s.iloc[i]
        a = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            if (not np.isnan(ax) and ax > adx_th
                and not np.isnan(sm) and c < sm * (1 - pb_pct)
                and not np.isnan(tm) and c > tm
                and not np.isnan(a)):
                action[i] = "BUY"
                target_buy[i] = sm * (1 - pb_pct)
                in_pos = True; entry_price = c
                sl_level = c - a * atr_k; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_vwap_revert(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """VWAP-like (volume-weighted MA) deviation revert"""
    close = df["close"]; volume = df["volume"]
    vwap_p     = int(params["vwap_period"])
    dev_pct    = float(params["deviation_pct"])
    trend_n    = int(params["trend_ma"])
    tp_pct     = float(params["take_profit_pct"])
    max_hold   = int(params["max_hold_days"])

    pv = close * volume
    vwap = pv.rolling(vwap_p).sum() / volume.rolling(vwap_p).sum().replace(0, np.nan)
    trend_s = sma(close, trend_n)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan

    for i in range(n):
        c = close.iloc[i]; vw = vwap.iloc[i]; tm = trend_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            if not np.isnan(tm):
                target_sl[i] = tm * 0.92
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(target_sl[i])) and c < target_sl[i]
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            if (not np.isnan(vw) and c < vw * (1 - dev_pct)
                and not np.isnan(tm) and c > tm * 0.88):
                action[i] = "BUY"; target_buy[i] = vw * (1 - dev_pct)
                in_pos = True; entry_price = c; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_yearly_high_break(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """52-week high breakout"""
    high = df["high"]; close = df["close"]
    lookback = int(params["lookback"])
    buf      = float(params["break_buffer"])
    trend_n  = int(params["trend_ma"])
    tp_pct   = float(params["take_profit_pct"])
    atr_k    = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    rolling_high = high.shift(1).rolling(lookback).max()
    trend_s = sma(close, trend_n)
    atr_s = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    target_buy_mode = [""] * n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan

    for i in range(n):
        c = close.iloc[i]; h = high.iloc[i]; rh = rolling_high.iloc[i]
        tm = trend_s.iloc[i]; a = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            if (not np.isnan(rh) and rh > 0
                and h >= rh * (1 + buf)
                and not np.isnan(tm) and c > tm
                and not np.isnan(a)):
                action[i] = "BUY"
                target_buy[i] = rh * (1 + buf)
                target_buy_mode[i] = "stop"
                in_pos = True; entry_price = h
                sl_level = c - a * atr_k; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl,
                          "target_buy_mode": target_buy_mode}, index=df.index)


def generate_keltner_breakout(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Keltner channel breakout"""
    close = df["close"]
    kc_p     = int(params["kc_period"])
    kc_mult  = float(params["kc_multiplier"])
    trend_n  = int(params["trend_ma"])
    tp_pct   = float(params["take_profit_pct"])
    atr_k    = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    mid = close.ewm(span=kc_p, adjust=False).mean()
    atr_s = atr(df, kc_p)
    upper = mid + kc_mult * atr_s
    lower = mid - kc_mult * atr_s
    trend_s = sma(close, trend_n)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    target_buy_mode = [""] * n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan

    for i in range(1, n):
        c0, c1 = close.iloc[i-1], close.iloc[i]
        u0, u1 = upper.iloc[i-1], upper.iloc[i]
        m1 = mid.iloc[i]
        tm = trend_s.iloc[i]
        a = atr_s.iloc[i]

        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c1 >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c1 < sl_level
            below_mid = (not np.isnan(m1)) and c1 < m1
            if tp_hit or sl_hit or below_mid or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            # break above upper
            break_up = (not np.isnan(c0) and not np.isnan(u0) and not np.isnan(c1) and not np.isnan(u1)
                         and c0 <= u0 and c1 > u1)
            if (break_up and not np.isnan(tm) and c1 > tm and not np.isnan(a)):
                action[i] = "BUY"
                target_buy[i] = u1
                target_buy_mode[i] = "stop"
                in_pos = True; entry_price = c1
                sl_level = c1 - a * atr_k; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl,
                          "target_buy_mode": target_buy_mode}, index=df.index)


def generate_mfi_oversold(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Money Flow Index oversold reversal"""
    high = df["high"]; low = df["low"]; close = df["close"]; volume = df["volume"]
    period   = int(params["mfi_period"])
    threshold = int(params["mfi_threshold"])
    trend_n  = int(params["trend_ma"])
    tp_pct   = float(params["take_profit_pct"])
    max_hold = int(params["max_hold_days"])

    tp = (high + low + close) / 3
    raw_money = tp * volume
    pos_flow = raw_money.where(tp > tp.shift(), 0)
    neg_flow = raw_money.where(tp < tp.shift(), 0)
    pos_sum = pos_flow.rolling(period).sum()
    neg_sum = neg_flow.rolling(period).sum().replace(0, np.nan)
    mfi = 100 - (100 / (1 + pos_sum / neg_sum))
    trend_s = sma(close, trend_n)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan

    for i in range(n):
        c = close.iloc[i]; m = mfi.iloc[i]; tm = trend_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            if not np.isnan(tm):
                target_sl[i] = tm * 0.92
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(target_sl[i])) and c < target_sl[i]
            mfi_overbought = (not np.isnan(m)) and m > 70
            if tp_hit or sl_hit or mfi_overbought or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            if (not np.isnan(m) and m < threshold and
                not np.isnan(tm) and c > tm * 0.85):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_roc_reversal(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Rate of Change extreme reversal"""
    close = df["close"]
    roc_p     = int(params["roc_period"])
    roc_th    = float(params["roc_threshold"])
    trend_n   = int(params["trend_ma"])
    tp_pct    = float(params["take_profit_pct"])
    atr_k     = float(params["atr_stop_k"])
    max_hold  = int(params["max_hold_days"])

    roc = (close - close.shift(roc_p)) / close.shift(roc_p)
    trend_s = sma(close, trend_n)
    atr_s = atr(df, 14)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan

    for i in range(n):
        c = close.iloc[i]; r = roc.iloc[i]; tm = trend_s.iloc[i]; a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            if (not np.isnan(r) and r < roc_th
                and not np.isnan(tm) and c > tm * 0.80
                and not np.isnan(a)):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c
                sl_level = c - a * atr_k; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_williams_r_extreme(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Williams %R extreme reversal"""
    high = df["high"]; low = df["low"]; close = df["close"]
    period   = int(params["wr_period"])
    wr_os    = int(params["wr_oversold"])
    wr_ob    = int(params["wr_overbought"])
    trend_n  = int(params["trend_ma"])
    tp_pct   = float(params["take_profit_pct"])
    max_hold = int(params["max_hold_days"])

    hh = high.rolling(period).max()
    ll = low.rolling(period).min()
    wr = -100 * (hh - close) / (hh - ll).replace(0, np.nan)
    trend_s = sma(close, trend_n)

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False; hold_days = 0; entry_price = np.nan

    for i in range(n):
        c = close.iloc[i]; w = wr.iloc[i]; tm = trend_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            if not np.isnan(tm):
                target_sl[i] = tm * 0.92
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(target_sl[i])) and c < target_sl[i]
            wr_overbought = (not np.isnan(w)) and w > wr_ob
            if tp_hit or sl_hit or wr_overbought or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            if (not np.isnan(w) and w < wr_os
                and not np.isnan(tm) and c > tm * 0.85):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ema_cross(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """EMA cross (similar to golden_cross but using EMA)"""
    close = df["close"]
    fast_n = int(params["fast_n"]); slow_n = int(params["slow_n"])
    trend_n = int(params["trend_ma"])
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])
    if fast_n >= slow_n:
        return pd.DataFrame({"action": ["HOLD"] * len(df)}, index=df.index)
    fast_s = close.ewm(span=fast_n, adjust=False).mean()
    slow_s = close.ewm(span=slow_n, adjust=False).mean()
    trend_s = sma(close, trend_n)
    atr_s = atr(df, 14)
    n = len(df)
    action = ["HOLD"] * n; target_buy = [np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan
    for i in range(1, n):
        c = close.iloc[i]
        f0, f1 = fast_s.iloc[i-1], fast_s.iloc[i]
        s0, s1 = slow_s.iloc[i-1], slow_s.iloc[i]
        tm = trend_s.iloc[i]; a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            death = (not np.isnan(f0) and not np.isnan(s0) and f0 >= s0 and f1 < s1)
            if tp_hit or sl_hit or death or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            golden = (not np.isnan(f0) and not np.isnan(s0) and f0 <= s0 and f1 > s1)
            if golden and not np.isnan(tm) and c > tm and not np.isnan(a):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c; sl_level = c - a * atr_k; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_gap_down_revert(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Gap-down + intraday reversal"""
    open_ = df["open"]; close = df["close"]
    gap_pct = float(params["gap_pct"])
    req_up = bool(params["require_close_up"])
    trend_n = int(params["trend_ma"])
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])
    trend_s = sma(close, trend_n)
    atr_s = atr(df, 14)
    n = len(df)
    action = ["HOLD"] * n; target_buy = [np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan
    for i in range(1, n):
        prev_c = close.iloc[i-1]; o = open_.iloc[i]; c = close.iloc[i]
        tm = trend_s.iloc[i]; a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            gap_down = prev_c > 0 and (prev_c - o) / prev_c >= gap_pct
            close_up = c > o
            cond = gap_down and (close_up if req_up else True)
            if cond and not np.isnan(tm) and c > tm * 0.85 and not np.isnan(a):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c
                sl_level = o - a * atr_k * 0.5; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_trend_confirm_hold(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Trend confirmation hold: fast_ma > slow_ma + price > fast_ma → long hold"""
    close=df["close"]
    fast_p=int(params["fast_ma"]); slow_p=int(params["slow_ma"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    if fast_p >= slow_p:
        return pd.DataFrame({"action": ["HOLD"]*len(df)}, index=df.index)
    fast_s=sma(close,fast_p); slow_s=sma(close,slow_p)
    atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(1,n):
        c=close.iloc[i]; f=fast_s.iloc[i]; s=slow_s.iloc[i]
        f0=fast_s.iloc[i-1]; s0=slow_s.iloc[i-1]
        a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            trend_break = (not np.isnan(f) and not np.isnan(s) and f<s)
            if tp_hit or sl_hit or trend_break or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            cross_up = (not np.isnan(f0) and not np.isnan(s0) and not np.isnan(f) and not np.isnan(s)
                        and f0<=s0 and f>s)
            confirm = (not np.isnan(f) and c>f)
            if cross_up and confirm and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_low_volume_reversal(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Low volume reversal: 量縮 + 反彈"""
    close=df["close"]; volume=df["volume"]
    vol_p=int(params["vol_period"])
    vol_ratio=float(params["vol_low_ratio"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    vol_avg=volume.rolling(vol_p).mean()
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(2,n):
        c=close.iloc[i]; v=volume.iloc[i]; va=vol_avg.iloc[i]
        c0=close.iloc[i-1]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            low_vol = (not np.isnan(va) and va>0 and v/va<vol_ratio)
            green_close = c > c0
            if low_vol and green_close and not np.isnan(tm) and c>tm*0.85 and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_deep_dip_long_hold(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Deep drawdown then long hold"""
    close=df["close"]
    lookback=int(params["lookback"])
    dd_pct=float(params["drawdown_pct"])
    tp_pct=float(params["take_profit_pct"])
    max_hold=int(params["max_hold_days"])
    rolling_max = close.rolling(lookback).max()
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan
    for i in range(n):
        c=close.iloc[i]; rm=rolling_max.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            if tp_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan
        else:
            if not np.isnan(rm) and rm>0 and (rm-c)/rm>=dd_pct:
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_weekly_low_buy(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Buy at weekly low (lookback N weeks)"""
    close=df["close"]; low=df["low"]
    weeks=int(params["lookback_weeks"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"])
    max_hold=int(params["max_hold_days"])
    rolling_low = low.rolling(weeks*5).min()
    trend_s=sma(close,trend_n)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan
    for i in range(n):
        c=close.iloc[i]; l=low.iloc[i]; rl=rolling_low.iloc[i]; tm=trend_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            if not np.isnan(tm): target_sl[i]=tm*0.92
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(target_sl[i])) and c<target_sl[i]
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            if not np.isnan(rl) and l<=rl*1.005 and not np.isnan(tm) and c>tm*0.85:
                action[i]="BUY"; target_buy[i]=rl
                in_pos=True; entry_price=c; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_simple_dip_buy(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Simple dip buy: price < MA × (1-dip_pct) → buy → hold N days"""
    close=df["close"]
    ma_p=int(params["ma_period"]); dip=float(params["dip_pct"])
    tp_pct=float(params["take_profit_pct"]); max_hold=int(params["max_hold_days"])
    ma=sma(close,ma_p)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan
    for i in range(n):
        c=close.iloc[i]; m=ma.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            if tp_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan
        else:
            if not np.isnan(m) and c<m*(1-dip):
                action[i]="BUY"; target_buy[i]=m*(1-dip)
                in_pos=True; entry_price=c; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_monthly_anchor(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """月初前 N 個交易日買入"""
    close=df["close"]
    md=int(params["month_day"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"])
    max_hold=int(params["max_hold_days"])
    trend_s=sma(close,trend_n)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan
    prev_month=-1
    day_of_month_count=0
    for i in range(n):
        c=close.iloc[i]; tm=trend_s.iloc[i]
        cur_month = df.index[i].month
        if cur_month != prev_month:
            day_of_month_count = 1
            prev_month = cur_month
        else:
            day_of_month_count += 1
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            if not np.isnan(tm): target_sl[i]=tm*0.95
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(target_sl[i])) and c<target_sl[i]
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            if day_of_month_count == md and not np.isnan(tm) and c>tm*0.85:
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_pivot_break(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Daily pivot break (classic floor pivots)"""
    high=df["high"]; low=df["low"]; close=df["close"]
    p=int(params["pivot_lookback"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    # Recent N-day pivot = avg of last N day's H+L+C
    hlc = (high+low+close)/3
    pivot = hlc.rolling(p).mean().shift(1)
    r1 = (2*pivot - low.shift(1)).rolling(p).mean()
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    target_buy_mode=[""]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(p+1,n):
        c=close.iloc[i]; c0=close.iloc[i-1]
        r1v=r1.iloc[i]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            br = (not np.isnan(r1v) and c>r1v and c0<=r1v)
            if br and not np.isnan(tm) and c>tm*0.85 and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=r1v; target_buy_mode[i]="stop"
                in_pos=True; entry_price=c
                sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl,
                          "target_buy_mode":target_buy_mode}, index=df.index)


def generate_short_momentum(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Short-term momentum trigger"""
    close=df["close"]
    p=int(params["ret_period"])
    min_r=float(params["min_return"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    ret = close.pct_change(p)
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(n):
        c=close.iloc[i]; r=ret.iloc[i]; tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            if not np.isnan(r) and r>=min_r and not np.isnan(tm) and c>tm and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_double_volume(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """2 連續放量"""
    close=df["close"]; volume=df["volume"]; open_=df["open"]
    vol_p=int(params["vol_period"])
    ratio=float(params["vol_ratio"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    vol_avg=volume.rolling(vol_p).mean()
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(2,n):
        c=close.iloc[i]
        v1=volume.iloc[i-1]; v0=volume.iloc[i-2]; va=vol_avg.iloc[i-2]
        c1=close.iloc[i-1]; o1=open_.iloc[i-1]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            double_vol = (not np.isnan(va) and va>0 and v0/va>=ratio and v1/va>=ratio)
            prev_green = c1>o1
            if double_vol and prev_green and not np.isnan(tm) and c>tm and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_failed_breakdown(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """跌破 N 日低後當日收回 (failed breakdown)"""
    high=df["high"]; low=df["low"]; close=df["close"]
    lookback=int(params["lookback"])
    trend_n=int(params["trend_ma"])
    atr_k=float(params["atr_stop_k"])
    tp_pct=float(params["take_profit_pct"]); max_hold=int(params["max_hold_days"])
    rolling_low=low.shift(1).rolling(lookback).min()
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(n):
        c=close.iloc[i]; l=low.iloc[i]; rl=rolling_low.iloc[i]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            # 當日 low 跌破 rolling_low 但 close 收回
            broke = (not np.isnan(rl) and l<rl and c>rl)
            if broke and not np.isnan(tm) and c>tm*0.85 and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=l-a*atr_k*0.5; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_volume_spike_reverse(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """大量黑K後反彈"""
    open_=df["open"]; close=df["close"]; volume=df["volume"]
    vol_p=int(params["vol_period"]); ratio=float(params["vol_ratio"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    vol_avg=volume.rolling(vol_p).mean()
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(1,n):
        c=close.iloc[i]; o=open_.iloc[i]
        c0=close.iloc[i-1]; v0=volume.iloc[i-1]; va=vol_avg.iloc[i-1]
        o0=open_.iloc[i-1]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            prev_high_vol = (not np.isnan(va) and va>0 and v0/va>=ratio)
            prev_red = c0<o0
            today_green = c>o
            if prev_high_vol and prev_red and today_green and not np.isnan(tm) and c>tm*0.80 and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_obv_uptrend(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """OBV 上升 N 日 (累積買盤)"""
    close=df["close"]; volume=df["volume"]
    obv_p=int(params["obv_period"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    # OBV
    direction = np.sign(close.diff().fillna(0))
    obv = (direction * volume).cumsum()
    obv_ma = obv.rolling(obv_p).mean()
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(obv_p+1,n):
        c=close.iloc[i]
        obv0=obv.iloc[i-1]; obv1=obv.iloc[i]
        oma=obv_ma.iloc[i]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            obv_up = obv1>obv0 and not np.isnan(oma) and obv1>oma
            if obv_up and not np.isnan(tm) and c>tm and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_inside_day_breakout(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Inside day (HL 在 T-1 HL 內) + T+1 高點突破"""
    high=df["high"]; low=df["low"]; close=df["close"]
    trend_n=int(params["trend_ma"])
    atr_k=float(params["atr_stop_k"])
    tp_pct=float(params["take_profit_pct"]); max_hold=int(params["max_hold_days"])
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    target_buy_mode=[""]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(1,n):
        c=close.iloc[i]; h=high.iloc[i]; l=low.iloc[i]
        h0=high.iloc[i-1]; l0=low.iloc[i-1]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            inside = (h<h0 and l>l0)
            if inside and not np.isnan(tm) and c>tm and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=h0; target_buy_mode[i]="stop"
                in_pos=True; entry_price=h0
                sl_level=l-a*atr_k*0.5; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl,
                          "target_buy_mode":target_buy_mode}, index=df.index)


def generate_three_white_soldiers(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """3 連紅 K + oversold context"""
    open_=df["open"]; close=df["close"]
    trend_n=int(params["trend_ma"])
    min_drop=float(params["min_drop_pct"])
    rsi_p=int(params["rsi_period"]); rsi_th=int(params["rsi_threshold"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    trend_s=sma(close,trend_n)
    rsi_s=rsi(close,rsi_p)
    atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(4,n):
        c=close.iloc[i]; tm=trend_s.iloc[i]; r=rsi_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            # 3 連紅
            c0,c1,c2=close.iloc[i-3],close.iloc[i-2],close.iloc[i-1]
            o0,o1,o2=open_.iloc[i-3],open_.iloc[i-2],open_.iloc[i-1]
            three_green = (c0>o0 and c1>o1 and c2>o2 and c1>c0 and c2>c1)
            # 之前 oversold 跌幅
            past_high = close.iloc[max(0,i-10):i-3].max()
            recent_low = close.iloc[i-3]
            drop = (past_high - recent_low)/past_high if past_high>0 else 0
            cond_drop = drop >= min_drop
            cond_rsi = (not np.isnan(r)) and r < rsi_th
            if three_green and cond_drop and cond_rsi and not np.isnan(tm) and c>tm*0.85 and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_outside_day_engulf(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Bullish engulfing pattern"""
    open_=df["open"]; close=df["close"]
    trend_n=int(params["trend_ma"])
    min_drop=float(params["min_prev_drop"])
    tp_pct=float(params["take_profit_pct"])
    atr_k=float(params["atr_stop_k"]); max_hold=int(params["max_hold_days"])
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(2,n):
        c=close.iloc[i]; o=open_.iloc[i]
        c0=close.iloc[i-1]; o0=open_.iloc[i-1]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            prev_red = c0 < o0
            engulf = (c > o and o < c0 and c > o0)
            prev_drop = (o0 - c0)/o0 if o0>0 else 0
            if prev_red and engulf and prev_drop >= min_drop and not np.isnan(tm) and c>tm*0.85 and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c
                sl_level=o-a*atr_k*0.5; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_linreg_slope_revert(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Buy when LR slope strongly negative (oversold extrema)"""
    close=df["close"]
    p=int(params["lr_period"]); thr=float(params["slope_threshold"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"]); max_hold=int(params["max_hold_days"])
    def lr_slope(s, n):
        x = np.arange(n)
        return s.rolling(n).apply(lambda y: np.polyfit(x, y, 1)[0] / np.mean(y) if np.mean(y) > 0 else 0, raw=True)
    slope = lr_slope(close, p)
    trend_s=sma(close,trend_n)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan
    for i in range(n):
        c=close.iloc[i]; sl=slope.iloc[i]; tm=trend_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            if not np.isnan(tm): target_sl[i]=tm*0.92
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(target_sl[i])) and c<target_sl[i]
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            if not np.isnan(sl) and sl<thr and not np.isnan(tm) and c>tm*0.85:
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_coppock_buy(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Coppock curve crosses 0"""
    close=df["close"]
    r1=int(params["roc1_n"]); r2=int(params["roc2_n"]); wma_n=int(params["wma_n"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"]); max_hold=int(params["max_hold_days"])
    roc1 = 100*(close.pct_change(r1))
    roc2 = 100*(close.pct_change(r2))
    s = roc1 + roc2
    # weighted MA
    w = pd.Series(range(1,wma_n+1))
    coppock = s.rolling(wma_n).apply(lambda x: (x*w).sum()/w.sum(), raw=True)
    trend_s=sma(close,trend_n)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan
    for i in range(1,n):
        c=close.iloc[i]; tm=trend_s.iloc[i]
        cp0,cp1=coppock.iloc[i-1],coppock.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            if not np.isnan(tm): target_sl[i]=tm*0.90
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(target_sl[i])) and c<target_sl[i]
            cross_down=(not np.isnan(cp0) and not np.isnan(cp1) and cp0>=0 and cp1<0)
            if tp_hit or sl_hit or cross_down or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            cross_up=(not np.isnan(cp0) and not np.isnan(cp1) and cp0<0 and cp1>=0)
            if cross_up and not np.isnan(tm) and c>tm*0.85:
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_ultimate_oscillator(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Ultimate Oscillator oversold"""
    high=df["high"]; low=df["low"]; close=df["close"]
    sn=int(params["uo_short"]); mn=int(params["uo_mid"]); ln=int(params["uo_long"])
    os_th=int(params["uo_oversold"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"]); max_hold=int(params["max_hold_days"])
    prev_close=close.shift()
    true_low = pd.concat([low, prev_close], axis=1).min(axis=1)
    true_range = pd.concat([(high-low).abs(), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    bp = close - true_low
    avg_s = bp.rolling(sn).sum() / true_range.rolling(sn).sum().replace(0, np.nan)
    avg_m = bp.rolling(mn).sum() / true_range.rolling(mn).sum().replace(0, np.nan)
    avg_l = bp.rolling(ln).sum() / true_range.rolling(ln).sum().replace(0, np.nan)
    uo = 100 * (4*avg_s + 2*avg_m + avg_l) / 7
    trend_s=sma(close,trend_n)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan
    for i in range(n):
        c=close.iloc[i]; u=uo.iloc[i]; tm=trend_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            if not np.isnan(tm): target_sl[i]=tm*0.92
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(target_sl[i])) and c<target_sl[i]
            uo_overbought=(not np.isnan(u)) and u>65
            if tp_hit or sl_hit or uo_overbought or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            if not np.isnan(u) and u<os_th and not np.isnan(tm) and c>tm*0.85:
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_yearly_low_revert(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """52-week low counter-trend bounce"""
    close = df["close"]; low = df["low"]
    lookback = int(params["lookback"]); buf = float(params["low_buffer"])
    trend_n = int(params["trend_ma"])
    tp_pct = float(params["take_profit_pct"]); atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])
    rolling_low = low.shift(1).rolling(lookback).min()
    trend_s = sma(close, trend_n); atr_s = atr(df, 14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(n):
        c=close.iloc[i]; l=low.iloc[i]; rl=rolling_low.iloc[i]
        tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            if (not np.isnan(rl) and rl>0 and l<=rl*(1+buf)
                and not np.isnan(a)):
                action[i]="BUY"; target_buy[i]=rl*(1+buf)
                in_pos=True; entry_price=c; sl_level=rl-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_atr_band_breakout(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """ATR band breakout"""
    close=df["close"]
    ma_p=int(params["ma_period"]); atr_p=int(params["atr_period"])
    mult=float(params["atr_mult"])
    trend_n=int(params["trend_ma"])
    tp_pct=float(params["take_profit_pct"]); max_hold=int(params["max_hold_days"])
    ma=sma(close,ma_p); atr_s=atr(df,atr_p)
    upper=ma+mult*atr_s; lower=ma-mult*atr_s
    trend_s=sma(close,trend_n)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    target_buy_mode=[""]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(1,n):
        c=close.iloc[i]; c0=close.iloc[i-1]
        u0,u1=upper.iloc[i-1],upper.iloc[i]
        m1=ma.iloc[i]; tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            below_mid=(not np.isnan(m1)) and c<m1
            if tp_hit or sl_hit or below_mid or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            br_up=(not np.isnan(c0) and not np.isnan(u0) and not np.isnan(u1)
                    and c0<=u0 and c>u1)
            if br_up and not np.isnan(tm) and c>tm and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=u1; target_buy_mode[i]="stop"
                in_pos=True; entry_price=c; sl_level=c-a*1.5; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl,
                          "target_buy_mode":target_buy_mode}, index=df.index)


def generate_double_pullback(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """2 successive pullbacks within window then bounce"""
    high=df["high"]; close=df["close"]
    trend_n=int(params["trend_ma"])
    pb_window=int(params["pullback_window"])
    min_pb=float(params["min_pullback_pct"])
    tp_pct=float(params["take_profit_pct"]); atr_k=float(params["atr_stop_k"])
    max_hold=int(params["max_hold_days"])
    trend_s=sma(close,trend_n); atr_s=atr(df,14)
    n=len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(pb_window*2, n):
        c=close.iloc[i]; tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days+=1
            if not np.isnan(entry_price): target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            # 找最近 pb_window×2 內的 2 個明顯 pullback
            window = close.iloc[i-pb_window*2:i]
            highs = high.iloc[i-pb_window*2:i]
            max_h = highs.max()
            if max_h > 0:
                drops_count = sum(1 for j in range(1, len(window))
                                   if (max_h - window.iloc[j]) / max_h >= min_pb)
                if drops_count >= 2 and not np.isnan(tm) and c > tm and c > window.iloc[-1] and not np.isnan(a):
                    action[i]="BUY"; target_buy[i]=c
                    in_pos=True; entry_price=c
                    sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_slow_trend_pullback(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Slow trend (long MA) + tiny pullback to short MA for low-vol blue chips"""
    close = df["close"]
    long_n  = int(params["long_ma"]); short_n = int(params["short_ma"])
    pb_pct  = float(params["pullback_pct"])
    tp_pct  = float(params["take_profit_pct"])
    atr_k   = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])
    long_s = sma(close, long_n); short_s = sma(close, short_n)
    atr_s = atr(df, 14)
    n = len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(n):
        c=close.iloc[i]; lm=long_s.iloc[i]; sm=short_s.iloc[i]; a=atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            if tp_hit or sl_hit or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            if (not np.isnan(lm) and not np.isnan(sm) and not np.isnan(a)
                and c > lm and c < sm * (1 - pb_pct)):
                action[i]="BUY"; target_buy[i]=sm*(1-pb_pct)
                in_pos=True; entry_price=c; sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_stoch_rsi(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Stochastic RSI"""
    close = df["close"]
    rsi_p = int(params["rsi_period"]); st_p = int(params["stoch_period"])
    os_th = int(params["oversold"]); ob_th = int(params["overbought"])
    trend_n = int(params["trend_ma"])
    tp_pct = float(params["take_profit_pct"])
    max_hold = int(params["max_hold_days"])
    rsi_s = rsi(close, rsi_p)
    rsi_min = rsi_s.rolling(st_p).min()
    rsi_max = rsi_s.rolling(st_p).max()
    stoch_rsi = 100 * (rsi_s - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
    trend_s = sma(close, trend_n)
    n = len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan
    for i in range(n):
        c=close.iloc[i]; sr=stoch_rsi.iloc[i]; tm=trend_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i]=entry_price*(1+tp_pct)
            if not np.isnan(tm): target_sl[i]=tm*0.92
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(target_sl[i])) and c<target_sl[i]
            ob=(not np.isnan(sr)) and sr>ob_th
            if tp_hit or sl_hit or ob or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            if (not np.isnan(sr) and sr<os_th
                and not np.isnan(tm) and c>tm*0.85):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_ao_zero_cross(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Awesome Oscillator zero-line cross from below"""
    high = df["high"]; low = df["low"]; close = df["close"]
    short_n = int(params["short_n"]); long_n = int(params["long_n"])
    trend_n = int(params["trend_ma"])
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])
    if short_n >= long_n:
        return pd.DataFrame({"action":["HOLD"]*len(df)}, index=df.index)
    mid = (high + low) / 2
    ao = sma(mid, short_n) - sma(mid, long_n)
    trend_s = sma(close, trend_n); atr_s = atr(df, 14)
    n = len(df); action=["HOLD"]*n; target_buy=[np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos=False; hold_days=0; entry_price=np.nan; sl_level=np.nan
    for i in range(1, n):
        c=close.iloc[i]; tm=trend_s.iloc[i]; a=atr_s.iloc[i]
        a0, a1 = ao.iloc[i-1], ao.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i]=entry_price*(1+tp_pct)
            target_sl[i]=sl_level
            tp_hit=(not np.isnan(target_tp[i])) and c>=target_tp[i]
            sl_hit=(not np.isnan(sl_level)) and c<sl_level
            cross_down=(not np.isnan(a0) and not np.isnan(a1) and a0>=0 and a1<0)
            if tp_hit or sl_hit or cross_down or hold_days>=max_hold:
                action[i]="SELL"; in_pos=False; hold_days=0
                target_tp[i]=np.nan; target_sl[i]=np.nan
        else:
            cross_up=(not np.isnan(a0) and not np.isnan(a1) and a0<=0 and a1>0)
            if cross_up and not np.isnan(tm) and c>tm*0.85 and not np.isnan(a):
                action[i]="BUY"; target_buy[i]=c
                in_pos=True; entry_price=c; sl_level=c-a*atr_k; hold_days=0
    return pd.DataFrame({"action":action,"target_buy":target_buy,
                          "target_tp":target_tp,"target_sl":target_sl}, index=df.index)


def generate_psar_flip(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Parabolic SAR flip from down to up"""
    high = df["high"]; low = df["low"]; close = df["close"]
    step = float(params["step"])
    max_step = float(params["max_step"])
    trend_n = int(params["trend_ma"])
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    # Simple PSAR
    psar = np.zeros(len(df)); trend = np.zeros(len(df))  # 1 = up, -1 = down
    af = step
    ep = float(high.iloc[0])
    psar[0] = float(low.iloc[0])
    trend[0] = 1
    for i in range(1, len(df)):
        prev = psar[i-1]
        if trend[i-1] == 1:  # uptrend
            psar[i] = prev + af * (ep - prev)
            if low.iloc[i] < psar[i]:
                trend[i] = -1; psar[i] = ep; ep = float(low.iloc[i]); af = step
            else:
                trend[i] = 1
                if high.iloc[i] > ep:
                    ep = float(high.iloc[i]); af = min(af + step, max_step)
        else:  # downtrend
            psar[i] = prev + af * (ep - prev)
            if high.iloc[i] > psar[i]:
                trend[i] = 1; psar[i] = ep; ep = float(high.iloc[i]); af = step
            else:
                trend[i] = -1
                if low.iloc[i] < ep:
                    ep = float(low.iloc[i]); af = min(af + step, max_step)

    trend_s = sma(close, trend_n)
    atr_s = atr(df, 14)
    n = len(df)
    action = ["HOLD"] * n; target_buy = [np.nan]*n; target_tp=[np.nan]*n; target_sl=[np.nan]*n
    in_pos = False; hold_days = 0; entry_price = np.nan; sl_level = np.nan
    for i in range(1, n):
        c = close.iloc[i]; tm = trend_s.iloc[i]; a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            flip_down = trend[i] == -1 and trend[i-1] == 1
            if tp_hit or sl_hit or flip_down or hold_days >= max_hold:
                action[i] = "SELL"; in_pos = False; hold_days = 0
                target_tp[i] = np.nan; target_sl[i] = np.nan
        else:
            flip_up = trend[i] == 1 and trend[i-1] == -1
            if flip_up and not np.isnan(tm) and c > tm * 0.85 and not np.isnan(a):
                action[i] = "BUY"; target_buy[i] = c
                in_pos = True; entry_price = c
                sl_level = c - a * atr_k; hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


# ════════════════════════════════════════════════════════════════════
# Ensemble / Composite Strategies
#
# These combine multiple sub-filters or sub-signals to produce stronger
# entry confirmation. Two patterns are used:
#
#   - vote_K_of_N: BUY when at least K of N independent filters fire
#     (reduces false positives vs single template; risks fewer trades)
#
#   - trend_filter_AND_entry: a long-term trend filter must hold AND
#     an entry signal must fire (intersection; only trades in favorable regime)
#
# Designed to fill the gap where individual templates produce too many
# false positives (low PF) or too few trades (low n).
# ════════════════════════════════════════════════════════════════════


def generate_ensemble_dip_vote(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """3 dip filters vote → BUY when at least 2 of 3 agree on same day.

    Filters:
        f1: RSI(rsi_period) < rsi_thresh (oversold momentum)
        f2: close < SMA(ma_period) × (1 - dip_pct) (price below trend MA)
        f3: close <= rolling_min(close, low_lookback) (touched recent low)

    Exit: TP_pct profit target OR max_hold_days elapsed.
    """
    close = df["close"]
    rsi_p = int(params["rsi_period"])
    rsi_thresh = float(params["rsi_thresh"])
    ma_p = int(params["ma_period"])
    dip = float(params["dip_pct"])
    low_n = int(params["low_lookback"])
    tp_pct = float(params["take_profit_pct"])
    max_hold = int(params["max_hold_days"])

    rsi_v = rsi(close, rsi_p)
    ma = sma(close, ma_p)
    rolling_min = close.rolling(low_n, min_periods=low_n).min()

    f1 = (rsi_v < rsi_thresh) & rsi_v.notna()
    f2 = (close < ma * (1 - dip)) & ma.notna()
    f3 = (close <= rolling_min) & rolling_min.notna()
    vote = f1.astype(int).fillna(0) + f2.astype(int).fillna(0) + f3.astype(int).fillna(0)
    buy_signal = vote >= 2

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    for i in range(n):
        c = close.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            if tp_hit or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_breakout_vote(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """3 breakout filters vote → BUY when at least 2 of 3 agree.

    Filters:
        f1: close > Donchian_high(donchian_n)[i-1] (breakout above prior N-day high)
        f2: close > SMA(ma_p) × (1 + breakout_pct) (price above trend MA by buffer)
        f3: volume > volume_ma(vol_n) × vol_ratio (volume confirmation)

    Exit: ATR-based trailing stop + TP_pct + max_hold.
    """
    close = df["close"]
    high = df["high"]
    volume = df["volume"]
    donchian_n = int(params["donchian_n"])
    ma_p = int(params["ma_period"])
    breakout_pct = float(params["breakout_pct"])
    vol_n = int(params["vol_period"])
    vol_ratio = float(params["vol_ratio"])
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    donchian_high = high.rolling(donchian_n, min_periods=donchian_n).max().shift(1)
    ma = sma(close, ma_p)
    vol_avg = volume_ma(volume, vol_n)
    atr_s = atr(df, 14)

    f1 = (close > donchian_high) & donchian_high.notna()
    f2 = (close > ma * (1 + breakout_pct)) & ma.notna()
    f3 = (volume > vol_avg * vol_ratio) & vol_avg.notna()
    vote = f1.astype(int).fillna(0) + f2.astype(int).fillna(0) + f3.astype(int).fillna(0)
    buy_signal = vote >= 2

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    sl_level = np.nan
    for i in range(n):
        c = close.iloc[i]
        a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c) and not np.isnan(a):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                sl_level = c - a * atr_k
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_oversold_vote(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """3 oversold indicators vote → BUY when at least 2 of 3 agree.

    Filters:
        f1: RSI(rsi_p) < rsi_thresh (oversold)
        f2: ROC(roc_p) < roc_thresh (price decline over N days)
        f3: close < BB_lower(bb_p, bb_std) (below lower Bollinger band)

    Exit: TP + time_stop.
    """
    close = df["close"]
    rsi_p = int(params["rsi_period"])
    rsi_thresh = float(params["rsi_thresh"])
    roc_p = int(params["roc_period"])
    roc_thresh = float(params["roc_thresh"])
    bb_p = int(params["bb_period"])
    bb_std = float(params["bb_std"])
    tp_pct = float(params["take_profit_pct"])
    max_hold = int(params["max_hold_days"])

    rsi_v = rsi(close, rsi_p)
    roc_v = close.pct_change(roc_p)
    bb = bollinger(close, bb_p, bb_std)
    bb_lower = bb["lower"]

    f1 = (rsi_v < rsi_thresh) & rsi_v.notna()
    f2 = (roc_v < roc_thresh) & roc_v.notna()
    f3 = (close < bb_lower) & bb_lower.notna()
    vote = f1.astype(int).fillna(0) + f2.astype(int).fillna(0) + f3.astype(int).fillna(0)
    buy_signal = vote >= 2

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    for i in range(n):
        c = close.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            if tp_hit or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_trend_confirm(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Trend filter AND oversold entry signal (intersection).

    Trend gate (must hold):
        close > SMA(trend_long_ma)   ← only trade in long-term uptrend
        close > SMA(trend_short_ma)  ← short-term recently bullish

    Entry trigger:
        RSI(rsi_p) crosses up from < rsi_low to >= rsi_recover
        AND volume > volume_ma(vol_n) × vol_ratio

    Exit: TP + ATR stop + max_hold.
    """
    close = df["close"]
    volume = df["volume"]
    trend_long = int(params["trend_long_ma"])
    trend_short = int(params["trend_short_ma"])
    rsi_p = int(params["rsi_period"])
    rsi_low = float(params["rsi_low"])
    rsi_recover = float(params["rsi_recover"])
    vol_n = int(params["vol_period"])
    vol_ratio = float(params["vol_ratio"])
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    ma_long = sma(close, trend_long)
    ma_short = sma(close, trend_short)
    rsi_v = rsi(close, rsi_p)
    vol_avg = volume_ma(volume, vol_n)
    atr_s = atr(df, 14)

    # Trend gate
    trend_ok = ((close > ma_long) & (close > ma_short)) & ma_long.notna() & ma_short.notna()
    # RSI cross-up: yesterday < rsi_low, today >= rsi_recover
    rsi_cross_up = (rsi_v.shift(1) < rsi_low) & (rsi_v >= rsi_recover)
    # Volume confirmation
    vol_ok = (volume > vol_avg * vol_ratio) & vol_avg.notna()

    buy_signal = trend_ok & rsi_cross_up & vol_ok

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    sl_level = np.nan
    for i in range(n):
        c = close.iloc[i]
        a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c) and not np.isnan(a):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                sl_level = c - a * atr_k
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_dip_or_bounce(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """OR-style ensemble: BUY when ANY of 3 dip patterns trigger (union, more trades).

    Designed for low-vol stocks where individual templates are too sparse.
    Trades whenever ANY of:
        f1: RSI < rsi_thresh AND close > MA(trend_ma) (oversold but in uptrend)
        f2: hammer pattern AND close < open AND lower_shadow >= 2× body
        f3: 3-day decline AND today's close > open (reversal day)

    Exit: TP + max_hold + stop_pct.
    """
    close = df["close"]
    open_ = df["open"]
    high = df["high"]
    low = df["low"]
    rsi_p = int(params["rsi_period"])
    rsi_thresh = float(params["rsi_thresh"])
    trend_ma_n = int(params["trend_ma"])
    decline_days = int(params["decline_days"])
    tp_pct = float(params["take_profit_pct"])
    stop_pct = float(params["stop_pct"])
    max_hold = int(params["max_hold_days"])

    rsi_v = rsi(close, rsi_p)
    ma = sma(close, trend_ma_n)

    # f1: oversold but uptrend
    f1 = (rsi_v < rsi_thresh) & (close > ma) & rsi_v.notna() & ma.notna()

    # f2: hammer pattern
    body = (close - open_).abs()
    upper_shadow = high - close.where(close >= open_, open_)
    lower_shadow = close.where(close < open_, open_) - low
    f2 = (lower_shadow >= 2 * body) & (lower_shadow > upper_shadow) & (body > 0)

    # f3: N-day decline + reversal
    is_down = close < close.shift(1)
    n_consec_down = is_down.rolling(decline_days).sum() == decline_days
    is_reversal = close > open_
    f3 = n_consec_down.shift(1).fillna(False) & is_reversal

    buy_signal = f1 | f2 | f3

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    for i in range(n):
        c = close.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
                target_sl[i] = entry_price * (1 - stop_pct)
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(target_sl[i])) and c <= target_sl[i]
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_regime_dip(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Regime-aware dip buying: only takes dip signals in non-BEAR regime.

    Combines:
        - Regime filter: 0050 regime != BEAR (passed as `regime` arg)
        - Dip signal: close < SMA(ma_p) × (1 - dip_pct) AND RSI < rsi_thresh
        - Both must hold simultaneously

    Designed for stocks that work in trending markets but get washed out in bear
    phases. Common in cyclical names that have edge in BULL/NEUTRAL only.
    """
    close = df["close"]
    rsi_p = int(params["rsi_period"])
    rsi_thresh = float(params["rsi_thresh"])
    ma_p = int(params["ma_period"])
    dip_pct = float(params["dip_pct"])
    tp_pct = float(params["take_profit_pct"])
    max_hold = int(params["max_hold_days"])
    allow_neutral = bool(params.get("allow_neutral", True))

    rsi_v = rsi(close, rsi_p)
    ma = sma(close, ma_p)

    # Regime filter — if regime arg provided, use it; else assume always OK
    if regime is not None:
        if allow_neutral:
            regime_ok = (regime != "BEAR")
        else:
            regime_ok = (regime == "BULL")
    else:
        regime_ok = pd.Series([True] * len(df), index=df.index)

    dip_signal = (close < ma * (1 - dip_pct)) & (rsi_v < rsi_thresh)
    dip_signal = dip_signal.fillna(False) & ma.notna() & rsi_v.notna()
    buy_signal = dip_signal & regime_ok

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    for i in range(n):
        c = close.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            if tp_hit or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_breakout_pullback(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Two-stage entry: wait for breakout above MA, then enter on pullback to MA.

    Stage 1: Within last `lookback_window` days, was there a recent close >
             MA(ma_breakout) × (1 + breakout_threshold)? (breakout occurred)
    Stage 2: NOW close is back within pullback_range of MA(ma_breakout)
             (price has pulled back from the breakout high).
    Both must hold → BUY (the "buy the pullback after breakout" pattern).

    Exit: TP + ATR stop + max_hold + immediate exit if close < MA(ma_breakout)×0.95.

    Designed for trending stocks that have clean breakouts followed by orderly
    consolidations — classic Mark Minervini / O'Neil entry style.
    """
    close = df["close"]
    high = df["high"]
    low = df["low"]
    ma_p = int(params["ma_breakout"])
    breakout_threshold = float(params["breakout_threshold"])
    lookback_window = int(params["lookback_window"])
    pullback_range = float(params["pullback_range"])
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    ma = sma(close, ma_p)
    atr_s = atr(df, 14)

    # Stage 1: breakout above MA × (1 + threshold) in last N days
    breakout_level = ma * (1 + breakout_threshold)
    had_breakout = (close > breakout_level).rolling(lookback_window, min_periods=1).max() > 0

    # Stage 2: now close is back near MA (within pullback_range)
    pullback_low = ma * (1 - pullback_range)
    pullback_high = ma * (1 + pullback_range)
    near_ma = (close >= pullback_low) & (close <= pullback_high)

    buy_signal = had_breakout.shift(1).fillna(False) & near_ma & ma.notna()

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    sl_level = np.nan
    for i in range(n):
        c = close.iloc[i]
        m = ma.iloc[i]
        a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            ma_break_down = (not np.isnan(m)) and c < m * 0.95
            if tp_hit or sl_hit or ma_break_down or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c) and not np.isnan(a):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                sl_level = c - a * atr_k
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_triple_confirm(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Strict 3-filter intersection (trend + momentum + volume).

    All three must hold simultaneously:
        - Trend: close > SMA(trend_ma) (above long-term MA)
        - Momentum: RSI(rsi_p) > rsi_min AND RSI rising (RSI > RSI[lookback])
        - Volume: volume > volume_ma(vol_n) × vol_ratio

    Exits: TP, ATR stop, max_hold, OR loss of trend (close < SMA × stop_buffer).
    High-quality but low-frequency signals — designed for strong trends where
    all three classic confirmations align.
    """
    close = df["close"]
    volume = df["volume"]
    trend_ma_n = int(params["trend_ma"])
    rsi_p = int(params["rsi_period"])
    rsi_min = float(params["rsi_min"])
    rsi_lookback = int(params["rsi_lookback"])
    vol_n = int(params["vol_period"])
    vol_ratio = float(params["vol_ratio"])
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])
    stop_buffer = float(params["stop_buffer"])

    ma = sma(close, trend_ma_n)
    rsi_v = rsi(close, rsi_p)
    vol_avg = volume_ma(volume, vol_n)
    atr_s = atr(df, 14)

    trend_ok = (close > ma) & ma.notna()
    momentum_ok = (rsi_v > rsi_min) & (rsi_v > rsi_v.shift(rsi_lookback)) & rsi_v.notna()
    volume_ok = (volume > vol_avg * vol_ratio) & vol_avg.notna()

    buy_signal = trend_ok & momentum_ok & volume_ok

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    sl_level = np.nan
    for i in range(n):
        c = close.iloc[i]
        m = ma.iloc[i]
        a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            trend_lost = (not np.isnan(m)) and c < m * stop_buffer
            if tp_hit or sl_hit or trend_lost or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c) and not np.isnan(a):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                sl_level = c - a * atr_k
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_bullish_divergence(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Bullish RSI divergence: price makes lower low while RSI makes higher low.

    Detection (within `lookback_window` days):
        - Two local lows: current (today) and a prior one (locally min)
        - Current close <= prior_low_close × (1 + tolerance) (similar/lower price)
        - Current RSI(rsi_p) > prior RSI by `div_threshold` (RSI higher)

    Enter on confirmation: BUY if divergence detected AND close > 1-day-ago close
    (price now turning up).

    Exit: TP + ATR stop + max_hold. Classic mean-reversion at exhaustion.
    """
    close = df["close"]
    rsi_p = int(params["rsi_period"])
    lookback_window = int(params["lookback_window"])
    tolerance = float(params["tolerance"])
    div_threshold = float(params["div_threshold"])
    rsi_max = float(params["rsi_max"])  # only enter if current RSI still oversold-ish
    tp_pct = float(params["take_profit_pct"])
    atr_k = float(params["atr_stop_k"])
    max_hold = int(params["max_hold_days"])

    rsi_v = rsi(close, rsi_p)
    atr_s = atr(df, 14)

    # For each day, find the min close in last lookback_window days
    # (excluding today). If today's close is approximately that low but RSI is higher → divergence.
    prior_low_close = close.shift(1).rolling(lookback_window, min_periods=1).min()
    # Index where the prior low occurred — using close index find argmin
    # For simplicity, also compute RSI at the prior low time using shift trick
    # Approximation: prior RSI = min RSI in same window
    prior_low_rsi = rsi_v.shift(1).rolling(lookback_window, min_periods=1).min()

    similar_low = close <= prior_low_close * (1 + tolerance)
    higher_rsi = rsi_v > (prior_low_rsi + div_threshold)
    oversold = rsi_v < rsi_max
    turning_up = close > close.shift(1)

    divergence = similar_low & higher_rsi & oversold & turning_up
    buy_signal = divergence.fillna(False) & rsi_v.notna() & prior_low_close.notna()

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    sl_level = np.nan
    for i in range(n):
        c = close.iloc[i]
        a = atr_s.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
            target_sl[i] = sl_level
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(sl_level)) and c < sl_level
            if tp_hit or sl_hit or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c) and not np.isnan(a):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                sl_level = c - a * atr_k
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


def generate_ensemble_dual_momentum(df: pd.DataFrame, params: dict, regime=None, chip_data=None) -> pd.DataFrame:
    """Dual momentum: stock momentum AND market regime both positive.

    Buy when:
        - Stock ROC(roc_p) >= roc_thresh (stock has positive momentum)
        - 0050 regime is BULL (passed via regime arg; if None, fallback to RSI)
        - close > SMA(ma_p) (above intermediate-term MA)

    Exit on TP or if stock momentum turns negative or max_hold reached.

    The idea: combining stock-specific and market-wide momentum reduces drawdowns
    in regime shifts while maintaining solid upside in trending markets.
    """
    close = df["close"]
    roc_p = int(params["roc_period"])
    roc_thresh = float(params["roc_thresh"])
    ma_p = int(params["ma_period"])
    tp_pct = float(params["take_profit_pct"])
    stop_pct = float(params["stop_pct"])
    max_hold = int(params["max_hold_days"])

    roc_v = close.pct_change(roc_p)
    ma = sma(close, ma_p)

    # Regime filter
    if regime is not None:
        regime_ok = (regime == "BULL")
    else:
        # Fallback: use 200-MA upslope as regime proxy
        ma200 = sma(close, 200)
        regime_ok = (close > ma200) & (ma200 > ma200.shift(20))

    momentum_signal = (roc_v >= roc_thresh) & (close > ma) & ma.notna() & roc_v.notna()
    buy_signal = momentum_signal & regime_ok

    # Momentum-turn exit
    momentum_neg = roc_v < 0

    n = len(df)
    action = ["HOLD"] * n
    target_buy = [np.nan] * n
    target_tp = [np.nan] * n
    target_sl = [np.nan] * n
    in_pos = False
    hold_days = 0
    entry_price = np.nan
    for i in range(n):
        c = close.iloc[i]
        if in_pos:
            hold_days += 1
            if not np.isnan(entry_price):
                target_tp[i] = entry_price * (1 + tp_pct)
                target_sl[i] = entry_price * (1 - stop_pct)
            tp_hit = (not np.isnan(target_tp[i])) and c >= target_tp[i]
            sl_hit = (not np.isnan(target_sl[i])) and c <= target_sl[i]
            momentum_turn = bool(momentum_neg.iloc[i])
            if tp_hit or sl_hit or momentum_turn or hold_days >= max_hold:
                action[i] = "SELL"
                in_pos = False
                hold_days = 0
                target_tp[i] = np.nan
                target_sl[i] = np.nan
        else:
            if bool(buy_signal.iloc[i]) and not np.isnan(c):
                action[i] = "BUY"
                target_buy[i] = c
                in_pos = True
                entry_price = c
                hold_days = 0
    return pd.DataFrame({"action": action, "target_buy": target_buy,
                          "target_tp": target_tp, "target_sl": target_sl}, index=df.index)


TEMPLATE_GENERATORS = {
    "trend_pullback":         generate_T1,
    "donchian_breakout":      generate_T2,
    "momentum_hold":          generate_T3,
    "chip_momentum":          generate_T4,
    "mean_reversion":         generate_T5,
    "volume_breakout":        generate_T6,
    "gap_continuation":       generate_T7,
    "low_vol_pullback":       generate_T8,
    "bollinger_squeeze":      generate_T9,
    "bb_extremes":            generate_bb_extremes,
    "narrow_range_breakout":  generate_narrow_range_breakout,
    "golden_cross":           generate_golden_cross,
    "three_day_reversal":     generate_three_day_reversal,
    "rsi_oversold_volume":    generate_rsi_oversold_volume,
    "support_bounce":         generate_support_bounce,
    "cci_extremes":           generate_cci_extremes,
    "hammer_revert":          generate_hammer_revert,
    "macd_cross":             generate_macd_cross,
    "kd_oversold_cross":      generate_kd_oversold_cross,
    "adx_trending_pullback":  generate_adx_trending_pullback,
    "vwap_revert":            generate_vwap_revert,
    "yearly_high_break":      generate_yearly_high_break,
    "keltner_breakout":       generate_keltner_breakout,
    "mfi_oversold":           generate_mfi_oversold,
    "roc_reversal":           generate_roc_reversal,
    "williams_r_extreme":     generate_williams_r_extreme,
    "ema_cross":              generate_ema_cross,
    "gap_down_revert":        generate_gap_down_revert,
    "psar_flip":              generate_psar_flip,
    "slow_trend_pullback":    generate_slow_trend_pullback,
    "stoch_rsi":              generate_stoch_rsi,
    "ao_zero_cross":          generate_ao_zero_cross,
    "yearly_low_revert":      generate_yearly_low_revert,
    "atr_band_breakout":      generate_atr_band_breakout,
    "double_pullback":        generate_double_pullback,
    "linreg_slope_revert":    generate_linreg_slope_revert,
    "coppock_buy":            generate_coppock_buy,
    "ultimate_oscillator":    generate_ultimate_oscillator,
    "inside_day_breakout":    generate_inside_day_breakout,
    "three_white_soldiers":   generate_three_white_soldiers,
    "outside_day_engulf":     generate_outside_day_engulf,
    "failed_breakdown":       generate_failed_breakdown,
    "volume_spike_reverse":   generate_volume_spike_reverse,
    "obv_uptrend":            generate_obv_uptrend,
    "pivot_break":            generate_pivot_break,
    "short_momentum":         generate_short_momentum,
    "double_volume":          generate_double_volume,
    "simple_dip_buy":         generate_simple_dip_buy,
    "monthly_anchor":         generate_monthly_anchor,
    "deep_dip_long_hold":     generate_deep_dip_long_hold,
    "weekly_low_buy":         generate_weekly_low_buy,
    "trend_confirm_hold":     generate_trend_confirm_hold,
    "low_volume_reversal":    generate_low_volume_reversal,
    "chip_streak":            generate_signals_chip_streak,
    "monthly_revenue_event":  generate_signals_monthly_revenue_event,
    # ── Ensemble / composite (5/16 新加) ────────────────────
    "ensemble_dip_vote":        generate_ensemble_dip_vote,
    "ensemble_breakout_vote":   generate_ensemble_breakout_vote,
    "ensemble_oversold_vote":   generate_ensemble_oversold_vote,
    "ensemble_trend_confirm":   generate_ensemble_trend_confirm,
    "ensemble_dip_or_bounce":   generate_ensemble_dip_or_bounce,
    # ── Phase 2 ensembles (5/17, regime-aware) ──────────────
    "ensemble_regime_dip":      generate_ensemble_regime_dip,
    "ensemble_breakout_pullback": generate_ensemble_breakout_pullback,
    "ensemble_dual_momentum":   generate_ensemble_dual_momentum,
    "ensemble_triple_confirm":  generate_ensemble_triple_confirm,
    "ensemble_bullish_divergence": generate_ensemble_bullish_divergence,
}
