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

def test_semantic_duplicate_load():
    code = '''pipeline p {
    load "d1.csv";
    load "d2.csv";
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 3" in err
    assert "'load' used more than once; a dataset was already loaded at line 2." in err

def test_semantic_empty_load_filename():
    code = '''pipeline p {
    load "";
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 2" in err
    assert "'load' requires a non-empty filename." in err

def test_semantic_clean_after_train():
    code = '''pipeline p {
    load "d.csv";
    split train = 80%;
    train m = dt;
    clean missing;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 5" in err
    assert "'clean' used after model 'm' was trained at line 4; data-preparation statements must appear before any 'train'." in err

def test_semantic_select_after_train():
    code = '''pipeline p {
    load "d.csv";
    split train = 80%;
    train m = dt;
    select col1;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 5" in err
    assert "'select' used after model 'm' was trained at line 4; data-preparation statements must appear before any 'train'." in err

def test_semantic_select_duplicate_column():
    code = '''pipeline p {
    load "d.csv";
    select cgpa, attendance, cgpa;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 3" in err
    assert "column 'cgpa' appears more than once in 'select'." in err

def test_semantic_duplicate_split():
    code = '''pipeline p {
    load "d.csv";
    split train = 50%;
    split train = 30%;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 4" in err
    assert "split 'train' is already defined at line 3." in err

def test_semantic_split_cumulative_over_100():
    code = '''pipeline p {
    load "d.csv";
    split train = 80%;
    split test = 20.1%;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 4" in err
    assert "cumulative split total would be 100.1%, which exceeds 100%." in err

def test_semantic_duplicate_model():
    code = '''pipeline p {
    load "d.csv";
    split train = 80%;
    train m = dt;
    train m = rf;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 5" in err
    assert "model 'm' is already defined at line 4." in err

def test_semantic_splits_80_20_valid():
    code = '''pipeline p {
    load "d.csv";
    split train = 80%;
    split test = 20%;
    train m = dt;
    evaluate m;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert table.splits["train"] == 80.0
    assert table.splits["test"] == 20.0

def test_semantic_splits_33_valid():
    code = '''pipeline p {
    load "d.csv";
    split s1 = 33.3%;
    split s2 = 33.3%;
    split s3 = 33.4%;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert len(table.splits) == 3

def test_semantic_split_100_or_0_invalid():
    code_100 = '''pipeline p {
    load "d.csv";
    split train = 100%;
}'''
    with pytest.raises(SemanticError) as exc1:
        analyze(Parser(tokenize(code_100)).parse_pipeline())
    assert "split percentage must be strictly between 0 and 100." in str(exc1.value)

    code_0 = '''pipeline p {
    load "d.csv";
    split train = 0%;
}'''
    with pytest.raises(SemanticError) as exc2:
        analyze(Parser(tokenize(code_0)).parse_pipeline())
    assert "split percentage must be strictly between 0 and 100." in str(exc2.value)

def test_semantic_split_after_train_valid():
    code = '''pipeline p {
    load "d.csv";
    split train = 70%;
    train m = dt;
    split test = 20%;
    evaluate m;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert "test" in table.splits
    assert table.splits["test"] == 20.0

def test_semantic_evaluate_twice_valid():
    code = '''pipeline p {
    load "d.csv";
    split train = 80%;
    train m = dt;
    evaluate m;
    evaluate m;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert "m" in table.models

def test_semantic_clean_select_before_train_valid():
    code = '''pipeline p {
    load "d.csv";
    clean missing;
    select c1, c2;
    split train = 80%;
    train m = dt;
    evaluate m;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert table.data_cleaned is True

def test_semantic_valid_drop_before_select():
    code = '''pipeline p {
    load "d.csv";
    drop id, name;
    select c1, c2;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert "id" in table.dropped_columns
    assert "name" in table.dropped_columns
    assert table.selected_columns == ["c1", "c2"]

def test_semantic_valid_select_then_drop():
    code = '''pipeline p {
    load "d.csv";
    select c1, c2, c3;
    drop c2;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert table.selected_columns == ["c1", "c3"]
    assert "c2" in table.dropped_columns

def test_semantic_drop_before_load_error():
    code = '''pipeline p {
    drop c1;
    load "d.csv";
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 2" in err
    assert "'drop' used before any 'load' statement." in err

def test_semantic_drop_after_train_error():
    code = '''pipeline p {
    load "d.csv";
    split train = 80%;
    train m = dt;
    drop c1;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 5" in err
    assert "'drop' used after model 'm' was trained at line 4; data-preparation statements must appear before any 'train'." in err

def test_semantic_drop_duplicate_column_error():
    code = '''pipeline p {
    load "d.csv";
    drop c1, c2, c1;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 3" in err
    assert "column 'c1' appears more than once in 'drop'." in err

def test_semantic_drop_already_dropped_error():
    code = '''pipeline p {
    load "d.csv";
    drop c1;
    drop c1;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 4" in err
    assert "column 'c1' was already dropped at line 3." in err

def test_semantic_drop_not_in_selection_error():
    code = '''pipeline p {
    load "d.csv";
    select c1, c2;
    drop c3;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 4" in err
    assert "cannot drop column 'c3': it is not in the current selection." in err

def test_semantic_drop_all_selected_error():
    code = '''pipeline p {
    load "d.csv";
    select c1, c2;
    drop c1, c2;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 4" in err
    assert "'drop' would remove every selected column." in err

def test_semantic_select_dropped_column_error():
    code = '''pipeline p {
    load "d.csv";
    drop c1;
    select c1, c2;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    err = str(exc_info.value)
    assert "line 4" in err
    assert "column 'c1' was dropped at line 3 and cannot be selected." in err

def test_semantic_drop_then_select_different_valid():
    code = '''pipeline p {
    load "d.csv";
    drop c1;
    select c2, c3;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert "c1" in table.dropped_columns
    assert table.selected_columns == ["c2", "c3"]

def test_semantic_drop_after_split_before_train_valid():
    code = '''pipeline p {
    load "d.csv";
    split train = 80%;
    drop c1;
    train m = dt;
    evaluate m;
}'''
    ast = Parser(tokenize(code)).parse_pipeline()
    table = analyze(ast)
    assert "c1" in table.dropped_columns
    assert "m" in table.models
