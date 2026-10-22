"""Streamlit UI and routing for the existing symbolic DSL compiler."""

from contextlib import contextmanager
from base64 import b64encode
from dataclasses import asdict, is_dataclass
import hashlib
from html import escape
import json
from pathlib import Path
import re
import sys
import traceback

DASHBOARD_DIR = Path(__file__).resolve().parent
ROOT = DASHBOARD_DIR.parent
for directory in (ROOT / "src", DASHBOARD_DIR):
    sys.path.insert(0, str(directory))

import compiler_runner
import performance_loader
import pandas as pd
import streamlit as st

LOGO_PATH = DASHBOARD_DIR / "logo.svg"
LOGO_URL = "data:image/svg+xml;base64," + b64encode(LOGO_PATH.read_bytes()).decode("ascii")

st.set_page_config(page_title="Data Science Pipeline DSL", page_icon=LOGO_URL, layout="wide")

EXAMPLES_DIR = ROOT / "examples"
PERFORMANCE_PATH = ROOT / "docs" / "performance.md"
PAGES = ("Overview", "Compiler Playground", "Architecture", "Performance")
SAMPLE = '''pipeline demo {
    load "students.csv";
    clean missing_values;
    select cgpa, attendance;
    split train = 80%;
    train model = decision_tree;
    evaluate model;
}
'''
for key, value in {"page": "Overview", "result": None, "compiled_hash": None,
                   "example_notice": None}.items():
    st.session_state.setdefault(key, value)

st.markdown("""<style>
:root {--ink:#17324D; --muted:#60758A; --teal:#087F8C; --line:#DFE8F0;}
.block-container {padding:2.2rem 2.5rem 3.5rem; max-width:1560px;}
[data-testid="stMain"] {background:#F7F9FC;}
[data-testid="stMain"] h2,[data-testid="stMain"] h3 {text-align:center; letter-spacing:-.025em;}
[data-testid="stMain"] [data-testid="stCaptionContainer"] {text-align:center; color:var(--muted);}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] > p {text-align:center;}
[data-testid="stColumn"] {min-width:0;}
.hero {box-sizing:border-box; width:100%; background:linear-gradient(120deg,#122C49,#1C4666);
 color:#FFF; border-radius:18px !important; overflow:hidden; isolation:isolate;
 padding:36px 30px 38px; margin:0 0 22px; text-align:center; box-shadow:0 8px 26px #17324D0D;}
.hero h1 {color:#FFF !important; background:transparent; font-size:clamp(1.8rem,2.8vw,2.55rem);
 font-weight:650; letter-spacing:-.04em; line-height:1.18; margin:12px 0 14px; padding:0;}
.hero p {color:#D6E5F0; font-size:.96rem; margin:0 auto; max-width:820px; line-height:1.8; text-align:center;}
.eyebrow {letter-spacing:.16em; font-size:.68rem; font-weight:650; color:#9FE3E0;}
.hero-brand {display:flex; align-items:center; justify-content:center; gap:10px;}
.hero-brand img {display:block; width:30px; height:30px; border-radius:8px;}
.section-label {color:var(--muted); font-size:.69rem; letter-spacing:.13em; text-transform:uppercase; font-weight:650;}
.language-label {text-align:center; color:var(--muted); font-size:.87rem; margin:0 0 20px;}
.language-label strong {color:var(--ink); font-weight:600;}
.language-panel {text-align:center; margin:8px auto 26px; max-width:950px;}
.declaration {display:inline-flex; flex-direction:column; gap:8px; padding:3px 26px 15px; margin-bottom:12px; border-bottom:1px solid var(--line);}
.declaration code {font-size:1.1rem; color:var(--ink); background:transparent; font-weight:600;}
.chips,.flow,.stage-strip {display:flex; flex-wrap:wrap; gap:9px; margin:14px 0 22px; align-items:center; justify-content:center;}
.chip {padding:7px 13px; border-radius:7px; font: .84rem Consolas,monospace; color:#07616D; background:#E6F2F2;}
.flow {row-gap:13px;}
.flow-node {padding:10px 14px; border-radius:9px; border:1px solid var(--line); background:#FFF; color:var(--ink); font-size:.82rem;}
.flow-arrow {color:#91A4B7; font-size:.85rem;}
.stage {border:1px solid var(--line); border-radius:12px; padding:13px 10px; background:#FFF;
 flex:1; min-width:112px; text-align:center;}
.stage strong {display:block; font-size:.82rem; margin-bottom:9px; color:var(--ink);}
.pill {display:inline-block; border-radius:20px; padding:3px 10px; font-size:.71rem; font-weight:600; line-height:1.45;}
.ok,.kept {color:#166534; background:#E5F5EB;} .failed {color:#991B1B; background:#FDEBEC;}
.skipped {color:#53657A; background:#EDF1F6;} .timing {display:block; font-size:.71rem; color:var(--muted); margin-top:7px;}
.compile-summary {text-align:center; color:var(--muted); font-size:.9rem; margin:6px 0 18px;}
[data-testid="stMetric"] {background:#FFF; border:1px solid var(--line); border-radius:12px; padding:19px 12px; text-align:center;}
[data-testid="stMetricLabel"] {justify-content:center; color:var(--muted);}
[data-testid="stMetricValue"] {font-size:1.9rem; font-weight:650; color:var(--ink);}
.fact-card {background:#FFF; border:1px solid var(--line); border-radius:12px; padding:21px 12px; text-align:center; height:100%;}
.fact-card .fact-value {color:var(--ink); font-size:1.75rem; font-weight:650; letter-spacing:-.04em; margin:8px 0 3px;}
.fact-card .fact-detail {font-size:.76rem; color:var(--muted);}
[data-testid="stSidebar"] {background:#FFF; border-right:1px solid var(--line);}
[data-testid="stSidebarUserContent"] {padding-top:2rem;}
.sidebar-brand {text-align:center; padding:0 8px 25px;}
.brand-mark {display:inline-flex; width:54px; height:54px; border-radius:14px; align-items:center; justify-content:center;
 margin-bottom:14px; box-shadow:0 5px 14px #142D4E15;}
.brand-mark img {display:block; width:54px; height:54px; border-radius:14px;}
.brand-name {font-size:1.28rem; font-weight:650; line-height:1.35; letter-spacing:-.035em; color:var(--ink);}
.brand-description {font-size:.73rem; color:var(--muted); margin-top:9px;}
.st-key-page [role="radiogroup"] {gap:5px;}
.st-key-page label[data-baseweb="radio"] {box-sizing:border-box; width:100%; margin:0; padding:12px 16px;
 border-left:3px solid transparent; border-radius:0 8px 8px 0; color:#53677D; transition:background .15s;}
.st-key-page label[data-baseweb="radio"] > div:first-child {display:none;}
.st-key-page label[data-baseweb="radio"] input {position:absolute; opacity:0;}
.st-key-page label[data-baseweb="radio"]:hover {background:#F5F8FB;}
.st-key-page label[data-baseweb="radio"]:has(input:checked) {background:#EDF6F6; border-left-color:var(--teal); color:#07616D;}
.st-key-page label[data-baseweb="radio"]:has(input:checked) p {font-weight:600;}
.st-key-page label[data-baseweb="radio"]:has(input:focus-visible) {outline:2px solid var(--teal); outline-offset:2px;}
.sidebar-language {margin:10px 8px 8px; text-align:center;}
.sidebar-root {display:flex; flex-direction:column; gap:7px; padding:17px 0 13px; color:var(--ink);}
.sidebar-root code {font-size:.98rem; background:transparent; color:var(--ink); font-weight:650;}
.sidebar-operations {display:flex; flex-wrap:wrap; justify-content:center; gap:7px; border-top:1px solid var(--line); padding:15px 0 8px;}
.sidebar-operations .chip {font-size:.73rem; padding:5px 10px;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {text-align:center; line-height:1.7;}
[data-baseweb="tab-list"] {justify-content:center; gap:8px; border-bottom:1px solid var(--line); margin-top:12px;}
[data-baseweb="tab"] {padding:12px 15px; font-size:.86rem;}
[data-baseweb="tab"][aria-selected="true"] {color:var(--teal); font-weight:600;}
[data-testid="stExpander"] {background:#FFF; border-radius:12px;}
[data-testid="stExpander"] details {border-color:var(--line); border-radius:12px;}
[data-testid="stTextArea"] textarea {font-family:Consolas,'Courier New',monospace; font-size:14px; line-height:1.8;}
[data-baseweb="textarea"],[data-baseweb="select"] > div {border-radius:10px;}
.st-key-compile_btn button {min-height:44px; border-radius:9px; font-weight:600; box-shadow:0 4px 10px #087F8C16;}
.source-wrap {overflow:auto; max-height:440px; border:1px solid var(--line); border-radius:10px; margin:12px 0; background:#FFF;}
.source-table {border-collapse:collapse; width:100%; font:13px/1.8 Consolas,monospace;}
.source-table td {padding:0 12px; white-space:pre; text-align:left;}
.source-table .line-no {width:45px; color:#65758B; border-right:1px solid #E4EAF0; user-select:none; text-align:right;}
.source-table tr.error-line {background:#FEE2E2; color:#7F1D1D;}
.source-table mark {background:#B91C1C; color:white; border-radius:3px; padding:1px 2px;}
.ir-grid {display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:20px; margin:24px 0 12px;}
.ir-panel {min-width:0;}
.ir-panel h4 {text-align:center; font-size:.98rem; font-weight:600; margin:0 0 13px; color:var(--ink);}
.ir-table-wrap {border:1px solid var(--line); border-radius:11px; background:#FFF; max-height:580px; overflow-y:auto;}
.ir-table {table-layout:fixed; border-collapse:collapse; width:100%; font-size:.76rem; color:var(--ink);}
.ir-table th {background:#EEF3F8; color:#53677D; font-size:.66rem; letter-spacing:.035em; font-weight:650; text-align:center; padding:12px 5px;}
.ir-table td {padding:11px 7px; border-top:1px solid #E9EEF4; vertical-align:top; white-space:normal; overflow-wrap:anywhere; text-align:center;}
.ir-table td.ir-args {font-family:Consolas,monospace; text-align:left; line-height:1.7;}
.ir-table .ir-op {font-family:Consolas,monospace; font-size:.72rem;}
.ir-table .ir-status {font-size:.65rem; border-radius:5px; padding:3px 4px; display:inline-block;}
.ir-table .removed {background:#FFF3E3; color:#875318;}
.ir-table tbody tr:nth-child(even) {background:#FBFCFE;}
.empty-ir {text-align:center; color:var(--muted); padding:24px; font-size:.85rem;}
.architecture-purpose {text-align:center; color:var(--ink); font-size:.95rem; margin:6px auto 21px; max-width:850px; line-height:1.8;}
.architecture-details {display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:24px; text-align:center; margin:0 12px 16px;}
.architecture-details p {font-size:.84rem; color:var(--muted); line-height:1.8; overflow-wrap:anywhere; margin:9px 0;}
.architecture-details code {color:#096875; background:transparent; font-size:.8rem;}
.stage-live {display:flex; justify-content:center; flex-wrap:wrap; gap:16px; align-items:center; border-top:1px solid #E8EEF4;
 padding:16px 0 2px; font-size:.8rem; color:var(--muted);}
.stage-live strong {color:var(--ink); font-weight:600;}
.pass-list {display:flex; flex-wrap:wrap; justify-content:center; gap:9px; margin:12px 0 20px;}
.pass-list span {font: .75rem Consolas,monospace; color:#096875; padding:6px 10px; background:#EDF6F6; border-radius:6px; overflow-wrap:anywhere;}
.st-key-grammar_reference [data-testid="stMarkdownContainer"] > p,.st-key-grammar_reference h2,.st-key-grammar_reference h3 {text-align:left;}
@media (max-width:1280px) {.ir-grid {grid-template-columns:minmax(0,1fr);} .ir-table {font-size:.8rem;}}
@media (max-width:850px) {
 .block-container {padding:1.3rem 1.2rem 2.5rem;} .hero {padding:29px 19px; border-radius:14px !important;}
 .architecture-details {grid-template-columns:minmax(0,1fr); gap:12px;} .stage {min-width:100px;}
 [data-baseweb="tab-list"] {justify-content:flex-start; gap:0;} [data-baseweb="tab"] {padding:10px 12px;}
}
</style>""", unsafe_allow_html=True)


@contextmanager
def safe_render(label):
    """Keep optional page/tab failures out of the main traceback view."""
    try:
        yield
    except Exception:
        st.warning(f"Could not display {label}. Please try again or choose another page.")
        with st.expander("Technical details"):
            st.code(traceback.format_exc(), language="text")


def header(title, description):
    st.markdown(f'<div class="hero"><div class="hero-brand"><img src="{LOGO_URL}" alt="">'
                '<div class="eyebrow">DATA SCIENCE PIPELINE DSL</div></div>'
                f'<h1>{escape(title)}</h1><p>{escape(description)}</p></div>', unsafe_allow_html=True)


def digest(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def source_view(source, error=None):
    lines = source.split("\n")
    # EOF errors may refer to a position one line beyond the supplied text.
    if error and error.line == len(lines) + 1:
        lines.append("")
    rows = []
    for number, line in enumerate(lines, 1):
        line = line.removesuffix("\r")
        highlight = error is not None and error.line == number
        content = escape(line)
        if highlight and error.kind == "Lexical" and error.col is not None:
            col = error.col  # The compiler reports zero-based columns.
            if 0 <= col < len(line):
                content = escape(line[:col]) + "<mark>" + escape(line[col]) + "</mark>" + escape(line[col + 1:])
        css = ' class="error-line"' if highlight else ""
        rows.append(f'<tr{css}><td class="line-no">{number}</td><td>{content or " "}</td></tr>')
    st.markdown('<div class="source-wrap"><table class="source-table" aria-label="Compiled source">'
                + "".join(rows) + '</table></div>', unsafe_allow_html=True)


def error_view(result):
    error = result.error
    location = f" - line {error.line}" if error.line is not None else ""
    if error.col is not None:
        location += f", col {error.col}"
    if error.kind == "Internal":
        st.error(f"Internal Error in {error.stage}. The compiler could not finish this source.")
        with st.expander("Compiler traceback"):
            st.code(result.traceback or error.message, language="text")
    else:
        st.error(f"{error.kind} Error{location}")
        st.code(error.message, language="text")
    if error.kind in {"Lexical", "Syntax", "Semantic"}:
        detector = {"Lexical": "The lexer detects invalid characters and strings",
                    "Syntax": "The parser detects grammar errors",
                    "Semantic": "The semantic analyzer detects dependency and state errors"}[error.kind]
        st.caption(f"{detector}; compilation stopped at {error.stage} after the first error.")
    source_view(result.source, error)


def show_table(rows):
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def ir_rows(instructions, labels=None):
    rows = []
    for i, instruction in enumerate(instructions, 1):
        args = {k: v for k, v in instruction.args.items() if k != "line"}
        row = {"index": i, "op": instruction.op, "args": repr(args), "line": instruction.args.get("line")}
        if labels is not None:
            row["status"] = labels[i - 1]
        rows.append(row)
    return rows


def ir_table_html(instructions, labels=None):
    """Presentation-only table: wrap real IR values instead of scrolling sideways."""
    if not instructions:
        return '<div class="ir-table-wrap"><div class="empty-ir">No IR instructions.</div></div>'
    headings = ("No.", "Operation", "Arguments", "Line") + (("Change",) if labels is not None else ())
    widths = ("7%", "21%", "48%", "9%", "15%") if labels is not None else ("7%", "23%", "60%", "10%")
    rows = []
    for row in ir_rows(instructions, labels):
        cells = (f'<td>{row["index"]}</td><td class="ir-op">{escape(row["op"])}</td>'
                 f'<td class="ir-args">{escape(row["args"])}</td>'
                 f'<td>{escape(str(row["line"])) if row["line"] is not None else "—"}</td>')
        if labels is not None:
            status = row["status"]
            css = "kept" if status == "kept" else "removed"
            cells += f'<td><span class="ir-status {css}">{escape(status.replace("/", " / "))}</span></td>'
        rows.append(f'<tr>{cells}</tr>')
    return ('<div class="ir-table-wrap"><table class="ir-table" aria-label="IR instructions">'
            '<colgroup>' + ''.join(f'<col style="width:{width}">' for width in widths) + '</colgroup>'
            '<thead><tr>' + ''.join(f'<th scope="col">{escape(h)}</th>' for h in headings) + '</tr></thead>'
            '<tbody>' + ''.join(rows) + '</tbody></table></div>')


def reached(result, stage):
    record = next(s for s in result.stages if s.name == stage)
    if record.status == "skipped":
        st.info(f"Not reached because compilation stopped at {result.failed_stage}")
        return False
    if record.status == "failed":
        st.info(f"{stage} failed; no completed output is available.")
        return False
    return True


def overview():
    header("A pipeline, from source to symbolic trace.",
           "Explore a compiler front-end for a Data Science pipeline language. Follow real source through lexical, "
           "syntactic and semantic analysis, then inspect its intermediate representation, four optimizer passes and symbolic execution.")
    st.markdown('<div class="language-label">Language: <strong>Data Science Pipeline DSL</strong> · .pipe</div>'
                '<div class="language-panel"><div class="declaration"><span class="section-label">Program declaration</span>'
                '<code>pipeline</code></div><div class="section-label">Pipeline operations</div><div class="chips">'
                + ''.join(f'<span class="chip">{escape(s)}</span>' for s in
                          ("load", "clean", "select", "drop", "split", "train", "evaluate"))
                + '</div></div>', unsafe_allow_html=True)
    examples = compiler_runner.list_examples(EXAMPLES_DIR)
    facts = [("Example programs", str(len(examples)), "Discovered in the example library")]
    evidence = ROOT / "docs" / "test_results.txt"
    try:
        match = re.search(r"(\d+) passed", evidence.read_text(encoding="utf-8"))
        if match:
            facts.append(("Passed tests", match[1], "Saved report · not a live test run"))
    except (OSError, UnicodeError):
        pass
    for column, (label, value, detail) in zip(st.columns(len(facts)), facts):
        with column:
            st.markdown(f'<div class="fact-card"><div class="section-label">{escape(label)}</div>'
                        f'<div class="fact-value">{escape(value)}</div><div class="fact-detail">{escape(detail)}</div></div>',
                        unsafe_allow_html=True)
    st.subheader("The compilation journey")
    st.markdown('<div class="flow">' + '<span class="flow-arrow" aria-hidden="true">→</span>'.join(
        f'<span class="flow-node">{escape(n)}</span>' for n in
        ("Source", "Lexer", "Parser / AST", "Semantic / symbols", "IR", "Optimizer", "Symbolic executor", "Trace"))
        + '</div>', unsafe_allow_html=True)
    grammar = ROOT / "docs" / "grammar.md"
    if grammar.is_file():
        with st.expander("Language grammar"):
            with st.container(key="grammar_reference"), safe_render("language grammar"):
                st.markdown(grammar.read_text(encoding="utf-8"))


def load_selected_example():
    """Widget callback writes editor state before the text_area is instantiated."""
    selected = st.session_state.get("example_choice")
    if selected:
        try:
            st.session_state["editor_text"] = compiler_runner.read_example(EXAMPLES_DIR / selected)
            st.session_state["example_notice"] = None
        except (OSError, UnicodeError):
            st.session_state["example_notice"] = f"Could not read {selected}. You can still edit and compile your source."


def compilation_tabs(result):
    names = ("Tokens", "AST", "Semantic Analysis", "IR", "Optimization", "Execution Trace")
    for tab, name, stage in zip(st.tabs(names), names, compiler_runner.STAGE_NAMES):
        with tab, safe_render(name):
            if name == "Semantic Analysis" and result.error and result.error.kind == "Semantic":
                st.error(f"Semantic Error - line {result.error.line}")
                st.code(result.error.message, language="text")
                continue
            if not reached(result, stage):
                continue
            if name == "Tokens":
                show_table([dict(index=i, **asdict(t)) for i, t in enumerate(result.tokens[:1000], 1)])
                if len(result.tokens) > 1000:
                    st.caption(f"showing first 1000 of {len(result.tokens)}")
                    st.caption(f"Final token (outside displayed range): {result.tokens[-1]!r}")
                st.caption("Token columns use the compiler's zero-based coordinates. EOF is included in the token stream.")
            elif name == "AST":
                st.write("Pipeline:", result.ast.name)
                rows = []
                for i, node in enumerate(result.ast.statements, 1):
                    fields = asdict(node) if is_dataclass(node) else dict(vars(node))
                    line = fields.pop("line", None)
                    rows.append({"index": i, "node type": type(node).__name__, "fields": repr(fields), "line": line})
                show_table(rows)
                with st.expander("Raw AST"):
                    st.json(asdict(result.ast) if is_dataclass(result.ast) else vars(result.ast))
                    st.code(repr(result.ast), language="text")
            elif name == "Semantic Analysis":
                st.success("No semantic errors")
                show_table([{"field": k, "value": repr(v)} for k, v in vars(result.symbol_table).items()])
            elif name == "IR":
                st.markdown(ir_table_html(result.ir), unsafe_allow_html=True)
            elif name == "Optimization":
                for col, label, value in zip(st.columns(4),
                        ("IR before", "IR after", "Instructions removed", "Reduction"),
                        (result.ir_before, result.ir_after, result.removed, f"{result.reduction_pct:.1f}%")):
                    col.metric(label, value)
                original = ir_table_html(result.ir, compiler_runner.match_ir(result.ir, result.optimized_ir))
                optimized = ir_table_html(result.optimized_ir)
                st.markdown('<div class="ir-grid"><section class="ir-panel"><h4>Original IR</h4>' + original
                            + '</section><section class="ir-panel"><h4>Optimized IR</h4>' + optimized
                            + '</section></div>', unsafe_allow_html=True)
                st.caption("Best-effort alignment from real op/args equality; merged drops appear as removed/merged.")
                st.markdown("**Optimizer notes**")
                if result.notes:
                    for note in result.notes:
                        st.text(f"• {note}")
                else:
                    st.info("no optimizations applied")
                counts = []
                if result.unoptimized_trace is not None:
                    counts.append(f"Unoptimized: {len(result.unoptimized_trace)} trace lines")
                if result.stages[-1].status == "ok":
                    counts.append(f"Optimized: {len(result.trace)} trace lines")
                if counts:
                    st.caption(" / ".join(counts))
                if result.comparison_error:
                    st.warning("The unoptimized trace comparison is unavailable.")
                    with st.expander("Comparison details"):
                        st.code(result.comparison_error, language="text")
            elif name == "Execution Trace":
                st.caption("Symbolic trace: nothing was read or trained.")
                st.code("\n".join(f"{i:>3}  {line}" for i, line in enumerate(result.trace, 1)) or "(empty trace)", language="text")


def playground():
    header("Compiler Playground", "Choose a program, edit the source and inspect every real compiler stage.")
    entries = compiler_runner.list_examples(EXAMPLES_DIR)
    if "editor_text" not in st.session_state:
        initial = next((e for e in entries if e.category == "Valid"), None)
        st.session_state["editor_text"] = SAMPLE
        if initial:
            st.session_state.setdefault("example_choice", initial.name)
            try:
                st.session_state["editor_text"] = compiler_runner.read_example(initial.path)
            except (OSError, UnicodeError):
                st.session_state["example_notice"] = "Could not read the initial example; a sample source is ready to edit."
    left, right = st.columns([1, 3], gap="large")
    with left:
        st.subheader("Source library")
        categories = ["All"] + sorted({e.category for e in entries})
        st.selectbox("Category", categories, key="example_category")
        category = st.session_state["example_category"]
        choices = [e.name for e in entries if category == "All" or e.category == category]
        if st.session_state.get("example_choice") not in choices:
            st.session_state["example_choice"] = choices[0] if choices else None
            load_selected_example()
        st.selectbox("Example program", choices, key="example_choice", on_change=load_selected_example,
                     disabled=not choices, placeholder="No examples available")
        if not entries:
            st.info("No .pipe examples found. Edit the sample source to get started.")
        if st.session_state["example_notice"]:
            st.warning(st.session_state["example_notice"])
        st.caption("Examples are compiled when you press Compile. Their outcomes come from the compiler.")
        st.caption(f"Source limit: {compiler_runner.MAX_SOURCE_CHARS:,} characters.")
    with right:
        st.text_area("Pipeline source", key="editor_text", height=380)
        _, action, _ = st.columns([1, 1, 1])
        with action:
            if st.button("Compile", key="compile_btn", type="primary", width="stretch"):
                source = st.session_state["editor_text"]
                st.session_state["result"] = compiler_runner.compile_source(source)
                st.session_state["compiled_hash"] = digest(source)
    result = st.session_state["result"]
    if result is None:
        st.info("Press Compile to inspect the compiler output.")
        return
    if digest(st.session_state["editor_text"]) != st.session_state["compiled_hash"]:
        st.caption("Source changed since last compile. Results below describe the last compiled source.")
    st.markdown('<div class="stage-strip">' + ''.join(
        f'<div class="stage"><strong>{escape(s.name)}</strong><span class="pill {escape(s.status)}">'
        f'{escape(s.status)}</span><span class="timing">{s.ms:.3f} ms</span></div>' for s in result.stages)
        + '</div>', unsafe_allow_html=True)
    facts = []
    if result.stages[0].status == "ok":
        facts.append(f"{len(result.tokens)} tokens (including EOF)")
    if result.ast is not None:
        facts.append(f"{len(result.ast.statements)} statements")
    if result.stages[4].status == "ok":
        facts.append(f"IR {result.ir_before} → {result.ir_after} / {result.reduction_pct:.1f}% reduction")
    elif result.stages[3].status == "ok":
        facts.append(f"{result.ir_before} IR instructions")
    if facts:
        st.markdown('<div class="compile-summary">' + escape(" · ".join(facts)) + '</div>', unsafe_allow_html=True)
    if result.error:
        error_view(result)
    else:
        st.success("Compiled successfully")
        with st.expander("Compiled source with line numbers"):
            source_view(result.source)
    compilation_tabs(result)


STAGE_INFO = (
    ("Lexer", "Recognizes tokens and records source coordinates.", "Source → list[Token]", "lexer.py / tokenize(source)",
     "LexicalError: unexpected character or unterminated string."),
    ("Parser", "Builds a statement AST with recursive-descent parsing.", "Tokens → PipelineNode", "parser.py / Parser(tokens).parse_pipeline()",
     "SyntaxError_: grammar mismatch, unexpected EOF or trailing input; one pipeline per file."),
    ("Semantic", "Checks dependencies and tracks pipeline state in a symbol table.", "AST → SymbolTable", "semantic.py / analyze(ast)",
     "SemanticError: duplicate or empty load; clean/select/drop before load or after training; duplicate, previously dropped or unavailable columns; "
     "dropping every selected column; split before load, invalid percentages, duplicate splits or total over 100%; missing train split, duplicate model or evaluation before training."),
    ("IR", "Lowers each statement into an instruction with source-line metadata.", "AST + SymbolTable → list[IRInstruction]", "ir.py / lower_to_ir(ast, table)",
     "No explicit compiler exception is raised by this module."),
    ("Optimizer", "Runs four ordered passes over real IR instructions.", "IR + notes list → optimized IR", "optimizer.py / optimize(ir, notes=None)",
     "No explicit compiler exception is raised by this module."),
    ("Executor", "Formats one symbolic trace entry for each instruction.", "Optimized IR → list[str]", "executor.py / execute(ir)",
     "No explicit compiler exception; unknown opcodes produce an Unknown instruction trace entry."),
)
PASSES = ("_remove_unreachable", "_remove_dead_trains", "_merge_adjacent_drops", "_collapse_duplicates")


def architecture():
    header("Inside the compiler", "Follow the front-end, the four optimizer passes and the symbolic executor.")
    result = st.session_state["result"]
    colors = {"ok": "#DCFCE7", "failed": "#FEE2E2", "skipped": "#E2E8F0"}
    statuses = {s.name: s for s in result.stages} if result else {}
    labels = {"Lexer": "Lexer", "Parser": "Parser / AST", "Semantic": "Semantic Analyzer\nSymbol Table",
              "IR": "IR Generator", "Optimizer": "Optimizer\n" + "\n".join(PASSES), "Executor": "Symbolic Executor"}
    dot = ['digraph compiler { rankdir=LR; bgcolor="transparent"; graph [pad="0.2"];',
           'node [shape=box style="rounded,filled" fontname="Arial" color="#94A3B8" fillcolor="#EDF2F7"];',
           'edge [color="#64748B"]; Source; Trace;']
    for stage, label in labels.items():
        fill = colors[statuses[stage].status] if result else "#EDF2F7"
        dot.append(f'{stage} [label={json.dumps(label)} fillcolor="{fill}"];')
    dot.append('Source -> Lexer -> Parser -> Semantic -> IR -> Optimizer -> Executor -> Trace;')
    for stage, label in (("Lexer", "Lexical Error"), ("Parser", "Syntax Error"), ("Semantic", "Semantic Error")):
        dot.append(f'{stage}Error [label={json.dumps(label)} color="#B91C1C" fillcolor="#FFF1F2"];')
        dot.append(f'{stage} -> {stage}Error [style=dashed color="#B91C1C"];')
    dot.append('}')
    st.graphviz_chart("\n".join(dot), width="stretch")
    st.caption("Stage colors reflect the last compile: green = ok, red = failed, grey = skipped." if result
               else "Compile a program in the Playground to see live stage colors.")
    for name, purpose, flow, module, errors in STAGE_INFO:
        with st.expander(name, expanded=name == "Semantic"):
            st.markdown(f'<p class="architecture-purpose">{escape(purpose)}</p>'
                        '<div class="architecture-details"><div><div class="section-label">Input → output</div>'
                        f'<p><code>{escape(flow)}</code></p><div class="section-label">Implementation</div>'
                        f'<p><code>{escape(module)}</code></p></div><div><div class="section-label">Validation &amp; diagnostics</div>'
                        f'<p>{escape(errors)}</p></div></div>', unsafe_allow_html=True)
            if name == "Optimizer":
                st.markdown('<div class="pass-list">' + ''.join(
                    f'<span>{i}. {escape(p)}</span>' for i, p in enumerate(PASSES, 1)) + '</div>', unsafe_allow_html=True)
            if name in statuses:
                stage = statuses[name]
                count = ""
                if stage.count is not None:
                    unit = {"Lexer": "tokens", "Parser": "statements", "Semantic": "symbol-table fields",
                            "IR": "IR instructions", "Optimizer": "optimized IR instructions", "Executor": "trace lines"}[name]
                    count = f'<span><strong>{stage.count}</strong> {escape(unit)}</span>'
                st.markdown('<div class="stage-live"><span class="section-label">Last compile</span>'
                            f'<span class="pill {escape(stage.status)}">{escape(stage.status)}</span>'
                            f'<span>{stage.ms:.3f} ms</span>{count}</div>', unsafe_allow_html=True)


def performance():
    data = performance_loader.load_performance(PERFORMANCE_PATH)
    if not data.available:
        st.warning(f"Performance report unavailable: {PERFORMANCE_PATH}\n\n{data.reason}\n\n"
                   "Generate it from the repository root with: python benchmarks/benchmark.py")
        return
    header("Recorded compiler performance", "Inspect the benchmark report saved with this project.")
    st.caption("Results read from docs/performance.md; generated by benchmarks/benchmark.py")
    if data.environment:
        st.subheader("Environment")
        st.text(data.environment)
    table = data.table
    st.subheader("Benchmark results")
    if data.marked_rows:
        st.warning("Marked rows report skipped runs or reduced repetitions; consult Status before comparing results.")
        st.dataframe(table.style.apply(lambda row: ["background-color: #FFF0C2" if row.name in data.marked_rows else ""] * len(row), axis=1),
                     hide_index=True, width="stretch")
    else:
        st.dataframe(table, hide_index=True, width="stretch")
    def chart(title, columns, stack=False):
        columns = [c for c in columns if c in table.columns]
        if "Statements" not in table or not columns:
            return
        numeric = table.loc[:, ["Statements"] + columns].dropna(subset=["Statements"])
        numeric = numeric.dropna(subset=columns, how="all")
        if numeric.empty:
            return
        numeric["Statements"] = numeric["Statements"].map(lambda n: f"{n:g}")
        numeric = numeric.set_index("Statements")
        st.subheader(title)
        st.bar_chart(numeric, stack=stack, sort=False, width="stretch")
    chart("Stage time by program size (ms)", ["Lexer ms", "Parser ms", "Semantic ms", "IR ms", "Optimizer ms", "Exec(opt) ms"], True)
    chart("Time per statement (µs)", ["us/stmt"])
    chart("IR size before and after optimization", ["IR before", "IR after"])
    if data.observations:
        st.subheader("Observations")
        st.text(data.observations)


with st.sidebar:
    st.markdown(f'<div class="sidebar-brand"><div class="brand-mark"><img src="{LOGO_URL}" alt="Data Science Pipeline DSL logo"></div>'
                '<div class="brand-name">Data Science<br>Pipeline DSL</div>'
                '<div class="brand-description">Source. Validate. Optimize.</div></div>', unsafe_allow_html=True)
    st.radio("Navigation", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    st.markdown('<div class="sidebar-language"><div class="section-label">Language reference</div>'
                '<div class="sidebar-root"><code>pipeline</code><span class="section-label">Program declaration</span></div>'
                '<div class="sidebar-operations">' + ''.join(f'<span class="chip">{escape(s)}</span>' for s in
                ("load", "clean", "select", "drop", "split", "train", "evaluate")) + '</div></div>', unsafe_allow_html=True)
    st.divider()
    st.caption("Symbolic execution only: no files are read, no models are trained.")

with safe_render(st.session_state["page"]):
    {"Overview": overview, "Compiler Playground": playground,
     "Architecture": architecture, "Performance": performance}[st.session_state["page"]]()
