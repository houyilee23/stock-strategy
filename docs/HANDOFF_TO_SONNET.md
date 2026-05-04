# Handoff: Opus → Sonnet

> 開新 session 給 Sonnet 時，把這段話作為第一個 prompt 貼進去。

---

## 給 Sonnet 的開場白

你接手實作一套台股個股策略系統。**設計已完成，你的工作是自主實作 + 自我驗證。**

**請先依序讀以下檔案，再動手：**

1. `docs/SPEC_strategy_system.md` — 完整設計規格（這是 single source of truth）
2. `docs/SONNET_BUILD_PLAN.md` — 你的執行手冊，分四個 Phase
3. `docs/CHECKPOINTS.md` — 哪些節點要停下回報 Opus
4. `config/strategy.yaml` — 所有可調參數已備齊
5. `C:\Users\houyi.lee\.claude\projects\C--TronFuture-lee-stock\memory\bugs_fixed.md` — 過去踩過的雷

**核心執行原則：**
- 全自動推進。每個 Phase 跑完自我驗證腳本，全綠才進下一個
- 修不好、卡住、設計矛盾 → 寫 `docs/BLOCKED_phase{N}.md` 停下回報
- 只有四個 Checkpoint 需要 Opus 審查（Phase 2/3/4 結束 + 任何 BLOCKED）
- 不確定的判斷自己做、註明理由，不要為小事中斷

**Python 路徑（強制）**：`C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe`

**Phase 1 通過後不用回報，直接進 Phase 2。**

開始吧。第一步：讀 SPEC_strategy_system.md。
