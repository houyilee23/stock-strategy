# Sonnet 自主建置計畫

> 給接手實作的 Sonnet session 看。Opus 已完成設計，本檔是執行手冊。
> **核心原則：每階段做完就跑自我驗證腳本，全綠才進下一階段。失敗就修，修不好才停下回報。**

---

## 0. 起手式（必讀）

1. 先讀 `docs/SPEC_strategy_system.md` 整份
2. 確認 Python：`C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe -c "import pandas, numpy, yaml; print('OK')"`
3. 讀 `main.py`、`src/utils.py`、`src/screener.py`、`config/watchlists.yaml`、`config/settings.yaml` 摸清現有風格
4. 讀使用者 memory：`C:\Users\houyi.lee\.claude\projects\C--TronFuture-lee-stock\memory\bugs_fixed.md` — 過去踩過的雷必避

完成 0 後直接進 Phase 1，不需要回報 Opus。

---

## Phase 1 — 指標層 + 基礎設施

### 交付物
- `src/strategy/__init__.py`（空）
- `src/strategy/indicators/{trend,momentum,volatility,volume}.py`
- `config/strategy.yaml`（已由 Opus 提供初版）
- `tests/test_indicators.py` — 單元測試

### 指標清單與函式簽章
所有函式接受 `pd.DataFrame`（含 OHLCV 欄位 `open/high/low/close/volume`），回傳 `pd.Series` 或新欄位。

```python
# trend.py
def sma(close: pd.Series, n: int) -> pd.Series
def ema(close: pd.Series, n: int) -> pd.Series
def macd(close: pd.Series, fast=12, slow=26, signal=9) -> pd.DataFrame  # 含 macd/signal/hist 三欄
def adx(df: pd.DataFrame, n: int = 14) -> pd.Series  # ⚠️ 注意 bugs_fixed.md #1，最終 ADX 平滑只能用 EMA

# momentum.py
def rsi(close: pd.Series, n: int = 14) -> pd.Series
def roc(close: pd.Series, n: int) -> pd.Series  # rate of change
def momentum_12_1(close: pd.Series) -> pd.Series  # 12月-1月動量

# volatility.py
def atr(df: pd.DataFrame, n: int = 14) -> pd.Series
def bollinger(close: pd.Series, n: int = 20, k: float = 2.0) -> pd.DataFrame  # 含 mid/upper/lower

# volume.py
def volume_ma(volume: pd.Series, n: int = 20) -> pd.Series
def obv(close: pd.Series, volume: pd.Series) -> pd.Series
```

### 自我驗證（必跑）
建立 `tests/test_indicators.py`，至少覆蓋：

1. **常數序列測試**：`close = [100]*100` → RSI 應為 50（恆定），SMA 為 100，ATR 應趨近 0
2. **單調遞增測試**：`close = range(100, 200)` → RSI 應 > 70，SMA 隨之上升
3. **已知答案測試**：載入 `data/raw/0050.csv` 計算 RSI(14)，最後一個值與手動計算（pandas 重算）對照
4. **ADX 防呆**：對 0050 計算 ADX(14)，斷言 0 < adx.mean() < 80（避免重蹈 bug #1，平均 525 那種錯誤）
5. **NaN 處理**：所有指標前 N-1 個值應為 NaN，第 N 個之後不應有 NaN

跑法：
```
C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe -m pytest tests/test_indicators.py -v
```

### Phase 1 通過條件
- 所有單元測試 pass
- 對 `data/raw/0050.csv` 計算所有指標不報錯，輸出無 inf

**通過後直接進 Phase 2，不需回報 Opus。**

---

## Phase 2 — 訊號層 + Regime

### 交付物
- `src/strategy/signals/regime.py`
- `src/strategy/signals/style1_pullback.py`（風格 1）
- `src/strategy/signals/style2_momentum.py`（風格 2）
- `tests/test_signals.py`

### 函式簽章
```python
# regime.py
def detect_regime(market_df: pd.DataFrame, ma_long: int = 200) -> pd.Series
# 回傳 'BULL' / 'BEAR' 序列，index 對齊 market_df

# style1_pullback.py
def generate_signals(df: pd.DataFrame, market_regime: pd.Series,
                     params: dict) -> pd.DataFrame
# 回傳含欄位：action(BUY/SELL/HOLD), entry_low, entry_high, stop_loss, reason

# style2_momentum.py
def rank_universe(price_dict: dict[str, pd.DataFrame],
                  asof_date: pd.Timestamp,
                  params: dict) -> pd.DataFrame
# 回傳：stock_id, momentum_score, rank（依 score 降冪）
```

### Style 1 規則（嚴格按 SPEC §5.1）
進場 BUY 條件全部滿足：
1. `Close > MA200` AND `MA50 > MA200`
2. `market_regime == 'BULL'`
3. `RSI(14) < 40` OR `Close < BollLower`
4. `Close > Open` AND `Close > prev Close`
5. `Volume > Volume_MA20 × 0.8`

出場 SELL 任一滿足：
1. `Close < HighestSinceEntry − k×ATR(14)`，k=2.5
2. `Close < MA200` 連續 2 日
3. `RSI(14) > 80` AND `Close > BollUpper`
4. 持倉 ≥ 120 日且當前未獲利

「HighestSinceEntry」需要狀態追蹤 — 在 generate_signals 內維護一個指標欄位即可。

### 自我驗證
1. 對 0050 跑 style1_pullback，斷言 BUY 訊號數 < 100（10年資料、不該太頻繁）
2. 斷言每個 BUY 後的下一個出場訊號是 SELL（不會連續兩個 BUY）
3. 對 2330 跑，BUY 訊號當天打印前 5 筆，人工肉眼檢查（log 印出即可，給 Opus 看）
4. regime 測試：0050 在 2020Q1 應有 BEAR 期間（COVID 崩盤）

跑法：
```
C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe -m pytest tests/test_signals.py -v
```

### Phase 2 通過條件
- 單元測試 pass
- 0050 / 2330 訊號數符合「不過頻」直覺
- 訊號輸出 CSV 寫到 `output/signals_phase2_check.csv`，含至少 5 筆 BUY 與 5 筆 SELL

**🛑 Phase 2 結束 → 回報 Opus 檢查訊號邏輯**
回報內容應包含：
- 0050 的 BUY/SELL 次數與分佈
- 2330 前 5 筆 BUY 訊號的日期與當時的 RSI / MA200 等指標值
- 任何實作上不確定的判斷（例如「持倉 120 日」是用交易日還是日曆日）

---

## Phase 3 — 回測引擎 + 評價層

### 交付物
- `src/strategy/backtest/{engine,fees,result}.py`
- `src/strategy/eval/{per_stock,portfolio,reporter}.py`
- `src/strategy/portfolio/allocator.py`
- `tests/test_backtest.py`

### 引擎核心
依 SPEC §6 實作。重點：
- **時間軸**：訊號 T 日產生，T+1 開盤成交
- **滑價**：買入 `price × 1.003`，賣出 `price × 0.997`
- **手續費**：`max(20, amount × 0.001425)`，賣出再加 `amount × 0.003` 證交稅
- **零股**：股數可為任意正整數
- **單股回測**：每次只投入一檔，全部資金；用來計算單股層指標
- **組合回測**：依 sizing_fn 配置；記錄 daily equity curve

### 評價計算
依 SPEC §4.1、§4.2。注意：
- In-market CAGR：分母只算「持倉日數 / 252」，不是總期間
- Profit Factor：總獲利 / |總虧損|，若無虧損則回傳 inf（報告時印「∞」）
- alpha vs 0050：用相同期間的 0050 buy&hold 年化作為 baseline

### 自我驗證
1. **零訊號測試**：所有 signals 都是 HOLD → equity curve 應為平行線
2. **buy&hold 對照**：用「Day1 BUY, 最後一日 SELL」訊號跑 0050，CAGR 應落在 5%~10%
3. **手續費正確性**：單筆交易扣除金額 == 公式手算
4. **組合測試**：對 Takeshi 清單跑組合回測，斷言報表 CSV 產出且 daily equity 不含 NaN
5. **時間防穿越**：在訊號的最後一日插入未來資訊（人工 hack），確認結果不變（如果變了代表有 look-ahead）

跑法：
```
C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe -m pytest tests/test_backtest.py -v
```

### Phase 3 通過條件
- 所有測試 pass
- 對 Takeshi 清單跑完整組合回測，產出 `output/backtest/portfolio_phase3_check.csv` 與 daily equity
- 0050 buy&hold 對照 CAGR 落在合理區間

**🛑 Phase 3 結束 → 回報 Opus 檢查回測結果**
回報內容應包含：
- Takeshi 清單組合回測的 CAGR / MaxDD / Sharpe / vs 0050 alpha
- 表現最好與最差的 3 檔股票（單股層）
- 任何看起來「太好」或「太差」的可疑數字 — 主動標出

---

## Phase 4 — CLI 整合 + 每日訊號報表

### 交付物
- 修改 `main.py`：加上 `signals` / `backtest` / `evaluate` 三個指令
- `src/strategy/eval/reporter.py` 完整版（支援 markdown 報告）
- `output/reports/{date}_signals_{account}.md` — 每日建議報告

### CLI 規格
```
python main.py signals --list Takeshi
  → 對 Takeshi 清單每檔跑 style1，產出今日建議
  → 輸出 console 表格 + output/reports/{今日}_signals_Takeshi.md
  → 表格欄位：股票, action, 收盤價, 建議買入區間, 建議停損, RSI, MA200狀態, 一句話說明

python main.py backtest --list Takeshi [--start 2017-01-01 --end today]
  → 訊號模式：每檔股票各自回測，輸出 per_stock CSV

python main.py backtest --list Katie --portfolio
  → 組合模式：跑 style2 的 top-N 配置回測，輸出 portfolio CSV + daily equity

python main.py evaluate --run-id <id>
  → 重算指標、產 markdown 報表
```

### 報表格式（每日訊號）
```markdown
# 今日訊號 — Takeshi (2026-04-22)

| 股票 | 名稱 | 收盤 | 動作 | 建議買入 | 建議停損 | RSI | 趨勢 | 說明 |
|------|------|------|------|---------|---------|-----|------|------|
| 1301 | 台塑 | 53.4 | HOLD | — | 50.2 | 45 | ✅ 多頭 | 持倉中，停損上移 |
| 2330 | 台積電 | 1080 | BUY | 1065~1075 | 1020 | 38 | ✅ 多頭 | 回檔進場機會 |
| ...  |
```

### 自我驗證
1. `python main.py signals --list Takeshi` 跑通且產出 md 檔
2. `python main.py backtest --list Takeshi` 跑通，per_stock CSV 14 列
3. `python main.py backtest --list Katie --portfolio` 跑通，產出 portfolio CSV
4. 對所有 CLI 指令跑 `--help`，不報錯

### Phase 4 通過條件
- 三個 CLI 指令全部跑通
- 報表格式符合上方範例
- 對 Takeshi 與 Katie 都跑過完整流程

**🛑 Phase 4 結束 → 回報 Opus 全面驗收**
回報內容：
- 三個 CLI 的執行結果（貼出 console 輸出）
- 兩份報表的範例（貼幾行）
- 任何已知缺陷或未完成項目

---

## 自動化執行腳本

每階段提供一鍵跑全部驗證的腳本：

```
tests/run_phase1.sh    # 或 .py
tests/run_phase2.sh
tests/run_phase3.sh
tests/run_phase4.sh
```

每個腳本失敗時應 exit code != 0，console 印出失敗點。

---

## 失敗處理規則

1. **可自行修復的**（語法錯、import 錯、明顯邏輯錯）：直接修，重跑驗證，不用回報
2. **設計不明確**（spec 沒寫到的細節）：自己判斷一個合理選擇，**在 commit message 或回報時標明「決策點：XXX，採 YYY 因為 ZZZ」**
3. **可能影響評價結果的判斷**（例如手續費公式、停損優先順序）：先做、再回報
4. **真的卡住**：把錯誤訊息、嘗試過的方法、卡住的具體點寫成 `docs/BLOCKED_phase{N}.md`，停下回報

---

## 不要做的事

- ❌ 不要寫進度 markdown / status report 檔案 (除非 BLOCKED)
- ❌ 不要動 `data/raw/` 的任何檔案
- ❌ 不要修改 `config/watchlists.yaml`（這是使用者資產）
- ❌ 不要為了過測試硬調參數，要先理解為什麼 fail
- ❌ 不要 commit 大量產出檔案 (output/ 應加入 .gitignore；目前無 git，但別塞進專案根)
- ❌ 不要在沒跑驗證腳本前自稱「Phase X 完成」
