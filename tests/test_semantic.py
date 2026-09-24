import pytest
from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze, SemanticError

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

INVALID_PROGRAM = '''
pipeline student_prediction {
    load "students.csv";
    clean missing_values;
    select cgpa, attendance, study_hours;
    train model = decision_tree;
    evaluate model;
}
'''

def test_semantic_valid():
    tokens = tokenize(VALID_PROGRAM)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    assert table.data_loaded is True
    assert table.data_cleaned is True
    assert "train" in table.splits
    assert table.splits["train"] == 80.0
    assert "model" in table.models

def test_semantic_invalid():
    tokens = tokenize(INVALID_PROGRAM)
    ast = Parser(tokens).parse_pipeline()
    with pytest.raises(SemanticError):
        analyze(ast)

INVALID_SPLIT_PROGRAM = '''
pipeline student_prediction {
    load "students.csv";
    clean missing_values;
    select cgpa, attendance, study_hours;
    split train = 150%;
    train model = decision_tree;
    evaluate model;
}
'''

def test_semantic_invalid_split():
    tokens = tokenize(INVALID_SPLIT_PROGRAM)
    ast = Parser(tokens).parse_pipeline()
    with pytest.raises(SemanticError):
        analyze(ast)
