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
