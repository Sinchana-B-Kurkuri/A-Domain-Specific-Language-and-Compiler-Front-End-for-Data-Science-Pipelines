import pytest
from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze
from ds_pipeline_dsl.ir import lower_to_ir
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute

VALID_PROGRAM = '''
pipeline student_prediction {
    load "students.csv";
    clean missing_values;
    select cgpa, attendance, study_hours;
    split train = 80%;
    train model = decision_tree;
    evaluate model;
}
'''

def test_executor():
    tokens = tokenize(VALID_PROGRAM)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    ir = lower_to_ir(ast, table)
    opt_ir = optimize(ir)
    
    trace = execute(opt_ir)
    
    assert len(trace) == 6
    assert trace[0] == "Loaded students.csv"
    assert trace[1] == "Cleaned using missing_values"
    assert trace[2] == "Selected columns: cgpa, attendance, study_hours"
    assert trace[3] == "Defined split 'train' = 80%"
    assert trace[4] == "Trained model 'model' using decision_tree"
    assert trace[5] == "Evaluated model 'model' (simulated accuracy trace)"

def test_executor_with_drop():
    program = '''
pipeline p {
    load "students.csv";
    drop a, b;
    select c;
}
'''
    tokens = tokenize(program)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    ir = lower_to_ir(ast, table)
    trace = execute(ir)
    assert "Dropped columns: a, b" in trace
    assert trace[1] == "Dropped columns: a, b"
