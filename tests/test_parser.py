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
