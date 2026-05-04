# Handoff: P0 Scaling-Out + P1 Bootstrap + Tiering

**Goal**：把目前 holdout 後只剩 2 檔可操作（2308, 2330）拉到 ≥ 20 檔，方法是：
1. **P0**：在 per-stock backtest 加入 scaling-out（分批出場）→ 降低 DD、把 BORDERLINE_DD 拉成 PASS
2. **P1**：用 Bootstrap PF 信賴區間 + 分級制度（S/A/B/C/F）取代「過/不過」二元判定 → 用部位大小換覆蓋率

**Run id 命名**：新一輪用 `python main.py auto_iterate --universe all`，自動產生 `YYYYMMDD_HHMMSS`。

**禁止改動**：
- `config/watchlists.yaml`（使用者資產）
- `config/strategy.yaml` 的 `fees` 區塊（買賣 0.1425% + 0.3% 滑價 + 0.3% 證交稅）
- `data/` 任何檔案

**必須使用**：
- Python `'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe'`
- Bash 工具（不要 PowerShell）
- 繁體中文回應 / 註解

---

## P0：Scaling-Out Exits

### 目標
讓贏家騎更久、輸家分批出，把 -32%~-37% 的 BORDERLINE_DD 壓到 30% 以下。

預期效果：3017×trend_pullback、6669×chip_momentum、2317×momentum_hold、2337×chip_momentum 等候選有機會升級為 PASS。

### 實作位置
- `src/strategy/backtest/engine.py` — 主要改動
- `src/strategy/backtest/result.py` — `TradeRecord` 改用 weighted avg
- `config/strategy.yaml` — 加 `scaling` 區塊
- `src/strategy/auto_iterate/templates.py` — 每個 template 宣告預設 `scaling_pattern`

### Scaling Pattern 規格

採用 **P2 階梯出場（scaling out）** 為唯一新增 pattern（P1 pyramiding 與 P3 confidence sizing 留待後續）：

```yaml
# config/strategy.yaml 新增
scaling:
  enabled: true
  pattern: "P2_scale_out"           # 目前只支援 P2，預留欄位
  P2_scale_out:
    # 分批出場規則
    legs:
      - profit_pct: 0.10            # 漲 10% 出 1/3
        sell_fraction: 0.333
      - profit_pct: 0.20            # 漲 20% 再出 1/3
        sell_fraction: 0.500        # 剩餘部位的 1/2 = 原始的 1/3
    # 剩餘 1/3 用 trailing stop
    trailing:
      method: "chandelier"          # high - k * ATR
      atr_period: 22
      atr_mult: 3.0
    # 一般 SELL 訊號 → 全出（含剩餘）
    sell_signal_mode: "exit_all"
```

注意：`legs[1].sell_fraction = 0.5` 是「賣掉當下持倉的一半」，不是「賣掉原始的 1/2」。
這樣兩個 leg 各觸發一次後剛好剩 1/3。

### TradeRecord 改動

每筆原始 BUY → 多筆 partial SELL，最後在 `engine.py` 內整合成 **單筆「合成 trade」** 寫入 `result.trades`：

```python
@dataclass
class TradeRecord:
    stock_id: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp        # 最後一筆出場日（含 trailing 或 SELL signal）
    entry_price: float
    exit_price: float              # weighted avg of partial exits
    shares: float                  # 原始買入股數
    pnl: float                     # 加總所有 partial 的 pnl
    pnl_pct: float                 # pnl / total_cost_basis
    hold_days: int                 # entry → 最後 partial exit
    # 新增（optional, 預設 None）
    n_partials: int = 1            # 1 = 沒分批；2/3/4 = 分批數
    exit_legs: list = field(default_factory=list)
    # exit_legs 元素： {date, price, shares, fraction, reason}
    #   reason ∈ {"profit_target_1", "profit_target_2", "trailing_stop", "sell_signal"}
```

`pnl_pct` 仍以 entry 成本為分母，整筆是真實盈虧；分批細節存 `exit_legs` 供報表用。

### Engine 改動（run_per_stock）

新增一個 helper class：

```python
class ScalingOutManager:
    """管理一次 BUY 後的分批出場狀態。
    
    狀態轉移：
        ARMED   ：剛買入，0 leg 觸發
        L1_DONE ：第 1 leg 出 1/3，剩 2/3
        L2_DONE ：第 2 leg 再出 1/3（持倉 1/2 之半），剩 1/3
        TRAILING：剩餘 1/3 由 chandelier 接管
        CLOSED  ：全部出場
    """
    def __init__(self, entry_date, entry_price, shares, atr_series, scaling_cfg):
        ...
    
    def update(self, date, high, low, close, sell_signal: bool) -> dict | None:
        """每日 high/low 觸發判斷。回傳 None 表示不出場，否則回傳 dict：
            {sell_shares: int, exec_price: float, reason: str, fraction_of_remaining: float}
        sell_signal 觸發時：剩餘部位全出（reason='sell_signal'）。
        """
        ...
```

判斷順序（在 T+1 開盤後，當日盤中）：
1. 若 T 日有 SELL 訊號 → T+1 開盤全出
2. 否則：當日 high 觸發 leg target → 用 target_price 出（保守：用 max(target, open)）
3. 否則：當日 low 觸發 chandelier stop → 用 stop_price 出
4. 兩個都不觸發 → 持倉

注意 atr_series 必須在進入 ScalingOutManager 前算好（用前 22 日 ATR），不要在 update 內 rolling 算。

### 預設啟用

修改 `Backtester.__init__` 載入 `scaling_cfg`：
```python
def __init__(self, config: BacktestConfig, scaling_cfg: dict | None = None):
    self.config = config
    self.scaling_cfg = scaling_cfg or {"enabled": False}
```

`auto_iterate/runner.py` 在建立 BacktestConfig 時傳入：
```python
scaling_cfg = cfg.get("scaling", {"enabled": False})
train_bt = Backtester(BacktestConfig(...), scaling_cfg=scaling_cfg)
```

但目前 backtest_one.py 是直接 `bt = Backtester(bt_cfg)`，要改成從外部接收 backtester 實例，或在 backtest_one 內讀 cfg。簡單做法：在 `backtest_one()` 內 `from src.strategy.runner import _load_cfg; scaling_cfg = _load_cfg().get("scaling", {})`。

### 測試
1. 寫 `tests/test_scaling_out.py`：
   - 模擬一檔股票漲 30% 後拉回 5%，期望分 3 leg 出場、最後 PnL ≈ +18%（10% × 1/3 + 20% × 1/3 + (30%-3%×ATR_implied) × 1/3）
   - 模擬漲 8% 後直接跌到 -10%（沒觸發任何 leg），期望走 SELL signal 全出
2. 跑 `pytest tests/ -x` 必須 100% 通過
3. 用 2308 + donchian_breakout 跑單一 backtest 對比 scaling on/off 的 DD：應該降低（即使 expectancy 略降也合理）

---

## P1：Bootstrap PF + Tier System

### 目標
1. 用 1000 次 bootstrap 算 PF 95% CI 下界 → 自動篩掉 SUSPICIOUS_PERFECT 和小樣本運氣
2. 把 PASS/WEAK 二元 → S/A/B/C/F 五級，每級對應建議部位上限

### 實作位置
- 新檔 `src/strategy/auto_iterate/bootstrap.py`
- 新檔 `src/strategy/auto_iterate/tiering.py`
- 修改 `src/strategy/auto_iterate/runner.py`：在 holdout validation 後呼叫 bootstrap + tiering
- 修改 `src/strategy/auto_iterate/backtest_one.py`：`classify()` 不變（保留向下相容），但 verdict 後再套 tier

### bootstrap.py

```python
def bootstrap_pf_ci(trades: list, n_iterations: int = 1000,
                    confidence: float = 0.95, seed: int = 42) -> dict:
    """對交易列表做 block bootstrap，回傳 PF 信賴區間。
    
    Args:
        trades: list of TradeRecord (or list of pnl_pct floats)
        n_iterations: 重抽次數
        confidence: 雙尾信賴水準（0.95 → 取 2.5% 與 97.5% 分位數）
    
    Returns:
        {
            "pf_mean": float,
            "pf_median": float,
            "pf_lower": float,    # 下界（confidence 的下半部）
            "pf_upper": float,    # 上界
            "pf_lower_pct": float,    # confidence 設 0.95 時 = 0.025
            "n_iterations": int,
            "n_original": int,
        }
    
    特殊處理：
        - 若某次重抽 gross_loss==0，PF 視為 5.0（與 score_single 的 cap 一致）
        - 若 trades < 5 → 回傳 {pf_lower: nan, ...}
        - 用 numpy random.default_rng(seed) 確保可重現
    """
```

### tiering.py

```python
TIER_RULES = {
    # tier: (pf_lower_min, expectancy_min, holdout_pass_required, position_pct_max, label)
    "S": dict(pf_lower=1.5, expectancy=0.05, holdouts="A_new+B+C", pos_max=1.00,
              label="ROBUST：訊號模式直接用，單檔上限 100%"),
    "A": dict(pf_lower=1.2, expectancy=0.03, holdouts="A_new + (B 或 C)", pos_max=0.50,
              label="STRONG：可用，建議 50% 部位"),
    "B": dict(pf_lower=1.0, expectancy=0.02, holdouts="A_new OR (B+C)",   pos_max=0.30,
              label="MODERATE：可用，建議 30% 部位 + 嚴格 trailing stop"),
    "C": dict(pf_lower=0.8, expectancy=0.01, holdouts="僅 train 過",      pos_max=0.15,
              label="WEAK：紙上交易 3 個月再啟用，最大 15%"),
    "F": dict(pf_lower=0.0, expectancy=-1.0, holdouts="全失效",            pos_max=0.00,
              label="FAIL：移出 universe"),
}

def assign_tier(
    test_metrics: dict,
    bootstrap_result: dict,
    holdouts: dict,        # {"A_new": bool, "B": bool, "C": bool}
) -> tuple[str, str]:
    """回傳 (tier, reason_str)。
    
    判斷順序：S → A → B → C → F，第一個全部條件符合就回傳。
    pf_lower 從 bootstrap_result["pf_lower"] 取；若 nan 則視為 0。
    """
```

### holdout 評估標準（給 tiering 用）

維持目前 V2 的標準，但要把每段是否通過 record 下來：

```python
HOLDOUT_PASS_CRITERIA = {
    "A_new": {  # 2010-2016（含 chip_momentum 例外）
        "expectancy": 0.01, "pf": 1.0, "n_min": 3,
    },
    "B": {      # 2018 震盪熊
        "pf": 0.8, "max_dd": 0.40,
    },
    "C": {      # 2022 熊
        "pf": 0.8, "max_dd": 0.40,
    },
}
```

### 整合到 runner.py

每個 (sid, template) 跑完 train + test 後再加：
```python
# Bootstrap PF on test trades
if test_m.get("n_trades", 0) >= 5:
    test_trades = ... # 從 backtest_one 改成 return result.trades 也行
    boot = bootstrap_pf_ci(test_trades, n_iterations=1000)
else:
    boot = {"pf_lower": float("nan"), ...}

# Holdout (V2 standard) — 跑 A_new (2010-2016), B (2018), C (2022)
holdout_a = backtest_one(sid, df, template, best_params, a_bt, ...)
holdout_b = backtest_one(sid, df, template, best_params, b_bt, ...)
holdout_c = backtest_one(sid, df, template, best_params, c_bt, ...)
holdouts = {
    "A_new": passes_holdout(holdout_a, "A_new"),
    "B":     passes_holdout(holdout_b, "B"),
    "C":     passes_holdout(holdout_c, "C"),
}

tier, tier_reason = assign_tier(test_m, boot, holdouts)
all_results[sid][template].update({
    "bootstrap": boot,
    "holdouts":  holdouts,
    "tier":      tier,
    "tier_reason": tier_reason,
})
```

### 報表新增

`per_stock_best.yaml` 多一個 `tier` 欄位：
```yaml
"2308":
  best_template: donchian_breakout
  verdict: PASS
  tier: S                            # 新增
  position_pct_recommended: 1.00     # 新增（從 TIER_RULES 取）
  bootstrap:                         # 新增
    pf_mean: 4.21
    pf_lower: 2.18
    pf_upper: 7.93
  holdouts:                          # 新增
    A_new: true
    B: false
    C: false
  ...
```

新增報告 `docs/TIERING_REPORT.md`：
- 列出每個 tier 的個股數
- 每檔顯示 tier、bootstrap PF lower、各 holdout 段過/不過
- 預期統計：S=2~3, A=5~7, B=8~10, C=6~8, F=剩餘
- 計算「可操作標的數 = S+A+B+C」目標 ≥ 20

### 測試
1. `tests/test_bootstrap.py`：
   - 給 10 筆固定 trades，pf_lower 應穩定（seed=42）
   - 給 5 筆全贏（avg_loss=0），pf_lower 應接近 5.0（cap）
   - 給 < 5 筆，回 nan
2. `tests/test_tiering.py`：
   - 給高 PF + 全 holdout 過 → S
   - 給 PF 1.3 + 只過 A_new + B → A
   - 給 PF 0.5 + 全失敗 → F
3. `pytest tests/ -x` 全過

---

## 執行流程

### Phase 1：P0 實作 + 測試
1. 修改 `engine.py`、`result.py`、`templates.py`、`config/strategy.yaml`
2. 寫 `tests/test_scaling_out.py`
3. 跑 pytest 全綠
4. 跑單檔 sanity：
   ```bash
   'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' -c "
   from src.strategy.auto_iterate.backtest_one import backtest_one
   from src.strategy.backtest.engine import BacktestConfig
   from src.strategy.runner import _load_adj_ohlcv, _load_cfg
   df = _load_adj_ohlcv('2308')
   cfg = _load_cfg()
   bt = BacktestConfig(fees=cfg['fees'], start_date='2024-01-01', end_date='2026-04-22', max_position_pct=1.0)
   m = backtest_one('2308', df, 'donchian_breakout', {'donchian_entry_n':20,'donchian_exit_n':55,'trend_ma':100,'atr_stop_k':4.0,'volume_min_ratio':1.0}, bt)
   print(m)
   "
   ```
   對照 scaling on/off 看 DD 是否下降。

### Phase 2：P1 實作 + 測試
1. 寫 `bootstrap.py`、`tiering.py`
2. 寫對應 pytest
3. 修改 `runner.py` 整合
4. 跑全 universe（34 檔 × 5 模板，預估 50~70 分鐘，因為多了 bootstrap + 3 段 holdout）：
   ```bash
   'C:/Users/houyi.lee/AppData/Local/anaconda3/python.exe' main.py auto_iterate --universe all
   ```
5. 產生新 run_id，更新 `docs/AUTO_ITERATE_REPORT.md` 加入 tier 統計

### 完成條件
- [ ] pytest 全綠
- [ ] `output/auto_iterate/<new_run_id>/per_stock_best.yaml` 含 `tier` + `bootstrap` + `holdouts` 欄位
- [ ] `docs/TIERING_REPORT.md` 產出，可操作標的（S+A+B+C）數量寫清楚
- [ ] 對比舊 run（`20260423_151107`）的 DD 變化：列出至少 3 檔 DD 顯著下降的個股

---

## 給 Sonnet 的注意事項

1. **不要改 watchlists.yaml**
2. **不要 silent fail**：所有錯誤用 `src/utils.log_error()` 落 `output/errors/{date}.csv`
3. **CSV 一律 utf-8-sig**
4. **scaling 改動有風險**：請保留 `scaling.enabled: false` 走原邏輯的 fallback，這樣可以隨時 A/B 對比
5. **進度報告**：每完成一個 phase（P0、P1）跟我講一聲，貼出 pytest 結果 + 一份 sanity 數字
6. **如果 bootstrap 算太慢**（單檔 1000 次 × 170 對 > 10 min）：把 n_iterations 降到 500 + 報告耗時

---

## 給 Opus（我）的後續工作

P0+P1 完成後我會做：
- 看新 tier 分布是否達 ≥ 20 檔可操作
- 如果 S 仍然只有 2 檔但 A/B 加起來夠多 → 寫使用者操作手冊（每 tier 對應的部位建議）
- 如果還是不夠 → 設計 P4 (P1 pyramid + P3 confidence sizing)
