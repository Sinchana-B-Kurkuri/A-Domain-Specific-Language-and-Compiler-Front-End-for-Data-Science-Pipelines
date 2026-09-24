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
