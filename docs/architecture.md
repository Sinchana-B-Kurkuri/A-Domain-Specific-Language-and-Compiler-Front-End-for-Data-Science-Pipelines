# System Architecture & Compiler Design

This document details the software architecture, compilation pipeline, symbol table structure, intermediate representation (IR), and execution model of the Data Science Pipeline DSL compiler (`ds_pipeline_dsl`).

---

## 1. Compiler Flow Architecture

The compiler implements a classic multi-stage pipeline with strict phase decoupling. Each stage is a pure function of its inputs, transforming the source representation into progressively lower representations:

### 1.1 Mermaid Pipeline Flowchart
*(Note: You can copy this diagram or export it to an image tool.)*

```mermaid
flowchart TD
    Source[".pipe Source File"] --> Lexer["1. Lexer (tokenize)"]
    Lexer -->|LexicalError (exit 1)| LexErr["Error Output"]
    Lexer -->|Tokens| Parser["2. Parser (recursive descent)"]
    Parser -->|SyntaxError_ (exit 1)| SynErr["Error Output"]
    Parser -->|AST (PipelineNode)| Semantic["3. Semantic Analyzer (analyze)"]
    Semantic -->|SemanticError (exit 1)| SemErr["Error Output"]
    Semantic -->|Symbol Table + Valid AST| Lowering["4. IR Lowering (lower_to_ir)"]
    Lowering -->|Raw IR List| Optimizer["5. Optimizer (optimize)"]
    
    subgraph OptimizerPasses ["Optimizer Passes (O(n) each)"]
        Pass1["Pass 1: _remove_unreachable"] --> Pass2["Pass 2: _remove_dead_trains"]
        Pass2 --> Pass3["Pass 3: _merge_adjacent_drops"]
        Pass3 --> Pass4["Pass 4: _collapse_duplicates"]
    end
    
    Optimizer --> OptimizerPasses
    OptimizerPasses -->|Optimized IR List + Notes| Executor["6. Symbolic Executor (execute)"]
    Executor --> Trace["Human-Readable Execution Trace"]

    CLI["CLI Driver (cli.py)"] -.->|Coordinates & Formats| Source
    CLI -.->|Optionally displays| Lexer
    CLI -.->|Optionally displays| Parser
    CLI -.->|Optionally displays| Lowering
    CLI -.->|Optionally displays| Optimizer
    CLI -.->|Optionally displays| Executor
```

### 1.2 ASCII Architecture Fallback
```text
  +-------------------------------------------------------------------------+
  |                             .pipe Source File                           |
  +-------------------------------------------------------------------------+
                                       |
                                       v
  +--------------------+    Raises LexicalError
  |    1. Lexer        | ------------------------> [Exit 1: Clean Message]
  |  (lexer.tokenize)  |
  +--------------------+
           | Tokens
           v
  +--------------------+    Raises SyntaxError_
  |    2. Parser       | ------------------------> [Exit 1: Clean Message]
  |  (parser.Parser)   |
  +--------------------+
           | Abstract Syntax Tree (AST)
           v
  +--------------------+    Raises SemanticError
  |    3. Semantic     | ------------------------> [Exit 1: Clean Message]
  | (semantic.analyze) | <--> SymbolTable (Tracks state & dependency rules)
  +--------------------+
           | Validated AST + SymbolTable
           v
  +--------------------+
  |  4. IR Lowering    | Converts AST statements to flat IRInstruction list
  |  (ir.lower_to_ir)  |
  +--------------------+
           | Raw IR Instructions
           v
  +-------------------------------------------------------------------------+
  |  5. Optimizer (optimizer.optimize)                                      |
  |     - Pass 1: _remove_unreachable (tail after last OP_EVAL)             |
  |     - Pass 2: _remove_dead_trains (models never evaluated)             |
  |     - Pass 3: _merge_adjacent_drops (contiguous drop runs merged)       |
  |     - Pass 4: _collapse_duplicates (consecutive identical clean/select)|
  +-------------------------------------------------------------------------+
           | Optimized IR Instructions (+ Optimization Notes)
           v
  +--------------------+
  | 6. Symbolic Engine | Walks IR and generates simulated accuracy/execution
  | (executor.execute) | trace messages without performing heavy computation
  +--------------------+
           |
           v
  +-------------------------------------------------------------------------+
  |                        Output Trace / CLI Display                       |
  +-------------------------------------------------------------------------+
```

---

## 2. Module Responsibilities & Key Symbols

| Module | Responsibility | Key Classes / Functions |
|:---|:---|:---|
| [`lexer.py`](../src/ds_pipeline_dsl/lexer.py) | Scans raw string source into token stream using master regex matching; tracks line and column coordinates; skips whitespace and `//` comments. | `Token`, `LexicalError`, `tokenize(source)` |
| [`parser.py`](../src/ds_pipeline_dsl/parser.py) | LL(1) recursive-descent parser; enforces grammar rules, single-pipeline scoping, and delimiters; produces typed AST nodes. | `SyntaxError_`, `Parser`, `Parser.parse_pipeline()` |
| [`ast_nodes.py`](../src/ds_pipeline_dsl/ast_nodes.py) | Typed dataclasses representing language statements and top-level pipeline declarations. | `PipelineNode`, `LoadStmt`, `CleanStmt`, `SelectStmt`, `DropStmt`, `SplitStmt`, `TrainStmt`, `EvaluateStmt` |
| [`semantic.py`](../src/ds_pipeline_dsl/semantic.py) | Verifies pipeline state dependencies, single-load, split boundaries, column sets, disjointness, and evaluation life-cycles. | `SymbolTable`, `SemanticError`, `analyze(pipeline_ast)` |
| [`ir.py`](../src/ds_pipeline_dsl/ir.py) | Defines the intermediate representation dataclass and lowers validated AST statements into a flat sequence of IR instructions. | `IRInstruction(op, args)`, `lower_to_ir(pipeline_ast, symbol_table)` |
| [`optimizer.py`](../src/ds_pipeline_dsl/optimizer.py) | Performs 4 independent, linear-time $O(n)$ optimization passes; records diagnostic optimization notes. | `optimize(ir_list, notes)`, `_remove_unreachable()`, `_remove_dead_trains()`, `_merge_adjacent_drops()`, `_collapse_duplicates()` |
| [`executor.py`](../src/ds_pipeline_dsl/executor.py) | Symbolic execution engine; walks IR instructions and generates formatted trace logs simulating pipeline execution. | `execute(ir_list)` |
| [`cli.py`](../src/ds_pipeline_dsl/cli.py) | CLI entry-point using `argparse`; handles command-line arguments, orchestrates compiler passes, and prints formatted sections. | `main()` |

---

## 3. Symbol Table State Tracking

The `SymbolTable` maintains contextual pipeline state during semantic analysis. Because pipelines represent directed data workflows, later operations depend on prior stage artifacts:

| Field Name | Type | Description / Tracked Invariant |
|:---|:---|:---|
| `data_loaded` | `bool` | Set to `True` when the first `load` statement executes. Required before any `clean`, `select`, `drop`, or `split`. |
| `load_line` | `Optional[int]` | Records the line number of the dataset `load` to provide precise diagnostic messages if duplicate loads appear. |
| `data_cleaned` | `bool` | Set to `True` when at least one `clean` statement executes. |
| `selected_columns` | `Optional[list[str]]` | Tracks the currently active selected column list. Updated by `select` and reduced when `drop` removes selected columns. |
| `dropped_columns` | `dict[str, int]` | Mapping of `column_name -> line_number` for every dropped column. Enforces that dropped columns cannot be re-dropped or selected. |
| `splits` | `dict[str, float]` | Mapping of `split_name -> percentage`. Enforces unique split names, `0 < percent < 100`, and cumulative $\le 100\%$. |
| `split_lines` | `dict[str, int]` | Records definition line number for each split partition. |
| `models` | `dict[str, str]` | Mapping of `model_name -> algorithm`. Enforces unique model names and verifies models exist before `evaluate`. |
| `model_lines` | `dict[str, int]` | Records definition line number for each trained model. |
| `first_train` | `Optional[tuple[str, int]]` | Stores `(model_name, line)` of the very first `train` statement. Used to reject data-preparation statements (`clean`, `select`, `drop`) occurring after model training. |

---

## 4. Intermediate Representation (IR) Specification

The Intermediate Representation is a flat, linear instruction list consisting of `IRInstruction` dataclasses:
```python
@dataclass
class IRInstruction:
    op: str       # Opcode identifier
    args: dict    # Instruction arguments, including source line coordinate
```

### IR Opcode Table

| Opcode | Arguments (`args` dict) | Description / Example Lowering |
|:---|:---|:---|
| `OP_LOAD` | `{"filename": str, "line": int}` | Loads dataset source. Example: `args={'filename': 'data.csv', 'line': 2}` |
| `OP_CLEAN` | `{"strategy": str, "line": int}` | Applies cleaning strategy. Example: `args={'strategy': 'missing_values', 'line': 3}` |
| `OP_SELECT` | `{"columns": list[str], "line": int}` | Specifies active feature columns. Example: `args={'columns': ['cgpa', 'attendance'], 'line': 4}` |
| `OP_DROP` | `{"columns": list[str], "line": int}` | Removes columns. Example: `args={'columns': ['student_id'], 'line': 5}` |
| `OP_SPLIT` | `{"name": str, "percent": float, "line": int}` | Configures dataset partition. Example: `args={'name': 'train', 'percent': 80.0, 'line': 6}` |
| `OP_TRAIN` | `{"model_name": str, "algorithm": str, "line": int}` | Instantiates model. Example: `args={'model_name': 'm1', 'algorithm': 'decision_tree', 'line': 7}` |
| `OP_EVAL` | `{"model_name": str, "line": int}` | Triggers evaluation. Example: `args={'model_name': 'm1', 'line': 8}` |

---

## 5. Optimizer Architecture & Safety Model

The optimizer transforms the linear IR through four independent passes in strict $O(n)$ time:
1. `_remove_unreachable`: Removes any dead tail instructions appearing after the final `OP_EVAL`.
2. `_remove_dead_trains`: Backward scan identifying models that are never evaluated; eliminates unused `OP_TRAIN` instructions.
3. `_merge_adjacent_drops`: Combines immediately adjacent runs of `OP_DROP` instructions into a single drop with deduplicated columns.
4. `_collapse_duplicates`: Removes consecutive identical `OP_CLEAN` or `OP_SELECT` instructions (excluding line numbers from comparison).

### Safety Argument
- **Observable Behavior**: In this DSL, the observable behavior of a program is defined strictly as the sequence of model evaluations produced at `OP_EVAL` points:
  $$\text{Record} = (\text{model\_name}, \text{algorithm}, \text{train\_state}, \text{eval\_state})$$
- Instructions appearing after the *last* evaluation cannot affect any evaluation record, making their removal safe.
- `OP_TRAIN` writes only to internal model state read solely by `OP_EVAL` of that model name. If no evaluation ever reads that model, eliminating the train leaves all evaluation records unchanged.
- Data-preparation idempotence (repeated clean or select) and set-union commutativity (adjacent drops) preserve exact state transitions.
- All four passes operate without mutating input IR structures, preserving data integrity.
