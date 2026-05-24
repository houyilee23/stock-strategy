"""Signal journal writer — 從 run_signals 的 result_df 提取訊號落帳。

設計原則：
  * 只記 BUY / SELL（HOLD / N/A / ERROR 不進 journal，避免噪音）
  * signal_date 用 T 日（資料最後一筆），不是執行 wall-clock 日，這樣
    週末重跑 signals 不會產生重複的 journal_id
  * append-only：已存在的 journal_id 不覆寫（保留 validator 寫過的狀態）
"""
from __future__ import annotations
import math
import os
from datetime import datetime
import pandas as pd

from src.journal import storage
from src.journal.schema import (
    ALL_FIELDS, SIGNAL_FIELDS, STATUS_PENDING, make_journal_id,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 真正要落帳的 actions（generator 可能輸出更多種，但這兩個才是「掛單」訊號）
LOG_ACTIONS = {"BUY", "SELL"}


def _safe(v, default=None):
    """nan / None → default。"""
    if v is None:
        return default
    if isinstance(v, float) and math.isnan(v):
        return default
    return v


def _resolve_signal_date(sid: str) -> str | None:
    """T 日 = data/adjusted/{sid}.csv 最後一筆的日期 (YYYY-MM-DD)。

    用 adjusted 而非 raw，與策略訊號使用的資料來源一致（避免日期錯位）。
    """
    path = os.path.join(BASE_DIR, "data", "adjusted", f"{sid}.csv")
    if not os.path.exists(path):
        path = os.path.join(BASE_DIR, "data", "raw", f"{sid}.csv")
        if not os.path.exists(path):
            return None
    try:
        df = pd.read_csv(path, dtype={"date": str})
        if df.empty or "date" not in df.columns:
            return None
        last = df["date"].iloc[-1]
        # YYYYMMDD → YYYY-MM-DD
        if len(last) == 8 and last.isdigit():
            return f"{last[:4]}-{last[4:6]}-{last[6:8]}"
        # 已經是 ISO 格式 / 含 -
        if len(last) == 10 and last[4] == "-":
            return last
        return None
    except Exception:
        return None


def _row_to_journal(row: pd.Series, account: str,
                     stock_names: dict[str, str] | None = None) -> dict | None:
    """把 signals result_df 的一列轉成 journal row dict。

    過濾規則：
      * action 必須在 LOG_ACTIONS
      * 找得到 signal_date（資料最後一筆）

    回傳 None 表示這筆不該落帳。
    """
    action = str(row.get("action", "")).upper()
    if action not in LOG_ACTIONS:
        return None

    sid = str(row["stock_id"])
    signal_date = _resolve_signal_date(sid)
    if signal_date is None:
        return None

    # 決定 limit_price：BUY 用 target_buy；SELL 沒明確掛單時用 None
    # （SELL 訊號的「掛單」是 TP/SL，validator 會分別看 take_profit / stop_loss）
    if action == "BUY":
        limit_price = _safe(row.get("target_buy"))
    else:  # SELL
        # SELL 通常不直接給 limit_price；驗證時看 TP/SL 是否觸發
        # 但 target_tp/target_sl 可能其中之一存在
        limit_price = None

    name = ""
    if stock_names:
        name = stock_names.get(sid, "") or stock_names.get(str(sid), "") or ""

    return {
        "journal_id":       make_journal_id(signal_date, sid, account, action),
        "signal_date":      signal_date,
        "logged_at":        datetime.now().isoformat(timespec="seconds"),
        "account":          account,
        "sid":              sid,
        "name":             name,
        "template":         _safe(row.get("template"), "—"),
        "tier":             _safe(row.get("tier"), "—"),
        "action":           action,
        "ref_close":        _safe(row.get("close")),
        "limit_price":      limit_price,
        "stop_loss":        _safe(row.get("target_sl")),
        "take_profit":      _safe(row.get("target_tp")),
        "position_pct_max": _safe(row.get("position_pct_max"), 0.0),
        "market_regime":    _safe(row.get("market_regime"), "N/A"),
        "in_position":      bool(row.get("in_position", False)),
        "real_entry":       _safe(row.get("real_entry")),
        "real_shares":      int(_safe(row.get("real_shares"), 0) or 0),
        "reason":           _safe(row.get("reason"), ""),
        # validator 待填
        "status":           STATUS_PENDING,
        "validated_at":     None,
        "fill_date":        None,
        "fill_price":       None,
        "bars_to_fill":     None,
        # exit tracking phase 2
        "exit_date":        None,
        "exit_price":       None,
        "exit_reason":      None,
        "realized_return":  None,
        "hold_days":        None,
    }


def log_signals(result_df: pd.DataFrame, account: str,
                stock_names: dict[str, str] | None = None) -> dict:
    """把 run_signals 的 result_df 過濾後落帳。

    Returns dict: {"inserted": N, "skipped": M, "files": [paths]}
    """
    rows = []
    for _, row in result_df.iterrows():
        j = _row_to_journal(row, account, stock_names)
        if j is not None:
            rows.append(j)
    return storage.upsert_rows(rows)
