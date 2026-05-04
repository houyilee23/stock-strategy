from dataclasses import dataclass, field
import pandas as pd


@dataclass
class TradeRecord:
    stock_id: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: float
    pnl: float          # 含手續費的淨損益
    pnl_pct: float      # 報酬率（相對 entry cost）
    hold_days: int      # 交易日數
    # P0 scaling-out：分批出場資訊（向下相容，預設 1 leg）
    n_partials: int = 1
    exit_legs: list = field(default_factory=list)
    # exit_legs 元素：{date, price, shares, fraction, reason}
    #   reason ∈ {"profit_target_1", "profit_target_2", "trailing_stop", "sell_signal"}


@dataclass
class StockResult:
    stock_id: str
    trades: list = field(default_factory=list)  # List[TradeRecord]
    equity_curve: pd.Series = field(default_factory=pd.Series)

    @property
    def n_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return float("nan")
        wins = sum(1 for t in self.trades if t.pnl > 0)
        return wins / len(self.trades)

    @property
    def avg_win(self) -> float:
        wins = [t.pnl_pct for t in self.trades if t.pnl > 0]
        return sum(wins) / len(wins) if wins else 0.0

    @property
    def avg_loss(self) -> float:
        losses = [t.pnl_pct for t in self.trades if t.pnl <= 0]
        return sum(losses) / len(losses) if losses else 0.0

    @property
    def expectancy(self) -> float:
        wr = self.win_rate
        if pd.isna(wr):
            return float("nan")
        return wr * self.avg_win + (1 - wr) * self.avg_loss

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        if gross_loss == 0:
            return float("inf")
        return gross_profit / gross_loss

    @property
    def max_drawdown(self) -> float:
        if self.equity_curve.empty:
            return float("nan")
        cummax = self.equity_curve.cummax()
        dd = (self.equity_curve - cummax) / cummax
        return dd.min()

    @property
    def in_market_cagr(self) -> float:
        """持倉期間年化報酬（分母只算持倉交易日數，用幾何複利）。
        若總持倉不足 21 交易日（約 1 個月），年化無統計意義，回傳 NaN。
        """
        if not self.trades:
            return float("nan")
        total_hold = sum(t.hold_days for t in self.trades)
        # 最少需 21 個交易日才有意義（避免短期 CAGR 爆炸）
        if total_hold < 21:
            return float("nan")
        years = total_hold / 252
        # 幾何複利（不用加法近似）
        compound = 1.0
        for t in self.trades:
            compound *= (1.0 + t.pnl_pct)
        if compound <= 0:
            return float("nan")
        return compound ** (1.0 / years) - 1

    @property
    def avg_hold_days(self) -> float:
        if not self.trades:
            return float("nan")
        return sum(t.hold_days for t in self.trades) / len(self.trades)

    @property
    def annual_trade_count(self) -> float:
        if not self.trades:
            return float("nan")
        all_dates = [t.entry_date for t in self.trades]
        years = (max(all_dates) - min(all_dates)).days / 365
        return len(self.trades) / max(years, 1)


@dataclass
class PortfolioResult:
    equity_curve: pd.Series = field(default_factory=pd.Series)
    stock_results: dict = field(default_factory=dict)  # {stock_id: StockResult}
    benchmark_cagr: float = float("nan")
    holdings_history: dict = field(default_factory=dict)  # {date: {sid: shares}}

    @property
    def cagr(self) -> float:
        if self.equity_curve.empty or len(self.equity_curve) < 2:
            return float("nan")
        start = self.equity_curve.iloc[0]
        end = self.equity_curve.iloc[-1]
        years = (self.equity_curve.index[-1] - self.equity_curve.index[0]).days / 365
        if years <= 0 or start <= 0:
            return float("nan")
        return (end / start) ** (1 / years) - 1

    @property
    def max_drawdown(self) -> float:
        if self.equity_curve.empty:
            return float("nan")
        cummax = self.equity_curve.cummax()
        dd = (self.equity_curve - cummax) / cummax
        return dd.min()

    @property
    def sharpe(self) -> float:
        if self.equity_curve.empty or len(self.equity_curve) < 2:
            return float("nan")
        daily_ret = self.equity_curve.pct_change().dropna()
        if daily_ret.std() == 0:
            return float("nan")
        return daily_ret.mean() / daily_ret.std() * (252 ** 0.5)

    @property
    def alpha(self) -> float:
        if pd.isna(self.cagr) or pd.isna(self.benchmark_cagr):
            return float("nan")
        return self.cagr - self.benchmark_cagr

    @property
    def in_market_pct(self) -> float:
        """資金利用率（有持倉的日數 / 總日數）"""
        if not self.stock_results:
            return float("nan")
        total_days = len(self.equity_curve)
        if total_days == 0:
            return float("nan")
        in_market_days = sum(
            t.hold_days for sr in self.stock_results.values() for t in sr.trades
        )
        return in_market_days / (total_days * max(len(self.stock_results), 1))

    @property
    def in_market_cagr(self) -> float:
        """P0-13：只計算有持倉日的年化報酬率。
        分母只算 portfolio 有持倉的交易日，還原資金閒置對報酬的稀釋效果。
        最少需 21 個交易日（約 1 個月）才有統計意義，否則回傳 NaN。
        """
        if self.equity_curve.empty or not self.holdings_history:
            return float("nan")
        eq = self.equity_curve
        # 每個日期是否有持倉（holdings_history[date] 非空字典即為有持倉）
        in_market_mask = pd.Series(
            [bool(self.holdings_history.get(d, {})) for d in eq.index],
            index=eq.index,
        )
        in_market_days = int(in_market_mask.sum())
        if in_market_days < 21:
            return float("nan")
        # 只取有持倉日的每日報酬，幾何複利累積後年化
        daily_ret = eq.pct_change().fillna(0)
        in_market_ret = daily_ret[in_market_mask]
        total_growth = (1 + in_market_ret).prod()
        if total_growth <= 0:
            return float("nan")
        years = in_market_days / 252
        return float(total_growth ** (1 / years) - 1)
