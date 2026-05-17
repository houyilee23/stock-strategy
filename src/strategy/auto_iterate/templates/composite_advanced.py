"""Event-driven / composite signals using auxiliary data.

chip_streak — institutional buy/sell streak from chip_data
monthly_revenue_event — revenue YoY gap continuation"""
from ._common import *


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


