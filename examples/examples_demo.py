import sys
import os

# Ensure ds_pipeline_dsl is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

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

def run_demo(source: str, label: str):
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}")
    tokens = tokenize(source)
    print(f"\n[LEXER OUTPUT] {len(tokens) - 1} tokens generated:")
    print(", ".join(f"{t.type}({t.value})" for t in tokens if t.type != "EOF"))

    ast = Parser(tokens).parse_pipeline()
    print(f"\n[PARSER OUTPUT] AST for pipeline '{ast.name}':")
    for s in ast.statements:
        print("   ", s)

    print("\n[SEMANTIC ANALYSIS]")
    try:
        table = analyze(ast)
        print("    No semantic errors found. Symbol table state:")
        print(f"    data_loaded={table.data_loaded}, "
              f"data_cleaned={table.data_cleaned}, "
              f"splits={table.splits}, models={table.models}")
    except SemanticError as e:
        print(f"    {e}")

if __name__ == "__main__":
    run_demo(VALID_PROGRAM, "DEMO 1: VALID PIPELINE (train after split)")
    run_demo(INVALID_PROGRAM, "DEMO 2: INVALID PIPELINE (train before split)")
