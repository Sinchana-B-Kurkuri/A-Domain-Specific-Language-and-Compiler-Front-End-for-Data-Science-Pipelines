import importlib.util
from pathlib import Path
import pytest

from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze
from ds_pipeline_dsl.ir import lower_to_ir
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute
from ds_pipeline_dsl.ast_nodes import (
    LoadStmt, CleanStmt, SelectStmt, DropStmt, SplitStmt, TrainStmt, EvaluateStmt
)

BENCHMARK_PATH = Path(__file__).resolve().parent.parent / "benchmarks" / "benchmark.py"
spec = importlib.util.spec_from_file_location("benchmark", BENCHMARK_PATH)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


# ==============================================================================
# COMPILE & STRUCTURAL INTEGRITY TESTS
# ==============================================================================

@pytest.mark.parametrize("n", [10, 50, 200])
def test_build_program_compiles_and_counts_match(n):
    counts = bench.expected_counts(n)
    source = bench.build_program(n)

    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    ir = lower_to_ir(ast, table)
    notes = []
    opt = optimize(ir, notes)
    trace = execute(opt)

    # 1. Statement counts
    assert len(ast.statements) == counts["statements"]
    assert len(ir) == counts["statements"]

    # 2. Optimized IR length == 6 + 2*U
    exp_opt = 6 + 2 * counts["U"]
    assert len(opt) == exp_opt
    assert len(opt) < len(ir)  # strictly shorter

    # 3. Evaluated model count == U
    eval_lines = [l for l in trace if l.startswith("Evaluated model")]
    assert len(eval_lines) == counts["U"]


@pytest.mark.parametrize("n", [10, 50, 200])
def test_structural_validity_from_ast_independent_of_analyze(n):
    source = bench.build_program(n)
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()

    # Rule 1: Exactly one LoadStmt
    load_stmts = [s for s in ast.statements if isinstance(s, LoadStmt)]
    assert len(load_stmts) == 1

    # Find the index of the first TrainStmt
    first_train_idx = next(
        (idx for idx, s in enumerate(ast.statements) if isinstance(s, TrainStmt)),
        None
    )
    assert first_train_idx is not None

    # Rule 2: No CleanStmt, SelectStmt, or DropStmt after the first TrainStmt
    for s in ast.statements[first_train_idx:]:
        assert not isinstance(s, (CleanStmt, SelectStmt, DropStmt)), (
            f"Found forbidden data preparation statement {type(s)} after first train at statement {s}"
        )

    # Rule 3: All DropStmt precede the first SelectStmt
    first_select_idx = next(
        (idx for idx, s in enumerate(ast.statements) if isinstance(s, SelectStmt)),
        None
    )
    assert first_select_idx is not None
    for idx, s in enumerate(ast.statements):
        if isinstance(s, DropStmt):
            assert idx < first_select_idx, "DropStmt found at or after first SelectStmt"

    # Rule 4: Model names are unique
    train_stmts = [s for s in ast.statements if isinstance(s, TrainStmt)]
    model_names = [s.model_name for s in train_stmts]
    assert len(model_names) == len(set(model_names)), "Duplicate model name detected"

    # Rule 5: Split names unique and percent total <= 100
    split_stmts = [s for s in ast.statements if isinstance(s, SplitStmt)]
    split_names = [s.name for s in split_stmts]
    assert len(split_names) == len(set(split_names)), "Duplicate split name detected"
    total_percent = sum(s.percent for s in split_stmts)
    assert total_percent <= 100.0 + 1e-9, f"Total split percent {total_percent} exceeds 100"

    # Rule 6: Dropped names disjoint from selected names
    dropped_cols = set()
    for s in ast.statements:
        if isinstance(s, DropStmt):
            dropped_cols.update(s.columns)

    selected_cols = set()
    for s in ast.statements:
        if isinstance(s, SelectStmt):
            selected_cols.update(s.columns)

    assert dropped_cols.isdisjoint(selected_cols), (
        f"Overlap between dropped and selected columns: {dropped_cols & selected_cols}"
    )

    # Rule 7: Every EvaluateStmt model has an earlier TrainStmt
    trained_so_far = set()
    for s in ast.statements:
        if isinstance(s, TrainStmt):
            trained_so_far.add(s.model_name)
        elif isinstance(s, EvaluateStmt):
            assert s.model_name in trained_so_far, (
                f"Model '{s.model_name}' evaluated before it was trained"
            )


# ==============================================================================
# PURE SAFEGUARD FUNCTION TESTS
# ==============================================================================

def test_safeguard_projected_seconds_pure_function():
    assert bench.projected_seconds(1.0, 1000, 10000) == 100.0
    assert bench.projected_seconds(0.5, 100, 200) == 2.0


def test_safeguard_should_run_pure_function():
    # Small projection within budget
    assert bench.should_run(projected_s=1.0, repeats=3, elapsed_s=10.0, budget_s=120.0) is True
    # Projection exceeds remaining budget
    assert bench.should_run(projected_s=40.0, repeats=3, elapsed_s=10.0, budget_s=120.0) is False
    # Exact boundary check
    assert bench.should_run(projected_s=10.0, repeats=3, elapsed_s=90.0, budget_s=120.0) is True
    assert bench.should_run(projected_s=10.1, repeats=3, elapsed_s=90.0, budget_s=120.0) is False


def test_safeguard_sizes_ascending_and_bounded():
    assert bench.SIZES == sorted(bench.SIZES), "SIZES list must be in strictly ascending order"
    assert max(bench.SIZES) <= bench.MAX_SIZE, "max(SIZES) must not exceed MAX_SIZE"


def test_build_program_rejects_exceeding_max_size():
    with pytest.raises(ValueError) as exc_info:
        bench.check_size_limit(bench.MAX_SIZE + 1)
    assert f"exceeds MAX_SIZE ({bench.MAX_SIZE})" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info2:
        bench.build_program(bench.MAX_SIZE + 1)
    assert f"exceeds MAX_SIZE ({bench.MAX_SIZE})" in str(exc_info2.value)
