import pytest
from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze
from ds_pipeline_dsl.ir import lower_to_ir, IRInstruction

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

def test_lower_to_ir():
    tokens = tokenize(VALID_PROGRAM)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    
    ir = lower_to_ir(ast, table)
    
    assert len(ir) == 6
    assert ir[0].op == "OP_LOAD"
    assert ir[0].args["filename"] == "students.csv"
    
    assert ir[1].op == "OP_CLEAN"
    assert ir[1].args["strategy"] == "missing_values"
    
    assert ir[2].op == "OP_SELECT"
    assert ir[2].args["columns"] == ["cgpa", "attendance", "study_hours"]
    
    assert ir[3].op == "OP_SPLIT"
    assert ir[3].args["name"] == "train"
    assert ir[3].args["percent"] == 80.0
    
    assert ir[4].op == "OP_TRAIN"
    assert ir[4].args["model_name"] == "model"
    assert ir[4].args["algorithm"] == "decision_tree"
    
    assert ir[5].op == "OP_EVAL"
    assert ir[5].args["model_name"] == "model"
