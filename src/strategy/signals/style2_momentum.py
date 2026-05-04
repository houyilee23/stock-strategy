import numpy as np
import pandas as pd

from src.strategy.indicators.momentum import momentum_12_1


def rank_universe(
    price_dict: dict,
    asof_date: pd.Timestamp,
    params: dict,
    market_regime: pd.Series = None,
) -> pd.DataFrame:
    """風格 2：動量排序

    Args:
        price_dict: {stock_id: OHLCV DataFrame}
        asof_date: 計算基準日（只用此日及之前資料）
        params: strategy.yaml 的 style2_momentum 區段
        market_regime: 大盤 regime 序列（'BULL'/'BEAR'）。
            P0-6 修正：BEAR regime 時整體現金，回傳空 DataFrame。

    Returns:
        DataFrame 欄位：stock_id, momentum_score, rank（依 score 降冪）
        空 DataFrame 代表應持全現金（BEAR regime）。
    """
    # P0-6：BEAR regime → 整體現金
    if market_regime is not None and len(market_regime) > 0:
        regime_sub = market_regime[market_regime.index <= asof_date]
        if len(regime_sub) > 0 and regime_sub.iloc[-1] == "BEAR":
            return pd.DataFrame(columns=["stock_id", "momentum_score", "rank"])

    scores = []
    for stock_id, df in price_dict.items():
        # 時間防穿越：只用 asof_date 及之前
        df_sub = df[df.index <= asof_date]
        if len(df_sub) == 0:
            continue
        mom = momentum_12_1(df_sub["close"])
        last_valid = mom.dropna()
        if len(last_valid) == 0:
            score = np.nan
        else:
            score = last_valid.iloc[-1]
        scores.append({"stock_id": stock_id, "momentum_score": score})

    result = pd.DataFrame(scores)
    if result.empty:
        return result

    result = result.dropna(subset=["momentum_score"])
    result = result.sort_values("momentum_score", ascending=False).reset_index(drop=True)
    result["rank"] = range(1, len(result) + 1)
    return result
