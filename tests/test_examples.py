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
