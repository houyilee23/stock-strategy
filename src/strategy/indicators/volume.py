import pandas as pd
import numpy as np


def volume_ma(volume: pd.Series, n: int = 20) -> pd.Series:
    return volume.rolling(n).mean()


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()
