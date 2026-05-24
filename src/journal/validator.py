"""Signal journal validator — 對 pending 訊號驗證假定成交。

核心邏輯（用「下一個出現的股價」，自動跳過放假/颱風/停牌）：

  BUY (limit_price 設定)：
    - 走訪 signal_date 之後的 OHLC bars
    - 第一個 bar low ≤ limit_price → filled
      * 若 bar open ≤ limit_price → fill_price = open（保守，常常開盤就跳低）
      * 否則 fill_price = limit_price
    - 走完 DEFAULT_EXPIRY_TRADING_DAYS bars 都沒觸及 → expired

  BUY (limit_price 為空 / NaN)：市價 BUY，假設下一交易日 open 成交。

  SELL：
    - 走訪 bars，每根判斷：
        * 若有 take_profit 且 high ≥ take_profit → filled at take_profit
        * 若有 stop_loss   且 low  ≤ stop_loss   → filled at stop_loss
        * 同根都觸及則保守用 stop_loss（最壞情境）
    - 走完都沒觸發 → not_filled（SELL 訊號意味著「該出了」但價格沒到出場條件）
    - 若 take_profit / stop_loss 都空 → 視為市價 SELL，下一交易日 open 成交。

時序假設：T 日訊號 → T+1 開盤之後才掛單，所以 fill 只看 T 日之後的 bars。
"""
from __future__ import annotations
import math
import os
from datetime import datetime
import pandas as pd

from src.journal import storage
from src.journal.schema import (
    STATUS_PENDING, STATUS_FILLED, STATUS_NOT_FILLED, STATUS_EXPIRED,
    STATUS_NO_DATA, DEFAULT_EXPIRY_TRADING_DAYS,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_ohlc(sid: str) -> pd.DataFrame | None:
    """讀 adjusted（若有）或 raw，回 date-indexed DataFrame。

    用 adjusted 跟 run_signals 使用的價格一致（避免 BUY/SELL 訊號是 adjusted
    算的、驗證卻用 raw → 除權息日附近全部誤判 not_filled）。
    """
    for sub in ("adjusted", "raw"):
        path = os.path.join(BASE_DIR, "data", sub, f"{sid}.csv")
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path, dtype={"date": str})
            df["date"] = pd.to_datetime(df["date"], format="mixed")
            df = df.sort_values("date").set_index("date")
            # adjusted 有 close_adj 就一致還原 OHL（同 runner._load_adj_ohlcv 邏輯）
            if sub == "adjusted" and "close_adj" in df.columns:
                df = df.astype({"open": float, "high": float, "low": float,
                                "close": float, "close_adj": float})
                factor = (df["close_adj"] / df["close"]).replace(
                    [float("inf"), -float("inf")], 1.0).fillna(1.0)
                df["open"]  = df["open"]  * factor
                df["high"]  = df["high"]  * factor
                df["low"]   = df["low"]   * factor
                df["close"] = df["close_adj"]
            return df[["open", "high", "low", "close"]].astype(float)
        except Exception:
            continue
    return None


def _is_nan(v) -> bool:
    return isinstance(v, float) and math.isnan(v)


def _has(v) -> bool:
    return v is not None and not _is_nan(v) and v != ""


def _validate_buy(bars: pd.DataFrame, limit_price) -> dict:
    """走訪 bars 判定 BUY 是否成交。回 dict：status, fill_date, fill_price, bars_to_fill。"""
    if not _has(limit_price):
        # 市價 BUY：下一交易日 open
        if bars.empty:
            return {"status": STATUS_EXPIRED, "fill_date": None,
                    "fill_price": None, "bars_to_fill": None}
        first = bars.iloc[0]
        return {
            "status": STATUS_FILLED,
            "fill_date": first.name.strftime("%Y-%m-%d"),
            "fill_price": float(first["open"]),
            "bars_to_fill": 1,
        }
    lp = float(limit_price)
    for i, (idx, bar) in enumerate(bars.iterrows(), start=1):
        if float(bar["low"]) <= lp:
            # 若 open 已經低於 limit → 用 open（更貼近真實）；否則用 limit
            fill_p = min(float(bar["open"]), lp) if float(bar["open"]) <= lp else lp
            return {
                "status": STATUS_FILLED,
                "fill_date": idx.strftime("%Y-%m-%d"),
                "fill_price": fill_p,
                "bars_to_fill": i,
            }
    # 沒觸及
    return {"status": STATUS_EXPIRED if len(bars) >= DEFAULT_EXPIRY_TRADING_DAYS
            else STATUS_NOT_FILLED,
            "fill_date": None, "fill_price": None,
            "bars_to_fill": len(bars) if len(bars) else None}


def _validate_sell(bars: pd.DataFrame, take_profit, stop_loss) -> dict:
    """走訪 bars 判定 SELL 是否觸發 TP / SL。"""
    has_tp = _has(take_profit)
    has_sl = _has(stop_loss)

    # 純市價 SELL：下一交易日 open
    if not has_tp and not has_sl:
        if bars.empty:
            return {"status": STATUS_EXPIRED, "fill_date": None,
                    "fill_price": None, "bars_to_fill": None}
        first = bars.iloc[0]
        return {
            "status": STATUS_FILLED,
            "fill_date": first.name.strftime("%Y-%m-%d"),
            "fill_price": float(first["open"]),
            "bars_to_fill": 1,
        }

    tp = float(take_profit) if has_tp else None
    sl = float(stop_loss) if has_sl else None

    for i, (idx, bar) in enumerate(bars.iterrows(), start=1):
        hit_sl = has_sl and float(bar["low"]) <= sl
        hit_tp = has_tp and float(bar["high"]) >= tp
        if hit_sl and hit_tp:
            # 同根都觸及：保守用 stop_loss（最壞情境）
            return {"status": STATUS_FILLED, "fill_date": idx.strftime("%Y-%m-%d"),
                    "fill_price": sl, "bars_to_fill": i}
        if hit_sl:
            return {"status": STATUS_FILLED, "fill_date": idx.strftime("%Y-%m-%d"),
                    "fill_price": sl, "bars_to_fill": i}
        if hit_tp:
            return {"status": STATUS_FILLED, "fill_date": idx.strftime("%Y-%m-%d"),
                    "fill_price": tp, "bars_to_fill": i}

    return {"status": STATUS_EXPIRED if len(bars) >= DEFAULT_EXPIRY_TRADING_DAYS
            else STATUS_NOT_FILLED,
            "fill_date": None, "fill_price": None,
            "bars_to_fill": len(bars) if len(bars) else None}


def _validate_one(row: pd.Series, expiry_days: int) -> dict:
    """驗證單一 pending row，回傳要 patch 進 row 的欄位 dict。"""
    sid = str(row["sid"])
    ohlc = _load_ohlc(sid)
    if ohlc is None:
        return {"status": STATUS_NO_DATA,
                "validated_at": datetime.now().isoformat(timespec="seconds")}

    # 取 signal_date 之後的 bars，最多 expiry_days 根
    sig_date = pd.Timestamp(row["signal_date"])
    next_bars = ohlc.loc[ohlc.index > sig_date].head(expiry_days)
    if next_bars.empty:
        # 還沒到 T+1，繼續 pending（不算驗證失敗）
        return {"validated_at": datetime.now().isoformat(timespec="seconds")}

    action = str(row["action"]).upper()
    if action == "BUY":
        result = _validate_buy(next_bars, row["limit_price"])
    elif action == "SELL":
        result = _validate_sell(next_bars, row["take_profit"], row["stop_loss"])
    else:
        return {"validated_at": datetime.now().isoformat(timespec="seconds")}

    result["validated_at"] = datetime.now().isoformat(timespec="seconds")
    return result


def validate_partition(partition: str, expiry_days: int = DEFAULT_EXPIRY_TRADING_DAYS,
                        revalidate_not_filled: bool = True) -> dict:
    """對單月 journal 驗證所有 pending（與可選的 not_filled）的 row。

    revalidate_not_filled=True：之前標 not_filled 的還會再驗，因為新的交易日
    可能讓掛單真的被觸及（特別是 not_filled 但還沒到 expiry_days 的）。
    """
    df = storage.load_partition(partition)
    if df.empty:
        return {"partition": partition, "validated": 0, "filled": 0,
                "not_filled": 0, "expired": 0, "no_data": 0}

    eligible = df["status"].isin([STATUS_PENDING])
    if revalidate_not_filled:
        eligible = eligible | (df["status"] == STATUS_NOT_FILLED)

    target_idx = df[eligible].index
    if len(target_idx) == 0:
        return {"partition": partition, "validated": 0, "filled": 0,
                "not_filled": 0, "expired": 0, "no_data": 0}

    # pandas 3.x：若 CSV 整欄空白會被推斷成 float64，後續寫字串會 raise
    # TypeError。先把所有要寫的欄位升級成 object 才能寫 str / None。
    for col in ("status", "validated_at", "fill_date", "fill_price",
                "bars_to_fill"):
        if col in df.columns:
            df[col] = df[col].astype(object)

    counts = {STATUS_FILLED: 0, STATUS_NOT_FILLED: 0,
              STATUS_EXPIRED: 0, STATUS_NO_DATA: 0, STATUS_PENDING: 0}
    for idx in target_idx:
        patch = _validate_one(df.loc[idx], expiry_days)
        for k, v in patch.items():
            df.at[idx, k] = v
        new_status = patch.get("status", df.at[idx, "status"])
        counts[new_status] = counts.get(new_status, 0) + 1

    storage.save_partition(partition, df)
    return {
        "partition":  partition,
        "validated":  len(target_idx),
        "filled":     counts[STATUS_FILLED],
        "not_filled": counts[STATUS_NOT_FILLED],
        "expired":    counts[STATUS_EXPIRED],
        "no_data":    counts[STATUS_NO_DATA],
        "still_pending": counts[STATUS_PENDING],
    }


def validate_all(expiry_days: int = DEFAULT_EXPIRY_TRADING_DAYS) -> list[dict]:
    """驗證所有月份檔案。回傳每月的統計列表。"""
    return [validate_partition(p, expiry_days) for p in storage.list_partitions()]
