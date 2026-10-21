# Final Report and Presentation Checklist

This document provides complete mapping matrices, presentation outlines, and evaluation checklists for the final Phase 3 university submission and Review 3 oral examination of the **Data Science Pipeline DSL Compiler** project.

---

## 1. University Manual Report Chapter Mapping

This table maps the standard academic project report chapters prescribed by the university compiler design manual to the concrete source code, documentation, test suites, and captured outputs in this repository.

| Chapter # | Chapter Title | Core Content & Objectives | Primary Repository Source Artifacts | Key References & Data to Include |
|-----------|---------------|---------------------------|-------------------------------------|----------------------------------|
| **1** | **Introduction** | Background of data science pipelines, declarative DSLs vs. imperative scripts, compiler front-end principles | [`README.md`](../README.md) (Overview, Features)<br>[`docs/Phase1.docx`](Phase1.docx)<br>[`docs/phase2_report.md`](phase2_report.md) | Domain-specific languages in data engineering, motivation for formal compile-time safety. |
| **2** | **Problem Statement** | Runtime failures in ML scripts (column mismatches, data leakage, training before splitting, unvalidated hyperparameters, silent errors) | [`README.md`](../README.md) (Limitations & Scope)<br>[`docs/architecture.md`](architecture.md)<br>[`examples/invalid_*.pipe`](../examples/) | Common ML pipeline traps: training on unsplit data, split sums $\ne 100\%$, evaluating untrained models. |
| **3** | **Objectives** | Design a formal DSL for ML workflows, build a 6-phase compiler pipeline, implement formal symbol table validation, IR generation, safe optimization, and symbolic execution | [`README.md`](../README.md)<br>[`docs/architecture.md`](architecture.md)<br>[`pyproject.toml`](../pyproject.toml) | Complete compiler front-end: Lexer $\to$ Parser $\to$ Semantic Analyzer $\to$ IR Lowerer $\to$ Optimizer $\to$ Symbolic Executor. |
| **4** | **Background Study / Literature Survey** | Compiler front-ends, LL(1) / recursive-descent parsing, intermediate representation designs (3-address code vs. tuple/opcode IR), peephole and dataflow optimizations | [`docs/grammar.md`](grammar.md)<br>[`docs/architecture.md`](architecture.md)<br>Compilers: Principles, Techniques, and Tools (Dragon Book) | Comparative study of domain DSLs (e.g., SQL, Airflow DAGs, TensorFlow Graph vs. declarative compiler front-ends). |
| **5** | **System Design** | Architectural block diagram, compiler phase interactions, intermediate data structures, SymbolTable design, IR opcode specification | [`docs/architecture.md`](architecture.md) (Mermaid Flowchart, ASCII diagram, Module Table, SymbolTable, IR Opcodes) | End-to-end dataflow, decoupling front-end syntax from target back-ends via flat `IRInstruction(op, args)`. |
| **6** | **Methodology** | Lexical specification, recursive-descent syntax parsing without backtracking, two-pass symbol table semantic analysis, pass-based IR transformations | [`docs/grammar.md`](grammar.md)<br>[`docs/architecture.md`](architecture.md)<br>[`benchmarks/benchmark.py`](../benchmarks/benchmark.py) | Grammar design in standard EBNF, single-token lookahead parsing, deterministic linear-time compilation. |
| **7** | **Compiler Concepts Used** | Detailed explanation of theoretical compiler constructs applied: regular expressions, CFG, LL(1) parsing, symbol tables, type/semantic checking, IR lowering, dead code elimination | [`docs/architecture.md`](architecture.md)<br>[`docs/grammar.md`](grammar.md)<br>[`docs/demo.md`](demo.md) (Viva Quick Reference) | Regular definitions, EBNF production rules, context-sensitive validation, 4 safe IR optimization passes. |
| **8** | **Implementation** | Module-by-module implementation walkthrough with key data structures, classes, and algorithms | [`src/ds_pipeline_dsl/`](../src/ds_pipeline_dsl/) (`lexer.py`, `parser.py`, `ast_nodes.py`, `semantic.py`, `ir.py`, `optimizer.py`, `executor.py`, `cli.py`) | AST dataclasses, recursive parser functions, symbol table state transitions, optimizer pass loops, symbolic tracer. |
| **9** | **Testing and Results** | Test suite organization, test methodology, unit and integration tests, error diagnosis tests, benchmark throughput and latency results | [`tests/`](../tests/) (11 test suites, 223 tests)<br>[`docs/test_results.txt`](test_results.txt)<br>[`docs/performance.md`](performance.md)<br>[`docs/demo_outputs/`](demo_outputs/) | 223 passing tests (100% pass rate in 0.25s), compilation latency $<1.0\text{ ms}$, throughput $>14,000\text{ lines/s}$. |
| **10** | **Conclusion** | Summary of completed compiler deliverables, verification of objectives, impact on data science pipeline reliability | [`README.md`](../README.md)<br>[`docs/demo.md`](demo.md) | Successfully created a verified compiler front-end with rigorous static checking and safe optimization. |
| **11** | **Future Enhancements** | Deferred scope items: concrete execution engine (pandas/scikit-learn backend), allowed-value type validation, multi-pipeline scripts, warning levels | Section 4 of this checklist<br>[`README.md`](../README.md) (Limitations & Scope) | Concrete runtime backends, multi-file modules, AST-level refactoring, rich IDE language server (LSP). |
| **Ref** | **References** | Academic literature, textbook citations, language manuals | Dragon Book (Aho et al.), Python `ast` docs, LLVM IR concepts, Domain-Specific Languages (Fowler) | Standard academic citation format (IEEE / ACM style). |
| **App** | **Appendix** | Complete EBNF grammar, CLI command manual, complete demo run scripts, benchmark data | [`docs/grammar.md`](grammar.md)<br>[`docs/demo.md`](demo.md)<br>[`docs/demo_outputs/`](demo_outputs/) | Source listings for grammar, test outputs, and complete execution traces. |

---

## 2. Phase 3 Deliverables and Review 3 Criteria Matrix

### Part A: Phase 3 Required Deliverables

| Deliverable | Repository Evidence / Location | Status | Verification Command |
|-------------|--------------------------------|--------|----------------------|
| **1. Complete Working Project** | Entire repository under `src/ds_pipeline_dsl/` driven by `cli.py` | Complete | `python -m ds_pipeline_dsl.cli examples/valid_basic.pipe` |
| **2. Source Code** | Modular architecture: `lexer.py`, `parser.py`, `ast_nodes.py`, `semantic.py`, `ir.py`, `optimizer.py`, `executor.py`, `cli.py` | Complete | `dir src\ds_pipeline_dsl` |
| **3. Test Cases** | 11 comprehensive test modules covering all 6 compiler phases + CLI + edge cases + benchmarks (223 tests) | Complete | `dir tests\test_*.py` |
| **4. Test Results** | Verified 223-test pass summary with environment header | Complete | [`docs/test_results.txt`](test_results.txt) |
| **5. Screenshots / Output Evidence** | Screenshot guide with 10 exact terminal commands and captured stdout/stderr outputs | Complete | [`docs/screenshots/README.md`](screenshots/README.md)<br>[`docs/demo_outputs/`](demo_outputs/) |
| **6. Final Report Checklist** | Academic chapter mapping and content breakdown | Complete | [`docs/report_and_presentation_checklist.md`](report_and_presentation_checklist.md) |
| **7. Presentation Structure** | 12-slide comprehensive presentation outline with slide-by-slide speaker notes | Complete | Section 3 of this document |
| **8. User Instructions** | Complete setup, installation, CLI flags, language reference, and troubleshooting guide | Complete | [`README.md`](../README.md)<br>[`docs/demo.md`](demo.md) |

### Part B: Review 3 Evaluation Criteria Mapping

| Review 3 Evaluation Criterion | Weight / Focus | How Addressed in This Project | Concrete Supporting Artifact |
|-------------------------------|----------------|-------------------------------|------------------------------|
| **1. Project Completion** | 100% of pipeline working | All 6 compiler stages (Lexer $\to$ Parser $\to$ Semantic $\to$ IR $\to$ Optimizer $\to$ Executor) fully implemented and integrated. | [`src/ds_pipeline_dsl/cli.py`](../src/ds_pipeline_dsl/cli.py)<br>[`docs/demo_outputs/01_valid_basic_all_stages.txt`](demo_outputs/01_valid_basic_all_stages.txt) |
| **2. Functional Correctness** | Correct language processing and error reporting | Correct parsing of all 8 statement types, precise line-numbered syntax/semantic errors, zero false positives. | [`docs/demo_outputs/03_lexical_error.txt`](demo_outputs/03_lexical_error.txt) through [`06_semantic_split_total_over_100.txt`](demo_outputs/06_semantic_split_total_over_100.txt) |
| **3. Technical Complexity** | Depth of compiler concepts | EBNF grammar, recursive-descent LL(1) parsing, symbol table tracking, flat IR lowering, multi-pass IR optimizer, symbolic tracer. | [`docs/grammar.md`](grammar.md)<br>[`docs/architecture.md`](architecture.md)<br>[`src/ds_pipeline_dsl/optimizer.py`](../src/ds_pipeline_dsl/optimizer.py) |
| **4. Compiler Integration** | Clean phase transitions | Every phase accepts the output of the predecessor without back-coupling; intermediate representations can be independently inspected. | `--tokens`, `--ast`, `--ir`, `--optimized-ir`, `--trace` CLI flags |
| **5. Innovation & Usability** | Domain-specific value | Prevents common data science errors (e.g., data leakage, train-before-split, invalid splits) statically without running slow ML jobs. | 21 domain semantic rules in [`src/ds_pipeline_dsl/semantic.py`](../src/ds_pipeline_dsl/semantic.py) |
| **6. Code Quality** | Clean code, modularity, type hints | Standard Python package, dataclasses for AST and IR, comprehensive docstrings, zero circular dependencies, zero global state. | PEP 8 compliant, 100% modular code in `src/ds_pipeline_dsl/` |
| **7. Testing Rigor** | Coverage, edge cases, error tests | 223 automated unit and end-to-end tests covering valid pipelines, syntax errors, all 21 semantic rules, and optimizer passes. | `tests/` directory (223 passed in $<0.3\text{ s}$) |
| **8. Demonstration** | Live execution and clarity | 10 scripted demo scenarios with step-by-step speaker cues and expected outputs. | [`docs/demo.md`](demo.md)<br>[`docs/demo_outputs/`](demo_outputs/) |
| **9. Documentation** | Completeness, clarity, diagrams | Extensive README, EBNF grammar specification, architecture document with Mermaid diagrams, benchmark analysis. | [`README.md`](../README.md), [`docs/grammar.md`](grammar.md), [`docs/architecture.md`](architecture.md) |
| **10. Viva Defense** | Conceptual grasp and defense | Viva quick reference covering compiler theory locations, optimizer safety proof, and worked walkthrough of adding statements. | [`docs/demo.md`](demo.md) (Viva Quick Reference Section) |

---

## 3. Suggested 10–12 Slide Presentation Outline

This presentation is structured for a 10–15 minute slide presentation followed by a 5-minute live demo and Q&A.

```
+-----------------------------------------------------------------------------------------+
| Slide 1: Title & Overview                                                               |
| Slide 2: Motivation & The Data Science Problem                                          |
| Slide 3: Language Design & Grammar Specification                                        |
| Slide 4: Compiler Architecture & Phase Pipeline                                         |
| Slide 5: Lexical & Syntax Analysis (Recursive Descent)                                  |
| Slide 6: Semantic Analysis & Symbol Table State Machine                                 |
| Slide 7: Intermediate Representation (IR) Lowering                                      |
| Slide 8: Multi-Pass IR Optimizer & Formal Safety Argument                               |
| Slide 9: Symbolic Execution Engine & User Interface (CLI)                               |
| Slide 10: Experimental Evaluation: Testing & Performance Benchmarks                     |
| Slide 11: Live Demonstration Highlights                                                 |
| Slide 12: Conclusion & Future Enhancements                                             |
+-----------------------------------------------------------------------------------------+
```

### Slide 1: Title & Overview
- **Title**: *Data Science Pipeline DSL: A Domain-Specific Compiler Front-End and Symbolic Executor*
- **Subtitle**: Automated Compile-Time Verification and Optimization of Machine Learning Workflows
- **Presenter**: Sinchana B Kurkuri
- **Course**: Compiler Design Capstone Project
- **Key Takeaway**: A formal compiler front-end that detects pipeline defects at compile-time in under 1 millisecond before costly training runs.

### Slide 2: Motivation & Problem Statement
- **The Problem**: Machine learning workflows written in imperative Python/Jupyter scripts suffer from:
  - Runtime crashes after hours of execution due to simple typo in column names or missing splits.
  - Data leakage (fitting transformers on test data or selecting columns inconsistently).
  - Silent errors: training models on unsplit data, evaluating wrong models, or redundant data loading.
- **The Solution**: A declarative domain-specific language (DSL) that encodes data science operations as first-class linguistic constructs with rigorous compile-time type, order, and invariant checking.

### Slide 3: Language Design & Grammar Specification
- **Declarative Simplicity**: 8 purpose-built statements: `pipeline`, `load`, `clean`, `select`, `drop`, `split`, `train`, `evaluate`.
- **Formal Grammar**: Deterministic EBNF with LL(1) single-token lookahead.
- **Lexical Highlights**:
  - Contextual identifier handling (`train` permitted as split partition identifier: `split train=80%`).
  - Strict string literal termination and C-style line comments (`//`).
  - Whitespace-insensitive with CRLF (`\r\n`) and LF (`\n`) cross-platform support.

### Slide 4: Compiler Architecture & Phase Pipeline
- **System Architecture Diagram**:
  - Source `.pipe` $\to$ Lexer $\to$ Tokens $\to$ Recursive-Descent Parser $\to$ AST $\to$ Semantic Analyzer (SymbolTable) $\to$ IR Lowerer $\to$ 4-Pass Optimizer $\to$ Symbolic Executor $\to$ CLI.
- **Design Decoupling**: Complete separation of front-end syntax parsing from intermediate representation and execution backend.
- **Diagnostic Ergonomics**: Single-line, human-readable error messages with precise line numbers and zero raw stack traces.

### Slide 5: Lexical & Syntax Analysis
- **Lexical Analyzer (`lexer.py`)**:
  - Regex-based tokenization with 16 distinct token classes.
  - Rejects invalid characters with line-numbered `LexicalError`.
- **Recursive-Descent Parser (`parser.py`)**:
  - Predictive parsing using `peek()`, `advance()`, and `expect()`.
  - Builds strongly typed dataclass AST (`ast_nodes.py`).
  - Enforces mandatory statement ordering (pipeline declaration must be first; trailing tokens rejected).

### Slide 6: Semantic Analysis & Symbol Table State Machine
- **Symbol Table (`SymbolTable`)**:
  - Tracks compile-time state: `dataset_loaded`, `active_columns`, `dropped_columns`, `splits`, `models`, `evaluations`, and `statements_seen`.
- **21 Semantic Validation Rules**:
  - **Dataset Rules**: Exactly one `load` per pipeline; no preprocessing before `load`.
  - **Column Consistency**: Cannot drop or select unselected/non-existent columns; cannot both drop and select overlapping columns.
  - **Data Leakage & Splitting**: Split percentages must sum to $\le 100\%$; cannot train before split.
  - **Model Integrity**: Unique model names; cannot evaluate untrained models; split referenced in evaluate must exist.

### Slide 7: Intermediate Representation (IR) Lowering
- **IR Architecture (`ir.py`)**:
  - Linear 3-address style instruction stream: `IRInstruction(op, args)`.
  - 7 discrete opcodes: `OP_LOAD`, `OP_CLEAN`, `OP_SELECT`, `OP_DROP`, `OP_SPLIT`, `OP_TRAIN`, `OP_EVAL`.
- **Benefits**:
  - Normalizes syntactic variations into standardized, machine-friendly instruction tuples.
  - Simplifies subsequent optimization passes and abstracts the back-end execution engine.

### Slide 8: Multi-Pass IR Optimizer & Formal Safety Argument
- **4 Sequential Optimization Passes (`optimizer.py`)**:
  1. *Unreachable Code Elimination*: Strips all instructions following the final `OP_EVAL`.
  2. *Dead Training Elimination*: Removes `OP_TRAIN` instructions for models that are never evaluated.
  3. *Consecutive Drop Merging*: Combines consecutive `OP_DROP` instructions into a unified column set.
  4. *Consecutive Duplicate Collapsing*: Collapses adjacent duplicate `OP_CLEAN` or `OP_SELECT` operations if both `op` and `args` match.
- **Safety Guarantee**:
  - Pass 1 preserves all observable output because evaluation is the sole externally visible effect.
  - Pass 2 is safe because training an un-evaluated model produces no observable trace or side effect.
  - Passes 3 & 4 are idempotent transformations preserving exact symbolic state at evaluation time.

### Slide 9: Symbolic Execution Engine & User Interface (CLI)
- **Symbolic Execution (`executor.py`)**:
  - Simulates pipeline execution order without requiring physical CSV files or running heavy ML algorithms.
  - Produces structured, human-readable execution traces showing dataset loading, column filtering, split allocations, and model evaluations.
- **CLI Ergonomics (`cli.py`)**:
  - Independent stage inspection: `--tokens`, `--ast`, `--ir`, `--optimized-ir`, `--trace`.
  - Default runs all stages sequentially.
  - Clean exit codes: `0` on compilation success, `1` on lexical/syntax/semantic/I-O failure.

### Slide 10: Experimental Evaluation: Testing & Performance
- **Automated Test Suite (`tests/`)**:
  - 11 test modules, **223 unit and integration tests** passing with 100% success rate.
  - Dedicated tests for every lexical token, grammar production, all 21 semantic rules, and optimizer transformations.
- **Performance Benchmark (`benchmarks/benchmark.py`)**:
  - Sub-millisecond latency: **0.08 ms** to **0.67 ms** total compilation time across small to large pipelines.
  - Linear scaling: $O(N)$ time complexity with throughput exceeding **14,000 lines/second**.
  - Zero memory accumulation across runs.

### Slide 11: Live Demonstration Highlights
- Brief summary of the 10 demonstration scenarios:
  1. Valid standard pipeline with full compiler flow.
  2. Feature exclusion via `drop` statement.
  3. Lexical error diagnostic (illegal character).
  4. Syntax error diagnostic (missing keyword).
  5. Semantic violation (training before split).
  6. Semantic violation (split percentage exceeding 100%).
  7. Optimizer before-and-after inspection showing dead training elimination and duplicate collapsing.
  8. Multi-model pipeline evaluation.
  9. Instantaneous pytest test suite execution (223 tests).
  10. Performance benchmark throughput verification.

### Slide 12: Conclusion & Future Work
- **Summary of Achievements**:
  - Complete, modular, production-ready compiler front-end for data science pipelines.
  - Static detection of data leakage, ordering violations, and configuration errors before execution.
  - Provably safe IR optimizations reducing redundant pipeline compute.
- **Future Enhancements**:
  - Concrete execution engine (code generation targeting PySpark or Scikit-Learn).
  - Allowed-value type checking for cleaner strategies and training algorithms.
  - Multi-pipeline workflow scripts and warning severity levels.

---

## 4. Deferred Scope & Future Enhancements

The following features were intentionally deferred from the core front-end scope to maintain strict boundary constraints and ensure $100\%$ verification of the core compiler pipeline. They represent immediate candidates for future research and development:

1. **Allowed-Value Strategy and Algorithm Validation**:
   - *Current Design*: Clean strategies (`missing_values`, `outliers`) and train algorithms (`random_forest`, `decision_tree`) are free identifiers to keep the compiler extensible without coupling it to specific ML libraries.
   - *Enhancement*: Introduce an optional enumeration or pluggable schema defining valid cleaning algorithms, valid model names, and mandatory hyperparameters per model type.
2. **Multi-Pipeline Programs**:
   - *Current Design*: Exactly one `pipeline <name> { ... }` block per `.pipe` source file.
   - *Enhancement*: Permit multiple pipeline declarations in a single source file, with cross-pipeline dependency graphs (e.g., pipeline $B$ consuming the transformed output of pipeline $A$).
3. **Multi-Error Recovery and Diagnostic Aggregation**:
   - *Current Design*: Fail-fast compiler that halts at the very first lexical, syntax, or semantic error to prevent cascading confusing messages.
   - *Enhancement*: Introduce panic-mode or statement-level synchronizing tokens (e.g., synchronizing on statement boundaries or newline) to collect and report multiple syntax or semantic errors in a single compiler pass.
4. **Compiler Warning Severities**:
   - *Current Design*: Binary outcome: either the pipeline passes all checks or it raises a fatal error.
   - *Enhancement*: Introduce a warning channel for non-fatal code smells, such as:
     - Model trained but never evaluated (warning when optimizer removes it).
     - Splitting dataset where validation set is $<10\%$ or test set is absent.
     - Redundant column operations that were collapsed.
5. **Additional Pipeline Statements**:
   - *Optional `scale` statement*: e.g., `scale standard using [col1, col2];`
   - *Feature engineering statements*: e.g., `encode onehot using [cat_col];` or `impute median using [num_col];`
6. **Target Code Generation Backends**:
   - *Target 1*: Generate standalone, executable Python scripts using Pandas, NumPy, and Scikit-Learn.
   - *Target 2*: Lower the optimized IR to Apache Airflow DAG definitions or Kubeflow pipeline YAMLs.
