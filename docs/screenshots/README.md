# Screenshot Capture Guide

This directory is reserved for visual evidence and screenshots of terminal runs for the final project report, presentation slides, and demonstration evaluation.

> [!NOTE]
> Per project guidelines, screenshots must be captured directly from live terminal runs by the presenter/author. No mock or fabricated images are placed in this repository.

---

## Recommended Screenshot Settings

To ensure high readability and presentation quality for thesis reports and projection slides:
- **Terminal Theme**: High contrast dark theme (e.g., One Dark, Dracula, or VS Code Dark Modern) or clean white background for printed documents.
- **Font**: Monospace with programming ligatures (e.g., Cascadia Code, JetBrains Mono, or Fira Code), size 14pt–16pt.
- **Window Sizing**: ~100–120 columns wide, avoiding line wraps on pipeline traces and AST trees.
- **Prompt Clarity**: Keep the command prompt clean (e.g., `PS C:\CD Project> ` or `$ `).

---

## Screenshot Inventory

The following 10 screenshots correspond directly to the automated demo suite documented in [`docs/demo.md`](../demo.md) and captured in [`docs/demo_outputs/`](../demo_outputs/):

| # | Suggested Filename | Exact Command to Run | What to Highlight in Screenshot | Corresponding Output File |
|---|--------------------|----------------------|---------------------------------|---------------------------|
| 1 | `01_valid_basic_all_stages.png` | `python -m ds_pipeline_dsl.cli examples/valid_basic.pipe` | Full 5-stage compilation flow: TOKENS, AST, IR, OPTIMIZED IR, and symbolic TRACE | [`docs/demo_outputs/01_valid_basic_all_stages.txt`](../demo_outputs/01_valid_basic_all_stages.txt) |
| 2 | `02_valid_drop_all_stages.png` | `python -m ds_pipeline_dsl.cli examples/valid_drop.pipe` | Stage 2 `drop` statement lowered to `OP_DROP` and simulated drop in symbolic TRACE | [`docs/demo_outputs/02_valid_drop_all_stages.txt`](../demo_outputs/02_valid_drop_all_stages.txt) |
| 3 | `03_lexical_error.png` | `python -m ds_pipeline_dsl.cli examples/invalid_lexical_error.pipe` | Clean lexical error message (`Lexical error at line 3: Unexpected character '@'`) and exit code 1 | [`docs/demo_outputs/03_lexical_error.txt`](../demo_outputs/03_lexical_error.txt) |
| 4 | `04_syntax_error.png` | `python -m ds_pipeline_dsl.cli examples/invalid_syntax_error.pipe` | Recursive-descent parser syntax error (`Syntax error at line 3: Expected 'using' after clean strategy`) | [`docs/demo_outputs/04_syntax_error.txt`](../demo_outputs/04_syntax_error.txt) |
| 5 | `05_semantic_train_before_split.png` | `python -m ds_pipeline_dsl.cli examples/invalid_train_before_split.pipe` | Symbol table semantic check (`Semantic error at line 5: train statement requires split statement before it`) | [`docs/demo_outputs/05_semantic_train_before_split.txt`](../demo_outputs/05_semantic_train_before_split.txt) |
| 6 | `06_semantic_split_total_over_100.png` | `python -m ds_pipeline_dsl.cli examples/invalid_split_total_over_100.pipe` | Multi-split validation error (`Semantic error at line 5: Cumulative split percentage exceeds 100%`) | [`docs/demo_outputs/06_semantic_split_total_over_100.txt`](../demo_outputs/06_semantic_split_total_over_100.txt) |
| 7 | `07_optimizer_before_after.png` | `python -m ds_pipeline_dsl.cli examples/optimizer_demo.pipe --ir --optimized-ir` | Side-by-side or stacked view showing dead code removal after evaluate and consecutive duplicate collapse | [`docs/demo_outputs/07_optimizer_before_after.txt`](../demo_outputs/07_optimizer_before_after.txt) |
| 8 | `08_complex_multi_model_trace.png` | `python -m ds_pipeline_dsl.cli examples/complex_multi_model.pipe --trace` | Multi-model evaluation trace for two models (`rf_model` and `gb_model`) on different splits | [`docs/demo_outputs/08_complex_multi_model_trace.txt`](../demo_outputs/08_complex_multi_model_trace.txt) |
| 9 | `09_pytest_suite.png` | `python -m pytest -q` | Fast test suite execution banner showing 223 passed tests with zero regressions | [`docs/demo_outputs/09_pytest.txt`](../demo_outputs/09_pytest.txt) |
| 10 | `10_benchmark_throughput.png` | `python benchmarks/benchmark.py` | Benchmark summary table showing sub-millisecond compile latency and ~14,000+ lines/sec throughput | [`docs/demo_outputs/10_benchmark_table.txt`](../demo_outputs/10_benchmark_table.txt) |

---

## Capture Procedure

1. Open PowerShell or Terminal at the repository root (`c:\Users\sinch\Desktop\CD Project`).
2. Run each command listed above.
3. Use your OS screenshot utility (e.g., Windows `Win + Shift + S`, macOS `Cmd + Shift + 4`, or Linux `flameshot`).
4. Save the screenshot with the corresponding filename in this folder (`docs/screenshots/`).
5. Reference these screenshots in the final report (Chapter 9: Testing & Results) and presentation slides.
