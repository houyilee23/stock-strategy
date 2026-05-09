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
    "bb_extremes":            generate_bb_extremes,            # 5/9 range-bound 反轉
    "narrow_range_breakout":  generate_narrow_range_breakout,  # 5/9 NR-N 突破
    "chip_streak":            generate_signals_chip_streak,
    "monthly_revenue_event":  generate_signals_monthly_revenue_event,
}
