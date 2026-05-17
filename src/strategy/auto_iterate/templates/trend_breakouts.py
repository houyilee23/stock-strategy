"""Trend-following + breakout + momentum templates (~21).

Patterns: golden cross, EMA cross, MACD cross, narrow range break,
Donchian/Keltner/ATR-band breakout, monthly anchor, ADX trend pullback,
pivot break, three-white-soldiers, outside-day engulf, PSAR flip, etc."""
from ._common import *


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


