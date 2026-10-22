import sys
import time
import statistics
import gc
import platform
from pathlib import Path
from datetime import datetime

# ==============================================================================
# ENVIRONMENT & PATH CONFIGURATION
# ==============================================================================
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze
from ds_pipeline_dsl.ir import lower_to_ir
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute

# ==============================================================================
# SAFEGUARD CONSTANTS
# ==============================================================================
# SIZES: input scale parameters tested in strictly ascending order.
SIZES = [10, 100, 1000, 10000]

# REPEATS: number of repetitions per benchmark size for median calculation.
REPEATS = 3

# MAX_SIZE: upper ceiling on size parameter; builds above this are rejected.
MAX_SIZE = 20000

# MAX_SOURCE_CHARS: maximum allowed source string character length.
MAX_SOURCE_CHARS = 2_000_000

# TOTAL_TIME_BUDGET_S: budget used by the projection check between sizes.
TOTAL_TIME_BUDGET_S = 120

# REPEAT_TIME_LIMIT_S: post-run threshold triggering reduced repetitions.
REPEAT_TIME_LIMIT_S = 30

# Static assertions on benchmark configuration
assert max(SIZES) <= MAX_SIZE, f"max(SIZES) ({max(SIZES)}) exceeds MAX_SIZE ({MAX_SIZE})"
assert SIZES == sorted(SIZES), "SIZES list must be in strictly ascending order"


def check_size_limit(n: int) -> None:
    """Validate that the requested size parameter does not exceed MAX_SIZE."""
    if n > MAX_SIZE:
        raise ValueError(f"Size {n} exceeds MAX_SIZE ({MAX_SIZE})")


def expected_counts(n: int) -> dict:
    """Compute deterministic structural counts from the sizing parameter n."""
    D = max(2, n // 10)
    U = max(1, (n - 8 - D) // 3)
    statements = 8 + D + 3 * U
    opt_size = 6 + 2 * U
    return {"D": D, "U": U, "statements": statements, "optimized_ir_size": opt_size}


def build_program(n: int) -> str:
    """Construct a valid synthetic DSL pipeline program parameterized by n.

    Redundancies engineered into the template:
      - 2 consecutive clean missing_values statements (collapsed to 1)
      - D consecutive adjacent drop junk_i statements (merged into 1)
      - 2 consecutive select statements (collapsed to 1)
      - U dead-model trains (trained but never evaluated; removed)
      - 1 trailing train statement after the last evaluate (removed as unreachable)
    """
    check_size_limit(n)
    counts = expected_counts(n)
    D = counts["D"]
    U = counts["U"]

    lines = [
        "pipeline bench {",
        '    load "data.csv";',
        "    clean missing_values;",
        "    clean missing_values;",
    ]
    for i in range(D):
        lines.append(f"    drop junk_{i};")
    lines.extend([
        "    select f0, f1, f2, f3;",
        "    select f0, f1, f2, f3;",
        "    split train = 70%;",
        "    split test = 30%;",
    ])
    for i in range(U):
        lines.append(f"    train model_{i} = decision_tree;")
        lines.append(f"    train unused_{i} = random_forest;")
        lines.append(f"    evaluate model_{i};")
    lines.append("    train trailing = knn;")
    lines.append("}")
    return "\n".join(lines)


def projected_seconds(last_run_s: float, last_n: int, next_n: int) -> float:
    """Project next size execution time assuming conservative quadratic growth."""
    return last_run_s * ((next_n / last_n) ** 2)


def should_run(projected_s: float, repeats: int, elapsed_s: float, budget_s: float) -> bool:
    """Check whether projected benchmark execution fits within remaining time budget."""
    return (projected_s * repeats) <= (budget_s - elapsed_s)


def run_correctness_guard(source: str, n: int) -> tuple[int, int, int]:
    """Execute end-to-end correctness verification on the generated program.

    Exits non-zero with diagnostic output if any invariant is violated.
    """
    counts = expected_counts(n)
    exp_stmts = counts["statements"]
    exp_opt_size = counts["optimized_ir_size"]
    exp_evals = counts["U"]

    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    ir = lower_to_ir(ast, table)

    actual_stmts = len(ast.statements)
    if actual_stmts != exp_stmts:
        sys.exit(f"Correctness guard failed for n={n}: statements={actual_stmts} != expected {exp_stmts}")
    if len(ir) != actual_stmts:
        sys.exit(f"Correctness guard failed for n={n}: unoptimized IR size={len(ir)} != statements {actual_stmts}")

    notes = []
    opt_ir = optimize(ir, notes)
    if len(opt_ir) != exp_opt_size:
        sys.exit(f"Correctness guard failed for n={n}: optimized IR size={len(opt_ir)} != expected {exp_opt_size}")

    trace_unopt = execute(ir)
    trace_opt = execute(opt_ir)

    evals_unopt = [line for line in trace_unopt if line.startswith("Evaluated model")]
    evals_opt = [line for line in trace_opt if line.startswith("Evaluated model")]

    if len(evals_unopt) != exp_evals:
        sys.exit(f"Correctness guard failed for n={n}: unoptimized evals={len(evals_unopt)} != expected {exp_evals}")
    if len(evals_opt) != exp_evals:
        sys.exit(f"Correctness guard failed for n={n}: optimized evals={len(evals_opt)} != expected {exp_evals}")
    if evals_opt != evals_unopt:
        sys.exit(f"Correctness guard failed for n={n}: optimized evals do not match unoptimized evals in order")

    return actual_stmts, len(tokens), len(opt_ir)


def run_benchmark() -> tuple[list, float]:
    """Execute benchmark across all sizes and collect timing telemetry."""
    t_start_all = time.perf_counter()
    last_total_s = None
    last_n = None
    skip_rest = False
    results = []

    for n in SIZES:
        counts = expected_counts(n)
        stmts_est = counts["statements"]

        if skip_rest:
            results.append({
                "statements": stmts_est, "tokens": "-", "lexer_ms": 0.0, "parser_ms": 0.0,
                "semantic_ms": 0.0, "ir_ms": 0.0, "opt_ms": 0.0, "exec_opt_ms": 0.0,
                "exec_unopt_ms": 0.0, "total_ms": 0.0, "us_per_stmt": 0.0,
                "ir_before": stmts_est, "ir_after": counts["optimized_ir_size"],
                "reduction_pct": 0.0, "status": "skipped",
            })
            continue

        elapsed_now = time.perf_counter() - t_start_all
        if last_total_s is not None:
            proj_s = projected_seconds(last_total_s, last_n, n)
            if not should_run(proj_s, REPEATS, elapsed_now, TOTAL_TIME_BUDGET_S):
                skip_rest = True
                results.append({
                    "statements": stmts_est, "tokens": "-", "lexer_ms": 0.0, "parser_ms": 0.0,
                    "semantic_ms": 0.0, "ir_ms": 0.0, "opt_ms": 0.0, "exec_opt_ms": 0.0,
                    "exec_unopt_ms": 0.0, "total_ms": 0.0, "us_per_stmt": 0.0,
                    "ir_before": stmts_est, "ir_after": counts["optimized_ir_size"],
                    "reduction_pct": 0.0, "status": f"skipped (projected {proj_s:.1f} s exceeds budget)",
                })
                continue

        source = build_program(n)
        assert len(source) <= MAX_SOURCE_CHARS, f"Source size {len(source)} exceeds MAX_SOURCE_CHARS"

        # Pre-timing correctness validation
        actual_stmts, tok_count, opt_size = run_correctness_guard(source, n)

        # Untimed warm-up pass
        w_tokens = tokenize(source)
        w_ast = Parser(w_tokens).parse_pipeline()
        w_table = analyze(w_ast)
        w_ir = lower_to_ir(w_ast, w_table)
        w_notes = []
        w_opt = optimize(w_ir, w_notes)
        execute(w_opt)
        execute(w_ir)
        del w_tokens, w_ast, w_table, w_ir, w_notes, w_opt
        gc.collect()

        loops = max(1, min(200, 2000 // actual_stmts))

        rep_lexer = []
        rep_parser = []
        rep_semantic = []
        rep_ir = []
        rep_opt = []
        rep_exec_opt = []
        rep_exec_unopt = []

        status = "ok"

        for rep in range(REPEATS):
            gc.collect()
            t_rep_start = time.perf_counter()

            # 1. Lexer
            gc.disable()
            try:
                t0 = time.perf_counter()
                for _ in range(loops):
                    tokens = tokenize(source)
                t_lex = (time.perf_counter() - t0) / loops
            finally:
                gc.enable()

            # 2. Parser
            gc.disable()
            try:
                t0 = time.perf_counter()
                for _ in range(loops):
                    ast = Parser(tokens).parse_pipeline()
                t_parse = (time.perf_counter() - t0) / loops
            finally:
                gc.enable()

            # 3. Semantic Analysis
            gc.disable()
            try:
                t0 = time.perf_counter()
                for _ in range(loops):
                    table = analyze(ast)
                t_sem = (time.perf_counter() - t0) / loops
            finally:
                gc.enable()

            # 4. IR Lowering
            gc.disable()
            try:
                t0 = time.perf_counter()
                for _ in range(loops):
                    ir = lower_to_ir(ast, table)
                t_ir_val = (time.perf_counter() - t0) / loops
            finally:
                gc.enable()

            # 5. Optimizer
            gc.disable()
            try:
                t0 = time.perf_counter()
                for _ in range(loops):
                    notes = []
                    opt_ir = optimize(ir, notes)
                t_opt_val = (time.perf_counter() - t0) / loops
            finally:
                gc.enable()

            # 6. Executor on optimized IR
            gc.disable()
            try:
                t0 = time.perf_counter()
                for _ in range(loops):
                    trace_opt = execute(opt_ir)
                t_ex_opt = (time.perf_counter() - t0) / loops
            finally:
                gc.enable()

            # 7. Executor on unoptimized IR
            gc.disable()
            try:
                t0 = time.perf_counter()
                for _ in range(loops):
                    trace_unopt = execute(ir)
                t_ex_unopt = (time.perf_counter() - t0) / loops
            finally:
                gc.enable()

            rep_duration = time.perf_counter() - t_rep_start

            rep_lexer.append(t_lex)
            rep_parser.append(t_parse)
            rep_semantic.append(t_sem)
            rep_ir.append(t_ir_val)
            rep_opt.append(t_opt_val)
            rep_exec_opt.append(t_ex_opt)
            rep_exec_unopt.append(t_ex_unopt)

            del tokens, ast, table, ir, opt_ir, trace_opt, trace_unopt
            gc.collect()

            if rep == 0 and rep_duration > REPEAT_TIME_LIMIT_S:
                status = "reduced repetitions"
                break

        del source
        gc.collect()

        lex_ms = statistics.median(rep_lexer) * 1000.0
        parse_ms = statistics.median(rep_parser) * 1000.0
        sem_ms = statistics.median(rep_semantic) * 1000.0
        ir_ms = statistics.median(rep_ir) * 1000.0
        opt_ms = statistics.median(rep_opt) * 1000.0
        ex_opt_ms = statistics.median(rep_exec_opt) * 1000.0
        ex_unopt_ms = statistics.median(rep_exec_unopt) * 1000.0

        total_ms = lex_ms + parse_ms + sem_ms + ir_ms + opt_ms + ex_opt_ms
        us_per_stmt = (total_ms * 1000.0) / actual_stmts
        red_pct = ((actual_stmts - opt_size) / actual_stmts) * 100.0

        last_total_s = total_ms / 1000.0
        last_n = n

        results.append({
            "statements": actual_stmts,
            "tokens": tok_count,
            "lexer_ms": lex_ms,
            "parser_ms": parse_ms,
            "semantic_ms": sem_ms,
            "ir_ms": ir_ms,
            "opt_ms": opt_ms,
            "exec_opt_ms": ex_opt_ms,
            "exec_unopt_ms": ex_unopt_ms,
            "total_ms": total_ms,
            "us_per_stmt": us_per_stmt,
            "ir_before": actual_stmts,
            "ir_after": opt_size,
            "reduction_pct": red_pct,
            "status": status,
        })

    wall_clock_s = time.perf_counter() - t_start_all
    return results, wall_clock_s


def generate_report(results: list, wall_clock_s: float) -> str:
    """Generate Markdown report from benchmark telemetry."""
    py_ver = platform.python_version()
    plat = platform.platform()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Compiler Performance Benchmark Report",
        "",
        "## Environment",
        f"- Python version: {py_ver}",
        f"- Platform: {platform.system()} ({plat})",
        f"- Benchmark run timestamp: {date_str}",
        f"- Total wall-clock duration: {wall_clock_s:.2f} s",
        "",
        "## Benchmark Template & Optimization Effects",
        "The benchmark evaluates scalable synthetic data science pipelines generated by `build_program(n)`.",
        "The template systematically exercises all compiler front-end stages and optimizer transformations:",
        "- Consecutive `clean` statements: adjacent duplicates collapsed into one.",
        "- Multiple `drop` statements: consecutive adjacent drop statements merged into a single drop with deduplicated columns.",
        "- Consecutive `select` statements: adjacent duplicates collapsed into one.",
        "- Multi-unit model definitions: each unit defines a model that is evaluated and an unused model that is never evaluated;",
        "  the dead-train elimination pass removes all unused models.",
        "- Trailing model train: placed after the final evaluate statement; removed by the unreachable-code elimination pass.",
        "",
        "## Safeguards & Methodology",
        "Sizes run in ascending order with quadratic projection checks against a total time budget",
        f"of {TOTAL_TIME_BUDGET_S} s; repetitions exceeding {REPEAT_TIME_LIMIT_S} s trigger fewer repeats after they finish.",
        "These are projection and post-run checks, not preemptive timeouts; a running stage is not interrupted.",
        f"source sizes are bounded at {MAX_SOURCE_CHARS} characters and size parameter at {MAX_SIZE}; each size performs an untimed",
        f"warm-up pass and correctness validation before timing; garbage collection is disabled during timed regions and run between repetitions;",
        "inner timing loops scale inversely with statement count to minimize timer quantization noise.",
        "",
        "## Results Table",
        "| Statements | Tokens | Lexer ms | Parser ms | Semantic ms | IR ms | Optimizer ms | Exec(opt) ms | Exec(unopt) ms | Total ms | us/stmt | IR before | IR after | Reduction % | Status |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]

    for r in results:
        stmts = r["statements"]
        toks = str(r["tokens"])
        lex = f"{r['lexer_ms']:.3f}" if r["lexer_ms"] > 0 else "-"
        parse = f"{r['parser_ms']:.3f}" if r["parser_ms"] > 0 else "-"
        sem = f"{r['semantic_ms']:.3f}" if r["semantic_ms"] > 0 else "-"
        ir = f"{r['ir_ms']:.3f}" if r["ir_ms"] > 0 else "-"
        opt = f"{r['opt_ms']:.3f}" if r["opt_ms"] > 0 else "-"
        ex_opt = f"{r['exec_opt_ms']:.3f}" if r["exec_opt_ms"] > 0 else "-"
        ex_unopt = f"{r['exec_unopt_ms']:.3f}" if r["exec_unopt_ms"] > 0 else "-"
        tot = f"{r['total_ms']:.3f}" if r["total_ms"] > 0 else "-"
        us_stmt = f"{r['us_per_stmt']:.2f}" if r["us_per_stmt"] > 0 else "-"
        ir_b = r["ir_before"]
        ir_a = r["ir_after"]
        red = f"{r['reduction_pct']:.1f}%" if r["reduction_pct"] > 0 else "-"
        stat = r["status"]
        row = f"| {stmts} | {toks} | {lex} | {parse} | {sem} | {ir} | {opt} | {ex_opt} | {ex_unopt} | {tot} | {us_stmt} | {ir_b} | {ir_a} | {red} | {stat} |"
        lines.append(row)

    lines.append("")
    lines.append("## Observations")

    completed = [r for r in results if r["status"] in ("ok", "reduced repetitions")]
    if len(completed) >= 2:
        s_prev = completed[-2]
        s_last = completed[-1]
        stmt_growth = s_last["statements"] / s_prev["statements"]
        time_growth = s_last["total_ms"] / s_prev["total_ms"] if s_prev["total_ms"] > 0 else 1.0
        us_ratio = s_last["us_per_stmt"] / s_prev["us_per_stmt"] if s_prev["us_per_stmt"] > 0 else 1.0
        linearity = "approximately linear" if us_ratio <= 2.0 else "super-linear: investigate"

        lines.append(f"1. Scaling between {s_prev['statements']} and {s_last['statements']} statements: statement count grew by {stmt_growth:.2f}x while total execution time grew by {time_growth:.2f}x.")
        lines.append(f"2. Microseconds per statement ratio between {s_prev['statements']} and {s_last['statements']} statements is {us_ratio:.2f} ({linearity}).")

        stages = {
            "Lexer": s_last["lexer_ms"],
            "Parser": s_last["parser_ms"],
            "Semantic": s_last["semantic_ms"],
            "IR": s_last["ir_ms"],
            "Optimizer": s_last["opt_ms"],
            "Executor (opt)": s_last["exec_opt_ms"],
        }
        dominant_name, dominant_time = max(stages.items(), key=lambda kv: kv[1])
        dominant_pct = (dominant_time / s_last["total_ms"] * 100.0) if s_last["total_ms"] > 0 else 0.0
        lines.append(f"3. Dominant stage at {s_last['statements']} statements: {dominant_name} ({dominant_time:.3f} ms, {dominant_pct:.1f}% of total pipeline time).")

        speedup = (s_last["exec_unopt_ms"] / s_last["exec_opt_ms"]) if s_last["exec_opt_ms"] > 0 else 1.0
        lines.append(f"4. Execution speedup from optimization at {s_last['statements']} statements: {speedup:.2f}x (unoptimized {s_last['exec_unopt_ms']:.3f} ms vs optimized {s_last['exec_opt_ms']:.3f} ms).")

    skipped_sizes = [r for r in results if "skipped" in r["status"]]
    reduced_sizes = [r for r in results if r["status"] == "reduced repetitions"]
    if skipped_sizes or reduced_sizes:
        for r in skipped_sizes:
            lines.append(f"5. Skipped size {r['statements']} statements: {r['status']}.")
        for r in reduced_sizes:
            lines.append(f"5. Reduced repetitions at {r['statements']} statements: single repetition exceeded {REPEAT_TIME_LIMIT_S} s.")
    else:
        lines.append("5. Status: all configured benchmark sizes completed successfully with full repetitions.")

    return "\n".join(lines)


def main():
    results, wall_clock_s = run_benchmark()
    report = generate_report(results, wall_clock_s)

    # Print table / report to stdout
    print(report)

    # Write report to docs/performance.md
    docs_dir = REPO_ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    perf_path = docs_dir / "performance.md"
    perf_path.write_text(report, encoding="utf-8")
    print(f"\nBenchmark report successfully written to {perf_path}")
    print(f"Total benchmark wall-clock runtime: {wall_clock_s:.2f} s")


if __name__ == "__main__":
    main()
