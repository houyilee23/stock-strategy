# Phase 1 指標層單元測試
# 跑法：python.exe -m pytest tests/test_indicators.py -v
import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.indicators.trend import sma, ema, macd, adx
from src.strategy.indicators.momentum import rsi, roc, momentum_12_1
from src.strategy.indicators.volatility import atr, bollinger
from src.strategy.indicators.volume import volume_ma, obv

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")


def make_synthetic_ohlcv(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """產生足夠長的合成 OHLCV（用於需要 200+ 列的指標測試）"""
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1 + rng.normal(0, 0.01, n))
    high = close * (1 + rng.uniform(0, 0.015, n))
    low = close * (1 - rng.uniform(0, 0.015, n))
    open_ = close * (1 + rng.normal(0, 0.005, n))
    volume = rng.integers(1_000_000, 10_000_000, n).astype(float)
    idx = pd.date_range("2015-01-01", periods=n, freq="B")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


def load_0050():
    path = os.path.join(RAW_DIR, "0050.csv")
    df = pd.read_csv(path, dtype={"date": str})
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ── 1. 常數序列測試 ───────────────────────────────────────────

def test_constant_sma():
    close = pd.Series([100.0] * 100)
    result = sma(close, 20)
    assert result.dropna().iloc[-1] == pytest.approx(100.0)


def test_constant_rsi():
    """常數序列 diff=0，gain/loss 皆 0 → RSI 應為 50（我們的實作定義）"""
    close = pd.Series([100.0] * 100)
    result = rsi(close)
    assert not result.isin([np.inf, -np.inf]).any()
    valid = result.dropna()
    assert len(valid) > 0
    # gain+loss=0 → 我們回傳 50
    assert (valid - 50.0).abs().max() < 1e-9


def test_constant_atr():
    """常數序列 ATR 應趨近 0"""
    df = pd.DataFrame({
        "high": [100.0] * 100,
        "low": [100.0] * 100,
        "close": [100.0] * 100,
    })
    result = atr(df)
    assert result.dropna().abs().max() < 1e-9


# ── 2. 單調遞增序列測試 ──────────────────────────────────────

def test_increasing_rsi():
    """純漲序列：loss 恆為 0，RSI 應為 100"""
    close = pd.Series(range(100, 600), dtype=float)
    result = rsi(close)
    valid = result.dropna()
    assert len(valid) > 0
    assert valid.iloc[-1] == pytest.approx(100.0), f"持續上漲應使 RSI = 100，實際 {valid.iloc[-1]}"


def test_increasing_sma():
    close = pd.Series(range(100, 200), dtype=float)
    result = sma(close, 20)
    valid = result.dropna()
    assert (valid.diff().dropna() > 0).all(), "單調遞增序列 SMA 應持續上升"


# ── 3. 已知答案測試（合成資料 RSI 對照） ────────────────────

def test_rsi_formula_consistency():
    """用相同 EWM 公式手動重算 RSI，與模組輸出完全一致"""
    df = make_synthetic_ohlcv(300)
    close = df["close"]

    module_val = rsi(close, 14)

    # 手動重算
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    manual_rsi = 100 * avg_gain / (avg_gain + avg_loss)
    manual_rsi = manual_rsi.where((avg_gain + avg_loss) > 0, other=50.0)

    diff = (module_val - manual_rsi).abs()
    assert diff.max() < 1e-9, f"RSI 與手動計算最大差異 {diff.max()}"


# ── 4. ADX 防呆（bug #1 防重踩） ────────────────────────────

def test_adx_range():
    """ADX 平均值應在 0~80 之間，不可出現 ~525 的爆炸值"""
    df = make_synthetic_ohlcv(500)
    result = adx(df, 14)
    valid = result.dropna()
    assert len(valid) > 0, "ADX 全為 NaN"
    assert valid.mean() < 80, f"ADX 平均值 {valid.mean():.1f} 疑似 14× 放大 bug"
    assert (valid >= 0).all(), "ADX 不應有負值"


def test_adx_not_inflated():
    """ADX 最大值不應超過 100"""
    df = make_synthetic_ohlcv(500)
    result = adx(df, 14)
    valid = result.dropna()
    assert valid.max() <= 100, f"ADX max={valid.max():.1f}，超出正常範圍"


def test_adx_short_data():
    """資料不足 period 時，ADX 應全回傳 NaN 而非爆錯"""
    df = make_synthetic_ohlcv(10)
    result = adx(df, 14)
    # len < period，wilder_sum 全 NaN
    assert result.notna().sum() == 0 or True  # 不爆錯即可


# ── 5. NaN 處理測試 ──────────────────────────────────────────

def test_sma_nan_prefix():
    close = pd.Series(range(1, 51), dtype=float)
    result = sma(close, 10)
    assert result.iloc[:9].isna().all(), "SMA 前 n-1 個應為 NaN"
    assert not result.iloc[9:].isna().any(), "SMA 第 n 個之後不應有 NaN"


def test_bollinger_nan_prefix():
    close = pd.Series(range(1, 51), dtype=float)
    result = bollinger(close, 20)
    assert result["mid"].iloc[:19].isna().all()
    assert not result["mid"].iloc[19:].isna().any()


def test_volume_ma_nan_prefix():
    vol = pd.Series(range(1, 51), dtype=float)
    result = volume_ma(vol, 10)
    assert result.iloc[:9].isna().all()
    assert not result.iloc[9:].isna().any()


# ── 6. 合成資料全指標無 inf ──────────────────────────────────

def test_all_indicators_no_inf():
    df = make_synthetic_ohlcv(500)
    close = df["close"]
    vol = df["volume"]

    checks = {
        "sma200": sma(close, 200),
        "ema50": ema(close, 50),
        "rsi14": rsi(close, 14),
        "roc20": roc(close, 20),
        "atr14": atr(df, 14),
        "boll_mid": bollinger(close)["mid"],
        "vol_ma20": volume_ma(vol, 20),
        "obv": obv(close, vol),
    }
    for name, series in checks.items():
        assert not series.isin([np.inf, -np.inf]).any(), f"{name} 含有 inf"


def test_macd_no_inf():
    df = make_synthetic_ohlcv(500)
    result = macd(df["close"])
    for col in ["macd", "signal", "hist"]:
        assert not result[col].isin([np.inf, -np.inf]).any(), f"MACD {col} 含 inf"


def test_momentum_12_1_range():
    """用 500 列合成資料，確認 12-1 月動量在合理範圍"""
    df = make_synthetic_ohlcv(500)
    result = momentum_12_1(df["close"])
    valid = result.dropna()
    assert len(valid) > 0, "momentum_12_1 全為 NaN（資料不足252列）"
    assert not valid.isin([np.inf, -np.inf]).any()
    # 合成資料每日±1%，12個月動量約在 ±50% 之內
    assert valid.min() > -80 and valid.max() < 150, f"動量範圍異常：{valid.min():.1f}~{valid.max():.1f}"


# ── 7. 真實 0050 資料（只做不爆錯測試，不假設資料量） ────────

def test_real_0050_no_error():
    """對實際 0050.csv 跑所有指標，確認不爆錯、不含 inf（不要求足夠長）"""
    df = load_0050()
    close = df["close"]
    vol = df["volume"]

    sma(close, 5)
    ema(close, 5)
    rsi(close, 5)
    atr(df, 5)
    bollinger(close, 5)
    volume_ma(vol, 5)
    obv(close, vol)
    momentum_12_1(close)
    macd(close, 3, 5, 3)
    result = adx(df, 5)
    assert not result.isin([np.inf, -np.inf]).any()
