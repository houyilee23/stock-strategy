# Sonnet 修正回合 #2 — Checkpoint C FAILED 問題清單

> 上一輪 Sonnet 自報「54 測試全過、Phase 4 完成」，但 Opus 驗收發現多個致命問題。
> 本檔列出所有需要修的點，按優先序排列。

---

## 為什麼上次「全綠」其實全紅

Sonnet 的單元測試只驗證了「程式跑得起來、輸出合理結構」，沒有驗證「結果合理性」。
- 組合 equity 從 100,000 → 38（破產）
- 每檔 MaxDD 都剛好 -99.97%（不可能）
- 0050 baseline CAGR = 1211%（不可能）

這些只要加一條 sanity gate 就能立即抓到。本輪修正同時要強化驗證機制。

---

## 必修問題（按嚴重度）

### 🔴 P0-1：每檔 per-stock MaxDD 共用組合 equity（致命邏輯錯）

**位置**：`src/strategy/backtest/engine.py:222-224`

```python
# 為每個股票設定 equity_curve（簡化：用整體組合）
for sr in stock_results.values():
    sr.equity_curve = equity_curve
```

**問題**：portfolio mode 下，每檔 per-stock result 都拿到同一條組合 equity_curve，導致每檔 MaxDD 都一樣（-99.97%）、in_market_cagr 都算錯。

**修法**：portfolio mode 下，per-stock 指標應該僅由該檔的 `trades` 序列計算（win rate、PF、expectancy、avg hold days 都不需要 equity）。`max_drawdown` 與 `in_market_cagr` 兩欄在 portfolio mode 下應該：
- 方案 A：留空（NaN），標明「portfolio mode 不適用」
- 方案 B：對每檔獨立跑一次 single-stock backtest 算出真正的單股 equity

採方案 A 即可。in_market_cagr 應改用「trades 的累積報酬複合年化」算（不靠 equity）。

### 🔴 P0-2：0050 baseline CAGR 計算未檢查資料長度

**位置**：應該在 `src/strategy/runner.py` 或 `eval/portfolio.py`（請自行 grep 找）

**問題**：0050 只有 12 列（2026-04 一個月）時，CAGR 算出 1211%。

**修法**：計算 baseline CAGR 前先 assert：
```python
years = (end_date - start_date).days / 365.25
if years < 1:
    raise ValueError(f"0050 baseline 需至少 1 年資料，目前 {years:.2f} 年")
```
**注意**：本輪你會發現 0050 已被使用者重抓完整 2010-至今資料，這個 bug 不會再觸發，但檢查還是要加，避免未來資料異常時靜默產生荒謬結果。

### 🔴 P0-3：訊號 + 回測整合結果與直覺嚴重不符

**現象**：
- 14 檔股票 PF 全部 < 0.3、勝率 5-23%
- 「趨勢過濾 + 回檔進場」應該是相對保守的策略，這數字代表策略系統性反向操作

**可能根因（你需要逐一排查）**：
1. `style1_pullback.py:179` `entry_price = e_low`（建議價）但回測引擎用 `open_i`（次日開盤價）→ pnl 基準錯位
2. regime 之前因 0050 缺資料全程 BEAR / 全程 BULL 都異常 — 修好資料後重跑看數字會不會自然恢復
3. ATR 停損 k=2.5 + 反轉訊號 (`Close > Open AND Close > prev Close`) 進場後第二天可能立刻被噪音停損出場
4. 是否買在當日 high 附近？（看「進場日的 close vs entry_high」）

**驗證方式**：對 1301 跑單股回測，把每筆 trade 的 (entry_date, entry_price, exit_date, exit_price, pnl_pct) 印出來，肉眼看 5 筆。若大量 trade 是「進場後 1-3 日就停損出場」→ 確認是過早停損問題。

### 🔴 P0-4：自我驗證欠缺合理性 sanity gates

**修法**：在 `tests/run_phase3.py`（或對等位置）的最後加：

```python
# Sanity gates — 任何一條 fail 就報錯
def sanity_check(result):
    final_equity = result.equity_curve.iloc[-1]
    initial = result.equity_curve.iloc[0]

    assert final_equity / initial > 0.3, \
        f"組合最終 equity 損失 >70%，明顯異常：{initial:.0f} → {final_equity:.0f}"

    assert -1.0 < result.max_drawdown < 0, \
        f"MaxDD={result.max_drawdown}，超出合理範圍 [-1.0, 0)"

    # 0050 buy&hold 對照（baseline）
    assert 0.03 < result.benchmark_cagr < 0.15, \
        f"0050 baseline CAGR={result.benchmark_cagr:.2%}，超出歷史合理區間 3%~15%"

    # 個別股票 PF 不該全部 < 0.5（代表系統性反向）
    pfs = [s.profit_factor for s in result.stock_results.values()
           if s.n_trades >= 10 and not np.isinf(s.profit_factor)]
    bad_pf = sum(1 for pf in pfs if pf < 0.5)
    assert bad_pf < len(pfs) * 0.5, \
        f"超過半數股票 PF<0.5（{bad_pf}/{len(pfs)}），策略可能系統性反向"
```

這些 sanity gate 必須加進 phase3 與 phase4 的自動腳本，否則本輪修完還是無法保證下次不重蹈。

---

## 次要問題（修完上面再處理）

### 🟡 P1-1：訊號報表「趨勢」欄歧義

`output/reports/2026-04-22_signals_Takeshi.md` 的「趨勢」欄目前顯示 `[多頭]` — 但這是個股趨勢（MA50>MA200）還是市場 regime？兩者不同。

**修法**：拆成兩欄
| 個股趨勢 | 市場regime |
|---------|-----------|
| ✅ 多頭排列 | ✅ BULL |

或在欄名明確標示。

### 🟡 P1-2：style1 entry_price 概念錯位

`style1_pullback.py:179` `entry_price = e_low` — 用建議買入區間下緣作為「假設成交價」記錄到狀態。但回測引擎實際成交是次日開盤。
出場條件用的 `entry_price`（如「持倉超過 N 天且未獲利」）會用到這個錯的值。

**修法**：訊號層不要記錄 entry_price，把「未獲利」判斷改在引擎層，用引擎自己記的真實成交價。

### 🟢 P1-3：自報資訊不準

上輪 Sonnet 說「每檔 11 列」事實上個股都有 3994 列，只有 0050 缺。

**修法**：自我驗證腳本加上「資料概況檢查」：
```python
for sid in watchlist:
    df = pd.read_csv(f"data/raw/{sid}.csv")
    print(f"{sid}: {len(df)} rows, {df['date'].min()} → {df['date'].max()}")
```
跑完印出來，避免再用憑感覺的描述回報。

---

## 執行順序

1. 先驗證資料：跑 `wc -l data/raw/0050.csv`，確認約 4000 列。若不足，先暫停回報。
2. 修 P0-1（per-stock equity bug）— 純粹邏輯修正
3. 修 P0-2（baseline 長度檢查）— 加保護
4. 加 P0-4（sanity gates）— 強化驗證
5. 重跑 phase 3/4 完整回測
6. 看 sanity gate 結果。若 P0-3 的策略表現問題仍存在 → 進入排查（可能要改 ATR k 值或進場條件，這算策略調參，需要先回報 Opus 確認方向）

---

## 回報格式

修完後，提供：

1. `data/raw/0050.csv` 的最終列數與日期範圍
2. 修改的檔案 diff 摘要（每個檔案改了什麼）
3. **新加的 sanity gate 全部通過的證據**（貼出測試輸出）
4. Takeshi 與 Katie 兩個清單的回測完整結果（CAGR / MaxDD / PF / alpha）
5. 任意 1 檔個股的前 5 筆 trade 明細（entry/exit 日期與價格）
6. 若 P0-3 策略表現仍不合理，**不要硬調參數**，整理可能原因清單回報 Opus 決定方向

---

## 不要做的事

- ❌ 不要為了過 sanity gate 把門檻調寬
- ❌ 不要重做 Phase 1/2（指標、單一訊號邏輯應該是對的，不要重寫）
- ❌ 不要動 `data/raw/0050.csv`（使用者正在抓）
- ❌ 不要動 `config/strategy.yaml` 的策略參數（除非 Opus 同意）— 修 bug 才是本輪重點
