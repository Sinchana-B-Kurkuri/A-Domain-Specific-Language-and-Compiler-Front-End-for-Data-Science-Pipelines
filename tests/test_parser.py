import pytest
from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser, SyntaxError_
from ds_pipeline_dsl.ast_nodes import PipelineNode, LoadStmt

def test_parser_valid():
    source = 'pipeline my_pipe { load "data.csv"; }'
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    assert isinstance(ast, PipelineNode)
    assert ast.name == "my_pipe"
    assert len(ast.statements) == 1
    assert isinstance(ast.statements[0], LoadStmt)
    assert ast.statements[0].filename == "data.csv"

def test_parser_invalid():
    source = 'pipeline my_pipe { load ; }'
    tokens = tokenize(source)
    with pytest.raises(SyntaxError_):
        Parser(tokens).parse_pipeline()

def test_parser_trailing_tokens():
    source = 'pipeline p { load "data.csv"; } extra;'
    tokens = tokenize(source)
    with pytest.raises(SyntaxError_) as exc_info:
        Parser(tokens).parse_pipeline()
    assert "unexpected token" in str(exc_info.value)
    assert "after end of pipeline" in str(exc_info.value)

def test_parser_second_pipeline():
    source = 'pipeline p1 { load "data1.csv"; } pipeline p2 { load "data2.csv"; }'
    tokens = tokenize(source)
    with pytest.raises(SyntaxError_) as exc_info:
        Parser(tokens).parse_pipeline()
    assert "only one pipeline per file is supported" in str(exc_info.value)

def test_parser_missing_rbrace():
    source = 'pipeline p { load "data.csv";'
    tokens = tokenize(source)
    with pytest.raises(SyntaxError_) as exc_info:
        Parser(tokens).parse_pipeline()
    assert "unexpected end of file" in str(exc_info.value)
    assert "expected '}' to close pipeline 'p'" in str(exc_info.value)

def test_parser_split_number_instead_of_percent():
    source = 'pipeline p { load "data.csv"; split train = 80; }'
    tokens = tokenize(source)
    with pytest.raises(SyntaxError_) as exc_info:
        Parser(tokens).parse_pipeline()
    assert "expected PERCENT, found NUMBER" in str(exc_info.value)

def test_parser_empty_body():
    source = 'pipeline p { }'
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    assert isinstance(ast, PipelineNode)
    assert ast.name == "p"
    assert len(ast.statements) == 0

def test_parser_drop_single_column():
    source = 'pipeline p { load "d.csv"; drop c1; }'
    ast = Parser(tokenize(source)).parse_pipeline()
    assert len(ast.statements) == 2
    stmt = ast.statements[1]
    assert stmt.__class__.__name__ == "DropStmt"
    assert stmt.columns == ["c1"]
    assert stmt.line == 1

def test_parser_drop_multiple_columns():
    source = 'pipeline p { load "d.csv"; drop c1, c2, c3; }'
    ast = Parser(tokenize(source)).parse_pipeline()
    assert len(ast.statements) == 2
    stmt = ast.statements[1]
    assert stmt.__class__.__name__ == "DropStmt"
    assert stmt.columns == ["c1", "c2", "c3"]
    assert stmt.line == 1

def test_parser_drop_missing_semicolon():
    source = 'pipeline p { load "d.csv"; drop c1 }'
    with pytest.raises(SyntaxError_):
        Parser(tokenize(source)).parse_pipeline()

def test_parser_drop_missing_column():
    source = 'pipeline p { load "d.csv"; drop ; }'
    with pytest.raises(SyntaxError_):
        Parser(tokenize(source)).parse_pipeline()

def test_parser_drop_trailing_comma():
    source = 'pipeline p { load "d.csv"; drop c1, ; }'
    with pytest.raises(SyntaxError_):
        Parser(tokenize(source)).parse_pipeline()
