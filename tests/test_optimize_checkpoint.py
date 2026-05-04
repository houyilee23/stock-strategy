"""tests/test_optimize_checkpoint.py

驗證 SQLite checkpointing 功能：
1. 全新 study：load_if_exists=True 不報錯，study.db 存在
2. 已存在 study：第二次呼叫能讀回正確 trial 數
3. enqueue 邏輯：新 study 會 enqueue current_params，resume 不會
"""
import sys
import os
import tempfile
import shutil
import yaml
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import optuna
optuna.logging.set_verbosity(optuna.logging.ERROR)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cfg_path = os.path.join(BASE_DIR, "config", "strategy.yaml")
with open(_cfg_path, encoding="utf-8") as f:
    _STRATEGY = yaml.safe_load(f)

from src.strategy.optimize.search_space import SEARCH_SPACE


# ── 共用 fixture：暫存目錄 ───────────────────────────────────────

@pytest.fixture
def tmp_out_dir():
    d = tempfile.mkdtemp(prefix="optuna_ckpt_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _make_db_url(out_dir: str) -> str:
    db_path = os.path.join(out_dir, "study.db")
    return "sqlite:///" + db_path.replace(os.sep, "/")


def _dummy_objective(trial):
    _ = trial.suggest_float("x", 0, 1)
    return 0.5


# ── Test 1: 全新 study，load_if_exists=True 不報錯 ──────────────

def test_new_study_creates_db(tmp_out_dir):
    """全新 study 應建立 study.db 且不拋錯。"""
    storage_url = _make_db_url(tmp_out_dir)
    study = optuna.create_study(
        study_name="test_new",
        storage=storage_url,
        direction="maximize",
        load_if_exists=True,
    )
    study.optimize(lambda t: t.suggest_float("x", 0, 1), n_trials=3)

    db_path = os.path.join(tmp_out_dir, "study.db")
    assert os.path.exists(db_path), "study.db 應存在"
    assert os.path.getsize(db_path) > 0, "study.db 不應為空"
    assert len(study.trials) == 3, f"應有 3 trials，實際 {len(study.trials)}"


# ── Test 2: 已存在 study，第二次呼叫能讀回 trial 數 ─────────────

def test_resume_reads_existing_trials(tmp_out_dir):
    """第一次跑 3 trials，第二次 load_if_exists=True 應讀回 3 trials。"""
    storage_url = _make_db_url(tmp_out_dir)
    study_name = "test_resume"

    # 第一次：跑 3 trials
    study1 = optuna.create_study(
        study_name=study_name,
        storage=storage_url,
        direction="maximize",
        load_if_exists=True,
    )
    study1.optimize(lambda t: t.suggest_float("x", 0, 1), n_trials=3)
    assert len(study1.trials) == 3

    # 第二次：同 study_name + storage，應讀回 3 trials 再跑 2
    study2 = optuna.create_study(
        study_name=study_name,
        storage=storage_url,
        direction="maximize",
        load_if_exists=True,
    )
    assert len(study2.trials) == 3, f"resume 後應看到 3 trials，實際 {len(study2.trials)}"
    study2.optimize(lambda t: t.suggest_float("x", 0, 1), n_trials=2)
    assert len(study2.trials) == 5, f"累計應有 5 trials，實際 {len(study2.trials)}"


# ── Test 3: enqueue 邏輯 ─────────────────────────────────────────

def test_enqueue_only_on_new_study(tmp_out_dir):
    """新 study 才 enqueue current_params；resume study 不 enqueue。"""
    storage_url = _make_db_url(tmp_out_dir)
    study_name = "test_enqueue"

    current_params = {k: _STRATEGY["style1_pullback"][k]
                      for k in SEARCH_SPACE if k in _STRATEGY["style1_pullback"]}

    # 第一次（新 study）：len(study.trials) == 0 → 應 enqueue
    study_new = optuna.create_study(
        study_name=study_name,
        storage=storage_url,
        direction="maximize",
        load_if_exists=True,
    )
    assert len(study_new.trials) == 0, "全新 study 應無 trials"

    # 模擬 walk_forward.py 的邏輯
    if len(study_new.trials) == 0:
        try:
            enqueue_params = {k: current_params[k] for k in SEARCH_SPACE if k in current_params}
            study_new.enqueue_trial(enqueue_params)
        except Exception:
            pass

    assert len(study_new.trials) == 1, "enqueue 後應有 1 個 WAITING trial"

    # 跑完這 1 trial
    study_new.optimize(lambda t: 0.5, n_trials=1)

    # 第二次（resume）：len(study.trials) > 0 → 不應再 enqueue
    study_resume = optuna.create_study(
        study_name=study_name,
        storage=storage_url,
        direction="maximize",
        load_if_exists=True,
    )
    trials_before = len(study_resume.trials)
    assert trials_before == 1, f"resume 前應有 1 trial，實際 {trials_before}"

    # 模擬 walk_forward.py resume 路徑（不 enqueue）
    did_enqueue = False
    if len(study_resume.trials) == 0:
        did_enqueue = True
        study_resume.enqueue_trial({k: 0 for k in SEARCH_SPACE})

    assert not did_enqueue, "resume 模式不應再 enqueue"
    assert len(study_resume.trials) == trials_before, "resume 後 trial 數不應增加"


# ── Test 4: Windows 路徑轉換正確 ─────────────────────────────────

def test_db_path_uses_forward_slashes(tmp_out_dir):
    """storage_url 必須用 forward slash，否則 Windows 上 sqlite3 可能報錯。"""
    storage_url = _make_db_url(tmp_out_dir)
    assert "sqlite:///" in storage_url, "storage_url 應以 sqlite:/// 開頭"
    # 三個斜線後不應有 backslash
    path_part = storage_url[len("sqlite:///"):]
    assert "\\" not in path_part, f"storage_url 包含 backslash：{storage_url}"
