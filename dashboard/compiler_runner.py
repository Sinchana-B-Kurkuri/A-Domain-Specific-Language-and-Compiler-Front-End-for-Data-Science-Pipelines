"""Pure adapter over the existing compiler; no compiler behavior is replaced."""

from contextlib import redirect_stdout
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
import re
from time import perf_counter
import traceback
from typing import Literal

from ds_pipeline_dsl.lexer import LexicalError, Token, tokenize
from ds_pipeline_dsl.parser import Parser, SyntaxError_
from ds_pipeline_dsl.semantic import SemanticError, SymbolTable, analyze
from ds_pipeline_dsl.ast_nodes import PipelineNode
from ds_pipeline_dsl.ir import IRInstruction, lower_to_ir
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute

MAX_SOURCE_CHARS = 100_000
STAGE_NAMES = ("Lexer", "Parser", "Semantic", "IR", "Optimizer", "Executor")


@dataclass
class StageResult:
    name: str
    status: Literal["ok", "failed", "skipped"] = "skipped"
    ms: float = 0.0
    count: int | None = None


@dataclass
class CompilerError:
    kind: Literal["Lexical", "Syntax", "Semantic", "Internal", "Input"]
    message: str
    line: int | None
    col: int | None
    stage: str


@dataclass
class CompileResult:
    source: str
    stages: list[StageResult] = field(default_factory=lambda: [StageResult(n) for n in STAGE_NAMES])
    tokens: list[Token] = field(default_factory=list)
    ast: PipelineNode | None = None
    symbol_table: SymbolTable | None = None
    ir: list[IRInstruction] = field(default_factory=list)
    optimized_ir: list[IRInstruction] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    unoptimized_trace: list[str] | None = None
    comparison_error: str | None = None
    error: CompilerError | None = None
    failed_stage: str | None = None
    traceback: str | None = None

    @property
    def ir_before(self) -> int:
        return len(self.ir)

    @property
    def ir_after(self) -> int:
        return len(self.optimized_ir)

    @property
    def removed(self) -> int:
        return self.ir_before - self.ir_after

    @property
    def reduction_pct(self) -> float:
        return 100.0 * self.removed / self.ir_before if self.ir_before else 0.0


def compile_source(source: str) -> CompileResult:
    """Run each real stage, retaining completed stages after the first failure.

    Compiler columns are zero-based. Timing covers each primary stage only;
    the optional unoptimized execution is a separate comparison.
    """
    result = CompileResult(source)
    if len(source) > MAX_SOURCE_CHARS:
        result.failed_stage = "Input"
        result.error = CompilerError(
            "Input", f"Source is too large. Please use at most {MAX_SOURCE_CHARS:,} characters.",
            None, None, "Input",
        )
        return result

    actions = (
        ("tokens", lambda: tokenize(source), len),
        ("ast", lambda: Parser(result.tokens).parse_pipeline(), lambda a: len(a.statements)),
        ("symbol_table", lambda: analyze(result.ast), lambda t: len(vars(t))),
        ("ir", lambda: lower_to_ir(result.ast, result.symbol_table), len),
        ("optimized_ir", lambda: optimize(result.ir, result.notes), len),
        ("trace", lambda: execute(result.optimized_ir), len),
    )
    with redirect_stdout(StringIO()):
        for record, (attribute, action, counter) in zip(result.stages, actions):
            start = perf_counter()
            try:
                value = action()
                setattr(result, attribute, value)
                record.count = counter(value)
                record.status = "ok"
            except Exception as exc:
                record.status = "failed"
                result.failed_stage = record.name
                kind = next((k for cls, k in (
                    (LexicalError, "Lexical"), (SyntaxError_, "Syntax"),
                    (SemanticError, "Semantic"),
                ) if isinstance(exc, cls)), "Internal")
                message = str(exc)
                location = re.search(r"at line (\d+)(?:, col (\d+))?", message)
                result.error = CompilerError(
                    kind, message, int(location[1]) if location else None,
                    int(location[2]) if location and location[2] else None, record.name,
                )
                if kind == "Internal":
                    result.traceback = traceback.format_exc()
                break
            finally:
                record.ms = (perf_counter() - start) * 1000

        # A failed comparison must never replace the primary compilation result.
        if result.stages[3].status == "ok":
            try:
                result.unoptimized_trace = execute(result.ir)
            except Exception:
                result.comparison_error = traceback.format_exc()
    return result


def match_ir(before: list[IRInstruction], after: list[IRInstruction]) -> list[str]:
    """Best-effort two-pointer alignment derived from real (op, args) equality.

    A merged run is consumed at once and its original drops are all labelled
    removed/merged. These labels are a display aid, not optimizer provenance.
    """
    labels = ["removed/merged"] * len(before)
    i = j = 0
    while i < len(before) and j < len(after):
        original, optimized = before[i], after[j]
        if (original.op, original.args) == (optimized.op, optimized.args):
            labels[i] = "kept"
            i += 1
            j += 1
        elif original.op == optimized.op == "OP_DROP":
            end, columns = i, []
            while end < len(before) and before[end].op == "OP_DROP":
                for col in before[end].args.get("columns", []):
                    if col not in columns:
                        columns.append(col)
                end += 1
            merged = dict(original.args, columns=columns)
            if end > i + 1 and merged == optimized.args:
                i, j = end, j + 1
            else:
                i += 1
        else:
            i += 1
    return labels


@dataclass(frozen=True)
class ExampleEntry:
    path: Path
    name: str
    category: str


def list_examples(examples_dir: str | Path) -> list[ExampleEntry]:
    """Discover the repository's valid_, invalid_, complex_, optimizer_ prefixes."""
    try:
        entries = []
        for path in Path(examples_dir).glob("*.pipe"):
            if path.is_file():
                prefix = path.stem.partition("_")[0]
                category = prefix.title() if prefix in {"valid", "invalid", "complex", "optimizer"} else "Other"
                entries.append(ExampleEntry(path, path.name, category))
        return sorted(entries, key=lambda e: (e.category, e.name))
    except OSError:
        return []


def read_example(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")
