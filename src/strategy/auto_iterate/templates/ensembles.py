"""10 ensemble strategies (5/16-5/17 — composite of multiple filters).

Vote-based: dip_vote, breakout_vote, oversold_vote, trend_confirm,
         dip_or_bounce
Regime-aware: regime_dip, breakout_pullback, dual_momentum
Intersection: triple_confirm, bullish_divergence

These reduce false-positives by requiring multi-filter agreement."""
from ._common import *


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


