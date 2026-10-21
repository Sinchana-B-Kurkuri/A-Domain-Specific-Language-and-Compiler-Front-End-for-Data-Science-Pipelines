# Compiler Demonstration Script & Viva Quick Reference

This document provides a complete, 5-minute step-by-step demonstration script for presentation and review, followed by a high-yield **Viva Quick Reference** guide for examiners and committee questions.

---

## Part 1: Five-Minute Demo Script (10 Steps)

Run each command from the repository root directory. The captured output of every command is preserved in [`docs/demo_outputs/`](demo_outputs/).

### Step 1: Baseline Valid Pipeline (All Five Stages)
- **Command**:
  ```bash
  python -m ds_pipeline_dsl.cli examples/valid_basic.pipe
  ```
- **What to say**:
  > "This is our baseline valid pipeline demonstrating the complete five-stage compiler pipeline operating on a clean six-statement data science program."
- **What to point at in output**:
  > Point to the clear stage headers (`=== TOKENS ===`, `=== AST ===`, `=== IR ===`, `=== OPTIMIZED IR ===`, `=== TRACE ===`) and the final simulated accuracy evaluation trace at the bottom.
- *Captured Output Reference*: [`docs/demo_outputs/01_valid_basic_all_stages.txt`](demo_outputs/01_valid_basic_all_stages.txt)

---

### Step 2: The `drop` Feature & Column Elimination
- **Command**:
  ```bash
  python -m ds_pipeline_dsl.cli examples/valid_drop.pipe
  ```
- **What to say**:
  > "Here we demonstrate the `drop` statement dropping unwanted columns (`student_id`, `name`) prior to feature selection, showing full front-end, lowering, and executor integration."
- **What to point at in output**:
  > Point to `Token(type='DROP')` in tokens, `DropStmt` in AST, `OP_DROP` in IR, and the resulting trace line `Dropped columns: student_id, name`.
- *Captured Output Reference*: [`docs/demo_outputs/02_valid_drop_all_stages.txt`](demo_outputs/02_valid_drop_all_stages.txt)

---

### Step 3: Lexical Error Handling
- **Command**:
  ```bash
  python -m ds_pipeline_dsl.cli examples/invalid_lexical_error.pipe
  ```
- **What to say**:
  > "Our scanner detects illegal characters immediately, reporting line and column coordinates with clean termination and zero Python traceback."
- **What to point at in output**:
  > Point to `Lexical Error at line 3, col 12: unexpected character '@'` and exit code 1.
- *Captured Output Reference*: [`docs/demo_outputs/03_lexical_error.txt`](demo_outputs/03_lexical_error.txt)

---

### Step 4: Syntax Error Handling
- **Command**:
  ```bash
  python -m ds_pipeline_dsl.cli examples/invalid_syntax_error.pipe
  ```
- **What to say**:
  > "The recursive-descent parser enforces formal EBNF grammar constraints, catching missing semicolons or delimiter errors with clear expected-versus-found tokens."
- **What to point at in output**:
  > Point to `Syntax Error at line 4: expected SEMI, found IDENT ('clean')`.
- *Captured Output Reference*: [`docs/demo_outputs/04_syntax_error.txt`](demo_outputs/04_syntax_error.txt)

---

### Step 5: Semantic Rule Enforcement (Train Before Split)
- **Command**:
  ```bash
  python -m ds_pipeline_dsl.cli examples/invalid_train_before_split.pipe
  ```
- **What to say**:
  > "Our semantic analyzer tracks state dependencies in a SymbolTable, preventing model training if no training partition has been defined."
- **What to point at in output**:
  > Point to `Semantic Error at line 5: training data has not been defined. A 'split train = <percent>%;' statement must appear before 'train model = decision_tree;'`.
- *Captured Output Reference*: [`docs/demo_outputs/05_semantic_train_before_split.txt`](demo_outputs/05_semantic_train_before_split.txt)

---

### Step 6: Semantic Boundary Checking (Cumulative Splits)
- **Command**:
  ```bash
  python -m ds_pipeline_dsl.cli examples/invalid_split_total_over_100.pipe
  ```
- **What to say**:
  > "The semantic analyzer verifies cumulative partition splits across the pipeline, ensuring partition percentages never exceed 100%."
- **What to point at in output**:
  > Point to `Semantic Error at line 5: cumulative split total would be 110%, which exceeds 100%`.
- *Captured Output Reference*: [`docs/demo_outputs/06_semantic_split_total_over_100.txt`](demo_outputs/06_semantic_split_total_over_100.txt)

---

### Step 7: Four-Pass Optimization & Diagnostic Notes
- **Command**:
  ```bash
  python -m ds_pipeline_dsl.cli examples/optimizer_demo.pipe --ir --optimized-ir
  ```
- **What to say**:
  > "Here we demonstrate our four linear-time optimization passes running on a program with duplicate cleans, adjacent drops, dead model training, and unreachable code."
- **What to point at in output**:
  > Point to the instruction reduction line `IR instructions: 11 -> 7` and the diagnostic explanation under `=== OPTIMIZATION NOTES ===` for unreachable, dead-train, drop-merge, and duplicate collapse.
- *Captured Output Reference*: [`docs/demo_outputs/07_optimizer_before_after.txt`](demo_outputs/07_optimizer_before_after.txt)

---

### Step 8: Multi-Model Evaluation Chain
- **Command**:
  ```bash
  python -m ds_pipeline_dsl.cli examples/complex_multi_model.pipe --trace
  ```
- **What to say**:
  > "In this complex pipeline with multiple evaluated models, both evaluations survive optimization while the unused dead train is safely eliminated."
- **What to point at in output**:
  > Point to the two sequential evaluation trace lines for `m1` and `m2`, and note that the dead model `m_dead` is never executed.
- *Captured Output Reference*: [`docs/demo_outputs/08_complex_multi_model_trace.txt`](demo_outputs/08_complex_multi_model_trace.txt)

---

### Step 9: Automated Test Suite Execution
- **Command**:
  ```bash
  python -m pytest -q
  ```
- **What to say**:
  > "Our automated pytest suite runs 223 comprehensive unit, boundary, integration, and equivalence tests across all stages in under 0.3 seconds."
- **What to point at in output**:
  > Point to `223 passed in ~0.25s` showing 100% test pass rate.
- *Captured Output Reference*: [`docs/demo_outputs/09_pytest.txt`](demo_outputs/09_pytest.txt)

---

### Step 10: Performance Benchmark & Scaling Verification
- **Command**:
  ```bash
  python benchmarks/benchmark.py
  ```
- **What to say**:
  > "Our automated performance benchmark proves strict linear $O(n)$ scaling across 10,000 statements with full safeguards against memory leaks and quadratic hangs."
- **What to point at in output**:
  > Point to the results table showing flat ~7.8 $\mu\text{s}$ per statement scaling, 40% instruction reduction, and a total runtime of only 0.67s.
- *Captured Output Reference*: [`docs/demo_outputs/10_benchmark_table.txt`](demo_outputs/10_benchmark_table.txt)

---

## Part 2: Viva Quick Reference

### 1. Where Compiler Concepts Live in Code
| Compiler Phase / Concept | Source Location | Implementation Details |
|:---|:---|:---|
| **Lexical Analysis (Scanner)** | [`src/ds_pipeline_dsl/lexer.py`](../src/ds_pipeline_dsl/lexer.py) | `tokenize()` uses a single compiled master regex `MASTER_PATTERN` matching 13 token patterns; tracks line/column numbers. |
| **Parsing (Recursive Descent)** | [`src/ds_pipeline_dsl/parser.py`](../src/ds_pipeline_dsl/parser.py) | LL(1) `Parser` class with `peek()`, `advance()`, `expect()`, and statement parsers for each grammar production. |
| **Abstract Syntax Tree (AST)** | [`src/ds_pipeline_dsl/ast_nodes.py`](../src/ds_pipeline_dsl/ast_nodes.py) | Python `@dataclass` nodes (`PipelineNode`, `LoadStmt`, `DropStmt`, etc.) preserving statement line numbers. |
| **Semantic Analysis & State** | [`src/ds_pipeline_dsl/semantic.py`](../src/ds_pipeline_dsl/semantic.py) | `SymbolTable` and `analyze()` enforce 21 semantic rules across loaded data, partition splits, column sets, and models. |
| **Intermediate Representation** | [`src/ds_pipeline_dsl/ir.py`](../src/ds_pipeline_dsl/ir.py) | Flat linear instruction list: `IRInstruction(op, args)` generated by `lower_to_ir()`. |
| **Code Optimization** | [`src/ds_pipeline_dsl/optimizer.py`](../src/ds_pipeline_dsl/optimizer.py) | Four independent linear-time passes: `_remove_unreachable`, `_remove_dead_trains`, `_merge_adjacent_drops`, `_collapse_duplicates`. |
| **Symbolic Execution** | [`src/ds_pipeline_dsl/executor.py`](../src/ds_pipeline_dsl/executor.py) | `execute()` simulates pipeline operations and produces human-readable trace logs without invoking external ML libraries. |
| **Driver & CLI** | [`src/ds_pipeline_dsl/cli.py`](../src/ds_pipeline_dsl/cli.py) | `main()` coordinates the pipeline stages, parses command-line flags, and handles clean error reporting. |

---

### 2. Semantic Rules Map
In [`src/ds_pipeline_dsl/semantic.py`](../src/ds_pipeline_dsl/semantic.py), every rule is enforced during the single AST walk in `analyze()`:
- **`LoadStmt`** (lines 28–40): Rejects duplicate load (`table.data_loaded`) and empty filename (`stmt.filename.strip() == ""`).
- **`CleanStmt`** (lines 41–54): Rejects clean before load (`not table.data_loaded`) and clean after train (`table.first_train`).
- **`SelectStmt`** (lines 55–83): Rejects select before load, select after train, duplicate columns in select list, and selection of previously dropped columns (`col in table.dropped_columns`).
- **`DropStmt`** (lines 84–130): Rejects drop before load, drop after train, duplicate column in drop list, dropping an already dropped column, dropping a column not in current selection, and dropping all selected columns.
- **`SplitStmt`** (lines 131–153): Rejects split before load, split percent $\le 0$ or $\ge 100$, duplicate split name, and cumulative split total $> 100\%$.
- **`TrainStmt`** (lines 154–170): Rejects training when `train` split is undefined, and duplicate model names.
- **`EvaluateStmt`** (lines 171–177): Rejects evaluating a model that has not been trained (`stmt.model_name not in table.models`).

---

### 3. How to Add a New Statement to the Compiler (Worked Example: `drop`)
Adding a statement requires walking sequentially through each compiler layer:
1. **Lexer** ([`lexer.py`](../src/ds_pipeline_dsl/lexer.py)):
   - Add `"drop"` to the `KEYWORDS` set.
   - Scanner automatically emits `Token("DROP", "drop", line, col)`.
2. **AST** ([`ast_nodes.py`](../src/ds_pipeline_dsl/ast_nodes.py)):
   - Define `@dataclass class DropStmt: columns: list[str]; line: int`.
3. **Parser** ([`parser.py`](../src/ds_pipeline_dsl/parser.py)):
   - In `parse_statement()`, add `if tok.type == "DROP": ...` to parse comma-separated column identifiers and semicolon.
4. **Semantic Analyzer** ([`semantic.py`](../src/ds_pipeline_dsl/semantic.py)):
   - Add `isinstance(stmt, DropStmt)` branch.
   - Check preconditions (`table.data_loaded`, `not table.first_train`, column validity).
   - Update `table.dropped_columns` and update/filter `table.selected_columns`.
5. **IR Lowering** ([`ir.py`](../src/ds_pipeline_dsl/ir.py)):
   - Lower `DropStmt` into `IRInstruction("OP_DROP", {"columns": stmt.columns, "line": stmt.line})`.
6. **Optimizer** ([`optimizer.py`](../src/ds_pipeline_dsl/optimizer.py)):
   - If adjacent drops appear, merge their column lists via `_merge_adjacent_drops()`.
7. **Executor** ([`executor.py`](../src/ds_pipeline_dsl/executor.py)):
   - In `execute()`, handle `instr.op == "OP_DROP"` and emit `Dropped columns: {cols}`.

---

### 4. How to Add a New Semantic Rule
To add a new semantic constraint (e.g. "disallow evaluating the same model more than three times"):
1. Open [`src/ds_pipeline_dsl/semantic.py`](../src/ds_pipeline_dsl/semantic.py).
2. Add a tracking field to `SymbolTable.__init__` (e.g., `self.eval_counts: dict[str, int] = {}`).
3. In `analyze()`, under the corresponding statement branch (e.g. `elif isinstance(stmt, EvaluateStmt):`), inspect the state:
   ```python
   count = table.eval_counts.get(stmt.model_name, 0)
   if count >= 3:
       raise SemanticError(f"Semantic Error at line {stmt.line}: model '{stmt.model_name}' evaluated more than 3 times.")
   table.eval_counts[stmt.model_name] = count + 1
   ```
4. Add corresponding pass/fail test cases to [`tests/test_semantic.py`](../tests/test_semantic.py).

---

### 5. The Optimizer Safety Argument in Five Lines
1. **Observable Equivalence**: The observable result of a pipeline is defined strictly by the evaluation records produced at `OP_EVAL` statements.
2. **Unreachable Code**: Any instructions appearing after the *last* `OP_EVAL` cannot alter any evaluation record and are safely deleted.
3. **Dead Training Elimination**: Unused `OP_TRAIN` instructions write only to model entries never read by any `OP_EVAL`; removing them produces zero observable trace difference.
4. **Data-Preparation Independence**: Semantic rules strictly prohibit data-prep statements (`clean`, `select`, `drop`) after training; removing dead trains can never bring data-prep statements adjacent.
5. **Local Idempotence**: Consecutive duplicate cleans, duplicate selects, and adjacent drops are idempotent under set and filtering semantics, preserving exact pipeline state transitions.
