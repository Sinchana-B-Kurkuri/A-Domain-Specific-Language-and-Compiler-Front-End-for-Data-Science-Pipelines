import pytest
from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze, SemanticError
from ds_pipeline_dsl.ir import lower_to_ir
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute
from tests.helpers import compile_to_ir

@pytest.mark.parametrize("pct,valid", [
    (0, False),
    (0.1, True),
    (99.9, True),
    (100, False),
    (100.1, False),
])
def test_boundary_split_percentages(pct, valid):
    source = f'pipeline p {{ load "d.csv"; split train = {pct}%; }}'
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    if valid:
        table = analyze(ast)
        assert table.splits["train"] == pct
    else:
        with pytest.raises(SemanticError) as exc_info:
            analyze(ast)
        assert "split percentage must be strictly between 0 and 100." in str(exc_info.value)

def test_boundary_cumulative_split_exactly_100_valid():
    source = 'pipeline p { load "d.csv"; split train = 60%; split test = 40%; }'
    ast = Parser(tokenize(source)).parse_pipeline()
    table = analyze(ast)
    assert table.splits["train"] == 60.0
    assert table.splits["test"] == 40.0

def test_boundary_cumulative_split_exceeds_100_invalid():
    source = 'pipeline p { load "d.csv"; split train = 60%; split test = 40.1%; }'
    ast = Parser(tokenize(source)).parse_pipeline()
    with pytest.raises(SemanticError) as exc_info:
        analyze(ast)
    assert "cumulative split total would be 100.1%, which exceeds 100%." in str(exc_info.value)

def test_boundary_empty_pipeline_body():
    source = "pipeline p { }"
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    ir = lower_to_ir(ast, table)
    assert ir == []
    opt = optimize(ir)
    assert opt == []
    trace = execute(opt)
    assert trace == []

def test_boundary_whole_program_on_one_line():
    source = 'pipeline p { load "d.csv"; clean missing; select c1; split train = 80%; train m = dt; evaluate m; }'
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    ir = lower_to_ir(ast, table)
    opt = optimize(ir)
    trace = execute(opt)
    assert len(trace) == 6
    assert trace[0] == "Loaded d.csv"
    assert trace[-1] == "Evaluated model 'm' (simulated accuracy trace)"

def test_boundary_no_trailing_newline():
    source = 'pipeline p {\n    load "d.csv";\n}'
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    ir = lower_to_ir(ast, table)
    assert len(ir) == 1
    assert ir[0].op == "OP_LOAD"

def test_boundary_select_200_columns():
    cols = [f"c_{i}" for i in range(200)]
    source = f'pipeline p {{ load "d.csv"; select {", ".join(cols)}; }}'
    ast = Parser(tokenize(source)).parse_pipeline()
    table = analyze(ast)
    assert table.selected_columns == cols

def test_boundary_drop_200_columns():
    cols = [f"c_{i}" for i in range(200)]
    source = f'pipeline p {{ load "d.csv"; drop {", ".join(cols)}; }}'
    ast = Parser(tokenize(source)).parse_pipeline()
    table = analyze(ast)
    assert len(table.dropped_columns) == 200

def test_boundary_identifier_5000_characters():
    long_name = "model_" + "a" * 5000
    source = f'pipeline p {{ load "d.csv"; split train = 80%; train {long_name} = dt; evaluate {long_name}; }}'
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    assert long_name in table.models
    ir = lower_to_ir(ast, table)
    trace = execute(ir)
    assert f"Trained model '{long_name}' using dt" in trace
    assert f"Evaluated model '{long_name}' (simulated accuracy trace)" in trace

def test_boundary_1000_statements_program():
    clean_stmts = "\n    ".join("clean strat;" for _ in range(996))
    source = f'''pipeline p {{
    load "d.csv";
    {clean_stmts}
    split train = 80%;
    train m = dt;
    evaluate m;
}}'''
    ir = compile_to_ir(source)
    assert len(ir) == 1000
    opt = optimize(ir)
    # The 996 duplicate clean statements will collapse into 1 clean statement!
    # Result: load, 1 clean, split, train, eval = 5 instructions
    assert len(opt) == 5
    trace = execute(opt)
    assert len(trace) == 5

def test_boundary_pipeline_with_only_load():
    source = 'pipeline p { load "dataset.csv"; }'
    ir = compile_to_ir(source)
    opt = optimize(ir)
    assert len(opt) == 1
    assert opt[0].op == "OP_LOAD"
    trace = execute(opt)
    assert trace == ["Loaded dataset.csv"]

def test_boundary_pipeline_with_no_evaluate_preserves_trains():
    source = 'pipeline p { load "d.csv"; split train = 80%; train m = dt; }'
    ir = compile_to_ir(source)
    opt = optimize(ir)
    train_inst = [i for i in opt if i.op == "OP_TRAIN"]
    assert len(train_inst) == 1
    assert train_inst[0].args["model_name"] == "m"
    trace = execute(opt)
    assert "Trained model 'm' using dt" in trace
    assert not any("Evaluated model" in t for t in trace)
