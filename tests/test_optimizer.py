import pytest
from ds_pipeline_dsl.ir import IRInstruction
from ds_pipeline_dsl.optimizer import optimize

def test_optimize_collapse_duplicates_identical_args():
    ir_list = [
        IRInstruction(op="OP_LOAD", args={"filename": "data.csv"}),
        IRInstruction(op="OP_CLEAN", args={"strategy": "strat1"}),
        IRInstruction(op="OP_CLEAN", args={"strategy": "strat1"}),
        IRInstruction(op="OP_SELECT", args={"columns": ["c1"]}),
        IRInstruction(op="OP_TRAIN", args={"model_name": "m", "algorithm": "a"})
    ]
    
    optimized = optimize(ir_list)
    assert len(optimized) == 4
    assert optimized[0].op == "OP_LOAD"
    assert optimized[1].op == "OP_CLEAN"
    assert optimized[1].args["strategy"] == "strat1"
    assert optimized[2].op == "OP_SELECT"
    assert optimized[3].op == "OP_TRAIN"

def test_optimize_no_collapse_different_args():
    ir_list = [
        IRInstruction(op="OP_LOAD", args={"filename": "data.csv"}),
        IRInstruction(op="OP_CLEAN", args={"strategy": "missing"}),
        IRInstruction(op="OP_CLEAN", args={"strategy": "duplicates"}),
        IRInstruction(op="OP_SELECT", args={"columns": ["c1"]}),
        IRInstruction(op="OP_TRAIN", args={"model_name": "m", "algorithm": "a"})
    ]
    
    optimized = optimize(ir_list)
    assert len(optimized) == 5
    assert optimized[0].op == "OP_LOAD"
    assert optimized[1].op == "OP_CLEAN"
    assert optimized[1].args["strategy"] == "missing"
    assert optimized[2].op == "OP_CLEAN"
    assert optimized[2].args["strategy"] == "duplicates"
    assert optimized[3].op == "OP_SELECT"
    assert optimized[4].op == "OP_TRAIN"

def test_optimize_unreachable_after_eval():
    ir_list = [
        IRInstruction(op="OP_LOAD", args={"filename": "data.csv"}),
        IRInstruction(op="OP_CLEAN", args={"strategy": "strat"}),
        IRInstruction(op="OP_TRAIN", args={"model_name": "m", "algorithm": "a"}),
        IRInstruction(op="OP_EVAL", args={"model_name": "m"}),
        IRInstruction(op="OP_CLEAN", args={"strategy": "strat2"}),
        IRInstruction(op="OP_TRAIN", args={"model_name": "m2", "algorithm": "a2"})
    ]
    
    optimized = optimize(ir_list)
    assert len(optimized) == 4
    assert optimized[0].op == "OP_LOAD"
    assert optimized[1].op == "OP_CLEAN"
    assert optimized[2].op == "OP_TRAIN"
    assert optimized[3].op == "OP_EVAL"


# ==============================================================================
# CATEGORY A: Oracle Sensitivity Tests
# Proves that the evaluation_records oracle detects any loss or reordering of
# observable pipeline semantics on a valid multi-model program.
# ==============================================================================

import copy
import os
import sys
from unittest.mock import patch
from io import StringIO

from ds_pipeline_dsl.optimizer import (
    _remove_unreachable,
    _remove_dead_trains,
    _merge_adjacent_drops,
    _collapse_duplicates,
)
from ds_pipeline_dsl.executor import execute
from ds_pipeline_dsl.cli import main
from tests.helpers import compile_to_ir, evaluation_records, assert_order_preserving

VALID_MULTI_MODEL_SOURCE = """pipeline MultiModel {
    load "data.csv";
    clean missing;
    clean outliers;
    clean missing;
    select a, b, c;
    drop c;
    split train = 80%;
    train m1 = dt;
    evaluate m1;
    train m2 = rf;
    evaluate m2;
}
"""

def test_oracle_sensitivity_delete_live_train():
    ir = compile_to_ir(VALID_MULTI_MODEL_SOURCE)
    orig_recs = evaluation_records(ir)
    mutated = [i for i in ir if not (i.op == "OP_TRAIN" and i.args.get("model_name") == "m1")]
    assert evaluation_records(mutated) != orig_recs

def test_oracle_sensitivity_delete_split():
    ir = compile_to_ir(VALID_MULTI_MODEL_SOURCE)
    orig_recs = evaluation_records(ir)
    mutated = [i for i in ir if i.op != "OP_SPLIT"]
    assert evaluation_records(mutated) != orig_recs

def test_oracle_sensitivity_truncate_after_first_eval():
    ir = compile_to_ir(VALID_MULTI_MODEL_SOURCE)
    orig_recs = evaluation_records(ir)
    first_eval_idx = next(idx for idx, i in enumerate(ir) if i.op == "OP_EVAL")
    mutated = ir[:first_eval_idx + 1]
    assert evaluation_records(mutated) != orig_recs

def test_oracle_sensitivity_remove_non_adjacent_clean():
    ir = compile_to_ir(VALID_MULTI_MODEL_SOURCE)
    orig_recs = evaluation_records(ir)
    clean_indices = [idx for idx, i in enumerate(ir) if i.op == "OP_CLEAN"]
    assert len(clean_indices) == 3
    # Remove the second non-adjacent 'clean missing'
    mutated = [i for idx, i in enumerate(ir) if idx != clean_indices[2]]
    assert evaluation_records(mutated) != orig_recs

def test_oracle_sensitivity_reorder_cleans():
    ir = compile_to_ir(VALID_MULTI_MODEL_SOURCE)
    orig_recs = evaluation_records(ir)
    clean_indices = [idx for idx, i in enumerate(ir) if i.op == "OP_CLEAN"]
    mutated = list(ir)
    mutated[clean_indices[0]], mutated[clean_indices[1]] = mutated[clean_indices[1]], mutated[clean_indices[0]]
    assert evaluation_records(mutated) != orig_recs

def test_oracle_sensitivity_delete_drop():
    ir = compile_to_ir(VALID_MULTI_MODEL_SOURCE)
    orig_recs = evaluation_records(ir)
    mutated = [i for i in ir if i.op != "OP_DROP"]
    assert evaluation_records(mutated) != orig_recs


# ==============================================================================
# CATEGORY B: Positive Optimization Tests
# ==============================================================================

def test_positive_tail_after_last_eval_removed():
    ir = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "dt", "line": 2}),
        IRInstruction("OP_EVAL", {"model_name": "m", "line": 3}),
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 4}),
        IRInstruction("OP_SPLIT", {"name": "test", "percent": 20.0, "line": 5}),
    ]
    notes = []
    opt = optimize(ir, notes)
    assert len(opt) == 3
    assert [i.op for i in opt] == ["OP_LOAD", "OP_TRAIN", "OP_EVAL"]
    assert any("unreachable: removed OP_CLEAN (line 4)" in n for n in notes)
    assert any("unreachable: removed OP_SPLIT (line 5)" in n for n in notes)

def test_positive_f4_multi_model_preserved_regression_a():
    src = """pipeline F4Regression {
        load "data.csv";
        split train = 80%;
        train m1 = dt;
        evaluate m1;
        train m2 = rf;
        evaluate m2;
    }"""
    ir = compile_to_ir(src)
    notes = []
    opt = optimize(ir, notes)
    assert len(opt) == len(ir)
    assert [i.op for i in opt] == [i.op for i in ir]
    evals = [i for i in opt if i.op == "OP_EVAL"]
    assert len(evals) == 2
    assert evals[0].args["model_name"] == "m1"
    assert evals[1].args["model_name"] == "m2"
    assert len(notes) == 0

def test_positive_dead_train_removed():
    src = """pipeline DeadTrain {
        load "data.csv";
        split train = 80%;
        train m1 = dt;
        train m2 = rf;
        evaluate m2;
    }"""
    ir = compile_to_ir(src)
    notes = []
    opt = optimize(ir, notes)
    train_models = [i.args["model_name"] for i in opt if i.op == "OP_TRAIN"]
    assert train_models == ["m2"]
    assert any("dead-train: removed OP_TRAIN 'm1'" in n for n in notes)

def test_positive_live_train_kept():
    src = """pipeline LiveTrain {
        load "data.csv";
        split train = 80%;
        train m1 = dt;
        evaluate m1;
    }"""
    ir = compile_to_ir(src)
    notes = []
    opt = optimize(ir, notes)
    train_models = [i.args["model_name"] for i in opt if i.op == "OP_TRAIN"]
    assert train_models == ["m1"]
    assert not any("dead-train" in n for n in notes)

def test_positive_two_and_three_adjacent_drops_merge():
    # Two adjacent drops
    ir2 = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_DROP", {"columns": ["col_a", "col_b"], "line": 2}),
        IRInstruction("OP_DROP", {"columns": ["col_b", "col_c"], "line": 3}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "dt", "line": 4}),
        IRInstruction("OP_EVAL", {"model_name": "m", "line": 5}),
    ]
    notes2 = []
    opt2 = optimize(ir2, notes2)
    assert len(opt2) == 4
    drop_instr = opt2[1]
    assert drop_instr.op == "OP_DROP"
    assert drop_instr.args["columns"] == ["col_a", "col_b", "col_c"]
    assert drop_instr.args["line"] == 2
    assert any("drop-merge: merged 2 adjacent OP_DROP (lines 2, 3) into one" in n for n in notes2)

    # Three adjacent drops
    ir3 = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_DROP", {"columns": ["x"], "line": 10}),
        IRInstruction("OP_DROP", {"columns": ["y"], "line": 11}),
        IRInstruction("OP_DROP", {"columns": ["x", "z"], "line": 12}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "dt", "line": 13}),
        IRInstruction("OP_EVAL", {"model_name": "m", "line": 14}),
    ]
    notes3 = []
    opt3 = optimize(ir3, notes3)
    assert len(opt3) == 4
    drop3 = opt3[1]
    assert drop3.op == "OP_DROP"
    assert drop3.args["columns"] == ["x", "y", "z"]
    assert drop3.args["line"] == 10
    assert any("drop-merge: merged 3 adjacent OP_DROP (lines 10, 11, 12) into one" in n for n in notes3)

def test_positive_duplicates_on_different_lines_collapse_regression_b():
    ir = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 2}),
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 3}),
        IRInstruction("OP_SELECT", {"columns": ["c1", "c2"], "line": 4}),
        IRInstruction("OP_SELECT", {"columns": ["c1", "c2"], "line": 5}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "dt", "line": 6}),
        IRInstruction("OP_EVAL", {"model_name": "m", "line": 7}),
    ]
    notes = []
    opt = optimize(ir, notes)
    assert len(opt) == 5
    assert opt[1].op == "OP_CLEAN" and opt[1].args["line"] == 2
    assert opt[2].op == "OP_SELECT" and opt[2].args["line"] == 4
    assert any("duplicate: removed repeated OP_CLEAN (line 3)" in n for n in notes)
    assert any("duplicate: removed repeated OP_SELECT (line 5)" in n for n in notes)

def test_positive_trailing_split_after_last_eval_removed():
    ir = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "dt", "line": 2}),
        IRInstruction("OP_EVAL", {"model_name": "m", "line": 3}),
        IRInstruction("OP_SPLIT", {"name": "test", "percent": 20.0, "line": 4}),
    ]
    notes = []
    opt = optimize(ir, notes)
    assert len(opt) == 3
    assert [i.op for i in opt] == ["OP_LOAD", "OP_TRAIN", "OP_EVAL"]
    assert any("unreachable: removed OP_SPLIT (line 4) after last OP_EVAL" in n for n in notes)


# ==============================================================================
# CATEGORY C: Negative ("Must NOT Optimize") Tests
# ==============================================================================

def test_negative_no_op_eval_leaves_ir_identical():
    ir = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 2}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "dt", "line": 3}),
    ]
    notes = []
    opt = optimize(ir, notes)
    assert len(opt) == 3
    assert [i.op for i in opt] == ["OP_LOAD", "OP_CLEAN", "OP_TRAIN"]
    assert opt[2].args["model_name"] == "m"
    assert len(notes) == 0

def test_negative_drops_separated_not_merged():
    # Separated by clean
    ir1 = [
        IRInstruction("OP_DROP", {"columns": ["a"], "line": 1}),
        IRInstruction("OP_CLEAN", {"strategy": "s", "line": 2}),
        IRInstruction("OP_DROP", {"columns": ["b"], "line": 3}),
    ]
    opt1 = optimize(ir1)
    assert len(opt1) == 3
    assert opt1[0].op == "OP_DROP" and opt1[0].args["columns"] == ["a"]
    assert opt1[2].op == "OP_DROP" and opt1[2].args["columns"] == ["b"]

    # Separated by select
    ir2 = [
        IRInstruction("OP_DROP", {"columns": ["a"], "line": 1}),
        IRInstruction("OP_SELECT", {"columns": ["x"], "line": 2}),
        IRInstruction("OP_DROP", {"columns": ["b"], "line": 3}),
    ]
    opt2 = optimize(ir2)
    assert len(opt2) == 3

    # Separated by split
    ir3 = [
        IRInstruction("OP_DROP", {"columns": ["a"], "line": 1}),
        IRInstruction("OP_SPLIT", {"name": "train", "percent": 80.0, "line": 2}),
        IRInstruction("OP_DROP", {"columns": ["b"], "line": 3}),
    ]
    opt3 = optimize(ir3)
    assert len(opt3) == 3

def test_negative_non_adjacent_duplicate_clean_kept():
    ir = [
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 1}),
        IRInstruction("OP_SELECT", {"columns": ["a"], "line": 2}),
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 3}),
    ]
    opt = optimize(ir)
    assert len(opt) == 3
    assert opt[0].op == "OP_CLEAN"
    assert opt[2].op == "OP_CLEAN"

def test_negative_adjacent_clean_different_strategy_kept():
    ir = [
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 1}),
        IRInstruction("OP_CLEAN", {"strategy": "outliers", "line": 2}),
    ]
    opt = optimize(ir)
    assert len(opt) == 2

def test_negative_select_different_columns_or_order_kept():
    # Different order
    ir1 = [
        IRInstruction("OP_SELECT", {"columns": ["a", "b"], "line": 1}),
        IRInstruction("OP_SELECT", {"columns": ["b", "a"], "line": 2}),
    ]
    opt1 = optimize(ir1)
    assert len(opt1) == 2

    # Different columns
    ir2 = [
        IRInstruction("OP_SELECT", {"columns": ["a"], "line": 1}),
        IRInstruction("OP_SELECT", {"columns": ["b"], "line": 2}),
    ]
    opt2 = optimize(ir2)
    assert len(opt2) == 2

def test_negative_clean_x_select_clean_x_kept():
    ir = [
        IRInstruction("OP_CLEAN", {"strategy": "norm", "line": 1}),
        IRInstruction("OP_SELECT", {"columns": ["col"], "line": 2}),
        IRInstruction("OP_CLEAN", {"strategy": "norm", "line": 3}),
    ]
    opt = optimize(ir)
    assert len(opt) == 3

def test_negative_instructions_between_evaluations_kept():
    ir = [
        IRInstruction("OP_TRAIN", {"model_name": "m1", "algorithm": "dt", "line": 1}),
        IRInstruction("OP_EVAL", {"model_name": "m1", "line": 2}),
        IRInstruction("OP_SPLIT", {"name": "test", "percent": 20.0, "line": 3}),
        IRInstruction("OP_TRAIN", {"model_name": "m2", "algorithm": "rf", "line": 4}),
        IRInstruction("OP_EVAL", {"model_name": "m2", "line": 5}),
    ]
    notes = []
    opt = optimize(ir, notes)
    assert len(opt) == 5
    assert opt[2].op == "OP_SPLIT"
    assert len(notes) == 0

def test_negative_model_evaluated_once_trained_before_another_eval_kept():
    ir = [
        IRInstruction("OP_TRAIN", {"model_name": "m1", "algorithm": "dt", "line": 1}),
        IRInstruction("OP_TRAIN", {"model_name": "m2", "algorithm": "rf", "line": 2}),
        IRInstruction("OP_EVAL", {"model_name": "m2", "line": 3}),
        IRInstruction("OP_EVAL", {"model_name": "m1", "line": 4}),
    ]
    opt = optimize(ir)
    assert len(opt) == 4
    train_models = [i.args["model_name"] for i in opt if i.op == "OP_TRAIN"]
    assert train_models == ["m1", "m2"]

def test_negative_evaluate_twice_keeps_train():
    ir = [
        IRInstruction("OP_TRAIN", {"model_name": "m1", "algorithm": "dt", "line": 1}),
        IRInstruction("OP_EVAL", {"model_name": "m1", "line": 2}),
        IRInstruction("OP_EVAL", {"model_name": "m1", "line": 3}),
    ]
    opt = optimize(ir)
    assert len(opt) == 3
    assert opt[0].op == "OP_TRAIN"

def test_negative_handbuilt_eval_missing_model_name_keeps_all_trains():
    ir = [
        IRInstruction("OP_TRAIN", {"model_name": "m1", "algorithm": "dt", "line": 1}),
        IRInstruction("OP_TRAIN", {"model_name": "m2", "algorithm": "rf", "line": 2}),
        IRInstruction("OP_EVAL", {}),
    ]
    opt = optimize(ir)
    assert len(opt) == 3
    assert opt[0].args.get("model_name") == "m1"
    assert opt[1].args.get("model_name") == "m2"

def test_negative_train_missing_model_name_kept():
    ir = [
        IRInstruction("OP_TRAIN", {}),
        IRInstruction("OP_TRAIN", {"model_name": "m1", "algorithm": "dt", "line": 1}),
        IRInstruction("OP_EVAL", {"model_name": "m1", "line": 2}),
    ]
    opt = optimize(ir)
    assert len(opt) == 3
    assert opt[0].op == "OP_TRAIN"
    assert opt[1].args.get("model_name") == "m1"

def test_negative_drop_missing_columns_not_merged():
    ir = [
        IRInstruction("OP_DROP", {}),
        IRInstruction("OP_DROP", {"columns": ["a"], "line": 1}),
    ]
    opt = optimize(ir)
    assert len(opt) == 2
    assert opt[0].args == {}
    assert opt[1].args["columns"] == ["a"]

def test_negative_empty_ir():
    assert optimize([]) == []

def test_negative_input_immutability():
    ir = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 2}),
        IRInstruction("OP_CLEAN", {"strategy": "missing", "line": 3}),
        IRInstruction("OP_DROP", {"columns": ["a"], "line": 4}),
        IRInstruction("OP_DROP", {"columns": ["b"], "line": 5}),
        IRInstruction("OP_TRAIN", {"model_name": "dead", "algorithm": "dt", "line": 6}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "rf", "line": 7}),
        IRInstruction("OP_EVAL", {"model_name": "m", "line": 8}),
        IRInstruction("OP_CLEAN", {"strategy": "tail", "line": 9}),
    ]
    orig_deepcopy = copy.deepcopy(ir)
    optimized = optimize(ir)
    assert len(ir) == len(orig_deepcopy)
    for orig, curr in zip(orig_deepcopy, ir):
        assert orig.op == curr.op
        assert orig.args == curr.args

def test_negative_notes_none_prints_nothing(capsys):
    ir = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "dt", "line": 2}),
        IRInstruction("OP_EVAL", {"model_name": "m", "line": 3}),
        IRInstruction("OP_CLEAN", {"strategy": "tail", "line": 4}),
    ]
    optimize(ir, notes=None)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

def test_negative_notes_empty_when_no_optimizations():
    ir = [
        IRInstruction("OP_LOAD", {"filename": "data.csv", "line": 1}),
        IRInstruction("OP_TRAIN", {"model_name": "m", "algorithm": "dt", "line": 2}),
        IRInstruction("OP_EVAL", {"model_name": "m", "line": 3}),
    ]
    notes = []
    opt = optimize(ir, notes)
    assert len(opt) == 3
    assert notes == []


# ==============================================================================
# CATEGORY D: Equivalence on >= 10 Valid Source Pipelines
# ==============================================================================

EQUIVALENCE_PIPELINES = {
    "dead_train": """pipeline DeadTrain {
        load "data.csv";
        split train = 80%;
        train m1 = dt;
        train m2 = rf;
        evaluate m2;
    }""",
    "trailing_train_split": """pipeline Trailing {
        load "data.csv";
        split train = 80%;
        train m1 = dt;
        evaluate m1;
        split test = 20%;
        train m2 = rf;
    }""",
    "duplicate_cleans": """pipeline DupCleans {
        load "data.csv";
        clean missing;
        clean missing;
        select a, b;
        split train = 80%;
        train m1 = dt;
        evaluate m1;
    }""",
    "adjacent_drops": """pipeline AdjDrops {
        load "data.csv";
        select a, b, c, d;
        drop a;
        drop b, c;
        split train = 80%;
        train m1 = dt;
        evaluate m1;
    }""",
    "multi_model": """pipeline MultiModel {
        load "data.csv";
        clean missing;
        select a, b;
        split train = 50%;
        train m1 = dt;
        evaluate m1;
        split test = 20%;
        train m2 = rf;
        evaluate m2;
        train m3 = svm;
        evaluate m3;
    }""",
    "key_split_after_train": """pipeline KeySplitAfterTrain {
        load "data.csv";
        split train = 70%;
        train m1 = dt;
        evaluate m1;
        split test = 30%;
        train m2 = rf;
        evaluate m2;
    }""",
    "eval_twice": """pipeline EvalTwice {
        load "data.csv";
        clean missing;
        split train = 80%;
        train m1 = dt;
        evaluate m1;
        evaluate m1;
    }""",
    "select_then_drop": """pipeline SelectThenDrop {
        load "data.csv";
        select a, b, c;
        drop c;
        split train = 80%;
        train m1 = dt;
        evaluate m1;
    }""",
    "no_eval": """pipeline NoEval {
        load "data.csv";
        clean missing;
        select a, b;
        split train = 80%;
        train m1 = dt;
    }""",
    "optimizer_demo": open(os.path.join(os.path.dirname(__file__), "..", "examples", "optimizer_demo.pipe")).read(),
}

def _assert_subsequence(sub: list, full: list) -> None:
    it = iter(full)
    for item in sub:
        assert item in it, f"'{item}' not in remainder of full trace"

@pytest.mark.parametrize("name,source", list(EQUIVALENCE_PIPELINES.items()))
def test_pipeline_equivalence_full_and_passes(name, source):
    unopt = compile_to_ir(source)
    notes = []
    opt = optimize(unopt, notes)

    # 1. Observable evaluation record equality
    unopt_recs = evaluation_records(unopt)
    opt_recs = evaluation_records(opt)
    assert unopt_recs == opt_recs, f"Pipeline {name}: evaluation_records differ"

    # 2. Pass-level record equality (each pass alone)
    for pass_fn in [_remove_unreachable, _remove_dead_trains, _merge_adjacent_drops, _collapse_duplicates]:
        pass_opt = pass_fn(unopt)
        assert evaluation_records(pass_opt) == unopt_recs, f"Pipeline {name}, pass {pass_fn.__name__} failed equivalence"

    # 3. Order-preserving two-pointer check
    assert_order_preserving(unopt, opt)

    # 4. Executor trace checks
    unopt_trace = execute(unopt)
    opt_trace = execute(opt)

    eval_unopt = [l for l in unopt_trace if l.startswith("Evaluated model")]
    eval_opt = [l for l in opt_trace if l.startswith("Evaluated model")]
    assert eval_unopt == eval_opt, f"Pipeline {name}: 'Evaluated model' lines differ"

    trace_sub = [l for l in opt_trace if not l.startswith("Dropped columns")]
    trace_full = [l for l in unopt_trace if not l.startswith("Dropped columns")]
    _assert_subsequence(trace_sub, trace_full)

    drop_cols_unopt = set()
    for l in unopt_trace:
        if l.startswith("Dropped columns: "):
            drop_cols_unopt.update(l.removeprefix("Dropped columns: ").split(", "))

    drop_cols_opt = set()
    for l in opt_trace:
        if l.startswith("Dropped columns: "):
            drop_cols_opt.update(l.removeprefix("Dropped columns: ").split(", "))

    assert drop_cols_unopt == drop_cols_opt, f"Pipeline {name}: union of dropped columns differ"


# ==============================================================================
# CATEGORY E: Idempotence Tests
# ==============================================================================

@pytest.mark.parametrize("name,source", list(EQUIVALENCE_PIPELINES.items()))
def test_pipeline_idempotence(name, source):
    unopt = compile_to_ir(source)
    opt1 = optimize(unopt)
    opt2 = optimize(opt1)
    assert len(opt1) == len(opt2), f"Pipeline {name}: lengths differ after second optimize"
    for i1, i2 in zip(opt1, opt2):
        assert i1.op == i2.op, f"Pipeline {name}: opcode differ: {i1.op} vs {i2.op}"
        assert i1.args == i2.args, f"Pipeline {name}: args differ: {i1.args} vs {i2.args}"


# ==============================================================================
# CATEGORY F: CLI Optimization Notes Tests
# ==============================================================================

def test_cli_optimizer_demo_notes():
    demo_path = os.path.join(os.path.dirname(__file__), "..", "examples", "optimizer_demo.pipe")
    test_args = ["cli.py", demo_path, "--ir", "--optimized-ir"]
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()

    assert "=== OPTIMIZATION NOTES ===" in output
    assert "unreachable:" in output
    assert "dead-train:" in output
    assert "drop-merge:" in output
    assert "duplicate:" in output
    assert "IR instructions: 11 -> 7" in output

