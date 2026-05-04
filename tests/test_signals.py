# Phase 2 訊號層測試
# 跑法：python.exe -m pytest tests/test_signals.py -v
import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.signals.regime import detect_regime
from src.strategy.signals.style1_pullback import generate_signals
from src.strategy.signals.style2_momentum import rank_universe

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

import yaml
_cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "strategy.yaml")
with open(_cfg_path, "r", encoding="utf-8") as _f:
    _STRATEGY = yaml.safe_load(_f)
STYLE1_PARAMS = _STRATEGY["style1_pullback"]


def make_ohlcv(n: int = 600, trend: str = "up", seed: int = 0) -> pd.DataFrame:
    """合成 OHLCV，trend='up'/'down'/'flat'"""
    rng = np.random.default_rng(seed)
    if trend == "up":
        drift = 0.0005
    elif trend == "down":
        drift = -0.0005
    else:
        drift = 0.0
    ret = rng.normal(drift, 0.012, n)
    close = 100.0 * np.cumprod(1 + ret)
    high = close * (1 + rng.uniform(0.002, 0.015, n))
    low = close * (1 - rng.uniform(0.002, 0.015, n))
    open_ = close * (1 + rng.normal(0, 0.005, n))
    volume = rng.integers(500_000, 5_000_000, n).astype(float)
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


def make_crash_then_recover(n: int = 2520) -> pd.DataFrame:
    """模擬含 crash 的走勢（用於 regime 測試，2520 交易日 ≈ 10 年）"""
    rng = np.random.default_rng(99)
    ret = rng.normal(0.0003, 0.012, n)
    # 在 1500-1600 模擬 crash（-50% 累積）
    ret[1500:1600] = -0.008
    close = 100.0 * np.cumprod(1 + ret)
    high = close * (1 + rng.uniform(0.002, 0.015, n))
    low = close * (1 - rng.uniform(0.002, 0.015, n))
    open_ = close * (1 + rng.normal(0, 0.005, n))
    volume = rng.integers(500_000, 5_000_000, n).astype(float)
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


# ── Regime 測試 ──────────────────────────────────────────────

def test_regime_bull_dominant_in_uptrend():
    """長期上漲序列中，大部分時間應為 BULL"""
    df = make_ohlcv(1000, "up")
    regime = detect_regime(df)
    valid = regime.dropna()
    bull_ratio = (valid == "BULL").mean()
    # MA200 需 200 日暖機，1000 日含暖機期後 BULL 佔 25%+ 合理
    assert bull_ratio > 0.25, f"上漲序列 BULL 比例 {bull_ratio:.1%} 太低"


def test_regime_bear_in_downtrend():
    """持續下跌序列中，後期應出現 BEAR"""
    df = make_ohlcv(1000, "down")
    regime = detect_regime(df)
    valid = regime.dropna()
    bear_ratio = (valid == "BEAR").mean()
    assert bear_ratio > 0.3, f"下跌序列 BEAR 比例 {bear_ratio:.1%} 太低"


def test_regime_crash_detected():
    """模擬 crash 後 regime 應出現 BEAR"""
    df = make_crash_then_recover(2520)
    regime = detect_regime(df)
    # crash 在 1500-1600，稍後 MA200 會反映，1700 之後應有 BEAR
    post_crash = regime.iloc[1700:1900]
    assert (post_crash == "BEAR").any(), "Crash 後應偵測到 BEAR regime"


def test_regime_only_bull_bear():
    """Regime 值只有 'BULL' 或 'BEAR'"""
    df = make_ohlcv(500)
    regime = detect_regime(df)
    assert set(regime.unique()).issubset({"BULL", "BEAR"})


# ── Style 1 進場/出場邏輯測試 ────────────────────────────────

def test_style1_buy_count_reasonable():
    """10 年資料 BUY 訊號數量應 < 100（不過頻繁）"""
    df = make_ohlcv(2520, "up")
    regime = detect_regime(df)
    signals = generate_signals(df, regime, STYLE1_PARAMS)
    buy_count = (signals["action"] == "BUY").sum()
    assert buy_count < 100, f"BUY 訊號 {buy_count} 筆，過於頻繁"
    assert buy_count >= 1, "上漲趨勢中應至少產生 1 筆 BUY"


def test_style1_no_consecutive_buys():
    """不應連續兩個 BUY（進場後要先出場才能再買）"""
    df = make_ohlcv(2520, "up")
    regime = detect_regime(df)
    signals = generate_signals(df, regime, STYLE1_PARAMS)
    actions = signals["action"].values
    for i in range(1, len(actions)):
        assert not (actions[i] == "BUY" and actions[i - 1] == "BUY"), \
            f"位置 {i} 出現連續 BUY"


def test_style1_sell_follows_buy():
    """每個 BUY 之後必須有對應 SELL（最終持倉除外）"""
    df = make_ohlcv(2520, "up")
    regime = detect_regime(df)
    signals = generate_signals(df, regime, STYLE1_PARAMS)
    actions = signals["action"].values
    in_pos = False
    for i, a in enumerate(actions):
        if a == "BUY":
            assert not in_pos, f"位置 {i}：已在持倉中又出現 BUY"
            in_pos = True
        elif a == "SELL":
            assert in_pos, f"位置 {i}：無持倉卻出現 SELL"
            in_pos = False


def test_style1_output_columns():
    """輸出欄位符合規格"""
    df = make_ohlcv(300)
    regime = detect_regime(df)
    signals = generate_signals(df, regime, STYLE1_PARAMS)
    required = ["action", "entry_low", "entry_high", "stop_loss", "reason"]
    for col in required:
        assert col in signals.columns, f"缺少欄位 {col}"
    assert set(signals["action"].unique()).issubset({"BUY", "SELL", "HOLD"})


def test_style1_entry_range_valid():
    """BUY 訊號的 entry_low ≤ entry_high"""
    df = make_ohlcv(2520, "up")
    regime = detect_regime(df)
    signals = generate_signals(df, regime, STYLE1_PARAMS)
    buys = signals[signals["action"] == "BUY"]
    if len(buys) == 0:
        pytest.skip("無 BUY 訊號可驗證")
    assert (buys["entry_low"] <= buys["entry_high"]).all(), "BUY 的 entry_low > entry_high"


def test_style1_stop_loss_below_close():
    """BUY 訊號的 stop_loss 應低於 close（否則立刻出場沒意義）"""
    df = make_ohlcv(2520, "up")
    regime = detect_regime(df)
    signals = generate_signals(df, regime, STYLE1_PARAMS)
    buys = signals[signals["action"] == "BUY"]
    if len(buys) == 0:
        pytest.skip("無 BUY 訊號可驗證")
    close_at_buy = df.loc[buys.index, "close"]
    invalid = (buys["stop_loss"] >= close_at_buy).sum()
    assert invalid == 0, f"{invalid} 筆 BUY 的 stop_loss >= close"


# ── Style 2 動量排序測試 ─────────────────────────────────────

def test_style2_rank_order():
    """rank 應按 momentum_score 降冪排列"""
    n = 350
    dfs = {str(i): make_ohlcv(n, seed=i) for i in range(5)}
    asof = pd.Timestamp("2016-06-01")
    params = _STRATEGY["style2_momentum"]
    result = rank_universe(dfs, asof, params)
    if len(result) < 2:
        pytest.skip("動量分數不足 2 筆")
    scores = result["momentum_score"].values
    assert (np.diff(scores) <= 0).all(), "rank 排序不正確"


def test_style2_no_future_data():
    """asof_date 之後的資料不應影響結果（時間防穿越）"""
    n = 350
    df = make_ohlcv(n, seed=1)
    dfs = {"A": df}
    asof = pd.Timestamp("2016-01-01")
    params = _STRATEGY["style2_momentum"]

    result1 = rank_universe(dfs, asof, params)
    # 在 asof 之後插入異常值
    df_hack = df.copy()
    future_idx = df_hack.index > asof
    df_hack.loc[future_idx, "close"] = 99999.0
    dfs_hack = {"A": df_hack}
    result2 = rank_universe(dfs_hack, asof, params)

    if len(result1) == 0 or len(result2) == 0:
        pytest.skip("無足夠資料計算動量")
    assert abs(result1["momentum_score"].iloc[0] - result2["momentum_score"].iloc[0]) < 1e-9, \
        "修改 asof 之後的資料影響了結果 → look-ahead bug"


# ── 訊號 CSV 輸出（Phase 2 通過條件：至少 5 BUY + 5 SELL） ──

def test_phase2_output_csv():
    """對合成上漲趨勢資料跑 10 年回測，輸出含 ≥5 BUY + ≥5 SELL 的 CSV"""
    df = make_ohlcv(2520, "up", seed=7)
    regime = detect_regime(df)
    signals = generate_signals(df, regime, STYLE1_PARAMS)

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "signals_phase2_check.csv")
    signals.to_csv(out_path, encoding="utf-8-sig")

    buy_count = (signals["action"] == "BUY").sum()
    sell_count = (signals["action"] == "SELL").sum()
    assert buy_count >= 5, f"BUY 只有 {buy_count} 筆（需要 ≥5）"
    assert sell_count >= 5, f"SELL 只有 {sell_count} 筆（需要 ≥5）"
    assert os.path.exists(out_path), "CSV 未產出"
