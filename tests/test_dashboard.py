"""Dashboard integration coverage; pure runner tests do not require Streamlit."""

from contextlib import redirect_stdout
from dataclasses import asdict
from io import StringIO
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
for directory in (ROOT / "src", ROOT / "dashboard"):
    sys.path.insert(0, str(directory))

import compiler_runner as runner
from performance_loader import load_performance
from ds_pipeline_dsl.lexer import tokenize, LexicalError
from ds_pipeline_dsl.parser import Parser, SyntaxError_
from ds_pipeline_dsl.semantic import analyze, SemanticError
from ds_pipeline_dsl.ir import lower_to_ir, IRInstruction
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute
from tests.test_examples import EXAMPLES_TABLE

EXPECTED = {name: outcome for name, outcome, _ in EXAMPLES_TABLE}
EXAMPLES = sorted((ROOT / "examples").glob("*.pipe"))
ERROR_TYPES = {LexicalError: "Lexical", SyntaxError_: "Syntax", SemanticError: "Semantic"}
ERROR_SOURCES = (
    ("Lexical", 'pipeline p {\n @\n}'),
    ("Syntax", 'pipeline p {\n load "d.csv"\n}'),
    ("Semantic", 'pipeline p {\n clean missing;\n}'),
)


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_runner_matches_direct_compiler_for_every_example(path):
    source = path.read_text(encoding="utf-8")
    result = runner.compile_source(source)
    direct = {}
    try:
        with redirect_stdout(StringIO()):
            direct["tokens"] = tokenize(source)
            direct["ast"] = Parser(direct["tokens"]).parse_pipeline()
            direct["symbol_table"] = analyze(direct["ast"])
            direct["ir"] = lower_to_ir(direct["ast"], direct["symbol_table"])
            direct["notes"] = []
            direct["optimized_ir"] = optimize(direct["ir"], direct["notes"])
            direct["trace"] = execute(direct["optimized_ir"])
    except tuple(ERROR_TYPES) as exc:
        assert EXPECTED[path.name] == ERROR_TYPES[type(exc)].lower()
        assert result.error.kind == ERROR_TYPES[type(exc)]
        assert result.error.message == str(exc)
        assert result.error.stage == result.failed_stage
        if result.error.line is not None:
            assert 1 <= result.error.line <= len(source.splitlines()) + 1
        failed = next(i for i, stage in enumerate(result.stages) if stage.status == "failed")
        assert all(s.status == "ok" for s in result.stages[:failed])
        assert all(s.status == "skipped" for s in result.stages[failed + 1:])
        if result.error.kind == "Syntax":
            assert result.tokens
        if result.error.kind == "Semantic":
            assert result.ast is not None
    else:
        assert EXPECTED[path.name] == "ok"
        assert result.error is None
        assert all(s.status == "ok" for s in result.stages)
        assert result.ir == direct["ir"]
        assert result.optimized_ir == direct["optimized_ir"]
        assert result.notes == direct["notes"]
        assert result.trace == direct["trace"]
        assert result.unoptimized_trace == execute(direct["ir"])
        assert vars(result.symbol_table) == vars(direct["symbol_table"])
        assert result.ir_before == len(direct["ir"])
        assert result.ir_after == len(direct["optimized_ir"])
        assert result.removed == result.ir_before - result.ir_after
        assert result.reduction_pct == pytest.approx(100 * result.removed / result.ir_before)
    if "tokens" in direct:
        assert [asdict(t) for t in result.tokens] == [asdict(t) for t in direct["tokens"]]
        assert result.tokens[-1].type == "EOF"
    if "ast" in direct:
        assert repr(result.ast) == repr(direct["ast"])


@pytest.mark.parametrize("kind,source", ERROR_SOURCES)
def test_inline_error_kinds(kind, source):
    result = runner.compile_source(source)
    assert result.error.kind == kind
    assert result.error.line is not None
    if kind == "Lexical":
        assert result.error.col == 1


@pytest.mark.parametrize("source", ["", " \t\r\n ", "pipeline empty {}"])
def test_empty_sources_and_zero_ir(source):
    result = runner.compile_source(source)
    assert result.reduction_pct == 0.0
    if source.startswith("pipeline"):
        assert result.error is None
        assert result.trace == result.unoptimized_trace == []
    else:
        assert result.error.kind == "Syntax"


def test_input_guard_does_not_call_compiler(monkeypatch):
    def forbidden(*args):
        pytest.fail("oversized source reached the compiler")
    monkeypatch.setattr(runner, "tokenize", forbidden)
    result = runner.compile_source(" " * (runner.MAX_SOURCE_CHARS + 1))
    assert result.error.kind == "Input"
    assert "100,000" in result.error.message
    assert all(s.status == "skipped" for s in result.stages)


def test_optimizer_demo_and_crlf():
    source = runner.read_example(ROOT / "examples" / "optimizer_demo.pipe")
    lf = runner.compile_source(source)
    crlf = runner.compile_source(source.replace("\n", "\r\n"))
    assert lf.error is crlf.error is None
    assert lf.reduction_pct > 0
    assert lf.notes
    assert lf.tokens == crlf.tokens
    assert lf.ir == crlf.ir
    assert lf.optimized_ir == crlf.optimized_ir
    assert lf.notes == crlf.notes
    assert lf.trace == crlf.trace


def test_match_ir_kept_removed_and_merged_drop():
    before = [IRInstruction("OP_LOAD", {"filename": "d.csv", "line": 1}),
              IRInstruction("OP_CLEAN", {"strategy": "x", "line": 2}),
              IRInstruction("OP_CLEAN", {"strategy": "x", "line": 3}),
              IRInstruction("OP_DROP", {"columns": ["a"], "line": 4}),
              IRInstruction("OP_DROP", {"columns": ["b"], "line": 5}),
              IRInstruction("OP_SELECT", {"columns": ["c"], "line": 6})]
    assert runner.match_ir(before, optimize(before)) == [
        "kept", "kept", "removed/merged", "removed/merged", "removed/merged", "kept"]
    assert runner.match_ir([], []) == []


def test_stdout_capture_and_internal_failure(monkeypatch, capsys):
    real_tokenize = runner.tokenize
    def noisy_tokenize(source):
        print("stray lexer output")
        return real_tokenize(source)
    monkeypatch.setattr(runner, "tokenize", noisy_tokenize)
    assert runner.compile_source("pipeline p {}").error is None
    def broken(*args):
        print("stray semantic output")
        raise RuntimeError("unexpected internal failure")
    monkeypatch.setattr(runner, "analyze", broken)
    result = runner.compile_source("pipeline p {}")
    assert result.error.kind == "Internal"
    assert result.failed_stage == "Semantic"
    assert "RuntimeError" in result.traceback
    assert result.ast is not None
    assert capsys.readouterr().out == ""


def test_unoptimized_comparison_cannot_break_result(monkeypatch, capsys):
    real_execute = runner.execute
    calls = []
    def execute_once(ir):
        calls.append(ir)
        print("stray executor output")
        if len(calls) == 2:
            raise RuntimeError("comparison unavailable")
        return real_execute(ir)
    monkeypatch.setattr(runner, "execute", execute_once)
    result = runner.compile_source("pipeline p {}")
    assert result.error is None
    assert result.stages[-1].status == "ok"
    assert result.unoptimized_trace is None
    assert "comparison unavailable" in result.comparison_error
    assert capsys.readouterr().out == ""


def test_example_discovery_and_utf8_roundtrip(tmp_path):
    entries = runner.list_examples(ROOT / "examples")
    assert len(entries) == len(EXAMPLES)
    assert [(e.category, e.name) for e in entries] == sorted((e.category, e.name) for e in entries)
    assert {e.category for e in entries} == {"Valid", "Invalid", "Complex", "Optimizer"}
    for entry in entries:
        assert entry.name
        assert runner.read_example(entry.path) == entry.path.read_text(encoding="utf-8")
    path = tmp_path / "custom.pipe"
    path.write_text('// café\npipeline p {}', encoding="utf-8")
    assert runner.read_example(path) == '// café\npipeline p {}'
    assert runner.list_examples(tmp_path)[0].category == "Other"
    assert runner.list_examples(tmp_path / "missing") == []
    assert runner.list_examples(path) == []


def test_performance_loader_header_driven_and_verbatim(tmp_path):
    pd = pytest.importorskip("pandas")
    path = tmp_path / "performance.md"
    report = ("# Report\n## Environment\n- Python: test\n\n## Results\n"
              "| Status | IR after | Statements | us/stmt | Lexer ms | Reduction % |\n"
              "|:---|---:|---:|---:|---:|---:|\n"
              "| ok | 7 | 10 | 2.3 | 0.1 | 30% |\n"
              "| skipped (budget) | - | 100 | n/a | - | - |\n"
              "| reduced repetitions | 70 | 1000 | 2.4 | .2 | 30% |\n\n"
              "## Observations\n1. Exact *text*.\n\n## Next\nexcluded\n")
    path.write_text(report, encoding="utf-8", newline="")
    data = load_performance(path)
    assert data.available
    assert list(data.table.columns) == ["Status", "IR after", "Statements", "us/stmt", "Lexer ms", "Reduction %"]
    assert data.table.loc[0, "Statements"] == 10
    assert data.table.loc[0, "Reduction %"] == 30
    assert pd.isna(data.table.loc[1, "us/stmt"])
    assert data.table.loc[1, "Status"] == "skipped (budget)"
    assert data.environment == "- Python: test\n\n"
    assert data.observations == "1. Exact *text*.\n\n"
    assert data.marked_rows == [1, 2]
    # Preserve CRLF section text too.
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(report.replace("\n", "\r\n"))
    assert load_performance(path).environment == "- Python: test\r\n\r\n"


@pytest.mark.parametrize("contents", ["garbage", "| Statements | Total ms |\n|---|---|\n", "| Statements | Total ms |\n|---|---|\n| 10 | 1 | extra |"])
def test_unavailable_performance_reports(tmp_path, contents):
    path = tmp_path / "report.md"
    assert not load_performance(path).available
    path.write_text(contents, encoding="utf-8")
    data = load_performance(path)
    assert not data.available
    assert data.reason


def test_real_performance_report_structure():
    pytest.importorskip("pandas")
    path = ROOT / "docs" / "performance.md"
    if not path.exists():
        pytest.skip("No recorded benchmark report")
    data = load_performance(path)
    assert data.available, data.reason
    assert "Statements" in data.table.columns
    assert not data.table.empty
    assert data.environment
    assert data.observations


@pytest.fixture
def app():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=30).run()


def playground(app):
    app.sidebar.radio(key="page").set_value("Compiler Playground").run()
    assert not app.exception
    return app


def test_ui_every_page_and_default_compile(app):
    for page in ("Overview", "Compiler Playground", "Architecture", "Performance"):
        app.sidebar.radio(key="page").set_value(page).run()
        assert not app.exception
        assert not app.warning
    playground(app).button(key="compile_btn").click().run()
    assert not app.exception
    assert any(s.value == "Compiled successfully" for s in app.success)
    assert app.session_state["result"].tokens[-1].type == "EOF"
    assert not app.warning


@pytest.mark.parametrize("kind,source", ERROR_SOURCES)
def test_ui_error_highlighting_and_live_architecture(app, kind, source):
    playground(app).text_area(key="editor_text").set_value(source).run()
    app.button(key="compile_btn").click().run()
    assert not app.exception
    assert not app.warning
    assert any(kind + " Error" in e.value and "line" in e.value for e in app.error)
    assert any('<tr class="error-line">' in m.value for m in app.markdown)
    result = app.session_state["result"]
    assert any(c.value == result.error.message for c in app.code)
    if kind == "Lexical":
        assert any("<mark>@</mark>" in m.value for m in app.markdown)
    app.sidebar.radio(key="page").set_value("Architecture").run()
    assert not app.exception
    assert not app.warning
    chart = app.get("graphviz_chart")[0]
    assert '#FEE2E2' in chart.proto.spec
    assert '#E2E8F0' in chart.proto.spec


def test_ui_optimizer_callback_stale_source_and_html_escaping(app):
    playground(app).selectbox(key="example_choice").select("optimizer_demo.pipe").run()
    assert "dead_model" in app.text_area(key="editor_text").value
    app.button(key="compile_btn").click().run()
    assert not app.exception
    result = app.session_state["result"]
    assert result.reduction_pct > 0 and result.notes
    assert not app.warning
    app.text_area(key="editor_text").set_value('pipeline p { load "<script>alert(1)</script>"; }').run()
    assert any("Source changed since last compile" in c.value for c in app.caption)
    app.button(key="compile_btn").click().run()
    assert not app.exception
    assert any("&lt;script&gt;" in m.value for m in app.markdown)
    assert not any("<script>" in m.value for m in app.markdown)
    app.selectbox(key="example_category").select("Invalid").run()
    assert not app.exception
    assert app.selectbox(key="example_choice").value.startswith("invalid_")
    assert app.text_area(key="editor_text").value == runner.read_example(ROOT / "examples" / app.selectbox(key="example_choice").value)


def test_ui_missing_docs_examples_and_unreadable_example(app, monkeypatch):
    monkeypatch.setattr(runner, "list_examples", lambda _: [])
    playground(app)
    assert not app.exception
    app.button(key="compile_btn").click().run()
    assert not app.exception
    monkeypatch.undo()
    playground(app)
    def unreadable(_):
        raise OSError("cannot read file")
    monkeypatch.setattr(runner, "read_example", unreadable)
    app.selectbox(key="example_choice").select("optimizer_demo.pipe").run()
    assert not app.exception
    assert any("Could not read" in w.value for w in app.warning)
    import performance_loader
    monkeypatch.setattr(performance_loader, "load_performance", lambda p: performance_loader.PerformanceData(False, "missing report"))
    app.sidebar.radio(key="page").set_value("Performance").run()
    assert not app.exception
    assert any("python benchmarks/benchmark.py" in w.value for w in app.warning)


def test_ui_empty_oversized_input_and_large_token_stream(app):
    playground(app)
    for source, kind in (("", "Syntax"), (" " * (runner.MAX_SOURCE_CHARS + 1), "Input")):
        app.text_area(key="editor_text").set_value(source).run()
        app.button(key="compile_btn").click().run()
        assert not app.exception
        assert any(kind + " Error" in e.value for e in app.error)
    source = 'pipeline p { load "d.csv";\n' + 'clean x;\n' * 350 + '}'
    app.text_area(key="editor_text").set_value(source).run()
    app.button(key="compile_btn").click().run()
    assert not app.exception
    assert any("showing first 1000 of" in c.value for c in app.caption)
    assert any("Final token" in c.value and "EOF" in c.value for c in app.caption)
