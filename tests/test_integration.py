import os
import sys
import tempfile
from io import StringIO
from unittest.mock import patch
import pytest

from ds_pipeline_dsl.cli import main
from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze
from ds_pipeline_dsl.ir import lower_to_ir, IRInstruction
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute
from tests.helpers import compile_to_ir, evaluation_records, assert_order_preserving

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")

def get_example_path(filename: str) -> str:
    return os.path.join(EXAMPLES_DIR, filename)

def run_cli_args(args: list) -> tuple[int, str]:
    test_args = ["cli.py"] + args
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            code = 0
            try:
                main()
            except SystemExit as e:
                code = e.code
            return code, fake_out.getvalue()


# ==============================================================================
# COMPLEX PIPELINE EXAMPLES & EQUIVALENCE
# ==============================================================================

def test_complex_multi_model():
    path = get_example_path("complex_multi_model.pipe")
    with open(path, "r") as f:
        src = f.read()

    unopt = compile_to_ir(src)
    notes = []
    opt = optimize(unopt, notes)

    # 1. Snapshot / record equivalence
    assert evaluation_records(unopt) == evaluation_records(opt)
    assert_order_preserving(unopt, opt)

    # 2. Assert both evaluations survive optimization
    evals = [i for i in opt if i.op == "OP_EVAL"]
    assert len(evals) == 2
    assert evals[0].args["model_name"] == "m1"
    assert evals[1].args["model_name"] == "m2"

    # 3. Dead train is removed
    train_models = [i.args["model_name"] for i in opt if i.op == "OP_TRAIN"]
    assert "m_dead" not in train_models
    assert train_models == ["m1", "m2"]
    assert any("dead-train: removed OP_TRAIN 'm_dead'" in n for n in notes)

    # 4. Trace has exactly 2 "Evaluated model" lines in order
    trace = execute(opt)
    eval_lines = [l for l in trace if l.startswith("Evaluated model")]
    assert eval_lines == [
        "Evaluated model 'm1' (simulated accuracy trace)",
        "Evaluated model 'm2' (simulated accuracy trace)",
    ]

    # 5. CLI runs with exit code 0
    code, output = run_cli_args([path, "--trace"])
    assert code == 0
    assert "Evaluated model 'm1'" in output
    assert "Evaluated model 'm2'" in output


def test_complex_redundant():
    path = get_example_path("complex_redundant.pipe")
    with open(path, "r") as f:
        src = f.read()

    unopt = compile_to_ir(src)
    notes = []
    opt = optimize(unopt, notes)

    # 1. Snapshot / record equivalence
    assert evaluation_records(unopt) == evaluation_records(opt)
    assert_order_preserving(unopt, opt)

    # 2. Exact optimized opcode sequence
    assert [i.op for i in opt] == [
        "OP_LOAD", "OP_CLEAN", "OP_SELECT", "OP_DROP", "OP_SPLIT", "OP_TRAIN", "OP_EVAL"
    ]

    # 3. Notes mention each pass
    assert any("unreachable:" in n for n in notes)
    assert any("dead-train:" in n for n in notes)
    assert any("drop-merge:" in n for n in notes)
    assert any("duplicate:" in n for n in notes)

    # 4. CLI runs with exit code 0
    code, output = run_cli_args([path, "--optimized-ir"])
    assert code == 0
    assert "=== OPTIMIZATION NOTES ===" in output
    assert "IR instructions: 12 -> 7" in output


def test_complex_valid_drop_chain():
    path = get_example_path("complex_valid_drop_chain.pipe")
    with open(path, "r") as f:
        src = f.read()

    unopt = compile_to_ir(src)
    notes = []
    opt = optimize(unopt, notes)

    # 1. Snapshot / record equivalence
    assert evaluation_records(unopt) == evaluation_records(opt)
    assert_order_preserving(unopt, opt)

    # 2. Both drops survive because they are not adjacent (separated by split)
    drops = [i for i in opt if i.op == "OP_DROP"]
    assert len(drops) == 2
    assert drops[0].args["columns"] == ["c1"]
    assert drops[1].args["columns"] == ["c2"]

    # 3. Trace check
    trace = execute(opt)
    assert "Dropped columns: c1" in trace
    assert "Dropped columns: c2" in trace
    assert "Evaluated model 'model' (simulated accuracy trace)" in trace

    # 4. CLI runs with exit code 0
    code, output = run_cli_args([path, "--trace"])
    assert code == 0
    assert "Dropped columns: c1" in output
    assert "Dropped columns: c2" in output


# ==============================================================================
# IR / EXECUTOR INTEGRATION
# ==============================================================================

def test_ir_and_executor_all_opcodes_order_and_traces():
    source = '''pipeline all_stmts {
    load "students.csv";
    clean missing_values;
    select a, b, c;
    drop c;
    split train = 80%;
    train model = decision_tree;
    evaluate model;
}'''
    ir = compile_to_ir(source)
    assert [i.op for i in ir] == [
        "OP_LOAD", "OP_CLEAN", "OP_SELECT", "OP_DROP", "OP_SPLIT", "OP_TRAIN", "OP_EVAL"
    ]

    trace = execute(ir)
    assert trace == [
        "Loaded students.csv",
        "Cleaned using missing_values",
        "Selected columns: a, b, c",
        "Dropped columns: c",
        "Defined split 'train' = 80%",
        "Trained model 'model' using decision_tree",
        "Evaluated model 'model' (simulated accuracy trace)",
    ]

def test_executor_unknown_instruction():
    ir = [IRInstruction("OP_CUSTOM_UNKNOWN", {"arg": "val"})]
    trace = execute(ir)
    assert trace == ["Unknown instruction: OP_CUSTOM_UNKNOWN"]


# ==============================================================================
# CLI END-TO-END INTEGRATION
# ==============================================================================

def test_cli_default_all_five_sections():
    path = get_example_path("valid_basic.pipe")
    code, output = run_cli_args([path])
    assert code == 0
    assert "=== TOKENS ===" in output
    assert "=== AST ===" in output
    assert "=== IR ===" in output
    assert "=== OPTIMIZED IR ===" in output
    assert "=== TRACE ===" in output
    assert "Loaded students.csv" in output

@pytest.mark.parametrize("flag,expected_section,other_sections", [
    ("--tokens", "=== TOKENS ===", ["=== AST ===", "=== IR ===", "=== OPTIMIZED IR ===", "=== TRACE ==="]),
    ("--ast", "=== AST ===", ["=== TOKENS ===", "=== IR ===", "=== OPTIMIZED IR ===", "=== TRACE ==="]),
    ("--ir", "=== IR ===", ["=== TOKENS ===", "=== AST ===", "=== OPTIMIZED IR ===", "=== TRACE ==="]),
    ("--optimized-ir", "=== OPTIMIZED IR ===", ["=== TOKENS ===", "=== AST ===", "=== IR ===", "=== TRACE ==="]),
    ("--trace", "=== TRACE ===", ["=== TOKENS ===", "=== AST ===", "=== IR ===", "=== OPTIMIZED IR ==="]),
])
def test_cli_single_flags_isolate_sections(flag, expected_section, other_sections):
    path = get_example_path("valid_basic.pipe")
    code, output = run_cli_args([path, flag])
    assert code == 0
    assert expected_section in output
    for other in other_sections:
        assert other not in output

def test_cli_lexical_error_clean_exit_no_traceback():
    path = get_example_path("invalid_lexical_error.pipe")
    code, output = run_cli_args([path])
    assert code == 1
    assert "Lexical Error" in output
    assert "Traceback" not in output

def test_cli_syntax_error_clean_exit_no_traceback():
    path = get_example_path("invalid_syntax_error.pipe")
    code, output = run_cli_args([path])
    assert code == 1
    assert "Syntax Error" in output
    assert "Traceback" not in output

def test_cli_semantic_error_clean_exit_no_traceback():
    path = get_example_path("invalid_train_before_split.pipe")
    code, output = run_cli_args([path])
    assert code == 1
    assert "Semantic Error" in output
    assert "Traceback" not in output

def test_cli_missing_file_clean_exit_no_traceback():
    code, output = run_cli_args(["non_existent_file.pipe"])
    assert code == 1
    assert "Error reading file:" in output
    assert "Traceback" not in output
