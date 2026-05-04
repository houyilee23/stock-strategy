import pandas as pd
import numpy as np


def sma(close: pd.Series, n: int) -> pd.Series:
    return close.rolling(n).mean()


def ema(close: pd.Series, n: int) -> pd.Series:
    return close.ewm(span=n, adjust=False).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def _wilder_sum_np(arr: np.ndarray, period: int) -> np.ndarray:
    """Wilder running sum（初始化為前 period 個簡單求和，之後迭代）。
    全用 numpy 避免 pandas CoW 的 iloc 問題。
    若序列長度不足 period，全回傳 NaN。
    """
    n = len(arr)
    result = np.full(n, np.nan)
    if n < period:
        return result
    # 找第一個能完整求和的起點（前 period 個值都不是 NaN）
    for start in range(n - period + 1):
        window = arr[start: start + period]
        if not np.any(np.isnan(window)):
            result[start + period - 1] = window.sum()
            for i in range(start + period, n):
                if np.isnan(arr[i]):
                    result[i] = np.nan
                else:
                    result[i] = result[i - 1] * (period - 1) / period + arr[i]
            break
    return result


def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """ADX — 最終平滑用 EMA（不可用 Wilder sum，否則值會 ~14× 放大）"""
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    close = df["close"].values.astype(float)

    prev_close = np.roll(close, 1)
    prev_close[0] = np.nan

    tr = np.maximum.reduce([
        high - low,
        np.abs(high - prev_close),
        np.abs(low - prev_close),
    ])
    tr[0] = np.nan

    high_diff = np.diff(high, prepend=np.nan)
    low_diff = -np.diff(low, prepend=np.nan)
    high_diff[0] = np.nan
    low_diff[0] = np.nan

    dm_plus = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
    dm_minus = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)
    dm_plus[0] = np.nan
    dm_minus[0] = np.nan

    atr_w = _wilder_sum_np(tr, n)
    dp_w = _wilder_sum_np(dm_plus, n)
    dm_w = _wilder_sum_np(dm_minus, n)

    with np.errstate(invalid="ignore", divide="ignore"):
        di_plus = 100 * dp_w / atr_w
        di_minus = 100 * dm_w / atr_w
        denom = di_plus + di_minus
        dx = np.where(denom == 0, np.nan, 100 * np.abs(di_plus - di_minus) / denom)

    dx_series = pd.Series(dx, index=df.index)
    # 最終 ADX 平滑只用 EMA（不用 Wilder sum 避免 ~14× 放大 bug）
    adx_series = dx_series.ewm(alpha=1 / n, adjust=False).mean()
    return adx_series
