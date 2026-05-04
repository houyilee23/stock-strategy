# Opus 審查關卡 (Checkpoints)

> Sonnet 在以下節點停下、回報、等 Opus 確認後再進下一階段。
> 每個 checkpoint 都有「自動可決定」與「需要 Opus 判斷」的明確分界。

---

## Checkpoint A — Phase 2 結束（訊號邏輯）

**為什麼需要 Opus**：訊號的「合理性」沒有單元測試能驗證。次數太多代表雜訊，太少代表過嚴；BUY 點是否打在「該打的位置」要人眼判斷。

**Sonnet 應提供**：

1. 對 0050 跑 style1 後的訊號統計：
   - BUY 總數、SELL 總數
   - 平均持倉天數
   - 訊號分佈（每年幾筆）
2. 對 2330 跑 style1 後的前 5 筆 BUY 訊號明細：
   - 日期 / 收盤價 / RSI(14) / Close 與 MA200 比例 / Volume 比 MA20
3. 對 0050 跑 regime 後，2020Q1 的 regime 變化日（驗證 COVID 崩盤被識別）

**Opus 判斷重點**：
- 訊號頻率合理嗎？（10 年 < 50 筆 BUY 算正常）
- BUY 訊號出現時的指標值是否符合「回檔進場」直覺？
- 有沒有看起來明顯該進場但沒進、或明顯不該進場卻進了的情況？

**通過 → 進 Phase 3**

---

## Checkpoint B — Phase 3 結束（回測結果）

**為什麼需要 Opus**：回測指標即使技術上正確，也可能存在 look-ahead、survivor bias、不合理的「過好」結果。需要對「合理數字範圍」做 sanity check。

**Sonnet 應提供**：

1. **0050 buy&hold 對照**：2017-01-01 ~ today 的 CAGR、MaxDD、Sharpe
2. **Takeshi 清單組合回測**結果摘要：
   - 組合 CAGR、MaxDD、Sharpe
   - vs 0050 alpha
   - 資金利用率 (in-market %)
3. **單股層 Top 3 與 Bottom 3**：14 檔中表現最好與最差各 3 檔的 per-stock 指標
4. **可疑數字主動標記**：任何 win rate > 80%、PF > 5、單筆獲利 > 50% 等都要標出

**Opus 判斷重點**：
- 0050 CAGR 是否落在 5%~10%？太高代表手續費沒算對；太低代表時間軸有問題
- 組合 CAGR 是否在 -5% ~ +20% 範圍？極端值通常有 bug
- alpha 是否合理？前期不需要強到爆，求穩定為上
- MaxDD 是否真的 ≤ 30%？超過要解釋為什麼

**通過 → 進 Phase 4**

---

## Checkpoint C — Phase 4 結束（全面驗收）

**為什麼需要 Opus**：使用體驗、報表清晰度、跨指令的一致性。

**Sonnet 應提供**：

1. `python main.py signals --list Takeshi` 完整 console 輸出
2. `python main.py signals --list Katie` 完整 console 輸出
3. 每日訊號 markdown 報表的實際內容
4. `python main.py backtest --list Takeshi` 完整輸出 + per_stock CSV 全文
5. `python main.py backtest --list Katie --portfolio` 完整輸出 + portfolio CSV 全文
6. 已知缺陷或未實作項目清單

**Opus 判斷重點**：
- 報表是否「直觀好懂」（使用者要求的 KPI）
- 兩使用者的輸出是否合理區分（訊號模式 vs 組合模式）
- 是否有需要二期再做的功能浮現

**通過 → 系統可上線使用**

---

## 什麼情況 Sonnet 應主動 ping Opus（非預定 checkpoint）

1. 發現 SPEC 有矛盾或漏洞，影響大方向
2. 連續嘗試 3 次仍無法通過某 phase 的自我驗證
3. 發現現有 codebase 有阻礙設計實現的問題（例如 `src/utils.py` 介面不適用）
4. 評估後認為某設計決策（例如 ATR k=2.5）顯著影響結果，想徵求調整意見

ping 方式：寫 `docs/PING_OPUS_{topic}.md`，內容含：
- 觸發點
- 問題具體描述
- 已嘗試的方法
- 你建議的處理方式 + 替代方案

---

## 對使用者的彙報

每個 checkpoint 通過時，Sonnet 應額外寫 `output/reports/checkpoint_{phase}_summary.md`，給使用者 Takeshi 看。內容用繁體中文，3-5 句話，重點是：

- 這個階段做完了什麼
- 對使用者最重要的「能用什麼」
- 下一階段會做什麼
- 如果有任何需要使用者決定的事，明確列出

不要塞技術細節，使用者要的是「現在我能用什麼」。
