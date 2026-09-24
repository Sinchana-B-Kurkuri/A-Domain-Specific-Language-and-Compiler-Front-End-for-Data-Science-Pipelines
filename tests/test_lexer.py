import pytest
from ds_pipeline_dsl.lexer import tokenize, Token, LexicalError

def test_tokenize_valid():
    source = 'pipeline my_pipe { load "data.csv"; }'
    tokens = tokenize(source)
    assert len(tokens) == 8
    assert tokens[0].type == "PIPELINE"
    assert tokens[1].type == "IDENT"
    assert tokens[1].value == "my_pipe"

def test_tokenize_invalid():
    source = 'pipeline @my_pipe { }'
    with pytest.raises(LexicalError):
        tokenize(source)
