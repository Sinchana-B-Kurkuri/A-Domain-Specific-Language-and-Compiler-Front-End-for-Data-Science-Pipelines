import pytest
import os
from ds_pipeline_dsl.lexer import tokenize, LexicalError
from ds_pipeline_dsl.parser import Parser, SyntaxError_
from ds_pipeline_dsl.semantic import analyze, SemanticError
from ds_pipeline_dsl.ir import lower_to_ir
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute

def get_example_path(filename):
    return os.path.join(os.path.dirname(__file__), '..', 'examples', filename)

def run_pipeline(filepath):
    with open(filepath, 'r') as f:
        code = f.read()
    tokens = tokenize(code)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    ir = lower_to_ir(ast, table)
    opt_ir = optimize(ir)
    return execute(opt_ir)

def test_valid_basic():
    trace = run_pipeline(get_example_path('valid_basic.pipe'))
    assert len(trace) == 6
    assert trace[0] == "Loaded students.csv"
    assert trace[1] == "Cleaned using missing_values"
    assert trace[2] == "Selected columns: cgpa, attendance, study_hours"
    assert trace[3] == "Defined split 'train' = 80%"
    assert trace[4] == "Trained model 'model' using decision_tree"
    assert trace[5] == "Evaluated model 'model' (simulated accuracy trace)"

def test_invalid_train_before_split():
    with pytest.raises(SemanticError):
        run_pipeline(get_example_path('invalid_train_before_split.pipe'))

def test_invalid_lexical_error():
    with pytest.raises(LexicalError):
        run_pipeline(get_example_path('invalid_lexical_error.pipe'))

def test_invalid_syntax_error():
    with pytest.raises(SyntaxError_):
        run_pipeline(get_example_path('invalid_syntax_error.pipe'))

def test_invalid_duplicate_load():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_duplicate_load.pipe'))
    assert "'load' used more than once" in str(exc_info.value)

def test_invalid_duplicate_split():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_duplicate_split.pipe'))
    assert "split 'train' is already defined" in str(exc_info.value)

def test_invalid_duplicate_model():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_duplicate_model.pipe'))
    assert "model 'model' is already defined" in str(exc_info.value)

def test_invalid_split_total_over_100():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_split_total_over_100.pipe'))
    assert "cumulative split total would be 110%, which exceeds 100%." in str(exc_info.value)

def test_invalid_clean_after_train():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_clean_after_train.pipe'))
    assert "'clean' used after model 'model' was trained" in str(exc_info.value)

def test_valid_drop():
    with open(get_example_path('valid_drop.pipe'), 'r') as f:
        code = f.read()
    tokens = tokenize(code)
    assert any(t.type == "DROP" for t in tokens)
    ast = Parser(tokens).parse_pipeline()
    assert any(stmt.__class__.__name__ == "DropStmt" for stmt in ast.statements)
    table = analyze(ast)
    ir = lower_to_ir(ast, table)
    assert any(i.op == "OP_DROP" for i in ir)
    opt_ir = optimize(ir)
    assert any(i.op == "OP_DROP" for i in opt_ir)
    trace = execute(opt_ir)
    assert "Dropped columns: student_id, name" in trace

def test_valid_select_then_drop():
    trace = run_pipeline(get_example_path('valid_select_then_drop.pipe'))
    assert "Dropped columns: extra_col" in trace

def test_invalid_drop_before_load():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_drop_before_load.pipe'))
    assert "'drop' used before any 'load' statement." in str(exc_info.value)

def test_invalid_drop_after_train():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_drop_after_train.pipe'))
    assert "'drop' used after model 'model' was trained" in str(exc_info.value)

def test_invalid_drop_all_selected():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_drop_all_selected.pipe'))
    assert "'drop' would remove every selected column." in str(exc_info.value)

def test_invalid_select_dropped_column():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_select_dropped_column.pipe'))
    assert "was dropped at line 4 and cannot be selected." in str(exc_info.value)

def test_invalid_drop_twice():
    with pytest.raises(SemanticError) as exc_info:
        run_pipeline(get_example_path('invalid_drop_twice.pipe'))
    assert "column 'student_id' was already dropped at line 4." in str(exc_info.value)


# ==============================================================================
# COMPREHENSIVE EXAMPLES TABLE & GUARD TEST
# ==============================================================================

EXAMPLES_TABLE = [
    ("valid_basic.pipe", "ok", "Evaluated model 'model'"),
    ("valid_drop.pipe", "ok", "Dropped columns: student_id, name"),
    ("valid_select_then_drop.pipe", "ok", "Dropped columns: extra_col"),
    ("optimizer_demo.pipe", "ok", "Evaluated model 'model1'"),
    ("complex_multi_model.pipe", "ok", "Evaluated model 'm2'"),
    ("complex_redundant.pipe", "ok", "Evaluated model 'live_model'"),
    ("complex_valid_drop_chain.pipe", "ok", "Dropped columns: c2"),
    ("invalid_clean_after_train.pipe", "semantic", "'clean' used after model 'model' was trained"),
    ("invalid_drop_after_train.pipe", "semantic", "'drop' used after model 'model' was trained"),
    ("invalid_drop_all_selected.pipe", "semantic", "'drop' would remove every selected column"),
    ("invalid_drop_before_load.pipe", "semantic", "'drop' used before any 'load' statement"),
    ("invalid_drop_twice.pipe", "semantic", "was already dropped at line"),
    ("invalid_duplicate_load.pipe", "semantic", "'load' used more than once"),
    ("invalid_duplicate_model.pipe", "semantic", "is already defined at line"),
    ("invalid_duplicate_split.pipe", "semantic", "is already defined at line"),
    ("invalid_lexical_error.pipe", "lexical", "unexpected character"),
    ("invalid_select_dropped_column.pipe", "semantic", "was dropped at line 4 and cannot be selected"),
    ("invalid_split_total_over_100.pipe", "semantic", "cumulative split total would be 110%, which exceeds 100%"),
    ("invalid_syntax_error.pipe", "syntax", "Syntax Error"),
    ("invalid_train_before_split.pipe", "semantic", "training data has not been defined"),
]

def test_all_examples_covered_by_table():
    examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples')
    all_pipe_files = {f for f in os.listdir(examples_dir) if f.endswith('.pipe')}
    table_files = {entry[0] for entry in EXAMPLES_TABLE}
    missing = all_pipe_files - table_files
    assert not missing, f"The following .pipe files in examples/ are missing from EXAMPLES_TABLE: {missing}"

@pytest.mark.parametrize("filename,outcome,substring", EXAMPLES_TABLE)
def test_example_from_table(filename, outcome, substring):
    filepath = get_example_path(filename)
    if outcome == "ok":
        trace = run_pipeline(filepath)
        assert any(substring in line for line in trace), f"Expected substring '{substring}' in trace: {trace}"
    elif outcome == "lexical":
        with pytest.raises(LexicalError) as exc_info:
            run_pipeline(filepath)
        assert substring in str(exc_info.value)
    elif outcome == "syntax":
        with pytest.raises(SyntaxError_) as exc_info:
            run_pipeline(filepath)
        assert substring in str(exc_info.value)
    elif outcome == "semantic":
        with pytest.raises(SemanticError) as exc_info:
            run_pipeline(filepath)
        assert substring in str(exc_info.value)
    else:
        pytest.fail(f"Unknown expected outcome: {outcome}")

