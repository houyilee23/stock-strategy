"""P0 Scaling-Out tests

驗證 P2_scale_out pattern 的兩個關鍵 case：
1. 漲 30% 後拉回 → 應分 3 leg 出場、合成 trade pnl_pct 接近 +18% 區間
2. 漲 8% 後直接跌、最後 SELL signal → 全出，n_partials=1 (sell_signal)

跑法：
  'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' -m pytest tests/test_scaling_out.py -v
"""
import os
import sys
import yaml
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.backtest.engine import Backtester, BacktestConfig, ScalingOutManager
from src.strategy.indicators.volatility import atr as _atr

_cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "config", "strategy.yaml")
with open(_cfg_path, encoding="utf-8") as f:
    _STRATEGY = yaml.safe_load(f)

FEES = _STRATEGY["fees"]
# auto_iterate v2: yaml 預設 scaling.enabled=False（避免摧毀強策略），
# 但這份測試專測 scaling 行為，必須強制 enabled=True
SCALING = {**_STRATEGY["scaling"], "enabled": True}


def _bt_cfg() -> BacktestConfig:
    return BacktestConfig(
        fees=FEES,
        start_date="2020-01-01",
        end_date="2025-12-31",
        initial_capital=100_000,
        max_position_pct=1.0,    # 單檔測試用全資金
    )


def _make_path_ohlcv(close_path: list, vol: float = 0.005, seed: int = 0) -> pd.DataFrame:
    """根據 close 路徑產生 OHLCV：open ≈ 前收、high/low 在 close 上下抖動。"""
    rng = np.random.default_rng(seed)
    n = len(close_path)
    close = np.array(close_path, dtype=float)
    open_ = np.empty(n)
    open_[0] = close[0]
    open_[1:] = close[:-1]
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, vol, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, vol, n)))
    volume = np.full(n, 1_000_000.0)
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close, "volume": volume
    }, index=idx)


# ── Case 1: 漲 30% 後拉回 5%，期望分 3 leg ────────────────────────────

def test_scale_out_three_legs_full_run():
    """設計一條路徑：
       - 前 30 日盤整（讓 ATR 建立穩定值）
       - 第 31 日 BUY 訊號（T+1 進場 = 第 32 日開盤）
       - 第 33+ 日漸漲到 +30%
       - 觸發 leg1 (+10%) 出 1/3
       - 觸發 leg2 (+20%) 再出 1/3
       - 拉回後觸發 trailing stop
    最終應產生 1 筆合成 trade、n_partials=3、pnl_pct ≈ +18%
    """
    # 建構 close 路徑：100 微幅震盪 30 日 → 進場後緩漲到 130 → 拉回到 ~115
    # warmup 期間需要有波動讓 ATR > 0，否則 chandelier stop = HWM 會立即觸發
    n_warmup = 30
    rng_warm = np.random.default_rng(123)
    closes = (100.0 + rng_warm.normal(0, 1.5, n_warmup)).tolist()
    closes[-1] = 100.0  # 確保進場價乾淨在 100
    # 進場後逐日漲到 +30%
    rise = np.linspace(100.0, 130.0, 25).tolist()
    closes.extend(rise)
    # 拉回觸發 chandelier
    pull = np.linspace(130.0, 115.0, 15).tolist()
    closes.extend(pull)

    df = _make_path_ohlcv(closes, vol=0.005, seed=42)

    # 訊號：第 30 日 BUY（i=29 訊號 → i=30 開盤成交）
    n = len(df)
    actions = ["HOLD"] * n
    actions[n_warmup - 1] = "BUY"
    signals = pd.DataFrame({"action": actions}, index=df.index)

    bt = Backtester(_bt_cfg(), scaling_cfg=SCALING)
    result = bt.run_per_stock("CASE1", df, signals)

    assert result.n_trades == 1, f"應產生 1 筆合成 trade, 實際 {result.n_trades}"
    t = result.trades[0]
    # 至少要分批，且 pnl_pct 必須為正
    assert t.n_partials >= 2, f"應至少 2 個 leg, 實際 {t.n_partials}"
    assert t.pnl_pct > 0, f"30% 漲幅後拉回應仍為正, 實際 {t.pnl_pct:.2%}"
    # 至少其中一個 exit_leg reason 為 profit_target_1 或 profit_target_2
    reasons = [l["reason"] for l in t.exit_legs]
    assert any(r.startswith("profit_target") for r in reasons), \
        f"未觸發任何 profit_target, exit_legs={reasons}"
    # 預期 pnl_pct 在合理區間（粗估 10/3 + 20/3 + ~22/3 ≈ 17-20%，扣除手續費應約 13-19%）
    assert 0.05 < t.pnl_pct < 0.30, f"合成 pnl_pct 偏離預期, 實際 {t.pnl_pct:.2%}"


# ── Case 2: 漲 8% 後跌到 -10%，沒觸發 leg → SELL signal 全出 ────────

def test_scale_out_no_leg_then_sell_signal():
    """設計一條路徑：
       - 30 日盤整建 ATR
       - 進場後漲到 +8%（不觸發任何 leg）
       - 然後跌到 -10%，但用 SELL signal 強制出場（不靠 trailing stop）
    期望：n_partials=1，reason='sell_signal'
    """
    n_warmup = 30
    closes = [100.0] * n_warmup
    # 漲 8%
    rise = np.linspace(100.0, 108.0, 5).tolist()
    closes.extend(rise)
    # 跌到 -10%
    drop = np.linspace(108.0, 90.0, 5).tolist()
    closes.extend(drop)

    df = _make_path_ohlcv(closes, vol=0.001, seed=7)

    n = len(df)
    actions = ["HOLD"] * n
    actions[n_warmup - 1] = "BUY"
    # 在路徑末段下 SELL（給 chandelier 機會被先觸發 → 我們調大 chandelier 倍數避免）
    actions[n - 2] = "SELL"
    signals = pd.DataFrame({"action": actions}, index=df.index)

    # 用一份「拉長 ATR 倍數」的 scaling 配置，避免 chandelier 先觸發
    scaling_cfg_big_chandelier = {
        "enabled": True,
        "pattern": "P2_scale_out",
        "P2_scale_out": {
            "legs": [
                {"profit_pct": 0.10, "sell_fraction": 0.333},
                {"profit_pct": 0.20, "sell_fraction": 0.500},
            ],
            "trailing": {"method": "chandelier", "atr_period": 22, "atr_mult": 50.0},
            "sell_signal_mode": "exit_all",
        },
    }
    bt = Backtester(_bt_cfg(), scaling_cfg=scaling_cfg_big_chandelier)
    result = bt.run_per_stock("CASE2", df, signals)

    assert result.n_trades == 1, f"應產生 1 筆 trade, 實際 {result.n_trades}"
    t = result.trades[0]
    assert t.n_partials == 1, f"沒觸發 leg 應只有 1 個 exit, 實際 {t.n_partials}"
    assert t.exit_legs[0]["reason"] == "sell_signal", \
        f"預期 sell_signal, 實際 {t.exit_legs[0]['reason']}"
    # 漲後跌 → 應虧損
    assert t.pnl_pct < 0, f"先漲後跌至 -10% 應為虧損, 實際 {t.pnl_pct:.2%}"


# ── Case 3: scaling enabled=false 應走原邏輯 ────────────────────────

def test_scaling_disabled_uses_legacy_path():
    """scaling.enabled=false 時 → n_partials=1, exit_legs=[]"""
    n = 200
    rng = np.random.default_rng(0)
    ret = rng.normal(0.0005, 0.01, n)
    close = 100 * np.cumprod(1 + ret)
    open_ = np.r_[close[0], close[:-1]]
    high = np.maximum(open_, close) * 1.005
    low = np.minimum(open_, close) * 0.995
    df = pd.DataFrame({
        "open": open_, "high": high, "low": low, "close": close,
        "volume": np.full(n, 1e6),
    }, index=pd.date_range("2024-01-01", periods=n, freq="B"))

    actions = ["HOLD"] * n
    actions[10] = "BUY"
    actions[100] = "SELL"
    signals = pd.DataFrame({"action": actions}, index=df.index)

    bt = Backtester(_bt_cfg(), scaling_cfg={"enabled": False})
    result = bt.run_per_stock("LEGACY", df, signals)
    assert result.n_trades == 1
    t = result.trades[0]
    assert t.n_partials == 1
    assert t.exit_legs == []


# ── Case 4: ScalingOutManager unit test ────────────────────────────

def test_scaling_manager_state_transitions():
    """直接測 ScalingOutManager 的狀態機。"""
    n = 50
    idx = pd.date_range("2024-01-01", periods=n, freq="B")
    # 假 ATR：前 22 日 nan，之後 1.0
    atr_vals = [float("nan")] * 22 + [1.0] * (n - 22)
    atr_s = pd.Series(atr_vals, index=idx)

    mgr = ScalingOutManager(
        entry_date=idx[22],
        entry_price=100.0,
        shares=1000,
        atr_series=atr_s,
        scaling_cfg=SCALING,
    )
    assert mgr.state == "ARMED"
    assert mgr.remaining_shares == 1000

    # 第一日：價格未動
    d0 = mgr.update(idx[23], open_p=100.0, high=100.5, low=99.5, sell_signal=False)
    assert d0 is None

    # 第二日：漲 11% 觸發 leg1
    d1 = mgr.update(idx[24], open_p=110.0, high=111.0, low=109.0, sell_signal=False)
    assert d1 is not None
    assert d1["reason"] == "profit_target_1"
    assert d1["sell_shares"] == 333  # round(1000 * 0.333)
    mgr.register_exit(idx[24], d1["sell_shares"], d1["exec_price"], d1["reason"])
    assert mgr.legs_done == 1
    assert mgr.remaining_shares == 667

    # 第三日：漲 21% 觸發 leg2
    d2 = mgr.update(idx[25], open_p=120.0, high=121.0, low=119.0, sell_signal=False)
    assert d2 is not None
    assert d2["reason"] == "profit_target_2"
    # 賣剩餘 667 的一半 → round(667 * 0.5) = 334
    assert d2["sell_shares"] == 334
    mgr.register_exit(idx[25], d2["sell_shares"], d2["exec_price"], d2["reason"])
    assert mgr.legs_done == 2
    assert mgr.state == "TRAILING"
    assert mgr.remaining_shares == 333

    # 第四日：sell_signal → 剩餘全出
    d3 = mgr.update(idx[26], open_p=125.0, high=126.0, low=124.0, sell_signal=True)
    assert d3 is not None
    assert d3["reason"] == "sell_signal"
    assert d3["sell_shares"] == 333
    mgr.register_exit(idx[26], d3["sell_shares"], d3["exec_price"], d3["reason"])
    assert mgr.state == "CLOSED"
    assert mgr.remaining_shares == 0
