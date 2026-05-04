# TODO：Audit 其他 templates 在限價單機制下的表現（家裡 PC 處理）

新增日期：2026-05-04（下班前）

---

## 用戶提出的問題

> 「那有檢查其他原本沒被選中的策略嗎？說不定在限價單功能加入後，其他策略會更好？」

**狀態**：尚未檢查。這是值得做的 audit。

---

## 為什麼要做

目前 `config/per_stock_recommendations.yaml` 中每檔的 `template` 欄位是 4/26 跑 auto_iterate 時用**舊機制（T+1 open 無條件成交）**選出來的。

5/4 加入限價單機制後：
- **同樣的 (template, params) 組合**：MaxDD 大幅降低、IM-CAGR 提升（已驗證 7 templates）
- **但「最佳 template」可能改變**：
  - 例如某檔現在被分到 `mean_reversion`，但若用 `donchian_breakout` 跑限價單可能更好
  - 或某檔目前是 F-tier，在新機制下某 template 可能反轉成可交易

→ **需要對每檔重新跑 7 個 limit-order template 做 audit**，找新機制下的 per-stock 最佳。

---

## 工程量估算

- 71 檔 × 7 templates = **497 個 backtest**
- 每個 ~1-3 秒（取決於資料量）
- 預估 **10~20 分鐘**（單檔 sequential；可並行加速）

---

## 推薦做法（兩段式）

### Phase 1：快速 audit（不改 best_params，只看哪些檔有改變）

寫一個 `scripts/audit_templates.py`：

```python
# 偽碼
for sid in 71_stocks:
    current_template = recommendations[sid]['template']
    results = {}
    for tpl in 7_limit_order_templates:
        params = load_best_params(tpl, sid)  # 從 merged auto_iterate yaml
        if not params: continue
        result = backtest_with_limit_order(sid, tpl, params)
        results[tpl] = {
            'cagr': result.in_market_cagr,
            'max_dd': result.max_drawdown,
            'pf': result.profit_factor,
            'n_trades': result.n_trades,
            'fill_rate': result.fill_rate,
        }
    # 用 risk-adjusted score 排名（例如 PF × log(n_trades)）
    best_new = pick_best(results)
    if best_new != current_template:
        print(f"⚠️  {sid}: 目前 {current_template}, 新最佳 {best_new}")
```

輸出：
- `output/audit_2026-05-04/template_comparison.csv` — 每檔 7 個 templates 的 metrics
- `output/audit_2026-05-04/changes.md` — 哪些檔的最佳 template 改變了

### Phase 2：是否更新 per_stock_recommendations.yaml？

**不要急著更新**，因為：
- best_params 仍是舊機制下優化的，新機制下未必是該 template 的最佳參數
- 例如 low_vol_pullback 的 take_profit_pct=0.09 在舊機制下最佳，但在新機制（intraday TP 觸發）可能 0.06 更好

**正確做法**：
- 看 audit 結果決定要不要做完整重訓
- 若大部分檔 best template 沒變 → 重訓不急
- 若顯著改變 → 進行完整重訓（見 `docs/TODO_RETRAIN.md`）

---

## 與重訓的關係

```
Phase 1 audit（10~20 分鐘）
   ↓ 結果決定下一步
   ├─ 若 best_template 改變 < 10% → 暫不重訓，繼續用 current best_params
   └─ 若改變 > 30% → 排重訓（2~5 小時，週末跑）
```

---

## 給家裡 PC Claude 的開場詞

```
我已經把限價單機制 v0.1 推到 7 個 templates。
請做兩件事：
1. 跑 docs/TODO_AUDIT_TEMPLATES.md 中的 Phase 1 audit
2. 完成後給我看 output/audit_2026-05-04/changes.md，我來決定要不要重訓
```

---

## 預期會看到的事

我的猜測（可驗證）：
1. **多數檔的 best template 不會改變**：因為新機制只是改成交模型，不改策略本質
2. **少數檔可能顯著改變**：
   - 某些原本 F-tier 的可能在限價單下變可交易（停損快、進場限價）
   - 某些原本 A-tier 的可能因 fill rate 過低（< 50%）變得不穩定
3. **fill rate 統計**：新指標。低 fill rate 的 template 不適合該檔（訊號常 miss）
