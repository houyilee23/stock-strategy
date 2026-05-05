"""策略系統入口：signals / backtest / evaluate 三個模式的執行邏輯。"""
import os
import math
import unicodedata
import yaml
import pandas as pd
from datetime import date, datetime


def _vwidth(s: str) -> int:
    """終端視覺寬度（East Asian Wide/Fullwidth 算 2 格）。"""
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1
               for c in str(s))


def _vpad(s, width: int, align: str = "<") -> str:
    """按視覺寬度 padding，align ∈ {'<', '>', '^'}。"""
    s = str(s)
    pad = max(0, width - _vwidth(s))
    if align == "<":
        return s + " " * pad
    if align == ">":
        return " " * pad + s
    left = pad // 2
    return " " * left + s + " " * (pad - left)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模組級快取，避免重複讀檔
_RECOMMENDATIONS_CACHE = None
_TEMPLATE_PARAMS_CACHE: dict = {}


def _load_strategy_cfg() -> dict:
    path = os.path.join(BASE_DIR, "config", "strategy.yaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_recommendations(path: str = None) -> dict:
    """讀取 config/per_stock_recommendations.yaml（auto_iterate 產出）。

    回傳 dict：{stock_id: {tier, template, params_ref, position_pct_max,
                            tradeable, name, ...}}
    若檔案不存在 → 回傳 {}（fallback 到 style1_pullback）。
    結果快取於模組層級，避免每次 signals 跑都重讀。
    """
    global _RECOMMENDATIONS_CACHE
    if path is None:
        # 預設走快取
        if _RECOMMENDATIONS_CACHE is not None:
            return _RECOMMENDATIONS_CACHE
        path = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")

    if not os.path.exists(path):
        if _RECOMMENDATIONS_CACHE is None and path == os.path.join(
                BASE_DIR, "config", "per_stock_recommendations.yaml"):
            _RECOMMENDATIONS_CACHE = {}
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        # YAML 中 stock_id 是字串 key (e.g. '2317')，全部 normalize 成 str
        result = {str(k): v for k, v in data.items() if isinstance(v, dict)}
    except Exception as e:
        from src.utils import log_error
        log_error("runner", "ALL", f"讀 per_stock_recommendations.yaml 失敗：{e}")
        result = {}

    if path == os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml"):
        _RECOMMENDATIONS_CACHE = result
    return result


def _resolve_params_ref(params_ref: str, base_dir: str = None) -> dict:
    """解析 params_ref 字串（e.g. 'donchian_breakout.yaml#per_stock.2317'），
    回傳該股的 best_params dict。

    格式：'<filename>.yaml#per_stock.<stock_id>'
    檔案位於 output/auto_iterate/<run_id>/<filename>.yaml
    自動找 output/auto_iterate/ 底下最新的 run_id 子目錄。
    若解析失敗回傳 {}。
    """
    if not params_ref or "#" not in params_ref:
        return {}
    filename, ref_path = params_ref.split("#", 1)
    parts = ref_path.split(".")
    if len(parts) < 2 or parts[0] != "per_stock":
        return {}
    sid = parts[1]

    if base_dir is None:
        base_dir = _find_latest_auto_iterate_dir()
        if base_dir is None:
            return {}

    yaml_path = os.path.join(base_dir, filename)
    cache_key = yaml_path
    if cache_key not in _TEMPLATE_PARAMS_CACHE:
        if not os.path.exists(yaml_path):
            _TEMPLATE_PARAMS_CACHE[cache_key] = {}
        else:
            try:
                with open(yaml_path, encoding="utf-8") as f:
                    _TEMPLATE_PARAMS_CACHE[cache_key] = yaml.safe_load(f) or {}
            except Exception as e:
                from src.utils import log_error
                log_error("runner", sid, f"讀 {filename} 失敗：{e}")
                _TEMPLATE_PARAMS_CACHE[cache_key] = {}

    data = _TEMPLATE_PARAMS_CACHE[cache_key]
    per_stock = (data or {}).get("per_stock", {})
    entry = per_stock.get(sid) or per_stock.get(str(sid)) or {}
    return entry.get("best_params", {}) or {}


def _find_latest_auto_iterate_dir() -> str:
    """找 output/auto_iterate/ 下實際對應 per_stock_recommendations.yaml 的
    run_id 子目錄。

    優先順序：
    1. 從 config/per_stock_recommendations.yaml 的 header 註解（'# Run: <id>'）
       取得實際 run_id（這是推薦表產出時的 batch，最可信）
    2. 若 header 無法解析或目錄不存在 → fallback 到最新「有任何 .yaml 檔」的子目錄
       （避免被空的 run_id dir 誤導，例如只有 .db 檔的進行中 run）
    若都不存在回傳 None。
    """
    ai_dir = os.path.join(BASE_DIR, "output", "auto_iterate")
    if not os.path.isdir(ai_dir):
        return None

    # 1) 從 recommendations 檔讀 header
    rec_path = os.path.join(BASE_DIR, "config", "per_stock_recommendations.yaml")
    if os.path.exists(rec_path):
        try:
            with open(rec_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# Run:"):
                        run_id = line.split(":", 1)[1].strip()
                        candidate = os.path.join(ai_dir, run_id)
                        if os.path.isdir(candidate):
                            return candidate
                        break
                    if not line.startswith("#"):
                        break  # header 結束
        except Exception:
            pass  # fallback below

    # 2) Fallback：選最新一個含 .yaml 檔的子目錄
    subs = [d for d in os.listdir(ai_dir)
            if os.path.isdir(os.path.join(ai_dir, d))]
    if not subs:
        return None
    subs.sort(reverse=True)  # 由新到舊
    for d in subs:
        full = os.path.join(ai_dir, d)
        try:
            if any(fn.endswith(".yaml") for fn in os.listdir(full)):
                return full
        except OSError:
            continue
    return None


def _load_ohlcv(stock_id: str) -> pd.DataFrame:
    """載入 data/raw/{stock_id}.csv，回傳以日期為 index 的 DataFrame。
    若檔案不存在或資料不足，回傳 None。
    """
    from src.utils import log_error
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    path = os.path.join(raw_dir, f"{stock_id}.csv")
    if not os.path.exists(path):
        log_error("runner", stock_id, f"找不到資料檔 {path}")
        return None
    try:
        df = pd.read_csv(path, dtype={"date": str})
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df = df.sort_values("date").set_index("date")
        # 確保有必要欄位
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                log_error("runner", stock_id, f"缺少欄位 {col}")
                return None
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df
    except Exception as e:
        log_error("runner", stock_id, str(e))
        return None


def _load_adj_ohlcv(stock_id: str) -> pd.DataFrame:
    """P0-12 + P0-12.1：載入 data/adjusted/{sid}.csv，OHLC 一致性還原。

    嚴重 bug 修正（2026-04-23）：原本只把 close 換成 close_adj，但 open/high/low
    保持 raw 原始價，導致 close < open 在歷史期間幾乎永遠成立（因為 close_adj
    被向後復權縮小），style1 的「反轉條件 close>open」永遠失敗 → 9 年只有 0~2 筆訊號。

    修法：用 daily factor = close_adj / close 同時套到 open/high/low，
    保持 OHLC 內部一致，indicators (MA/RSI/BB/ATR) 才有意義。
    Volume 不調（dividend 不影響，split 影響有限，相對 MA 比較仍合理）。

    若 adjusted 檔不存在，fallback 到 raw（並寫 error log）。
    """
    from src.utils import log_error
    adj_dir = os.path.join(BASE_DIR, "data", "adjusted")
    path = os.path.join(adj_dir, f"{stock_id}.csv")
    if not os.path.exists(path):
        log_error("runner", stock_id, f"adjusted 不存在，改用 raw：{path}")
        return _load_ohlcv(stock_id)
    try:
        df = pd.read_csv(path, dtype={"date": str})
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
        df = df.sort_values("date").set_index("date")
        if "close_adj" not in df.columns:
            log_error("runner", stock_id, "adjusted CSV 缺少 close_adj 欄位，改用 raw")
            return _load_ohlcv(stock_id)
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in df.columns:
                log_error("runner", stock_id, f"adjusted CSV 缺少欄位 {col}")
                return _load_ohlcv(stock_id)
        # P0-12.1: 計算 daily factor (close_adj / close)，套到 OHL 保持一致
        df = df.astype({"open": float, "high": float, "low": float,
                        "close": float, "close_adj": float, "volume": float})
        # 防呆：raw close 為 0 時 factor 設 1.0（理論上不應發生）
        factor = (df["close_adj"] / df["close"]).replace([float("inf"), -float("inf")], 1.0).fillna(1.0)
        df["open"]  = df["open"]  * factor
        df["high"]  = df["high"]  * factor
        df["low"]   = df["low"]   * factor
        df["close"] = df["close_adj"]
        return df[["open", "high", "low", "close", "volume"]]
    except Exception as e:
        log_error("runner", stock_id, str(e))
        return None


def _load_market_df(cfg: dict, adjusted: bool = False) -> pd.DataFrame:
    """載入大盤代理（0050）。
    adjusted=True → 使用還原股價（回測 / regime 偵測用）
    adjusted=False → 使用 raw（訊號顯示用）
    """
    proxy = cfg.get("regime", {}).get("market_proxy", "0050")
    if adjusted:
        return _load_adj_ohlcv(proxy)
    return _load_ohlcv(proxy)


def _generate_for_stock(sid: str, df: pd.DataFrame, stock_regime: pd.Series,
                        recommendations: dict, fallback_params: dict) -> tuple:
    """依推薦表為單一股票派工到對應 template。

    回傳 (signals_df, template_used, tier, position_pct_max, tradeable)。
    若 stock 不在推薦表中或 tradeable=false → fallback 到 style1_pullback。
    """
    from src.strategy.signals.style1_pullback import generate_signals as _style1_gen
    from src.strategy.auto_iterate.templates import TEMPLATE_GENERATORS

    rec = recommendations.get(str(sid)) or recommendations.get(sid)
    if not rec or not rec.get("tradeable", False):
        # Fallback：F-tier 或不在表內 → 沿用原 style1_pullback 行為
        signals = _style1_gen(df, stock_regime, fallback_params)
        return (signals, "style1_pullback",
                (rec or {}).get("tier", "—"),
                float((rec or {}).get("position_pct_max", 0.0)),
                bool((rec or {}).get("tradeable", False)))

    template = rec.get("template", "trend_pullback")
    params_ref = rec.get("params_ref", "")
    tier = rec.get("tier", "—")
    pos_max = float(rec.get("position_pct_max", 0.0))

    gen_fn = TEMPLATE_GENERATORS.get(template)
    if gen_fn is None:
        from src.utils import log_error
        log_error("signals", sid,
                  f"未知 template={template}，fallback to style1_pullback")
        signals = _style1_gen(df, stock_regime, fallback_params)
        return signals, "style1_pullback", tier, pos_max, True

    best_params = _resolve_params_ref(params_ref)
    if not best_params:
        from src.utils import log_error
        log_error("signals", sid,
                  f"找不到 {params_ref} 的 best_params，fallback to style1_pullback")
        signals = _style1_gen(df, stock_regime, fallback_params)
        return signals, "style1_pullback", tier, pos_max, True

    try:
        # chip_momentum 需 chip_data，目前訊號模式不載入 → 視同無 chip 信號
        signals = gen_fn(df, best_params, regime=stock_regime, chip_data=None)
    except Exception as e:
        from src.utils import log_error
        log_error("signals", sid,
                  f"template={template} 產出錯誤：{e}，fallback to style1_pullback")
        signals = _style1_gen(df, stock_regime, fallback_params)
        return signals, "style1_pullback", tier, pos_max, True

    return signals, template, tier, pos_max, True


def _load_best_params(template: str, stock_id: str) -> dict:
    """從 merged auto_iterate run 讀某檔某 template 的 best_params。"""
    merged_dir = os.path.join(BASE_DIR, "output", "auto_iterate",
                                "merged_20260426_120034")
    yaml_path = os.path.join(merged_dir, f"{template}.yaml")
    if not os.path.exists(yaml_path):
        return {}
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    per_stock = data.get("per_stock", {}) if isinstance(data, dict) else {}
    rec = per_stock.get(stock_id)
    if not isinstance(rec, dict):
        return {}
    return rec.get("best_params", {}) or {}


def _load_real_positions(account_name: str) -> dict:
    """讀取真實持倉（從 trades_{account}.csv）

    回傳 dict: {stock_id: {entry_price, shares, open_date}}
    多筆 BUY 同一檔 → 用平均成本當 entry_price。
    若帳戶名稱不存在對應 trades 檔（例如 "research"）→ 回傳空 dict。
    """
    try:
        from src.ledger import load_trades, compute_open_positions
    except Exception:
        return {}
    try:
        trades = load_trades(account_name)
        if trades.empty:
            return {}
        open_lots = compute_open_positions(trades)
    except Exception:
        return {}

    # 把多 lot 同一檔合併（average cost）
    by_sid: dict = {}
    for lot in open_lots:
        sid = lot["stock_id"]
        if sid not in by_sid:
            by_sid[sid] = {"shares": 0, "cost": 0.0, "open_date": lot["open_date"]}
        by_sid[sid]["shares"] += int(lot["shares"])
        by_sid[sid]["cost"] += float(lot["open_price"]) * int(lot["shares"])
        # 取最早的 open_date
        if lot["open_date"] < by_sid[sid]["open_date"]:
            by_sid[sid]["open_date"] = lot["open_date"]

    out = {}
    for sid, agg in by_sid.items():
        if agg["shares"] > 0:
            out[sid] = {
                "entry_price": agg["cost"] / agg["shares"],
                "shares": agg["shares"],
                "open_date": agg["open_date"],
            }
    return out


def _compute_personal_tp(real_pos: dict | None, template_name: str,
                          params: dict) -> float:
    """根據真實持倉算「個人化 TP」（與 generator 的 hypothetical TP 並存）。

    只有 entry-dependent template 才有意義：
      - low_vol_pullback: real_entry × (1 + take_profit_pct)
      - mean_reversion 的 TP 用 short_ma 不依賴 entry → 不需個人化
    """
    if real_pos is None:
        return float("nan")
    real_entry = real_pos["entry_price"]
    if template_name == "low_vol_pullback":
        tp_pct = float(params.get("take_profit_pct", 0.09))
        return real_entry * (1 + tp_pct)
    return float("nan")


def run_signals(stock_ids: list, account_name: str, cfg: dict = None) -> None:
    """訊號模式：對 watchlist 產出今日建議。

    新版（2026-04）：依 config/per_stock_recommendations.yaml 為每檔派工到
    其最佳 template；F-tier 或缺記錄者 fallback 到 style1_pullback。

    新版（2026-05）：限價單機制 + 整合真實持倉。
    讀 data/trades_{account}.csv 取得用戶實際持倉，調整最後一筆訊號的
    target_tp/target_sl 為真實 entry 計算。
    """
    from src.strategy.signals.regime import detect_regime
    from src.strategy.eval.reporter import save_daily_signals_md
    from src.strategy.indicators.momentum import rsi as _rsi
    from src.strategy.indicators.trend import sma as _sma

    if cfg is None:
        cfg = _load_strategy_cfg()

    # 讀取真實持倉（research 等觀察清單會回空 dict）
    real_positions = _load_real_positions(account_name)

    market_df = _load_market_df(cfg)
    if market_df is not None:
        regime = detect_regime(market_df, cfg["regime"]["ma_long"])
    else:
        regime = pd.Series(dtype=str)

    fallback_params = cfg["style1_pullback"]
    recommendations = _load_recommendations()
    rows = []

    # 取最新一日的市場 regime
    last_market_regime = "N/A"
    if len(regime) > 0:
        last_market_regime = regime.iloc[-1]

    for sid in stock_ids:
        df = _load_ohlcv(sid)
        if df is None or len(df) < 30:
            rec = recommendations.get(str(sid), {}) or {}
            rows.append({
                "stock_id": sid, "close": float("nan"), "action": "N/A",
                "entry_low": float("nan"), "entry_high": float("nan"),
                "stop_loss": float("nan"), "rsi_val": float("nan"),
                "ma200": float("nan"), "ma50": float("nan"),
                "market_regime": last_market_regime,
                "template": rec.get("template", "—"),
                "tier": rec.get("tier", "—"),
                "position_pct_max": float(rec.get("position_pct_max", 0.0)),
                "tradeable": bool(rec.get("tradeable", False)),
                "reason": "資料不足",
            })
            continue

        try:
            # 對齊 regime index
            if len(regime) == 0:
                stock_regime = pd.Series("BEAR", index=df.index)
            else:
                stock_regime = regime.reindex(df.index, method="ffill").fillna("BEAR")

            signals, template_used, tier, pos_max, tradeable = _generate_for_stock(
                sid, df, stock_regime, recommendations, fallback_params)

            # 整合真實持倉：保持 generator 訊號中性（給家人/觀察都看得到 BUY 訊號）；
            # 額外計算「個人化 TP」（用真實 entry）作 reason 註記
            real_pos = real_positions.get(str(sid))
            params_for_personal = {}
            if template_used == "low_vol_pullback":
                params_for_personal = _load_best_params(template_used, str(sid))
            personal_tp = _compute_personal_tp(real_pos, template_used,
                                                  params_for_personal)

            last = signals.iloc[-1]
            close = df["close"].iloc[-1]

            # 共用顯示用指標：MA50/MA200/RSI（不論 template 為何）
            ma50_s = _sma(df["close"], 50)
            ma200_s = _sma(df["close"], 200)
            rsi_s = _rsi(df["close"], 14)
            ma50_last = ma50_s.iloc[-1] if not ma50_s.empty else float("nan")
            ma200_last = ma200_s.iloc[-1] if not ma200_s.empty else float("nan")
            rsi_last = rsi_s.iloc[-1] if not rsi_s.empty else float("nan")

            # 部分 template 不產 entry_low/high/stop_loss/rsi_val/ma200 欄
            def _g(col, default):
                if col in signals.columns:
                    v = last[col]
                    if isinstance(v, float) and math.isnan(v):
                        return default
                    return v
                return default

            rec = recommendations.get(str(sid), {}) or {}
            rows.append({
                "stock_id": sid,
                "close": close,
                "action": last["action"],
                "entry_low": _g("entry_low", float("nan")),
                "entry_high": _g("entry_high", float("nan")),
                "stop_loss": _g("stop_loss", float("nan")),
                "rsi_val": _g("rsi_val", rsi_last),
                "ma200": _g("ma200", ma200_last),
                "ma50": ma50_last,
                "market_regime": last_market_regime,
                "template": template_used,
                "tier": tier,
                "position_pct_max": pos_max,
                "tradeable": tradeable,
                "bnh_tier": rec.get("bnh_tier"),
                "bnh_position_pct_max": float(rec.get("bnh_position_pct_max") or 0.0),
                "bnh_cagr": rec.get("bnh_cagr"),
                "reason": _g("reason", ""),
                # v0.1 限價單機制：只有 low_vol_pullback / mean_reversion 會輸出
                "target_buy": _g("target_buy", float("nan")),
                "target_tp": _g("target_tp", float("nan")),
                "target_sl": _g("target_sl", float("nan")),
                # 真實持倉資訊（從 trades_{account}.csv）
                "in_position": real_pos is not None,
                "real_entry": real_pos["entry_price"] if real_pos else float("nan"),
                "real_shares": real_pos["shares"] if real_pos else 0,
                # 個人化 TP（用真實 entry 算的）— 與 generator 的 hypothetical TP 並存
                "personal_tp": personal_tp,
            })
        except Exception as e:
            from src.utils import log_error
            log_error("signals", sid, str(e))
            rec = recommendations.get(str(sid), {}) or {}
            rows.append({
                "stock_id": sid, "close": float("nan"), "action": "ERROR",
                "entry_low": float("nan"), "entry_high": float("nan"),
                "stop_loss": float("nan"), "rsi_val": float("nan"),
                "ma200": float("nan"), "ma50": float("nan"),
                "market_regime": last_market_regime,
                "template": rec.get("template", "—"),
                "tier": rec.get("tier", "—"),
                "position_pct_max": float(rec.get("position_pct_max", 0.0)),
                "tradeable": bool(rec.get("tradeable", False)),
                "reason": str(e)[:50],
            })

    result_df = pd.DataFrame(rows)

    # Console 輸出
    _print_signals_table(result_df, account_name)

    # Markdown 報表（補股名 dict）
    # 優先 watchlists.yaml 註解（人寫的最準），其次 per_stock_recommendations.yaml
    # 注意：final_report.py 對沒名字的股票會 fallback 寫 name=stock_id，要過濾掉
    stock_names = {}
    try:
        import re
        wl_path = os.path.join(BASE_DIR, "config", "watchlists.yaml")
        with open(wl_path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^\s*-\s*"([^"]+)"\s*#\s*(.+?)(?:\s*\(|\s*$)', line)
                if m:
                    sid, name = m.group(1), m.group(2).strip()
                    if name and name != sid:
                        stock_names[sid] = name
    except Exception:
        pass
    # 其次補：recommendations 裡若有合理 name（非 stock_id）才用
    for sid, rec in recommendations.items():
        if sid in stock_names:
            continue
        if isinstance(rec, dict):
            n = rec.get("name")
            if n and n != sid:
                stock_names[sid] = n
    path = save_daily_signals_md(result_df, account_name, stock_names=stock_names)
    print(f"\n  報表已儲存：{path}")


def _print_signals_table(df: pd.DataFrame, account_name: str) -> None:
    today_str = date.today().strftime("%Y-%m-%d")
    print(f"\n{'='*110}")
    print(f"  今日訊號 — {account_name} ({today_str})")
    print(f"{'='*110}")
    print(f"  {_vpad('股票',6)} {_vpad('在倉',4,'^')} {_vpad('收盤',7,'>')} "
          f"{_vpad('動作',6,'^')} {_vpad('Tier',4,'^')} {_vpad('倉位',5,'>')} "
          f"{_vpad('Template',18)} {_vpad('掛單',8,'>')} {_vpad('RSI',4,'>')} "
          f"{_vpad('趨勢',6,'^')} {_vpad('Regime',7,'^')} 說明")
    print(f"{'-'*110}")

    def f(v, fmt=".1f"):
        if isinstance(v, float) and math.isnan(v):
            return "  -  "
        return format(v, fmt)

    for _, row in df.iterrows():
        sid = row["stock_id"]
        close_s = f(row["close"])
        action = row["action"]
        rsi_v = f(row.get("rsi_val", float("nan")), ".0f")
        ma200 = row.get("ma200", float("nan"))
        ma50 = row.get("ma50", float("nan"))
        close_v = row["close"]
        mkt_regime = str(row.get("market_regime", "N/A"))
        tier = str(row.get("tier", "—"))
        pos_max = row.get("position_pct_max", 0.0)
        # BNH 候選：tier=F 但 bnh_tier in (BNH_S/BNH_A/BNH_B) → 顯示 BNH 替代建議
        bnh_tier = row.get("bnh_tier")
        bnh_pos = row.get("bnh_position_pct_max", 0.0) or 0.0
        bnh_active = (tier == "F" and bnh_tier in ("BNH_S", "BNH_A", "BNH_B")
                      and bnh_pos > 0)
        if bnh_active:
            tier_disp = bnh_tier.replace("BNH_", "B")  # BNH_S → BS / BA / BB
            pos_str = f"{bnh_pos*100:.0f}%*"
        else:
            tier_disp = tier
            pos_str = (f"{pos_max*100:.0f}%"
                       if isinstance(pos_max, (int, float)) and pos_max > 0
                       else "  -  ")
        template = str(row.get("template", "—"))[:18]

        # 個股趨勢：Close > MA200 AND MA50 > MA200
        if not (isinstance(ma200, float) and math.isnan(ma200)) and \
           not (isinstance(close_v, float) and math.isnan(close_v)) and \
           not (isinstance(ma50, float) and math.isnan(ma50)):
            stock_trend = "[多]" if (close_v > ma200 and ma50 > ma200) else "[空]"
        elif not (isinstance(ma200, float) and math.isnan(ma200)) and \
             not (isinstance(close_v, float) and math.isnan(close_v)):
            stock_trend = "[>M2]" if close_v > ma200 else "[<M2]"
        else:
            stock_trend = "  -  "

        reason = str(row.get("reason", ""))[:24]
        if bnh_active and not reason:
            reason = f"[BNH 長持 CAGR {row.get('bnh_cagr', 0)*100:+.0f}%]"
        # 掛單目標價（限價單機制 v0.1，只有部分 template 有）
        # 訊號保持中性：不論在倉與否，generator 給的目標都顯示
        # （給家人建議、忘記改倉位等場景都需要看到 BUY 訊號）
        target_buy = row.get("target_buy", float("nan"))
        target_tp = row.get("target_tp", float("nan"))
        target_sl = row.get("target_sl", float("nan"))
        in_pos = bool(row.get("in_position", False))
        has_buy = isinstance(target_buy, (int, float)) and not math.isnan(target_buy)
        has_tp = isinstance(target_tp, (int, float)) and not math.isnan(target_tp)
        has_sl = isinstance(target_sl, (int, float)) and not math.isnan(target_sl)
        if action == "BUY" and has_buy:
            order_disp = f"買{target_buy:.1f}"
        elif has_tp or has_sl:
            tp_s = f"{target_tp:.0f}" if has_tp else "—"
            sl_s = f"{target_sl:.0f}" if has_sl else "—"
            order_disp = f"{tp_s}/{sl_s}"
        else:
            order_disp = "  -  "

        # 個人化 TP 註記（與 generator TP 不同時）
        personal_tp = row.get("personal_tp", float("nan"))
        if in_pos and isinstance(personal_tp, (int, float)) and not math.isnan(personal_tp):
            real_entry = row.get("real_entry", float("nan"))
            rs_v = row.get("real_shares", 0)
            real_shares = int(rs_v) if isinstance(rs_v, (int, float)) and not math.isnan(rs_v) else 0
            personal_note = f"持{real_shares}@{real_entry:.1f}|你TP {personal_tp:.1f}"
            reason = (reason + " " if reason else "") + personal_note
        elif in_pos:
            real_entry = row.get("real_entry", float("nan"))
            rs_v = row.get("real_shares", 0)
            real_shares = int(rs_v) if isinstance(rs_v, (int, float)) and not math.isnan(rs_v) else 0
            personal_note = f"持{real_shares}@{real_entry:.1f}"
            reason = (reason + " " if reason else "") + personal_note

        # 在倉指示（用 CJK 字元避免 cp950 console 壞）
        in_pos_disp = "持" if in_pos else "-"

        print(f"  {_vpad(sid,6)} {_vpad(in_pos_disp,4,'^')} {_vpad(close_s,7,'>')} "
              f"{_vpad(action,6,'^')} {_vpad(tier_disp,4,'^')} {_vpad(pos_str,5,'>')} "
              f"{_vpad(template,18)} {_vpad(order_disp,8,'>')} {_vpad(rsi_v,4,'>')} "
              f"{_vpad(stock_trend,6,'^')} {_vpad(mkt_regime,7,'^')} {reason}")
    print(f"{'='*110}")
    # 圖例：* 號代表 tier 已被 BNH 候選取代（timing 失敗但長持 OK）
    if any((r.get("tier") == "F" and r.get("bnh_tier") in
            ("BNH_S", "BNH_A", "BNH_B"))
           for _, r in df.iterrows()):
        print("  圖例：BS/BA/BB = BNH_S/BNH_A/BNH_B 長持替代；* 表示部位來自 BNH 評估\n")


def run_backtest(stock_ids: list, account_name: str,
                 portfolio_mode: bool = False,
                 start_date: str = None, end_date: str = None,
                 cfg: dict = None) -> None:
    """回測模式"""
    from src.strategy.backtest.engine import Backtester, BacktestConfig
    from src.strategy.signals.regime import detect_regime
    from src.strategy.signals.style1_pullback import generate_signals
    from src.strategy.eval.reporter import save_per_stock_csv, save_portfolio_csv, save_summary_md
    from src.strategy.eval.per_stock import metrics_to_df

    if cfg is None:
        cfg = _load_strategy_cfg()

    bt_cfg_dict = cfg["backtest"]
    sd = start_date or bt_cfg_dict["start_date"]
    ed = end_date or bt_cfg_dict["end_date"]

    account_cfg = cfg.get("accounts", {}).get(account_name, {})
    init_cap = account_cfg.get("initial_capital", bt_cfg_dict["initial_capital_portfolio"])

    bt_cfg = BacktestConfig(
        fees=cfg["fees"],
        start_date=sd,
        end_date=ed,
        initial_capital=init_cap,
        max_position_pct=bt_cfg_dict["max_position_pct"],
    )
    bt = Backtester(bt_cfg)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # P0-12: 回測改用還原股價（adj_close）偵測 regime + 計算指標
    market_df = _load_market_df(cfg, adjusted=True)
    if market_df is not None:
        regime = detect_regime(market_df, cfg["regime"]["ma_long"])
    else:
        regime = pd.Series(dtype=str)

    params = cfg["style1_pullback"]

    dfs = {}
    signals_dict = {}
    for sid in stock_ids:
        # P0-12: 訊號用 adj_close（無除權息跳空），引擎用 raw（真實成交價 / P&L）
        df_adj = _load_adj_ohlcv(sid)   # adj_close → close，用於 MA/RSI/BB 計算
        df_raw = _load_ohlcv(sid)       # raw open/close，用於引擎執行 + equity 追蹤
        if df_adj is None or len(df_adj) < 50:
            continue
        if df_raw is None or len(df_raw) < 50:
            df_raw = df_adj  # fallback
        # 以 adj_close 的日期為準，對齊 raw
        df_raw = df_raw.reindex(df_adj.index)
        if len(regime) == 0:
            stock_regime = pd.Series("BEAR", index=df_adj.index)
        else:
            stock_regime = regime.reindex(df_adj.index, method="ffill").fillna("BEAR")
        dfs[sid] = df_raw                                          # raw → 引擎 P&L
        signals_dict[sid] = generate_signals(df_adj, stock_regime, params)  # adj → 訊號

    if not dfs:
        print("[錯誤] 所有股票資料不足，無法回測")
        return

    if portfolio_mode:
        from src.strategy.portfolio.allocator import top_n_equal_weight_sizing
        mom_params = cfg["style2_momentum"]
        max_pos = bt_cfg.max_position_pct

        # P0-5/P0-6 修正：月頻換倉 + 每日 regime 即時保護
        from src.strategy.portfolio.allocator import make_monthly_portfolio_sizing
        sizing_fn = make_monthly_portfolio_sizing(regime, mom_params, max_pos)

        # 計算 benchmark CAGR（0050 buy-and-hold）
        bh_cagr = _calc_benchmark_cagr(market_df, bt_cfg, cfg)
        result = bt.run_portfolio(dfs, signals_dict, sizing_fn, benchmark_cagr=bh_cagr)

        p_path = save_portfolio_csv(result, run_id)
        stock_results = list(result.stock_results.values())
        ps_path = save_per_stock_csv(stock_results, run_id)
        md_path = save_summary_md(stock_results, result, run_id,
                                   {"portfolio": cfg["eval_portfolio"],
                                    "per_stock": cfg["eval_per_stock"]})
        from src.strategy.eval.portfolio import calc_portfolio_metrics
        pm = calc_portfolio_metrics(result)
        print(f"\n  組合回測完成 run_id={run_id}")
        sharpe_str = f"  Sharpe={pm['sharpe']:.2f}" if not math.isnan(pm.get('sharpe', float('nan'))) else ""
        print(f"  CAGR={pm['cagr']:.1%}  MaxDD={pm['max_drawdown']:.1%}{sharpe_str}")
        # P0-13: 印出有持倉時段的年化報酬
        imc = result.in_market_cagr
        if not math.isnan(imc):
            print(f"  In-Market CAGR={imc:.1%}  （有持倉日年化，排除現金稀釋）")

        # Regime 統計輸出
        eq_index = result.equity_curve.index
        if len(eq_index) > 0:
            regime_in_range = regime.reindex(eq_index, method="ffill").fillna("BEAR")
            bull_ratio = (regime_in_range == "BULL").mean()
            bear_ratio = (regime_in_range == "BEAR").mean()
            bear_mask = (regime_in_range == "BEAR")
            if bear_mask.sum() > 0 and len(result.equity_curve) > 0:
                init_eq = result.equity_curve.iloc[0]
                bear_eq_mean = result.equity_curve[bear_mask].mean()
                bear_util_pct = bear_eq_mean / init_eq if init_eq > 0 else float("nan")
                print(f"  Regime：BULL {bull_ratio:.1%} / BEAR {bear_ratio:.1%}")
                print(f"  BEAR 期間 equity 均值/初始 = {bear_util_pct:.2%}（接近 1.0 = 已清倉）")
        print(f"  報表：{p_path}")
    else:
        stock_results = []
        for sid in list(dfs.keys()):
            res = bt.run_per_stock(sid, dfs[sid], signals_dict[sid])
            stock_results.append(res)

        ps_path = save_per_stock_csv(stock_results, run_id)
        df_m = metrics_to_df(stock_results, cfg["eval_per_stock"]["min_trades"])
        print(f"\n  訊號回測完成 run_id={run_id}（{len(stock_results)} 檔）")
        print(df_m[["stock_id", "n_trades", "win_rate", "profit_factor",
                      "max_drawdown"]].to_string(index=False))
        print(f"  CSV：{ps_path}")


def _calc_benchmark_cagr(market_df: pd.DataFrame, bt_cfg: "BacktestConfig",
                          cfg: dict) -> float:
    """計算 0050 同期 buy-and-hold 年化報酬。
    P0-2 修正：資料不足 1 年時 raise ValueError，避免荒謬的短期 CAGR。
    P0-12 修正：若有 adjusted 資料，改用 adj_close 計算（含除息 + 拆分還原的真實報酬）。
    """
    if market_df is None or len(market_df) < 2:
        return float("nan")
    from datetime import date as date_cls

    start = pd.Timestamp(bt_cfg.start_date)
    end_str = bt_cfg.end_date
    if end_str == "today":
        end_str = date_cls.today().strftime("%Y-%m-%d")
    end = pd.Timestamp(end_str)

    # P0-12: 優先用 adj_close 直接計算真實 CAGR（不依賴 raw open 執行價格）
    proxy = cfg.get("regime", {}).get("market_proxy", "0050")
    adj_path = os.path.join(BASE_DIR, "data", "adjusted", f"{proxy}.csv")
    if os.path.exists(adj_path):
        try:
            df_adj = pd.read_csv(adj_path, dtype={"date": str})
            df_adj["date"] = pd.to_datetime(df_adj["date"], format="%Y%m%d")
            df_adj = df_adj.sort_values("date").set_index("date")
            if "close_adj" in df_adj.columns:
                df_sub_adj = df_adj[(df_adj.index >= start) & (df_adj.index <= end)]
                years_avail = (
                    (df_sub_adj.index[-1] - df_sub_adj.index[0]).days / 365.25
                    if len(df_sub_adj) >= 2 else 0
                )
                if years_avail < 1:
                    raise ValueError(
                        f"0050 baseline 需至少 1 年資料（{start.date()} ~ {end.date()}），"
                        f"目前僅 {years_avail:.2f} 年（{len(df_sub_adj)} 列）。"
                        f"請先執行 python main.py fetch --list 0050 補充資料。"
                    )
                p0 = float(df_sub_adj["close_adj"].iloc[0])
                p1 = float(df_sub_adj["close_adj"].iloc[-1])
                if p0 > 0 and p1 > 0:
                    return (p1 / p0) ** (1 / years_avail) - 1
        except ValueError:
            raise
        except Exception:
            pass  # fallback to raw

    # P0-2: fallback — 用 raw open 執行法（原版）
    df_sub = market_df[(market_df.index >= start) & (market_df.index <= end)]
    years_avail = (df_sub.index[-1] - df_sub.index[0]).days / 365.25 if len(df_sub) >= 2 else 0
    if years_avail < 1:
        raise ValueError(
            f"0050 baseline 需至少 1 年資料（{start.date()} ~ {end.date()}），"
            f"目前僅 {years_avail:.2f} 年（{len(df_sub)} 列）。"
            f"請先執行 python main.py fetch --list 0050 補充資料。"
        )

    from src.strategy.backtest.engine import Backtester
    actions = ["HOLD"] * len(df_sub)
    actions[0] = "BUY"
    actions[-2] = "SELL"
    sig = pd.DataFrame({"action": actions}, index=df_sub.index)

    bt = Backtester(bt_cfg)
    result = bt.run_per_stock("0050_bh", df_sub, sig)
    if result.n_trades == 0:
        return float("nan")
    t = result.trades[0]
    h = max(t.hold_days, 1)
    return (1 + t.pnl_pct) ** (252 / h) - 1


def run_evaluate(run_id: str, cfg: dict = None) -> None:
    """重算指標、產 Markdown 報表"""
    from src.strategy.eval.reporter import save_summary_md
    from src.strategy.backtest.result import PortfolioResult, StockResult
    import pandas as pd

    if cfg is None:
        cfg = _load_strategy_cfg()

    bt_dir = os.path.join(BASE_DIR, "output", "backtest")
    ps_path = os.path.join(bt_dir, f"per_stock_{run_id}.csv")
    port_path = os.path.join(bt_dir, f"portfolio_{run_id}.csv")
    equity_path = os.path.join(bt_dir, f"equity_{run_id}.csv")

    if not os.path.exists(ps_path):
        print(f"[錯誤] 找不到 per_stock CSV：{ps_path}")
        return

    ps_df = pd.read_csv(ps_path)

    # 重建 StockResult（僅含指標，不重跑回測）
    stock_results = []
    for _, row in ps_df.iterrows():
        sr = StockResult(stock_id=str(row["stock_id"]))
        stock_results.append(sr)

    port_result = PortfolioResult()
    if os.path.exists(equity_path):
        eq = pd.read_csv(equity_path, index_col=0, parse_dates=True)
        port_result.equity_curve = eq.iloc[:, 0]

    if os.path.exists(port_path):
        port_df = pd.read_csv(port_path)
        if len(port_df) > 0 and "benchmark_cagr" in port_df.columns:
            v = port_df["benchmark_cagr"].iloc[0]
            port_result.benchmark_cagr = float(v) if not pd.isna(v) else float("nan")

    eval_cfg = {
        "portfolio": cfg.get("eval_portfolio", {}),
        "per_stock": cfg.get("eval_per_stock", {}),
    }
    md_path = save_summary_md(stock_results, port_result, run_id, eval_cfg)
    print(f"  報表已產出：{md_path}")
