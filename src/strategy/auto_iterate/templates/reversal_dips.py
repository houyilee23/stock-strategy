"""Mean-reversion / dip-buying templates (~23).

Patterns: BB extremes, RSI/MFI/Williams oversold, ROC reversal,
hammer, three-day reversal, gap-down revert, simple/weekly/deep dip,
yearly low revert, KD/stoch RSI, AO zero cross, VWAP revert, etc."""
from ._common import *


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


