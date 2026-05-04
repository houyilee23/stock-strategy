# Handoff: Opus → Sonnet (Round 2 - 修 bug)

> 開新 Sonnet session 時，把這段話貼進去當第一個 prompt。

---

## 給 Sonnet 的開場白

上一輪 Sonnet 自報「Phase 4 完成」，但 Opus 驗收失敗 — 多個致命 bug 與假陽性自我驗證。

**你的任務：依 `docs/SONNET_FIX_ROUND2.md` 修 bug，不重做整套系統。**

**請先依序讀：**

1. `docs/SONNET_FIX_ROUND2.md` — 問題清單與修法（這是本輪 single source of truth）
2. `docs/SPEC_strategy_system.md` — 原始設計（沒變）
3. `CLAUDE.md` — 專案約束
4. `~/.claude/projects/C--TronFuture-lee-stock/memory/bugs_fixed.md` — 過往 bug 教訓

**核心執行原則：**
- 全自動推進，依 SONNET_FIX_ROUND2.md 的「執行順序」一條條做
- **每步加新 sanity gate，不只是讓舊測試通過**
- 最後依「回報格式」整理結果，回報 Opus
- 卡住就寫 `docs/BLOCKED_round2.md`

**執行前先確認**：`wc -l data/raw/0050.csv` 應該約 4000 列（使用者已重抓）。若仍 < 1000，停下回報。

**Python 路徑（強制）**：`C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe`

開始吧。
