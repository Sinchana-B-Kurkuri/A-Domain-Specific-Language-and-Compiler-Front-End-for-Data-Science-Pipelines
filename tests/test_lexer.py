import pytest
from ds_pipeline_dsl.lexer import tokenize, LexicalError

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

def test_tokenize_crlf_vs_lf():
    lf_source = 'pipeline my_pipe {\n    load "data.csv";\n    clean missing;\n}\n'
    crlf_source = 'pipeline my_pipe {\r\n    load "data.csv";\r\n    clean missing;\r\n}\r\n'
    tokens_lf = tokenize(lf_source)
    tokens_crlf = tokenize(crlf_source)
    assert len(tokens_lf) == len(tokens_crlf)
    for t_lf, t_crlf in zip(tokens_lf, tokens_crlf):
        assert t_lf.type == t_crlf.type
        assert t_lf.value == t_crlf.value
        assert t_lf.line == t_crlf.line
        assert t_lf.col == t_crlf.col

def test_tokenize_unterminated_string():
    source = 'pipeline my_pipe { load "data.csv; }'
    with pytest.raises(LexicalError) as exc_info:
        tokenize(source)
    assert "unterminated string literal" in str(exc_info.value)

def test_tokenize_string_with_comment_slashes():
    source = 'load "path//to//data.csv";'
    tokens = tokenize(source)
    str_tokens = [t for t in tokens if t.type == "STRING"]
    assert len(str_tokens) == 1
    assert str_tokens[0].value == '"path//to//data.csv"'

def test_tokenize_multiline_string_unterminated():
    source = 'load "line1\nline2";'
    with pytest.raises(LexicalError) as exc_info:
        tokenize(source)
    assert "unterminated string literal" in str(exc_info.value)

def test_tokenize_drop_keyword():
    source = 'drop col1, col2;'
    tokens = tokenize(source)
    assert tokens[0].type == "DROP"
    assert tokens[0].value == "drop"
    assert tokens[1].type == "IDENT"
    assert tokens[1].value == "col1"

def test_tokenize_droplet_identifier():
    source = 'select droplet;'
    tokens = tokenize(source)
    assert tokens[1].type == "IDENT"
    assert tokens[1].value == "droplet"

@pytest.mark.parametrize("illegal_char", ["@", "#", "$", "-"])
def test_tokenize_illegal_characters(illegal_char):
    source = f"pipeline p {{ {illegal_char} }}"
    with pytest.raises(LexicalError) as exc_info:
        tokenize(source)
    assert f"unexpected character {illegal_char!r}" in str(exc_info.value)

def test_tokenize_negative_percent_error():
    source = "pipeline p { split train = -5%; }"
    with pytest.raises(LexicalError) as exc_info:
        tokenize(source)
    assert "unexpected character '-'" in str(exc_info.value)

def test_tokenize_non_ascii_in_ident_error():
    source = "select café;"
    with pytest.raises(LexicalError) as exc_info:
        tokenize(source)
    assert "unexpected character" in str(exc_info.value)

def test_tokenize_non_ascii_in_comment_and_string_valid():
    source = '// Café résumé\nload "café_dataset.csv";'
    tokens = tokenize(source)
    str_tokens = [t for t in tokens if t.type == "STRING"]
    assert len(str_tokens) == 1
    assert str_tokens[0].value == '"café_dataset.csv"'

def test_tokenize_comment_at_eof_without_newline():
    source = 'load "data.csv"; // trailing comment'
    tokens = tokenize(source)
    assert tokens[0].type == "LOAD"
    assert tokens[1].type == "STRING"
    assert tokens[2].type == "SEMI"
    assert tokens[3].type == "EOF"

@pytest.mark.parametrize("ident", ["dropped", "trainer", "loader", "cleaner", "evaluator", "splitter"])
def test_tokenize_keyword_prefixes_are_identifiers(ident):
    source = f"select {ident};"
    tokens = tokenize(source)
    assert tokens[1].type == "IDENT"
    assert tokens[1].value == ident

def test_tokenize_line_and_col_numbers_line3_plus():
    source = 'load "d.csv";\n\nclean missing;\n'
    tokens = tokenize(source)
    clean_tok = next(t for t in tokens if t.value == "clean")
    missing_tok = next(t for t in tokens if t.value == "missing")
    assert clean_tok.line == 3
    assert clean_tok.col == 0
    assert missing_tok.line == 3
    assert missing_tok.col == 6
