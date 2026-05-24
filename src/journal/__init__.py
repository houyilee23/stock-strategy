"""訊號日誌（signal journal）— 三層架構：

  writer    每次 signals 跑完，提取 BUY/SELL 訊號落帳到 月切 CSV
  validator 事後讀 OHLC 判斷掛單假定是否成交（用下一個出現的股價，自動跳過放假）
  reporter  讀多月份 CSV 出績效報表（命中率、浮動報酬、依 template/tier 拆解）

對外公開 API：

  from src.journal import log_signals, validate_all, write_report
  log_signals(result_df, account)                  # writer
  validate_all()                                   # validator（驗所有月份）
  write_report(start='2026-05', account='Takeshi') # reporter → MD 檔

CSV 儲存於 output/signal_journal/{YYYY-MM}.csv（append-only，依 journal_id 去重）。
完整設計文件：docs/SIGNAL_JOURNAL.md
"""
from src.journal.writer import log_signals
from src.journal.validator import (
    validate_partition, validate_all,
)
from src.journal.reporter import (
    write_markdown as write_report,
    print_console_summary,
    build_summary,
    group_summary,
)
from src.journal import storage, schema

__all__ = [
    "log_signals",
    "validate_partition", "validate_all",
    "write_report", "print_console_summary",
    "build_summary", "group_summary",
    "storage", "schema",
]
