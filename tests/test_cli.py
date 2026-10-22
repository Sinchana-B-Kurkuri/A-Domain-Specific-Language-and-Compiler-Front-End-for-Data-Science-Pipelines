import sys
import pytest
from unittest.mock import patch
from io import StringIO
import tempfile
import os

from ds_pipeline_dsl.cli import main

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
    split train = 80%;
    evaluate model;
}
'''

@pytest.fixture
def valid_file():
    fd, path = tempfile.mkstemp(suffix=".pipe")
    with os.fdopen(fd, 'w') as f:
        f.write(VALID_PROGRAM)
    yield path
    os.remove(path)

@pytest.fixture
def invalid_file():
    fd, path = tempfile.mkstemp(suffix=".pipe")
    with os.fdopen(fd, 'w') as f:
        f.write(INVALID_PROGRAM)
    yield path
    os.remove(path)

def test_cli_trace_valid(valid_file):
    test_args = ["cli.py", valid_file, "--trace"]
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()

    assert "=== TRACE ===" in output
    assert "Loaded students.csv" in output
    assert "Evaluated model 'model'" in output
    assert "=== TOKENS ===" not in output

def test_cli_no_flags(valid_file):
    test_args = ["cli.py", valid_file]
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()

    assert "=== TOKENS ===" in output
    assert "=== AST ===" in output
    assert "=== IR ===" in output
    assert "=== OPTIMIZED IR ===" in output
    assert "=== TRACE ===" in output

def test_cli_semantic_error(invalid_file):
    test_args = ["cli.py", invalid_file, "--trace"]
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1
            output = fake_out.getvalue()

    assert "Semantic Error" in output
    assert "=== TRACE ===" not in output

def test_cli_valid_drop():
    example_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'valid_drop.pipe')
    test_args = ["cli.py", example_path]
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            main()
            output = fake_out.getvalue()
    assert "Token(type='DROP'" in output
    assert "DropStmt(" in output
    assert "IRInstruction(op='OP_DROP'" in output
    assert "Dropped columns: student_id, name" in output

def test_cli_invalid_drop():
    example_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'invalid_drop_before_load.pipe')
    test_args = ["cli.py", example_path]
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with pytest.raises(SystemExit) as e:
                main()
            assert e.value.code == 1
            output = fake_out.getvalue()
    assert "'drop' used before any 'load' statement." in output
    assert "Traceback" not in output


def test_cli_reads_utf8_source_with_legacy_default_encoding(tmp_path, monkeypatch, capsys):
    """Explicit UTF-8 reads must work even when the platform default is ASCII."""
    import builtins
    source = tmp_path / "unicode.pipe"
    source.write_text('pipeline p { load "\u03b4.csv"; }', encoding="utf-8")
    actual_open = builtins.open

    def legacy_open(file, mode="r", *args, **kwargs):
        if str(file) == str(source) and "encoding" not in kwargs:
            kwargs["encoding"] = "ascii"
        return actual_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", legacy_open)
    monkeypatch.setattr(sys, "argv", ["cli.py", str(source), "--trace"])
    main()
    assert "Loaded \u03b4.csv" in capsys.readouterr().out
