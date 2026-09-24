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
