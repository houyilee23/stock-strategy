import numpy as np
import pandas as pd
from src.strategy.signals.style2_momentum import rank_universe


def make_monthly_portfolio_sizing(
    regime: pd.Series,
    mom_params: dict,
    max_position_pct: float,
) -> "callable":
    """建立月頻換倉 + 每日 regime 即時保護 的 sizing_fn。

    邏輯：
    - BEAR regime（每日檢查）→ 立即清倉，重置 rebalance 計時
    - BULL regime + 同月已 rebalance → 維持現有持倉
    - BULL regime + 新月份 → 執行完整 rebalance
    """
    _last_rb = [None]

    def sizing_fn(date: pd.Timestamp, signals_dict: dict, cash: float,
                  ohlcv_dict: dict, holdings: dict) -> dict:
        # 每日 regime 檢查：BEAR → 立即清倉
        regime_sub = regime[regime.index <= date]
        current_regime = regime_sub.iloc[-1] if len(regime_sub) > 0 else "BEAR"
        if current_regime == "BEAR":
            if holdings:
                _last_rb[0] = None  # 重置，確保回 BULL 後立即 rebalance
                return {sid: 0 for sid in holdings}
            return {}

        # BULL regime：月頻 rebalance gate
        if _last_rb[0] == date.month and holdings:
            return holdings
        _last_rb[0] = date.month
        return top_n_equal_weight_sizing(
            date, signals_dict, cash, ohlcv_dict, holdings, mom_params,
            max_position_pct, market_regime=regime,
        )

    return sizing_fn


def top_n_equal_weight_sizing(
    date: pd.Timestamp,
    signals_dict: dict,
    cash: float,
    ohlcv_dict: dict,
    current_holdings: dict,
    params: dict,
    max_position_pct: float = 0.25,
    market_regime: pd.Series = None,
) -> dict:
    """Top-N 等權配置（月頻 rebalance）。

    P0-6：傳入 market_regime；BEAR regime 時清倉還現金。
    P0-7：個股需多頭排列（Close > MA200 AND MA50 > MA200）才納入候選。
    P0-8：保留 cash_reserve_pct 現金緩衝，預設 20%。

    Returns:
        {stock_id: target_shares} — rebalance 日回傳目標配置；
        BEAR regime 時所有持股清零。
    """
    top_n = params.get("top_n", 5)

    # 計算動量排名（P0-6：傳入 regime；BEAR 時 rank_universe 回空 DataFrame）
    rank_df = rank_universe(ohlcv_dict, date, params, market_regime=market_regime)

    # P0-6：BEAR regime → rank_df 為空 → 清倉還現金
    if rank_df.empty:
        return {sid: 0 for sid in current_holdings}

    # 取 top_n 候選，套用 P0-7 多頭排列 + SELL 篩選
    candidates = rank_df.head(top_n)
    selected = []

    for _, row in candidates.iterrows():
        sid = row["stock_id"]

        # P0-7：個股多頭排列篩選（Close > MA200 AND MA50 > MA200）
        if sid in ohlcv_dict:
            df_c = ohlcv_dict[sid]
            df_c_sub = df_c.loc[df_c.index <= date, "close"]
            if len(df_c_sub) < 50:
                continue  # MA50 不足，跳過
            close_v  = df_c_sub.iloc[-1]
            ma50_v   = df_c_sub.iloc[-50:].mean()
            ma200_v  = df_c_sub.iloc[-200:].mean() if len(df_c_sub) >= 200 else np.nan
            if np.isnan(ma200_v):
                continue  # MA200 不足，跳過
            if not (close_v > ma200_v and ma50_v > ma200_v):
                continue  # 個股非多頭排列 → 跳過

        # SELL 訊號過濾（P0-7 強化後保留此條件）
        sig = signals_dict.get(sid)
        if sig is not None:
            sig_sub = sig[sig.index <= date]
            if not sig_sub.empty and sig_sub["action"].iloc[-1] == "SELL":
                continue  # 訊號明確賣出 → 跳過

        selected.append(sid)

    if not selected:
        # 無合格標的 → 清倉
        return {sid: 0 for sid in current_holdings}

    # P0-8：計算可投資金額（保留 cash_reserve_pct 現金緩衝）
    total_value = cash + sum(
        current_holdings.get(sid, 0) * ohlcv_dict[sid].loc[date, "close"]
        for sid in ohlcv_dict
        if date in ohlcv_dict[sid].index
    )
    cash_reserve_pct = params.get("cash_reserve_pct", 0.20)
    investable = total_value * (1 - cash_reserve_pct)
    alloc_per_stock = min(investable / len(selected), total_value * max_position_pct)

    target = {}
    for sid in selected:
        if sid not in ohlcv_dict or date not in ohlcv_dict[sid].index:
            continue
        price = ohlcv_dict[sid].loc[date, "close"]
        if price > 0:
            shares = int(alloc_per_stock / price)
            if shares > 0:
                target[sid] = shares

    # 不在 selected 中的現有持股 → 清零
    for sid in list(current_holdings.keys()):
        if sid not in target:
            target[sid] = 0

    return target
