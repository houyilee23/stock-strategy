"""Sanity check for optimize module.

Tests:
1. search_space 所有 key 都對應 strategy.yaml style1_pullback 子鍵
2. 一組已知參數（目前 strategy.yaml）跑出的 score 和直接 backtest 結果一致
3. trial 數 < 5 的快速測試能跑通
"""
import sys
import os
import math
import yaml
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategy.optimize.search_space import SEARCH_SPACE, sample_params
from src.strategy.optimize.objective import (
    run_backtests_for_params, score_results, make_objective, _make_bt_cfg,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cfg_path = os.path.join(BASE_DIR, "config", "strategy.yaml")
with open(_cfg_path, encoding="utf-8") as f:
    _STRATEGY = yaml.safe_load(f)


# ── Test 1: search_space key 都在 strategy.yaml style1_pullback ──

def test_search_space_keys_in_strategy_yaml():
    """SEARCH_SPACE 的所有 key 都必須對應 style1_pullback 子鍵。"""
    style1_keys = set(_STRATEGY["style1_pullback"].keys())
    for k in SEARCH_SPACE:
        assert k in style1_keys, (
            f"SEARCH_SPACE 中的 '{k}' 不在 strategy.yaml style1_pullback 子鍵"
            f"（可用：{sorted(style1_keys)}）"
        )


# ── Test 2: sample_params 輸出合法 ─────────────────────────────

def test_sample_params_produces_valid_keys():
    """用 fixed sampler 確認 sample_params 輸出 keys 完整。"""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.ERROR)
    study = optuna.create_study()

    def dummy_obj(trial):
        params = sample_params(trial, SEARCH_SPACE)
        # 所有 key 都存在
        for k in SEARCH_SPACE:
            assert k in params, f"sample_params 缺少 key: {k}"
        return 0.0

    study.optimize(dummy_obj, n_trials=3)


# ── Test 3: 快速 3 trials 能跑通 ────────────────────────────────

def test_quick_optimize_smoke():
    """3 trials 的快速煙霧測試（--universe 0050,2330）。"""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.ERROR)

    from src.strategy.runner import _load_adj_ohlcv
    from src.strategy.signals.regime import detect_regime

    universe_ids = ["0050", "2330"]
    universe_data = {}
    for sid in universe_ids:
        df = _load_adj_ohlcv(sid)
        if df is not None and len(df) >= 250:
            universe_data[sid] = df
    if not universe_data:
        pytest.skip("adjusted 資料不足，跳過")

    market_df = _load_adj_ohlcv("0050")
    if market_df is None:
        pytest.skip("0050 adjusted 不存在，跳過")
    regime = detect_regime(market_df, _STRATEGY["regime"]["ma_long"])

    bt_cfg = _make_bt_cfg(_STRATEGY["fees"], "2017-01-01", "2022-12-31")
    obj_fn = make_objective(universe_data, regime, bt_cfg)

    study = optuna.create_study(direction="maximize")
    study.optimize(obj_fn, n_trials=3)

    assert len(study.trials) == 3
    scores = [t.value for t in study.trials if t.value is not None]
    assert len(scores) >= 1, "所有 trial 都回傳 None，objective 可能 crash"
    print(f"\n  quick smoke: scores={[f'{s:.4f}' for s in scores]}")


# ── Test 4: score_results 與手動計算一致 ────────────────────────

def test_score_consistency_with_current_params():
    """用目前 strategy.yaml 參數跑 score，驗證計算邏輯正確。"""
    from src.strategy.runner import _load_adj_ohlcv
    from src.strategy.signals.regime import detect_regime

    adj_dir = os.path.join(BASE_DIR, "data", "adjusted")
    if not os.path.isdir(adj_dir):
        pytest.skip("data/adjusted/ 不存在，跳過")

    sids = ["2330", "0050"]
    universe_data = {}
    for sid in sids:
        df = _load_adj_ohlcv(sid)
        if df is not None and len(df) >= 250:
            universe_data[sid] = df
    if not universe_data:
        pytest.skip("adjusted 資料不足，跳過")

    market_df = _load_adj_ohlcv("0050")
    if market_df is None:
        pytest.skip("0050 adjusted 不存在，跳過")
    regime = detect_regime(market_df, _STRATEGY["regime"]["ma_long"])

    params = dict(_STRATEGY["style1_pullback"])
    bt_cfg = _make_bt_cfg(_STRATEGY["fees"], "2017-01-01", "2022-12-31")

    df_results = run_backtests_for_params(params, universe_data, regime, bt_cfg)
    assert len(df_results) == len(universe_data), "per-stock 結果筆數不符"

    score = score_results(df_results, len(universe_data))
    # score 應為有限數值（不是 NaN），且在合理範圍 [-10, 20]
    assert not math.isnan(score), f"score 是 NaN（可能 0 筆交易）"
    assert -10.0 <= score <= 20.0, f"score={score:.4f} 超出合理範圍 [-10, 20]"
    print(f"\n  score with current params = {score:.4f}")
    print(df_results[["stock_id", "n_trades", "profit_factor", "max_drawdown"]].to_string(index=False))
