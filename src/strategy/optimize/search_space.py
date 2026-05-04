"""style1_pullback 的可調參數空間定義。"""

SEARCH_SPACE = {
    # 趨勢過濾
    "ma_long":          {"type": "categorical", "choices": [150, 200, 250]},
    "ma_short":         {"type": "categorical", "choices": [30, 50, 100]},
    # 回檔判斷
    "rsi_period":       {"type": "categorical", "choices": [10, 14, 21]},
    "rsi_oversold":     {"type": "int",  "low": 25, "high": 50, "step": 5},
    "bollinger_period": {"type": "categorical", "choices": [15, 20, 25]},
    "bollinger_k":      {"type": "float", "low": 1.5, "high": 2.5, "step": 0.25},
    # 量能
    "volume_ma_period": {"type": "categorical", "choices": [10, 20, 30]},
    "volume_min_ratio": {"type": "float", "low": 0.5, "high": 1.5, "step": 0.1},
    # 出場
    "atr_period":       {"type": "categorical", "choices": [10, 14, 20]},
    "atr_stop_k":       {"type": "float", "low": 1.5, "high": 3.5, "step": 0.25},
    "trend_break_days": {"type": "int",  "low": 1, "high": 5, "step": 1},
    "rsi_overbought":   {"type": "int",  "low": 70, "high": 85, "step": 5},
    "max_hold_days":    {"type": "categorical", "choices": [60, 90, 120, 180, 240]},
}


def sample_params(trial, space: dict = None) -> dict:
    """從 search space 用 optuna trial 採一組參數。"""
    if space is None:
        space = SEARCH_SPACE
    params = {}
    for name, cfg in space.items():
        t = cfg["type"]
        if t == "categorical":
            params[name] = trial.suggest_categorical(name, cfg["choices"])
        elif t == "int":
            params[name] = trial.suggest_int(name, cfg["low"], cfg["high"], step=cfg["step"])
        elif t == "float":
            params[name] = trial.suggest_float(name, cfg["low"], cfg["high"], step=cfg["step"])
        else:
            raise ValueError(f"未知 search_space type: {t}")
    return params
