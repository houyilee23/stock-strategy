import pandas as pd
from src.strategy.indicators.trend import sma


def detect_regime(market_df: pd.DataFrame, ma_long: int = 200) -> pd.Series:
    """大盤 Regime 偵測。
    BULL: Close > MA200 AND MA50 > MA200
    BEAR: 其他
    回傳 'BULL'/'BEAR' 序列，index 對齊 market_df。
    """
    close = market_df["close"]
    ma200 = sma(close, 200)
    ma50 = sma(close, 50)
    regime = pd.Series("BEAR", index=close.index)
    regime[(close > ma200) & (ma50 > ma200)] = "BULL"
    return regime
