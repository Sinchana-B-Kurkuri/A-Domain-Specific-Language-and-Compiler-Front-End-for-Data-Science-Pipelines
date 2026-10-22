# Five-minute project demonstration

Prepare the dashboard, VS Code and the final PDF before the review. Keep the Streamlit server running and load the examples in advance. The objective is to demonstrate a compiler with observable intermediate representations and tested transformations. State the symbolic execution boundary at the start.

## Timed sequence

| Time | Show | Say |
|---|---|---|
| 0:00–0:30 | Dashboard Overview | “This project is a compiler front-end for a data science pipeline language. It checks declarations and dependencies, lowers them to an IR, optimizes that IR and produces a symbolic trace. It does not read datasets or train real models.” |
| 0:30–1:30 | Playground: compile `valid_drop.pipe`; show source, Tokens, AST and Semantic Analysis | “The lexer records source coordinates. The recursive-descent parser builds statement nodes. The analyzer tracks loaded data, columns, splits and models, rejecting invalid relationships before execution.” |
| 1:30–2:05 | Compile `invalid_train_before_split.pipe`; show error and skipped stages | “The syntax is valid, but the model has no earlier training split. Semantic analysis reports the source line and prevents lowering and execution. Lexical and syntax failures are separate categories.” |
| 2:05–3:10 | Compile `optimizer_demo.pipe`; open Optimization, compare IR and notes | “Eleven instructions become seven: the compiler trims after the last evaluation, removes an unused training declaration, merges adjacent drops and collapses a repeated clean. Tests compare evaluation records, not identical full trace text.” |
| 3:10–3:45 | VS Code: `optimizer.py` pass ordering, then `tests/helpers.py` record snapshot | “The test oracle retains model and algorithm plus separate training and evaluation states. This detects lost later evaluations and changes to relevant pipeline state. Cleaning idempotence is an assumption of this symbolic model.” |
| 3:45–4:15 | Architecture: diagram, expand one stage | “The CLI and UI use the same modules. Completed stages stay inspectable after errors. Stage details show input/output and implementation references.” |
| 4:15–4:45 | Performance: saved table and IR-size chart | “These are saved measurements for 13, 99, 999 and 9999 actual statements. The largest row is 73.560 ms and reduces IR from 9999 to 6000. This is one machine and one synthetic template, not a universal complexity proof.” |
| 4:45–5:00 | `docs/test_results.txt`, then final report contents | “The current suite has 268 passing tests, including 44 dashboard cases. All 20 examples were exercised. The report documents the language, safety arguments, results and limitations.” |

If questions interrupt, shorten the token/AST browsing and architecture explanation. Do not run installations, the whole test suite or a fresh benchmark within the five-minute presentation; keep captured outputs available.

## Code tabs to keep open

- [lexer.py](../src/ds_pipeline_dsl/lexer.py): `TOKEN_SPEC`, `Token`, `tokenize`.
- [parser.py](../src/ds_pipeline_dsl/parser.py): `expect`, `parse_pipeline`, statement branches.
- [semantic.py](../src/ds_pipeline_dsl/semantic.py): `SymbolTable`, dependency and ordering checks.
- [ir.py](../src/ds_pipeline_dsl/ir.py): `IRInstruction`, statement lowering.
- [optimizer.py](../src/ds_pipeline_dsl/optimizer.py): pass order, last-evaluation boundary and duplicate comparison.
- [tests/helpers.py](../tests/helpers.py) and [test_optimizer.py](../tests/test_optimizer.py): evaluation-state oracle and regression cases.

Keep the [final PDF](../final_report/Final_Report.pdf) at Chapter 7 for concepts and Chapter 9 for results. It is the preserved academic snapshot; the newer portfolio audit adds a CLI encoding regression, so current verification has one additional test.

## Useful follow-up answers

**Why recursive descent?** Each body statement begins with a distinct keyword. Commas select list continuations and a closing brace ends the statement sequence, so one-token lookahead suffices for this grammar.

**Why the last evaluation?** A later train/evaluate pair is legal. Trimming after the first evaluation would lose observable results.

**What does “accuracy trace” mean?** It is an existing string label. There is no numeric score or real ML computation.

**Is an empty pipeline legal?** Yes. Loads are required by dependent operations; an empty body has no final mandatory-load check.

**Is performance always linear?** No universal bound is claimed. The saved template scales approximately linearly, but split-total summation and column-list work depend on input shape.

**Do guards interrupt a slow benchmark?** No. They check projected cost between sizes and reduce repetitions after a slow repetition finishes.

## CLI fallback

```powershell
python -m ds_pipeline_dsl.cli examples/valid_drop.pipe --trace
python -m ds_pipeline_dsl.cli examples/invalid_train_before_split.pipe --trace
python -m ds_pipeline_dsl.cli examples/optimizer_demo.pipe --ir --optimized-ir
python -m ds_pipeline_dsl.cli examples/complex_multi_model.pipe --trace
```

The invalid command intentionally exits 1. [Captured outputs](demo_outputs/) and the [test log](test_results.txt) are available if the UI or network is unavailable. Follow [deployment troubleshooting](deployment.md) for a refused local connection.
