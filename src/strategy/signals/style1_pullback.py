import numpy as np
import pandas as pd

from src.strategy.indicators.trend import sma
from src.strategy.indicators.momentum import rsi
from src.strategy.indicators.volatility import atr, bollinger
from src.strategy.indicators.volume import volume_ma


def generate_signals(
    df: pd.DataFrame,
    market_regime: pd.Series,
    params: dict,
) -> pd.DataFrame:
    """風格 1：趨勢過濾 + 回檔進場

    Args:
        df: 個股 OHLCV DataFrame（index 為日期，欄位含 open/high/low/close/volume）
        market_regime: 大盤 regime 序列（'BULL'/'BEAR'），index 需對齊
        params: strategy.yaml 的 style1_pullback 區段

    Returns:
        DataFrame，欄位：action(BUY/SELL/HOLD), entry_low, entry_high,
                         stop_loss, reason, rsi_val, ma200, high_since_entry
    """
    p = params
    close = df["close"]
    high = df["high"]
    low = df["low"]
    vol = df["volume"]

    # ── 指標計算 ──────────────────────────────────────────────
    ma200 = sma(close, p["ma_long"])
    ma50 = sma(close, p["ma_short"])
    ma20 = sma(close, 20)
    rsi_val = rsi(close, p["rsi_period"])
    boll = bollinger(close, p["bollinger_period"], p["bollinger_k"])
    atr_val = atr(df, p["atr_period"])
    vol_ma = volume_ma(vol, p["volume_ma_period"])

    # 對齊 regime（左 join，市場 regime 可能索引不同）
    regime_aligned = market_regime.reindex(close.index, method="ffill").fillna("BEAR")

    n = len(df)
    action = ["HOLD"] * n
    entry_low = [np.nan] * n
    entry_high = [np.nan] * n
    stop_loss = [np.nan] * n
    reason = [""] * n
    high_since = [np.nan] * n

    in_position = False
    entry_price = np.nan
    hold_days = 0
    current_high_since_entry = np.nan
    trend_break_count = 0
    k_atr = p["atr_stop_k"]

    for i in range(n):
        c = close.iloc[i]
        h = high.iloc[i]
        prev_c = close.iloc[i - 1] if i > 0 else np.nan
        prev_o = df["open"].iloc[i - 1] if i > 0 else np.nan

        r = rsi_val.iloc[i]
        bl = boll["lower"].iloc[i]
        bu = boll["upper"].iloc[i]
        m200 = ma200.iloc[i]
        m50 = ma50.iloc[i]
        m20 = ma20.iloc[i]
        v_ma = vol_ma.iloc[i]
        atr_i = atr_val.iloc[i]
        regime = regime_aligned.iloc[i]
        o = df["open"].iloc[i]

        if in_position:
            # 更新 high_since_entry
            current_high_since_entry = max(current_high_since_entry, h) if not np.isnan(current_high_since_entry) else h
            hold_days += 1

            # 判斷出場條件
            sell_reason = ""
            atr_stop = current_high_since_entry - k_atr * atr_i if not np.isnan(atr_i) else np.nan
            ma200_stop = m200 if not np.isnan(m200) else np.nan

            # 1. ATR 移動停損
            if not np.isnan(atr_stop) and c < atr_stop:
                sell_reason = f"ATR停損 stop={atr_stop:.2f}"

            # 2. 趨勢破壞（Close < MA200 連續 2 日）
            elif not np.isnan(m200) and c < m200:
                trend_break_count += 1
                if trend_break_count >= p["trend_break_days"]:
                    sell_reason = f"趨勢破壞 連{trend_break_count}日<MA200"
            else:
                trend_break_count = 0

            # 3. 超漲止盈
            if not sell_reason and not np.isnan(r) and not np.isnan(bu):
                if r > p["rsi_overbought"] and c > bu:
                    sell_reason = f"超漲止盈 RSI={r:.1f}"

            # 4. 持倉超過 N 天就出場（P1-2 修正：不在訊號層判斷未獲利，
            # 因為 entry_price=e_low 是建議限價，不等於實際成交價 T+1 open）
            if not sell_reason and hold_days >= p["max_hold_days"]:
                sell_reason = f"持倉{hold_days}日逾期出場"

            if sell_reason:
                action[i] = "SELL"
                reason[i] = sell_reason
                # 建議停損：ATR停損與MA200取較高者（保護更多）
                if not np.isnan(atr_stop) and not np.isnan(ma200_stop):
                    stop_loss[i] = max(atr_stop, ma200_stop)
                elif not np.isnan(atr_stop):
                    stop_loss[i] = atr_stop
                else:
                    stop_loss[i] = ma200_stop
                high_since[i] = current_high_since_entry
                in_position = False
                entry_price = np.nan
                hold_days = 0
                current_high_since_entry = np.nan
                trend_break_count = 0
            else:
                action[i] = "HOLD"
                # 持倉中給停損建議
                if not np.isnan(atr_stop) and not np.isnan(ma200_stop):
                    stop_loss[i] = max(atr_stop, ma200_stop)
                elif not np.isnan(atr_stop):
                    stop_loss[i] = atr_stop
                else:
                    stop_loss[i] = ma200_stop
                high_since[i] = current_high_since_entry
                if not np.isnan(r) and r > 70:
                    reason[i] = f"持倉中 RSI={r:.1f}>70 接近超漲"
                else:
                    reason[i] = f"持倉中 持{hold_days}日"
        else:
            # 判斷進場條件
            can_buy = True
            buy_reason_parts = []

            # 1. 長期趨勢 OK
            if np.isnan(m200) or np.isnan(m50) or not (c > m200 and m50 > m200):
                can_buy = False

            # 2. 大盤 regime OK
            if regime != "BULL":
                can_buy = False

            # 3. 短期回檔
            pullback_ok = (not np.isnan(r) and r < p["rsi_oversold"]) or \
                          (not np.isnan(bl) and c < bl)
            if not pullback_ok:
                can_buy = False

            # 4. 反轉訊號（當日 Close > Open AND Close > 前一日 Close）
            if i == 0 or np.isnan(prev_c) or not (c > o and c > prev_c):
                can_buy = False

            # 5. 量能配合
            if np.isnan(v_ma) or vol.iloc[i] < v_ma * p["volume_min_ratio"]:
                can_buy = False

            if can_buy:
                action[i] = "BUY"
                # 建議買入區間：[今日 Low, 前一日 Low]，上限不超過 MA20
                e_low = low.iloc[i]
                e_high = min(low.iloc[i - 1] if i > 0 else low.iloc[i], m20 if not np.isnan(m20) else e_low * 1.02)
                if e_high < e_low:
                    e_high = e_low * 1.01
                entry_low[i] = e_low
                entry_high[i] = e_high
                # 初始停損：MA200
                stop_loss[i] = m200 if not np.isnan(m200) else c * 0.95
                reason[i] = "回檔進場" + (f" RSI={r:.1f}" if not np.isnan(r) else "")
                # 進場：以 entry_low 作為 entry_price（限價單概念）
                in_position = True
                entry_price = e_low
                hold_days = 0
                current_high_since_entry = h
                trend_break_count = 0
            else:
                action[i] = "HOLD"
                # 接近進場條件時給買入區間建議
                trend_ok = not np.isnan(m200) and not np.isnan(m50) and c > m200 and m50 > m200
                pullback_near = (not np.isnan(r) and r < 50) or (not np.isnan(bl) and c < bl * 1.05)
                if trend_ok and pullback_near and regime == "BULL":
                    e_low = low.iloc[i]
                    e_high = min(low.iloc[i - 1] if i > 0 else e_low, m20 if not np.isnan(m20) else e_low * 1.02)
                    if e_high < e_low:
                        e_high = e_low * 1.01
                    entry_low[i] = e_low
                    entry_high[i] = e_high
                    stop_loss[i] = m200 if not np.isnan(m200) else c * 0.95
                    reason[i] = "觀察中" + (f" RSI={r:.1f}" if not np.isnan(r) else "")

    return pd.DataFrame({
        "action": action,
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": stop_loss,
        "reason": reason,
        "rsi_val": rsi_val.values,
        "ma200": ma200.values,
        "high_since_entry": high_since,
    }, index=df.index)
