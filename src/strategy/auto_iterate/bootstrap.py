"""Bootstrap PF (Profit Factor) 信賴區間計算。

對 trades 的 pnl_pct 列表做 1000 次重抽，計算 PF 信賴區間下界。
用途：篩掉 SUSPICIOUS_PERFECT 與小樣本運氣（PF 在小樣本時非常不穩定）。

設計要點：
- 接 list of pnl_pct (float)，與 TradeRecord 解耦，方便測試
- 與 score_single 一致：gross_loss == 0 時 PF cap = 5.0
- 小樣本 (< 5 trades) 直接回 nan
- 用 numpy.random.default_rng(seed) 確保可重現
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np


# 與 score_single 一致的 PF cap，避免 1 次重抽剛好抽到全贏導致 inf
_PF_CAP = 5.0


def bootstrap_pf_ci(
    trades_pnl_pct: Sequence[float],
    n_iterations: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict:
    """對交易 pnl_pct 做 bootstrap，計算 PF 雙尾信賴區間。

    Args:
        trades_pnl_pct: list of pnl_pct floats（相對 entry cost 的報酬率）
        n_iterations: 重抽次數，預設 1000
        confidence: 雙尾信賴水準，0.95 → 取 2.5% / 97.5% 分位數
        seed: numpy.random.default_rng 的 seed，預設 42

    Returns:
        {
            "pf_mean":       float, 1000 次 PF 的平均
            "pf_median":     float, 1000 次 PF 的中位數
            "pf_lower":      float, 信賴區間下界 (e.g. 2.5%)
            "pf_upper":      float, 信賴區間上界 (e.g. 97.5%)
            "pf_lower_pct":  float, 下界分位數 (e.g. 0.025)
            "n_iterations":  int,
            "n_original":    int, 原始 trades 筆數
        }

        若原始 trades < 5：所有 pf_* 欄位為 nan。
    """
    n_orig = len(trades_pnl_pct)
    nan_result = {
        "pf_mean":      float("nan"),
        "pf_median":    float("nan"),
        "pf_lower":     float("nan"),
        "pf_upper":     float("nan"),
        "pf_lower_pct": (1 - confidence) / 2,
        "n_iterations": n_iterations,
        "n_original":   n_orig,
    }
    if n_orig < 5:
        return nan_result

    arr = np.asarray(trades_pnl_pct, dtype=float)
    # 過濾 nan（理論不應有）
    arr = arr[~np.isnan(arr)]
    if len(arr) < 5:
        return nan_result

    rng = np.random.default_rng(seed)
    pf_samples = np.empty(n_iterations, dtype=float)

    for i in range(n_iterations):
        # 有放回抽樣，size = 原始 n
        sample = rng.choice(arr, size=len(arr), replace=True)
        gross_profit = float(sample[sample > 0].sum())
        gross_loss = float(-sample[sample < 0].sum())  # 取絕對值

        if gross_loss == 0:
            # 全贏：與 score_single 一致 cap = 5.0
            pf = _PF_CAP
        else:
            pf = gross_profit / gross_loss
            if pf > _PF_CAP or math.isinf(pf):
                pf = _PF_CAP
        pf_samples[i] = pf

    lower_pct = (1 - confidence) / 2
    upper_pct = 1 - lower_pct
    pf_lower = float(np.percentile(pf_samples, lower_pct * 100))
    pf_upper = float(np.percentile(pf_samples, upper_pct * 100))

    return {
        "pf_mean":      float(pf_samples.mean()),
        "pf_median":    float(np.median(pf_samples)),
        "pf_lower":     pf_lower,
        "pf_upper":     pf_upper,
        "pf_lower_pct": lower_pct,
        "n_iterations": n_iterations,
        "n_original":   n_orig,
    }
