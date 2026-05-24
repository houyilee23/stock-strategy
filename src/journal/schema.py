"""Signal journal schema：欄位、狀態、partition 規則。

Single source of truth — writer / validator / reporter 都從這裡 import。
"""
from __future__ import annotations
from typing import Final

# ---- status 列舉（避免散落 magic string） -----------------------------------

STATUS_PENDING: Final[str]      = "pending"        # 剛落帳，還沒驗
STATUS_FILLED: Final[str]       = "filled"         # 假定掛單已成交
STATUS_NOT_FILLED: Final[str]   = "not_filled"     # 下一個交易日價格未觸及
STATUS_EXPIRED: Final[str]      = "expired"        # 連續 N 個交易日未觸及
STATUS_NO_DATA: Final[str]      = "no_data"        # 找不到對應股票資料
STATUS_SKIPPED: Final[str]      = "skipped"        # HOLD / N/A / ERROR，不參與驗證

ALL_STATUSES = (
    STATUS_PENDING, STATUS_FILLED, STATUS_NOT_FILLED,
    STATUS_EXPIRED, STATUS_NO_DATA, STATUS_SKIPPED,
)

# 預設過幾個交易日就標 expired（避免一直 pending 累積）
DEFAULT_EXPIRY_TRADING_DAYS: Final[int] = 10

# ---- CSV 欄位定義（順序即輸出順序）-----------------------------------------

# (1) 訊號落帳時就有的欄位
SIGNAL_FIELDS = [
    "journal_id",          # f"{signal_date}_{sid}_{account}_{action}"，unique key
    "signal_date",         # YYYY-MM-DD，T 日（資料最後一筆的日期，不是執行日）
    "logged_at",           # 落帳的 wall-clock 時間（ISO8601），純供 debug
    "account",             # Takeshi / Katie / universe / ...
    "sid",                 # 股票代號
    "name",                # 股票名稱（盡量帶上，方便人讀）
    "template",            # 策略 template 名稱
    "tier",                # A/B/C/D/E/F/S/—
    "action",              # BUY / SELL（HOLD 不落帳）
    "ref_close",           # T 日收盤（baseline）
    "limit_price",         # 掛單價：BUY → target_buy；SELL → target_tp 或 target_sl
    "stop_loss",           # target_sl（SELL 才有意義）
    "take_profit",         # target_tp（SELL 才有意義）
    "position_pct_max",    # 倉位上限（從 recommendations）
    "market_regime",       # BULL / BEAR
    "in_position",         # T 日是否已在倉（從 trades_{account}.csv）
    "real_entry",          # 在倉時的平均成本
    "real_shares",         # 在倉股數
    "reason",              # generator 給的 reason / 人讀備註
]

# (2) validator 補上的欄位
FILL_FIELDS = [
    "status",              # 見 STATUS_*
    "validated_at",        # validator 寫入時間
    "fill_date",           # 假定成交日（T+1 或之後）
    "fill_price",          # 假定成交價
    "bars_to_fill",        # 經過幾個交易日才 fill（filled / not_filled 才有）
]

# (3) 後續 Phase 2 — exit tracking（先預留欄位，validator 不會填）
EXIT_FIELDS = [
    "exit_date",
    "exit_price",
    "exit_reason",         # take_profit / stop_loss / time_stop / next_signal / manual
    "realized_return",     # (fill_price - exit_price) / fill_price，含手續費前
    "hold_days",
]

# 完整欄位（寫 CSV 時用這個順序）
ALL_FIELDS = SIGNAL_FIELDS + FILL_FIELDS + EXIT_FIELDS


def make_journal_id(signal_date: str, sid: str, account: str, action: str) -> str:
    """Composite unique key。同一天同一股同一帳號同一動作只會有一筆。"""
    return f"{signal_date}_{sid}_{account}_{action}"


def partition_for(signal_date: str) -> str:
    """signal_date='2026-05-23' → '2026-05'（月切檔名）。"""
    return signal_date[:7]
