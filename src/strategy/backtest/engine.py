import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Callable, Optional

from src.strategy.backtest.fees import calc_buy_cost, calc_sell_proceeds, \
    calc_buy_exec_price, calc_sell_exec_price
from src.strategy.backtest.result import StockResult, PortfolioResult, TradeRecord
from src.strategy.indicators.volatility import atr as _atr


@dataclass
class BacktestConfig:
    fees: dict
    start_date: str = "2017-01-01"
    end_date: str = "today"
    initial_capital: float = 100_000
    max_position_pct: float = 0.25
    execution_lag_days: int = 1  # T+1 成交


class ScalingOutManager:
    """管理一次 BUY 後的分批出場狀態。

    狀態轉移：
        ARMED   ：剛買入，0 leg 觸發
        L1_DONE ：第 1 leg 出原始 1/3，剩 2/3
        L2_DONE ：第 2 leg 再出原始 1/3，剩 1/3
        TRAILING：剩餘 1/3 由 chandelier 接管
        CLOSED  ：全部出場

    判斷順序（在 T+1 開盤後，當日盤中）：
        1. 若 T 日有 SELL 訊號 → 剩餘部位全出（reason='sell_signal'）
        2. 否則：當日 high 觸發 leg target → 用 max(target, open) 出
        3. 否則：當日 low 觸發 chandelier stop → 用 stop_price 出
        4. 兩個都不觸發 → 持倉
    """

    def __init__(self, entry_date, entry_price: float, shares: int,
                 atr_series: pd.Series, scaling_cfg: dict):
        self.entry_date = entry_date
        self.entry_price = float(entry_price)
        self.original_shares = int(shares)
        self.remaining_shares = int(shares)
        self.atr_series = atr_series
        self.cfg = scaling_cfg

        p2 = scaling_cfg.get("P2_scale_out", {})
        self.legs_cfg = p2.get("legs", [])
        self.trailing_cfg = p2.get("trailing", {})
        self.atr_mult = float(self.trailing_cfg.get("atr_mult", 3.0))

        self.legs_done = 0          # 已觸發的 leg 數（0/1/2）
        self.state = "ARMED"
        self.high_water_mark = float(entry_price)  # chandelier 用：進場後最高價
        self.exit_legs = []         # 已實現的分批出場記錄
        self.last_exit_date = entry_date

    def _leg_target_price(self, leg_idx: int) -> float:
        """第 leg_idx 個 leg 的觸發價（漲 X% 觸發）"""
        profit_pct = float(self.legs_cfg[leg_idx]["profit_pct"])
        return self.entry_price * (1.0 + profit_pct)

    def _chandelier_stop(self, date) -> float:
        """根據 high_water_mark 與當日 ATR 計算 chandelier 停損價。

        若該日無 ATR（前 22 日）回傳 -inf（不觸發）。
        """
        if date not in self.atr_series.index:
            return float("-inf")
        a = self.atr_series.loc[date]
        if pd.isna(a) or a <= 0:
            return float("-inf")
        return self.high_water_mark - self.atr_mult * float(a)

    def _shares_to_sell_for_leg(self, leg_idx: int) -> int:
        """計算第 leg_idx leg 應該賣掉幾股。

        leg_idx=0：原始 1/3（用 round；保證至少 1 股）
        leg_idx=1：剩餘的 1/2（也就是原始 1/3）
        """
        leg = self.legs_cfg[leg_idx]
        if leg_idx == 0:
            # 原始的 fraction（通常 0.333）
            target = int(round(self.original_shares * float(leg["sell_fraction"])))
        else:
            # 賣掉「當下持倉」的 fraction（通常 0.5）
            target = int(round(self.remaining_shares * float(leg["sell_fraction"])))
        # 邊界保護
        target = max(1, min(target, self.remaining_shares))
        return target

    def update(self, date, open_p: float, high: float, low: float,
               sell_signal: bool) -> Optional[dict]:
        """每日呼叫一次。回傳 None 表示不出場，否則回傳 dict。

        回傳：
            {
                "sell_shares": int,
                "exec_price": float,    # 用 raw 價（slip/fee 由外部計算）
                "reason": str,
                "fraction_of_remaining": float,
            }

        外部完成成交後請呼叫 register_exit() 更新內部狀態。
        """
        if self.remaining_shares <= 0:
            return None

        # 更新 high water mark（用當日 high；保守用 high 比 close 接近真實峰值）
        if high > self.high_water_mark:
            self.high_water_mark = float(high)

        # 1) SELL 訊號 → 全出（exit_all 模式）
        if sell_signal:
            mode = self.cfg.get("P2_scale_out", {}).get("sell_signal_mode", "exit_all")
            if mode == "exit_all":
                return {
                    "sell_shares": self.remaining_shares,
                    "exec_price": float(open_p),  # T+1 開盤
                    "reason": "sell_signal",
                    "fraction_of_remaining": 1.0,
                }

        # 2) leg target 觸發（用當日 high 對比）
        if self.legs_done < len(self.legs_cfg):
            target_px = self._leg_target_price(self.legs_done)
            if high >= target_px:
                # 保守：用 max(target, open) 模擬市場已 gap up 的狀況
                exec_px = max(target_px, float(open_p))
                shares = self._shares_to_sell_for_leg(self.legs_done)
                reason = f"profit_target_{self.legs_done + 1}"
                return {
                    "sell_shares": shares,
                    "exec_price": exec_px,
                    "reason": reason,
                    "fraction_of_remaining": shares / self.remaining_shares,
                }

        # 3) chandelier trailing stop（任何時候都判一次：即使前 leg 還沒觸發，
        #    若價格暴跌也應出場以保護資本）
        stop_px = self._chandelier_stop(date)
        if stop_px > float("-inf") and low <= stop_px:
            # 保守：若 open 已 gap down 低於 stop，用 open；否則用 stop
            exec_px = min(stop_px, float(open_p)) if open_p < stop_px else stop_px
            return {
                "sell_shares": self.remaining_shares,
                "exec_price": float(exec_px),
                "reason": "trailing_stop",
                "fraction_of_remaining": 1.0,
            }

        return None

    def register_exit(self, date, sell_shares: int, exec_price: float, reason: str):
        """外部成交完成後呼叫此函式更新內部狀態。"""
        fraction_of_original = sell_shares / self.original_shares if self.original_shares > 0 else 0.0
        self.exit_legs.append({
            "date": date,
            "price": float(exec_price),
            "shares": int(sell_shares),
            "fraction": float(fraction_of_original),
            "reason": reason,
        })
        self.remaining_shares -= int(sell_shares)
        self.last_exit_date = date

        if reason.startswith("profit_target_"):
            self.legs_done += 1
            if self.legs_done >= len(self.legs_cfg):
                self.state = "TRAILING"
            else:
                self.state = f"L{self.legs_done}_DONE"

        if self.remaining_shares <= 0:
            self.state = "CLOSED"


class Backtester:
    def __init__(self, config: BacktestConfig, scaling_cfg: dict | None = None):
        self.config = config
        # scaling 預設關閉，走原邏輯（向下相容 + A/B 對比用）
        self.scaling_cfg = scaling_cfg if scaling_cfg is not None else {"enabled": False}

    def _resolve_end_date(self) -> pd.Timestamp:
        from datetime import date
        end = self.config.end_date
        if end == "today":
            end = date.today().strftime("%Y-%m-%d")
        return pd.Timestamp(end)

    def _filter_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        start = pd.Timestamp(self.config.start_date)
        end = self._resolve_end_date()
        return df[(df.index >= start) & (df.index <= end)]

    def run_per_stock(self, stock_id: str, ohlcv: pd.DataFrame,
                      signals: pd.DataFrame) -> StockResult:
        """單股回測：用全部資金進單一標的，產出單股層指標。
        訊號 T 日，T+1 開盤成交（execution_lag_days=1）。

        若 self.scaling_cfg.get("enabled") == True，啟用分批出場
        （P2_scale_out pattern），否則走原本 BUY/SELL 全進全出邏輯。
        """
        ohlcv = self._filter_dates(ohlcv)
        signals = signals.reindex(ohlcv.index)
        if "action" not in signals.columns:
            return StockResult(stock_id=stock_id)

        scaling_enabled = bool(self.scaling_cfg.get("enabled", False))
        if scaling_enabled:
            return self._run_per_stock_scaling(stock_id, ohlcv, signals)
        return self._run_per_stock_legacy(stock_id, ohlcv, signals)

    def _run_per_stock_legacy(self, stock_id: str, ohlcv: pd.DataFrame,
                              signals: pd.DataFrame) -> StockResult:
        """原本全進全出邏輯（保留作 A/B 對比 baseline）。

        若 signals 含 target_buy / target_tp / target_sl 欄位（且非全 NaN），
        會啟用「限價單機制」：
          - BUY action 配合 target_buy → T+1 limit fill (low ≤ target_buy 才成交)
          - 在倉時 target_tp / target_sl → T+1 OCO 觸發出場
        否則走純舊邏輯（T+1 open 無條件成交）。
        """
        # 偵測是否啟用限價單機制
        has_targets = (
            "target_buy" in signals.columns
            and signals["target_buy"].notna().any()
        )
        if has_targets:
            return self._run_per_stock_limit_orders(stock_id, ohlcv, signals)

        cfg = self.config.fees
        trades = []
        equity_vals = []
        equity_idx = []

        cash = self.config.initial_capital
        shares = 0.0
        entry_price = np.nan
        entry_date = None
        hold_days_count = 0

        n = len(ohlcv)
        for i in range(n):
            date = ohlcv.index[i]
            close_i = ohlcv["close"].iloc[i]

            # 取前一日（T）訊號，今日（T+1）開盤執行
            if i >= self.config.execution_lag_days:
                t_idx = i - self.config.execution_lag_days
                action = signals["action"].iloc[t_idx] if t_idx < len(signals) else "HOLD"
                open_i = ohlcv["open"].iloc[i]

                if action == "BUY" and shares == 0:
                    exec_price = calc_buy_exec_price(open_i, cfg)
                    if exec_price > 0:
                        budget = cash * self.config.max_position_pct
                        cost_per_share_est = exec_price * (1 + cfg["buy_commission_rate"])
                        shares_to_buy = max(1, int(budget / cost_per_share_est))
                        while shares_to_buy > 0 and calc_buy_cost(open_i, shares_to_buy, cfg) > budget:
                            shares_to_buy -= 1
                        total_cost = calc_buy_cost(open_i, shares_to_buy, cfg)
                        if shares_to_buy >= 1 and total_cost <= cash:
                            cash -= total_cost
                            shares = shares_to_buy
                            entry_price = open_i
                            entry_date = date
                            hold_days_count = 0

                elif action == "SELL" and shares > 0:
                    proceeds = calc_sell_proceeds(open_i, shares, cfg)
                    cost_basis = calc_buy_cost(entry_price, shares, cfg)
                    pnl = proceeds - cost_basis
                    pnl_pct = pnl / cost_basis if cost_basis > 0 else 0.0
                    trades.append(TradeRecord(
                        stock_id=stock_id,
                        entry_date=entry_date,
                        exit_date=date,
                        entry_price=entry_price,
                        exit_price=open_i,
                        shares=shares,
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        hold_days=hold_days_count,
                    ))
                    cash += proceeds
                    shares = 0.0
                    entry_price = np.nan
                    entry_date = None
                    hold_days_count = 0

            if shares > 0:
                hold_days_count += 1

            portfolio_value = cash + shares * close_i
            equity_vals.append(portfolio_value)
            equity_idx.append(date)

        equity_curve = pd.Series(equity_vals, index=equity_idx)
        result = StockResult(stock_id=stock_id, trades=trades, equity_curve=equity_curve)
        return result

    def _run_per_stock_limit_orders(self, stock_id: str, ohlcv: pd.DataFrame,
                                     signals: pd.DataFrame) -> StockResult:
        """限價單機制（v0.1）。

        每日 T close 後，從 signals 取得隔日掛單目標：
          - target_buy : 限價買；T+1 low ≤ target_buy 才成交
          - target_tp  : 限價賣（停利）；T+1 high ≥ target_tp 觸發
          - target_sl  : 停損價；T+1 low ≤ target_sl 觸發
          - action="SELL" : 走 fallback（max_hold 到期 / RSI 反轉等）→ T+1 open market sell

        OCO 衝突：同日 high ≥ tp 且 low ≤ sl，假設最壞情況 → 先觸發 SL。
        """
        cfg = self.config.fees
        trades = []
        equity_vals = []
        equity_idx = []

        cash = self.config.initial_capital
        shares = 0
        entry_price = np.nan
        entry_date = None
        hold_days_count = 0

        # 統計成交率
        buy_signals_count = 0
        buy_filled_count = 0

        n = len(ohlcv)
        for i in range(n):
            date = ohlcv.index[i]
            close_i = float(ohlcv["close"].iloc[i])

            if i >= self.config.execution_lag_days:
                t_idx = i - self.config.execution_lag_days
                if t_idx < len(signals):
                    action = signals["action"].iloc[t_idx]
                    target_buy = signals["target_buy"].iloc[t_idx] if "target_buy" in signals.columns else np.nan
                    target_tp = signals["target_tp"].iloc[t_idx] if "target_tp" in signals.columns else np.nan
                    target_sl = signals["target_sl"].iloc[t_idx] if "target_sl" in signals.columns else np.nan
                else:
                    action = "HOLD"
                    target_buy = target_tp = target_sl = np.nan

                open_i = float(ohlcv["open"].iloc[i])
                high_i = float(ohlcv["high"].iloc[i])
                low_i = float(ohlcv["low"].iloc[i])

                # ── 出場處理（在倉中）──
                if shares > 0:
                    fill_price = None
                    reason = None

                    # 1) max_hold timeout / RSI 等其他 SELL 訊號 → 市價 open 賣
                    if action == "SELL":
                        fill_price = open_i
                        reason = "sell_signal"
                    else:
                        # 2) OCO: 檢查 SL 與 TP 是否觸發
                        hit_sl = (not np.isnan(target_sl)) and (low_i <= target_sl)
                        hit_tp = (not np.isnan(target_tp)) and (high_i >= target_tp)

                        if hit_sl and hit_tp:
                            # 同日兩個都觸發 → 假設最壞 SL 先到
                            # 若開盤已 gap down 在 SL 以下 → 用 open；否則用 SL
                            fill_price = open_i if open_i <= target_sl else float(target_sl)
                            reason = "stop_loss_oco"
                        elif hit_sl:
                            fill_price = open_i if open_i <= target_sl else float(target_sl)
                            reason = "stop_loss"
                        elif hit_tp:
                            # 限價賣：開盤已超過 tp → 用 open；否則用 tp
                            fill_price = open_i if open_i >= target_tp else float(target_tp)
                            reason = "take_profit"

                    if fill_price is not None:
                        proceeds = calc_sell_proceeds(fill_price, shares, cfg)
                        cost_basis = calc_buy_cost(entry_price, shares, cfg)
                        pnl = proceeds - cost_basis
                        pnl_pct = pnl / cost_basis if cost_basis > 0 else 0.0
                        trades.append(TradeRecord(
                            stock_id=stock_id,
                            entry_date=entry_date,
                            exit_date=date,
                            entry_price=entry_price,
                            exit_price=fill_price,
                            shares=shares,
                            pnl=pnl,
                            pnl_pct=pnl_pct,
                            hold_days=hold_days_count,
                            exit_legs=[{"date": date, "price": fill_price,
                                          "shares": shares, "fraction": 1.0,
                                          "reason": reason}],
                        ))
                        cash += proceeds
                        shares = 0
                        entry_price = np.nan
                        entry_date = None
                        hold_days_count = 0

                # ── 進場處理（不在倉）──
                if shares == 0 and action == "BUY" and not np.isnan(target_buy):
                    buy_signals_count += 1
                    # buy_mode: 'limit'（預設，跌到 target_buy 才買）vs 'stop'（漲到 target_buy 才買）
                    buy_mode = "limit"
                    if "target_buy_mode" in signals.columns:
                        m = signals["target_buy_mode"].iloc[t_idx]
                        if isinstance(m, str) and m == "stop":
                            buy_mode = "stop"

                    fill_price = None
                    if buy_mode == "limit":
                        # T+1 low ≤ target_buy 才成交
                        if low_i <= target_buy:
                            # 開盤已 gap down → 用 open（更便宜）；否則用 target_buy
                            fill_price = open_i if open_i <= target_buy else float(target_buy)
                    else:  # stop mode（突破型）
                        # T+1 high ≥ target_buy 才成交（價格突破時觸發）
                        if high_i >= target_buy:
                            # 開盤已 gap up 過 target_buy → 用 open（追高）；否則用 target_buy
                            fill_price = open_i if open_i >= target_buy else float(target_buy)

                    if fill_price is not None:
                        exec_price = calc_buy_exec_price(fill_price, cfg)
                        if exec_price > 0:
                            budget = cash * self.config.max_position_pct
                            cost_per_share_est = exec_price * (1 + cfg["buy_commission_rate"])
                            shares_to_buy = max(1, int(budget / cost_per_share_est))
                            while shares_to_buy > 0 and calc_buy_cost(fill_price, shares_to_buy, cfg) > budget:
                                shares_to_buy -= 1
                            total_cost = calc_buy_cost(fill_price, shares_to_buy, cfg)
                            if shares_to_buy >= 1 and total_cost <= cash:
                                cash -= total_cost
                                shares = shares_to_buy
                                entry_price = fill_price
                                entry_date = date
                                hold_days_count = 0
                                buy_filled_count += 1

            if shares > 0:
                hold_days_count += 1

            portfolio_value = cash + shares * close_i
            equity_vals.append(portfolio_value)
            equity_idx.append(date)

        equity_curve = pd.Series(equity_vals, index=equity_idx)
        result = StockResult(stock_id=stock_id, trades=trades, equity_curve=equity_curve)
        # 把 fill rate 統計掛在 result 上（非 dataclass 欄位，動態屬性）
        result.buy_signals_count = buy_signals_count
        result.buy_filled_count = buy_filled_count
        result.fill_rate = (buy_filled_count / buy_signals_count) if buy_signals_count > 0 else float("nan")
        return result

    def _run_per_stock_scaling(self, stock_id: str, ohlcv: pd.DataFrame,
                               signals: pd.DataFrame) -> StockResult:
        """啟用 P2_scale_out 分批出場的版本。"""
        from src.utils import log_error

        cfg = self.config.fees
        trades = []
        equity_vals = []
        equity_idx = []

        cash = self.config.initial_capital
        shares = 0
        entry_price = np.nan
        entry_date = None
        hold_days_count = 0
        manager: Optional[ScalingOutManager] = None

        # 預先算 ATR(22) 一次（不在 manager 內部 rolling）
        atr_period = int(self.scaling_cfg.get("P2_scale_out", {})
                         .get("trailing", {}).get("atr_period", 22))
        try:
            atr_series = _atr(ohlcv, n=atr_period)
        except Exception as e:
            log_error("backtest.scaling", stock_id, f"ATR 計算失敗：{e}")
            atr_series = pd.Series([float("nan")] * len(ohlcv), index=ohlcv.index)

        # 為了在每筆 BUY 後產生「合成 trade」，需追蹤每筆 BUY 的 entry 成本
        entry_cost_basis = 0.0
        accumulated_proceeds = 0.0  # 該筆 BUY 累積收到的賣出 proceeds

        n = len(ohlcv)
        for i in range(n):
            date = ohlcv.index[i]
            close_i = ohlcv["close"].iloc[i]
            high_i = float(ohlcv["high"].iloc[i])
            low_i = float(ohlcv["low"].iloc[i])
            open_i = float(ohlcv["open"].iloc[i])

            if i >= self.config.execution_lag_days:
                t_idx = i - self.config.execution_lag_days
                action = signals["action"].iloc[t_idx] if t_idx < len(signals) else "HOLD"

                # ── 出場處理（持倉中才會走分批邏輯）──
                if shares > 0 and manager is not None:
                    sell_signal = (action == "SELL")
                    decision = manager.update(date, open_i, high_i, low_i, sell_signal)

                    while decision is not None and shares > 0:
                        sell_n = int(decision["sell_shares"])
                        exec_px = float(decision["exec_price"])
                        reason = decision["reason"]
                        if sell_n > shares:
                            sell_n = shares
                        if sell_n <= 0:
                            break
                        proceeds = calc_sell_proceeds(exec_px, sell_n, cfg)
                        cash += proceeds
                        accumulated_proceeds += proceeds
                        shares -= sell_n
                        manager.register_exit(date, sell_n, exec_px, reason)

                        # 若還有剩，且觸發是 leg target，可能同日 chandelier 也觸發
                        # （但同一日只允許一個 leg 觸發 + 不再追 chandelier，否則會雙重出場）
                        # → 直接 break，留待下一日再判斷
                        decision = None

                    if shares == 0:
                        # 整筆 BUY 結束，產生合成 TradeRecord
                        legs = list(manager.exit_legs)
                        n_partials = len(legs)
                        # weighted avg exit price（用股數加權）
                        total_exit_shares = sum(l["shares"] for l in legs)
                        if total_exit_shares > 0:
                            wavg_exit_px = sum(l["price"] * l["shares"] for l in legs) / total_exit_shares
                        else:
                            wavg_exit_px = float("nan")
                        pnl = accumulated_proceeds - entry_cost_basis
                        pnl_pct = pnl / entry_cost_basis if entry_cost_basis > 0 else 0.0
                        last_exit_date = legs[-1]["date"] if legs else date
                        trades.append(TradeRecord(
                            stock_id=stock_id,
                            entry_date=entry_date,
                            exit_date=last_exit_date,
                            entry_price=float(entry_price),
                            exit_price=float(wavg_exit_px),
                            shares=manager.original_shares,
                            pnl=pnl,
                            pnl_pct=pnl_pct,
                            hold_days=hold_days_count,
                            n_partials=n_partials,
                            exit_legs=legs,
                        ))
                        entry_price = np.nan
                        entry_date = None
                        hold_days_count = 0
                        entry_cost_basis = 0.0
                        accumulated_proceeds = 0.0
                        manager = None

                # ── 進場處理（無持倉才買）──
                if action == "BUY" and shares == 0:
                    exec_price = calc_buy_exec_price(open_i, cfg)
                    if exec_price > 0:
                        budget = cash * self.config.max_position_pct
                        cost_per_share_est = exec_price * (1 + cfg["buy_commission_rate"])
                        shares_to_buy = max(1, int(budget / cost_per_share_est))
                        while shares_to_buy > 0 and calc_buy_cost(open_i, shares_to_buy, cfg) > budget:
                            shares_to_buy -= 1
                        total_cost = calc_buy_cost(open_i, shares_to_buy, cfg)
                        if shares_to_buy >= 1 and total_cost <= cash:
                            cash -= total_cost
                            shares = shares_to_buy
                            entry_price = open_i
                            entry_date = date
                            hold_days_count = 0
                            entry_cost_basis = total_cost
                            accumulated_proceeds = 0.0
                            manager = ScalingOutManager(
                                entry_date=date,
                                entry_price=open_i,
                                shares=shares_to_buy,
                                atr_series=atr_series,
                                scaling_cfg=self.scaling_cfg,
                            )

            if shares > 0:
                hold_days_count += 1

            portfolio_value = cash + shares * close_i
            equity_vals.append(portfolio_value)
            equity_idx.append(date)

        # 若回測結束時仍持倉，依最後一日收盤價強制平倉（記為 sell_signal-flush）
        if shares > 0 and manager is not None and len(ohlcv) > 0:
            last_date = ohlcv.index[-1]
            last_close = float(ohlcv["close"].iloc[-1])
            proceeds = calc_sell_proceeds(last_close, shares, cfg)
            cash += proceeds
            accumulated_proceeds += proceeds
            manager.register_exit(last_date, shares, last_close, "sell_signal")
            shares = 0
            legs = list(manager.exit_legs)
            n_partials = len(legs)
            total_exit_shares = sum(l["shares"] for l in legs)
            wavg_exit_px = (sum(l["price"] * l["shares"] for l in legs) / total_exit_shares
                            if total_exit_shares > 0 else float("nan"))
            pnl = accumulated_proceeds - entry_cost_basis
            pnl_pct = pnl / entry_cost_basis if entry_cost_basis > 0 else 0.0
            trades.append(TradeRecord(
                stock_id=stock_id,
                entry_date=entry_date,
                exit_date=last_date,
                entry_price=float(entry_price),
                exit_price=float(wavg_exit_px),
                shares=manager.original_shares,
                pnl=pnl,
                pnl_pct=pnl_pct,
                hold_days=hold_days_count,
                n_partials=n_partials,
                exit_legs=legs,
            ))

        equity_curve = pd.Series(equity_vals, index=equity_idx)
        result = StockResult(stock_id=stock_id, trades=trades, equity_curve=equity_curve)
        return result

    def run_portfolio(self, ohlcv_dict: dict, signals_dict: dict,
                      sizing_fn: Callable,
                      benchmark_cagr: Optional[float] = None) -> PortfolioResult:
        """組合回測：依 sizing_fn 決定每日持倉，記錄 daily equity curve。

        Args:
            ohlcv_dict: {stock_id: OHLCV DataFrame}
            signals_dict: {stock_id: signals DataFrame（含 action 欄）}
            sizing_fn: callable(date, signals_dict, cash, ohlcv_dict, params) → {stock_id: target_shares}
            benchmark_cagr: 用於計算 alpha

        Returns:
            PortfolioResult
        """
        # 取所有股票的聯集日期
        all_dates = sorted(set(
            d for df in ohlcv_dict.values()
            for d in self._filter_dates(df).index
        ))
        all_dates = [d for d in all_dates
                     if d >= pd.Timestamp(self.config.start_date)
                     and d <= self._resolve_end_date()]
        if not all_dates:
            return PortfolioResult(benchmark_cagr=benchmark_cagr or float("nan"))

        cfg = self.config.fees
        cash = self.config.initial_capital
        holdings = {}   # {stock_id: shares}
        stock_results = {sid: StockResult(stock_id=sid) for sid in ohlcv_dict}

        # 追蹤每筆 per-stock 交易
        entry_info = {}  # {stock_id: (entry_date, entry_price, shares)}

        equity_vals = []
        equity_idx = []
        holdings_history = {}  # P0-13: {date: {sid: shares}}

        for i, date in enumerate(all_dates):
            # 取前一日訊號（T+1 成交）
            prev_date = all_dates[i - 1] if i > 0 else None

            # sizing_fn 依 T 日訊號決定目標持倉
            if prev_date is not None:
                target = sizing_fn(prev_date, signals_dict, cash, ohlcv_dict, holdings)
            else:
                target = {}

            # 執行調倉
            for sid, target_shares in target.items():
                if sid not in ohlcv_dict:
                    continue
                df_s = ohlcv_dict[sid]
                if date not in df_s.index:
                    continue
                open_price = df_s.loc[date, "open"]
                current_shares = holdings.get(sid, 0)

                if target_shares > current_shares:
                    # 買入
                    add_shares = target_shares - current_shares
                    cost = calc_buy_cost(open_price, add_shares, cfg)
                    if cost <= cash:
                        cash -= cost
                        holdings[sid] = holdings.get(sid, 0) + add_shares
                        if sid not in entry_info:
                            entry_info[sid] = (date, open_price, add_shares)

                elif target_shares < current_shares:
                    # 賣出
                    sell_shares = current_shares - target_shares
                    proceeds = calc_sell_proceeds(open_price, sell_shares, cfg)
                    cash += proceeds
                    holdings[sid] = holdings.get(sid, 0) - sell_shares
                    if holdings[sid] <= 0:
                        holdings.pop(sid, None)
                        # 記錄交易
                        if sid in entry_info:
                            e_date, e_price, e_shares = entry_info.pop(sid)
                            cost_basis = calc_buy_cost(e_price, e_shares, cfg)
                            pnl = proceeds - cost_basis
                            pnl_pct = pnl / cost_basis if cost_basis > 0 else 0.0
                            hold_d = (date - e_date).days
                            stock_results[sid].trades.append(TradeRecord(
                                stock_id=sid,
                                entry_date=e_date,
                                exit_date=date,
                                entry_price=e_price,
                                exit_price=open_price,
                                shares=e_shares,
                                pnl=pnl,
                                pnl_pct=pnl_pct,
                                hold_days=max(hold_d, 1),
                            ))

            # 當日 equity（持倉用收盤價；若當日無資料，用最近一個有效收盤價）
            portfolio_value = cash
            for sid, sh in holdings.items():
                df_s = ohlcv_dict[sid]
                if date in df_s.index:
                    portfolio_value += sh * df_s.loc[date, "close"]
                else:
                    # 股票今日無資料（假日/停牌/資料缺口）→ 用最後一個有效收盤價估值
                    sub = df_s[df_s.index < date]
                    if len(sub) > 0:
                        portfolio_value += sh * sub["close"].iloc[-1]
            equity_vals.append(portfolio_value)
            equity_idx.append(date)
            holdings_history[date] = dict(holdings)  # P0-13: 快照當日持倉

        equity_curve = pd.Series(equity_vals, index=equity_idx)

        # P0-1 修正：portfolio mode 下不把整體 equity_curve 塞進每檔 per-stock result
        # 每檔的 MaxDD / in_market_cagr 由各自的 trades 計算，equity_curve 留空
        # （組合 equity_curve 只存在 PortfolioResult 層）

        return PortfolioResult(
            equity_curve=equity_curve,
            stock_results=stock_results,
            benchmark_cagr=benchmark_cagr if benchmark_cagr is not None else float("nan"),
            holdings_history=holdings_history,
        )
