"""Original 9 templates (T1-T9) — the seed set.

T1 trend_pullback / T2 donchian_breakout / T3 momentum_hold /
T4 chip_momentum / T5 mean_reversion / T6 volume_breakout /
T7 gap_continuation / T8 low_vol_pullback / T9 bollinger_squeeze"""
from ._common import *


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


