# 台股個股策略系統 — 設計規格 (v1)

> 由 Opus 撰寫，交給 Sonnet 自主實作。
> 所有設計決策已與使用者 Takeshi 確認。修改本檔需先告知。

---

## 1. 系統定位

雙模式策略系統：

- **訊號模式 (signal mode)**：對 watchlist 中每檔股票各自產生「進場 / 出場 / 持有 + 建議價位區間」。Takeshi 用，配置由人手動決定。
- **組合模式 (portfolio mode)**：在訊號模式之上，加一層資金配置邏輯（同時持幾檔、每檔多少錢、何時換股）。Katie 用。

兩模式共用：資料層、指標層、訊號層、回測引擎、評價框架。差異只在「最上層的決策包裝」。

---

## 2. 使用者場景與資金條件

| 使用者 | 資金規模 | 模式 | 持倉風格 |
|---|---|---|---|
| Takeshi | ~3 萬 | 訊號模式為主 | 個別判讀進出，零股交易 |
| Katie | ~10 萬 | 組合模式 | 系統決定配置，月頻 rebalance |

- 市場：TWSE（TPEX 暫緩）
- 操作頻率：每日盤後看一次
- 下單方式：手動（券商 app），不做自動化
- 持倉過夜 OK，不做當沖

---

## 3. 目標與限制

| 項目 | 設定 |
|---|---|
| 主目標 | 長期年化打贏 0050 (alpha > 0) |
| 評價窗口 | 7~10 年（含完整牛熊循環） |
| 可接受 MaxDD | ≤ 30% |
| 交易單位 | **零股為主**（涵蓋整股） |
| 滑價假設 | 0.3%（買賣各 0.3%） |
| 手續費 | 買 0.1425% + 賣 0.1425% + 賣方交易稅 0.3% |
| 零股費率調整 | 實際觀察 0.5%~1.5%，回測時統一用上述公式即可，誤差由滑價吸收 |
| 最低手續費 | 多數券商 NT$20，單筆金額過小時須加上 |

---

## 4. 評價基準（方案 A：雙層分離評分）

### 4.1 單股層指標（per-stock，訊號模式核心）

針對「單檔股票上單一策略」的回測結果，計算：

| 指標 | 定義 | 合格門檻（暫定） |
|---|---|---|
| 交易次數 (N) | 完整買賣回合數 | ≥ 10 才算有統計意義 |
| 勝率 (Win Rate) | 獲利交易數 / N | — (與 PF 配合看) |
| 平均獲利 / 平均虧損 | 個別交易報酬均值 | — |
| **每筆交易期望值 E** | `WR × AvgWin − (1−WR) × |AvgLoss|` | > 0 |
| **Profit Factor (PF)** | 總獲利 / 總虧損絕對值 | ≥ 1.5 |
| 持倉期間年化 (In-market CAGR) | 只計入持倉日數的年化 | > buy&hold of same stock |
| 單股 MaxDD | 策略對該股的最大回檔 | ≤ 30% |
| 平均持有天數 | — | 用來判斷策略性質 |
| 年均交易次數 | N / years | 過密代表手續費侵蝕嚴重 |

**「閒置資金失真」問題**在此層完全繞過：分母是「有持倉的天數」，沒有資金閒置概念。

### 4.2 組合層指標（portfolio，組合模式 + 多股加總）

針對「整個資金池在 14 檔上跑策略」的整體結果：

| 指標 | 定義 | 合格門檻 |
|---|---|---|
| 組合 CAGR | 整個資金池的年化報酬 | > 0050 同期 CAGR |
| 組合 MaxDD | 整體資金最大回檔 | ≤ 30% |
| Sharpe Ratio | (CAGR − rf) / σ；rf = 0 即可 | > 0.5 |
| **vs 0050 alpha** | 組合 CAGR − 0050 同期 CAGR | > 0（核心 KPI） |
| 資金利用率 | 平均「持倉資金 / 總資金」 | 報告即可，不設門檻 |
| 換手率 | 年總成交量 / 平均持倉 | 報告即可 |

### 4.3 報表規格

回測完成後產出兩份 CSV：

- `output/backtest/per_stock_{run_id}.csv` — 每檔股票一列，欄位為 4.1 的所有指標
- `output/backtest/portfolio_{run_id}.csv` — 一列摘要 + 一份 daily equity curve

額外產出 `output/backtest/{run_id}_summary.md`，給人看的報告，含：
- 整體結論（PASS / FAIL 對門檻）
- 表現最好 / 最差的 3 檔股票
- 與 0050 同期 buy&hold 對照圖數據

---

## 5. 策略設計

### 5.1 風格 1：趨勢過濾 + 回檔進場（訊號模式核心）

**進場條件**（全部成立才 BUY）：
1. 長期趨勢 OK：`Close > MA200` AND `MA50 > MA200`（黃金排列）
2. 大盤 regime OK：0050 (或 TAIEX) `Close > MA200`
3. 短期回檔：`RSI(14) < 40` OR `Close < BollLower(20, 2)`
4. 出現反轉訊號：當日 `Close > Open` AND `Close > 前一日 Close`
5. 量能配合：當日 `Volume > MA(Volume, 20) × 0.8`（不要極度量縮）

**出場條件**（任一成立即 SELL）：
1. ATR 移動停損：`Close < HighSinceEntry − k × ATR(14)`，預設 k=2.5
2. 趨勢破壞：`Close < MA200` 連續 2 日
3. 超漲止盈（可選）：`RSI(14) > 80` AND `Close > BollUpper(20, 2)`
4. 持倉超過 N 天且未獲利：N=120 預設

**價位建議**（每日輸出）：
- 若「無持倉 + 接近進場條件」：給「建議買入區間」 = [今日 Low, 前一日 Low]，上限不超過 MA20
- 若「有持倉」：給「建議停損價」 = max(ATR 停損價, MA200)
- 若「持倉中且 RSI > 70」：給「警示：接近超漲區間」

### 5.2 風格 2：動量排序 + Top-N 等權（組合模式配置層）

每月最後交易日：
1. 對 watchlist 每檔計算 12-1 月動量（過去 12 個月報酬扣掉最近 1 個月，標準動量定義）
2. 套用 regime filter（5.1 #2）；regime FAIL 時整體現金
3. 取動量排名前 N 檔（N=5 暫定，可調）
4. 等權配置；下個月維持
5. 月底重新排序，異動的部位下個月初換股

**重要**：組合模式仍要過 5.1 的個股訊號層 — 動量排前 N 但訊號 SELL 的，不買進；動量出 top-N 但訊號未觸發 SELL 的，可保留至下次 rebalance。

### 5.3 共用：Regime Detection

獨立模組 `src/strategy/signals/regime.py`：
- 以 0050 (台灣市場代理) 為輸入
- `regime = "BULL" if Close > MA200 and MA50 > MA200 else "BEAR"`
- 兩種模式都呼叫此函式

---

## 6. 回測引擎規格（自刻 pandas 輕量版）

### 6.1 設計原則
- 純 pandas 向量化 + 必要時 for-loop 單股 event loop
- 不引入 vectorbt / backtrader
- 預期程式碼總量 < 500 行
- 雙模式共用同一個 `Backtester` 類別，差別在傳入的 `position_sizing` 函式

### 6.2 介面設計

```python
# src/strategy/backtest/engine.py

class Backtester:
    def __init__(self, config: BacktestConfig):
        self.config = config  # 含手續費、滑價、起始資金、起訖日

    def run_per_stock(self, stock_id: str, signals: pd.DataFrame) -> StockResult:
        """單股回測，輸出單股層指標 (4.1)"""

    def run_portfolio(self, signals_dict: dict[str, pd.DataFrame],
                      sizing_fn) -> PortfolioResult:
        """組合回測，輸出組合層指標 (4.2)"""
```

### 6.3 成交模型
- 訊號日 = T，成交日 = T+1 開盤價（避免 look-ahead）
- 成交價 = 開盤價 × (1 + 滑價)（買）or × (1 − 滑價)（賣）
- 手續費按公式扣除，最低 NT$20
- 零股無條件接受全額成交（流動性假設不考慮）

### 6.4 資金管理（組合模式預設）
- 起始資金：可由 config 指定（預設 100,000）
- 配置上限：單檔最多 25% 資金（避免集中風險）
- 現金部位無利息

---

## 7. 模組結構

```
src/strategy/
├── __init__.py
├── indicators/
│   ├── __init__.py
│   ├── trend.py          # MA, MACD, ADX
│   ├── momentum.py       # RSI, ROC, 12-1 momentum
│   ├── volatility.py     # ATR, BollingerBands
│   └── volume.py         # OBV, Volume MA
├── signals/
│   ├── __init__.py
│   ├── regime.py         # 大盤 regime detection
│   ├── style1_pullback.py  # 風格1：趨勢回檔
│   └── style2_momentum.py  # 風格2：動量排序
├── backtest/
│   ├── __init__.py
│   ├── engine.py         # Backtester 核心
│   ├── fees.py           # 手續費 / 滑價 / 稅
│   └── result.py         # StockResult / PortfolioResult dataclass
├── eval/
│   ├── __init__.py
│   ├── per_stock.py      # 單股層指標計算
│   ├── portfolio.py      # 組合層指標計算
│   └── reporter.py       # CSV / Markdown 報表輸出
└── portfolio/
    ├── __init__.py
    └── allocator.py       # Top-N 等權配置邏輯
```

新增 CLI：
```
python main.py signals --list Takeshi              # 訊號模式：對清單產出今日建議
python main.py backtest --list Takeshi             # 訊號模式回測（單股層）
python main.py backtest --list Katie --portfolio   # 組合模式回測
python main.py evaluate --run-id 20260422_120000   # 重算指標、產報表
```

---

## 8. 設定檔 `config/strategy.yaml`

新建檔。所有可調參數集中於此，避免散落程式碼。Sonnet 實作時必須讀此檔，不得 hardcode 數值。

預設值見實作交付後的 `config/strategy.yaml` 樣板（見另一份檔案）。

---

## 9. 重要約束（Sonnet 必須遵守）

1. **不得 hardcode 任何 magic number**。所有參數讀 `config/strategy.yaml`。
2. **不得引入新的回測框架**（vectorbt / backtrader / zipline）。
3. **時間防穿越**：所有訊號計算只能用「當日及之前」的資料；成交在 T+1。
4. **沿用現有設施**：`src/utils.py` 的 PATHS / logger / settings；`main.py` 的 CLI dispatch；`config/watchlists.yaml` 的清單機制。
5. **錯誤要落到 `output/errors/{date}.csv`**（沿用既有 `log_error()`），不要 silent fail。
6. **Python 路徑**：執行測試請用 `C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe`（base anaconda，有 pandas/numpy/yaml）。
7. **編碼**：CSV 寫入用 `utf-8-sig`，與既有風格一致。
8. **Bug history 警告**：見 memory `bugs_fixed.md`。特別注意 ADX 計算（wilder() 不能用在最終 ADX 平滑步驟）、Risk/Reward 要用 entry 價而非 close。

---

## 10. 不在本期範圍

- 自動篩選新標的（screener 已有，但選股邏輯不擴充）
- 自動下單 / 券商 API 串接
- TPEX 上櫃股票（資料源待修）
- 月線時間框架（資料量不足）
- 機器學習模型
- 走前最佳化 (walk-forward optimization) — 第二期再做

---

## 11. 成功定義（驗收）

整套系統交付完成，需通過以下關卡（自動 + Opus 審查混合）：

1. ✅ 單元測試：所有指標對照已知數值通過
2. ✅ 整合測試：對 0050 跑 buy&hold，CAGR 落在歷史合理區間（5%~10%）
3. ✅ 訊號模式：對 1301、2330 各跑一次回測，per-stock 報表產出且指標非 NaN
4. ✅ 組合模式：對 Takeshi watchlist 跑一次組合回測，portfolio 報表產出
5. ✅ 與 0050 對照：組合模式 7 年 CAGR ≥ 0050 同期 CAGR（容許小幅低於，重點是 alpha 趨近 0 以上）
6. ✅ 每日訊號：`python main.py signals --list Takeshi` 跑通並產出今日建議

詳細關卡與自動化檢查腳本見 `docs/SONNET_BUILD_PLAN.md`。
