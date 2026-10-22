# A Domain-Specific Language and Compiler Front-End for Data Science Pipelines

A robust, modular compiler front-end and symbolic execution engine for a data-science-pipeline domain-specific language (`ds_pipeline_dsl`). The system validates, lowers, optimizes, and simulates data science workflow declarations with complete lexical, syntactic, semantic, and intermediate representation (IR) guarantees.

---

## 1. Overview & Key Features

`ds_pipeline_dsl` is designed for declaring end-to-end data science pipelines (loading, cleaning, column selection, column dropping, partitioning, model training, and evaluation). It replaces unstructured configuration scripts with a statically validated language.

- **Modular Compiler Architecture**: Decoupled multi-pass pipeline: Lexer $\to$ Recursive-Descent Parser $\to$ AST $\to$ Semantic Analyzer (SymbolTable) $\to$ IR Lowering $\to$ Four-Pass Optimizer $\to$ Symbolic Execution Engine.
- **Strict Dependency & Semantic Validation**: Enforces dataset availability, partition constraints ($0 < p < 100$, cumulative $\le 100\%$), strict data-preparation ordering before training, column set disjointness, duplicate detection, and model life-cycle checks.
- **Safe Linear-Time ($O(n)$) Optimization**: Four independent passes eliminate unreachable instructions, dead model training, duplicate consecutive cleans/selects, and merge contiguous drop statements.
- **Symbolic Simulation Engine**: Fast, deterministic execution trace generation without invoking heavy machine learning libraries or reading external CSV data.
- **Complete Test & Benchmark Suite**: 223 automated unit and integration tests passing in under 0.3s; reproducible performance benchmark demonstrating linear scaling across 10,000 statements in 0.67s.

---

## 2. Project Layout

```text
.
├── src/ds_pipeline_dsl/      # Core compiler package
│   ├── __init__.py           # Package exports and version metadata
│   ├── ast_nodes.py          # Typed AST dataclasses for pipeline nodes and statements
│   ├── cli.py                # Command-line driver and output formatter
│   ├── executor.py           # Symbolic execution engine generating trace logs
│   ├── ir.py                 # Intermediate representation dataclass and AST lowering
│   ├── lexer.py              # Regex-based scanner with line and column coordinate tracking
│   ├── optimizer.py          # Four-pass linear-time dead code & redundancy optimizer
│   ├── parser.py             # LL(1) recursive-descent parser producing validated AST
│   └── semantic.py           # Symbol table state tracking and semantic validation rules
├── tests/                    # Comprehensive pytest test suite (223 tests)
│   ├── helpers.py            # Test helpers: compile_to_ir, evaluation_records, assert_order_preserving
│   ├── test_benchmark.py     # Benchmark structural integrity, counts, and safeguard tests
│   ├── test_boundary.py      # Edge cases: 200 cols, 1k stmts, single-line, 5k ident, boundaries
│   ├── test_cli.py           # CLI invocation, argument flags, exit codes, trace formatting
│   ├── test_examples.py      # Parametrized validation table covering every .pipe file in examples/
│   ├── test_executor.py      # Symbolic execution traces and opcode format validation
│   ├── test_integration.py   # Multi-stage integration tests, clean error exits without tracebacks
│   ├── test_ir.py            # AST-to-IR lowering and opcode mapping tests
│   ├── test_lexer.py         # Token scanning, CRLF, non-ASCII handling, error diagnostics
│   ├── test_optimizer.py     # Equivalence, idempotence, positive, negative, and sensitivity tests
│   ├── test_parser.py        # Grammar constraints, missing delimiters, syntax error checks
│   └── test_semantic.py      # Comprehensive semantic rules pass/fail unit tests
├── examples/                 # Canonical DSL programs (.pipe files)
│   ├── valid_basic.pipe      # Baseline canonical 6-statement pipeline
│   ├── valid_drop.pipe       # Pipeline showcasing column drop before selection
│   ├── ...                   # 20 curated valid, invalid, and complex pipeline examples
├── benchmarks/               # Performance measurement
│   └── benchmark.py          # Automated benchmark with safeguards, quadratic projection, and report generator
├── docs/                     # Technical documentation & captured evidence
│   ├── architecture.md       # Architectural flowchart, ASCII diagram, and IR specification
│   ├── grammar.md            # Formal EBNF grammar and lexical specification
│   ├── performance.md        # Benchmark measurements, scaling factors, and observations
│   ├── test_results.txt      # Full pytest execution log (223 passed)
│   ├── demo.md               # 5-minute presentation script and viva quick reference
│   ├── demo_outputs/         # Captured stdout/stderr logs for all demo commands
│   ├── screenshots/          # Suggested screenshots guide for submission
│   └── report_and_presentation_checklist.md # Mapping to university manual chapters & criteria
├── pyproject.toml            # Project packaging specification
└── README.md                 # Project documentation and user manual
```

---

## 3. Installation & Usage

### 3.1 Requirements & Installation
- **Python**: Version 3.12 or newer.
- **Dependencies**: Python standard library only (no external dependencies required). `pytest` is used for running tests.

Install the package in editable mode from the repository root:
```bash
pip install -e .
```

### 3.2 Running the Compiler via CLI
The compiler driver is accessible via the module CLI:
```bash
python -m ds_pipeline_dsl.cli <path_to_pipe_file> [flags]
```

#### Available Flags
- `--tokens`: Display the scanned token stream with line and column numbers.
- `--ast`: Display the parsed Abstract Syntax Tree representation.
- `--ir`: Display the unoptimized linear Intermediate Representation instructions.
- `--optimized-ir`: Display the optimized IR instructions and diagnostic optimization notes.
- `--trace`: Display the simulated execution trace produced by the symbolic engine.
- *(No flags specified)*: By default, displays all five stages sequentially.

#### Exit Codes
- `0`: Successful compilation and execution.
- `1`: Error encountered during lexical analysis, parsing, semantic analysis, or file reading. Errors print a clean, single-line message to `stderr`/`stdout` without Python stack traces.

---

## 4. Language Reference (All 8 Statements)

| Statement | Syntax | Purpose & Description | Example |
|:---|:---|:---|:---|
| `pipeline` | `pipeline <IDENT> { <statements> }` | Top-level pipeline block container. Exactly one per file. | `pipeline student_model { ... }` |
| `load` | `load "<filepath>";` | Loads the source dataset. Exactly one load required per pipeline. | `load "students.csv";` |
| `clean` | `clean <strategy>;` | Applies a data cleaning strategy (free identifier). | `clean missing_values;` |
| `select` | `select <col1>, <col2>, ...;` | Selects feature columns. Replaces prior column selection. | `select cgpa, attendance, hours;` |
| `drop` | `drop <col1>, <col2>, ...;` | Drops specified columns. Cannot drop columns not in current selection. | `drop student_id, name;` |
| `split` | `split <name> = <percent>%;` | Partitions dataset ($0 < p < 100$; cumulative total $\le 100\%$). | `split train = 80%;` |
| `train` | `train <model> = <algorithm>;` | Trains model using algorithm (free identifier). Requires `train` split. | `train model1 = decision_tree;` |
| `evaluate` | `evaluate <model>;` | Evaluates a previously trained model. Can be called multiple times. | `evaluate model1;` |

---

## 5. Diagnostic Errors & Error Classes

The compiler halts on the first encountered error and produces clean, line-referenced diagnostic messages:

### 5.1 Lexical Errors (`LexicalError`)
- **Unterminated string literal**: `Lexical Error at line 2, col 9: unterminated string literal`
- **Unexpected character**: `Lexical Error at line 3, col 12: unexpected character '@'`

### 5.2 Syntax Errors (`SyntaxError_`)
- **Expected token mismatch**: `Syntax Error at line 2: expected SEMI, found IDENT ('clean')`
- **Missing closing brace / unexpected EOF**: `Syntax Error at line 5: unexpected end of file; expected '}' to close pipeline 'p'`
- **Multiple pipelines**: `Syntax Error at line 8: only one pipeline per file is supported`
- **Unexpected token after pipeline**: `Syntax Error at line 10: unexpected token IDENT ('extra') after end of pipeline`
- **Invalid percentage format**: `Syntax Error at line 4: expected PERCENT, found NUMBER ('80')`
- **Missing column in select/drop**: `Syntax Error at line 3: expected IDENT, found SEMI (';')`

### 5.3 Semantic Errors (`SemanticError`)
All 21 semantic error conditions checked in [`semantic.py`](src/ds_pipeline_dsl/semantic.py):
1. **Duplicate load**: `Semantic Error at line 3: 'load' used more than once; a dataset was already loaded at line 2.`
2. **Empty load filename**: `Semantic Error at line 2: 'load' requires a non-empty filename.`
3. **Clean before load**: `Semantic Error at line 2: 'clean' used before any 'load' statement. No dataset is available.`
4. **Clean after train**: `Semantic Error at line 5: 'clean' used after model 'm' was trained at line 4; data-preparation statements must appear before any 'train'.`
5. **Select before load**: `Semantic Error at line 2: 'select' used before any 'load' statement.`
6. **Select after train**: `Semantic Error at line 5: 'select' used after model 'm' was trained at line 4; data-preparation statements must appear before any 'train'.`
7. **Duplicate column in select**: `Semantic Error at line 3: column 'cgpa' appears more than once in 'select'.`
8. **Select of dropped column**: `Semantic Error at line 4: column 'c1' was dropped at line 3 and cannot be selected.`
9. **Drop before load**: `Semantic Error at line 2: 'drop' used before any 'load' statement.`
10. **Drop after train**: `Semantic Error at line 5: 'drop' used after model 'm' was trained at line 4; data-preparation statements must appear before any 'train'.`
11. **Duplicate column in drop**: `Semantic Error at line 3: column 'c1' appears more than once in 'drop'.`
12. **Drop already dropped column**: `Semantic Error at line 4: column 'c1' was already dropped at line 3.`
13. **Drop column not in selection**: `Semantic Error at line 4: cannot drop column 'c3': it is not in the current selection.`
14. **Drop all selected columns**: `Semantic Error at line 4: 'drop' would remove every selected column.`
15. **Split before load**: `Semantic Error at line 2: 'split' used before any 'load' statement.`
16. **Split percentage out of bounds**: `Semantic Error at line 3: split percentage must be strictly between 0 and 100.`
17. **Duplicate split name**: `Semantic Error at line 4: split 'train' is already defined at line 3.`
18. **Cumulative split exceeds 100%**: `Semantic Error at line 4: cumulative split total would be 100.1%, which exceeds 100%.`
19. **Train before split definition**: `Semantic Error at line 3: training data has not been defined. A 'split train = <percent>%;' statement must appear before 'train m = dt;'.`
20. **Duplicate model name**: `Semantic Error at line 5: model 'm' is already defined at line 4.`
21. **Evaluate before train**: `Semantic Error at line 4: model 'm' is evaluated before it has been trained.`

---

## 6. Optimizer Architecture & Safety Principles

The optimizer [`optimizer.py`](src/ds_pipeline_dsl/optimizer.py) executes four independent, linear-time ($O(n)$) passes in strict program order:

1. `_remove_unreachable`: Removes instructions appearing after the **last** `OP_EVAL`. If no evaluations exist, the IR is untouched.
2. `_remove_dead_trains`: Backward scan identifying models evaluated in the pipeline; eliminates `OP_TRAIN` instructions for models that are never evaluated.
3. `_merge_adjacent_drops`: Combines consecutive runs of $\ge 2$ `OP_DROP` instructions into a single merged drop with ordered, deduplicated columns.
4. `_collapse_duplicates`: Collapses consecutive identical `OP_CLEAN` or `OP_SELECT` instructions (ignoring source line numbers during comparison).

### Safety Argument
- **Observable Behavior**: The observable behavior of a pipeline is defined as the sequence of model evaluation records:
  $$\text{Record} = (\text{model\_name}, \text{algorithm}, \text{train\_state}, \text{eval\_state})$$
- Instructions appearing after the last evaluation produce no observable records and affect no subsequent evaluations.
- Models trained but never evaluated write only to internal model state that is never read. Removing them produces zero observable difference.
- Because data-preparation statements cannot appear after model training (enforced by semantic rules), dead train elimination never makes previously separated data-preparation statements adjacent.
- If a pipeline contains no `evaluate` statement, the optimizer conservatively preserves all instructions without pruning.

---

## 7. Example Programs & Test Suite

The `examples/` directory contains 20 curated pipeline programs covering all language features:

| File Name | Purpose | Expected Outcome |
|:---|:---|:---|
| [`valid_basic.pipe`](examples/valid_basic.pipe) | Baseline canonical 6-statement pipeline | Compiles & executes (Exit 0) |
| [`valid_drop.pipe`](examples/valid_drop.pipe) | Drop columns before selection | Compiles & executes (Exit 0) |
| [`valid_select_then_drop.pipe`](examples/valid_select_then_drop.pipe) | Select columns and drop a subset | Compiles & executes (Exit 0) |
| [`optimizer_demo.pipe`](examples/optimizer_demo.pipe) | Exercises all 4 optimizer passes in one program | Compiles, optimizes (11 $\to$ 7), executes (Exit 0) |
| [`complex_multi_model.pipe`](examples/complex_multi_model.pipe) | Multi-model evaluation chain with dead train removal | Compiles & executes both evaluations (Exit 0) |
| [`complex_redundant.pipe`](examples/complex_redundant.pipe) | Heavy redundancies (cleans, selects, drops, dead trains) | Compiles, optimizes (12 $\to$ 7), executes (Exit 0) |
| [`complex_valid_drop_chain.pipe`](examples/complex_valid_drop_chain.pipe) | Non-adjacent drops separated by a split statement | Compiles, preserves separate drops, executes (Exit 0) |
| [`invalid_clean_after_train.pipe`](examples/invalid_clean_after_train.pipe) | Data cleaning after model training | Semantic Error (Exit 1) |
| [`invalid_drop_after_train.pipe`](examples/invalid_drop_after_train.pipe) | Dropping columns after model training | Semantic Error (Exit 1) |
| [`invalid_drop_all_selected.pipe`](examples/invalid_drop_all_selected.pipe) | Dropping all currently selected columns | Semantic Error (Exit 1) |
| [`invalid_drop_before_load.pipe`](examples/invalid_drop_before_load.pipe) | Dropping columns before dataset loading | Semantic Error (Exit 1) |
| [`invalid_drop_twice.pipe`](examples/invalid_drop_twice.pipe) | Dropping the same column multiple times | Semantic Error (Exit 1) |
| [`invalid_duplicate_load.pipe`](examples/invalid_duplicate_load.pipe) | Loading multiple datasets in one pipeline | Semantic Error (Exit 1) |
| [`invalid_duplicate_model.pipe`](examples/invalid_duplicate_model.pipe) | Training multiple models with identical names | Semantic Error (Exit 1) |
| [`invalid_duplicate_split.pipe`](examples/invalid_duplicate_split.pipe) | Defining multiple splits with identical names | Semantic Error (Exit 1) |
| [`invalid_lexical_error.pipe`](examples/invalid_lexical_error.pipe) | Illegal character (`@`) in pipeline body | Lexical Error (Exit 1) |
| [`invalid_select_dropped_column.pipe`](examples/invalid_select_dropped_column.pipe) | Selecting a column that was previously dropped | Semantic Error (Exit 1) |
| [`invalid_split_total_over_100.pipe`](examples/invalid_split_total_over_100.pipe) | Cumulative split percentages exceeding 100% | Semantic Error (Exit 1) |
| [`invalid_syntax_error.pipe`](examples/invalid_syntax_error.pipe) | Syntax error (missing statement semicolon) | Syntax Error (Exit 1) |
| [`invalid_train_before_split.pipe`](examples/invalid_train_before_split.pipe) | Training a model before defining the `train` split | Semantic Error (Exit 1) |

---

## 8. Running Tests & Benchmarks

### 8.1 Automated Test Suite
Run the complete test suite with `pytest`:
```bash
python -m pytest -q
```
*Expected Result*: `223 passed in ~0.25s` with 0 failures and 0 warnings.

### 8.2 Performance Benchmark
Run the automated performance benchmark driver:
```bash
python benchmarks/benchmark.py
```
*Expected Result*: Measures execution across 10, 100, 1,000, and 10,000 statements, outputs the performance table to stdout, and updates [`docs/performance.md`](docs/performance.md) in ~0.67s.

---

## 9. Scope & Limitations

1. **Symbolic Execution Only**: The compiler analyzes and simulates pipeline execution logic; it does not read physical CSV files or execute numeric machine learning routines.
2. **Single Pipeline per File**: Exactly one pipeline declaration per `.pipe` file.
3. **Fail-Fast Error Handling**: Emits diagnostic messages on the first encountered lexical, syntactic, or semantic error.
4. **Reserved Keywords**: Language keywords (`load`, `clean`, `select`, `drop`, `split`, `train`, `evaluate`, `pipeline`) cannot be used as column or model names.
5. **Free Identifiers**: Strategy names in `clean` and algorithm names in `train` are free identifiers to accommodate arbitrary data science frameworks.


## Web Dashboard

The Streamlit dashboard presents the existing compiler for a live university demo: real tokens, AST, semantic state, original and optimized IR, optimizer notes, and symbolic execution traces. The compiler is unchanged. Execution is symbolic only: no CSV is read, no model is trained, and no numeric accuracy or prediction is produced. The UI runs locally and works offline after dependencies are installed; it makes no external network calls.

From the repository root in PowerShell, run these five commands:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install -r requirements-dashboard.txt
python -m streamlit run dashboard/app.py
```

Open http://localhost:8501. If PowerShell blocks activation, first run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. If `streamlit` is not on PATH, always use `python -m streamlit` as above. If port 8501 is busy, launch with `python -m streamlit run dashboard/app.py --server.port 8502` and open http://localhost:8502. Stop the server with Ctrl+C.

The dashboard inserts the local `src/` directory into its import path, so it also works without an editable package install. The dashboard dependency file adds only Streamlit (tested with 1.66.0); pandas is supplied by Streamlit. No system Graphviz installation is needed.

Page guide:

- **Overview**: project purpose, language statements, discovered example count, saved test evidence if present, and the language grammar if available.
- **Compiler Playground**: choose an example category, edit the source, press Compile, and inspect the six output tabs. Results remain visible when the editor changes, with a notice that they describe the previous source. Errors retain the compiler's original message and highlight its source location; columns use the compiler's zero-based numbering.
- **Architecture**: the real compilation flow, semantic checks, four optimizer passes in execution order, and stage colors from the last compile.
- **Performance**: the saved benchmark table, environment, stage-time and IR charts, and verbatim observations. It reads `docs/performance.md`; `python benchmarks/benchmark.py` creates that report. The dashboard never runs a benchmark automatically, and missing reports produce a friendly message.

Five-step live demo (about five minutes):

1. Open Compiler Playground, compile `valid_basic.pipe`, and inspect Tokens, AST, Semantic Analysis, IR and Execution Trace.
2. Compile `invalid_lexical_error.pipe`, `invalid_syntax_error.pipe` and `invalid_train_before_split.pipe`; explain the error class, highlighted line and skipped later stages.
3. Compile `optimizer_demo.pipe`, open Optimization, and compare the real instruction counts, removed/merged labels, optimizer notes and trace-line counts.
4. Open Architecture to show the successful stage colors and the four ordered optimizer passes. Return after an invalid compilation to demonstrate failed/skipped colors.
5. Open Performance to discuss the recorded environment, scaling and IR reduction without launching a new benchmark during the presentation.

Run all compiler and dashboard tests from the repository root:

```powershell
python -m pytest -q
```

Pure runner tests always run; UI smoke tests use `streamlit.testing.v1.AppTest` and skip cleanly when Streamlit is absent. Benchmark parsing tests requiring pandas skip when pandas is absent. The dashboard handles empty sources using the real compiler, preserves partial results after a failure, and rejects sources longer than 100,000 characters. Token tables display at most 1,000 rows and retain the final EOF token in a caption for longer streams. IR kept/removed/merged labels are a best-effort comparison of real instruction data, not optimizer provenance. Trace counts can differ because optimization changes the symbolic instruction log; they are not a claim of identical full traces.
