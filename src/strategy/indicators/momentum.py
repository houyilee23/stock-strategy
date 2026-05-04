import pandas as pd
import numpy as np


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False).mean()
    # avg_loss=0 表示無虧損 → RSI=100；avg_gain=0 表示無獲利 → RSI=0
    rsi_val = avg_gain / (avg_gain + avg_loss)
    rsi_val = rsi_val.where((avg_gain + avg_loss) > 0, other=0.5)
    return 100 * rsi_val


def roc(close: pd.Series, n: int) -> pd.Series:
    return (close / close.shift(n) - 1) * 100


def momentum_12_1(close: pd.Series) -> pd.Series:
    """12月-1月動量：過去12個月報酬扣掉最近1個月（標準動量定義）。
    使用21個交易日≈1個月、252個交易日≈12個月。
    """
    month1 = 21
    month12 = 252
    return (close.shift(month1) / close.shift(month12) - 1) * 100
