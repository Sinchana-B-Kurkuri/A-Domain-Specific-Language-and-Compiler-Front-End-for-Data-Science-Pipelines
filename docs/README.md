# Project documentation

All final academic deliverables are kept in this folder. The final report covers the complete implemented project.

| Phase | Report | Review presentation |
|---|---|---|
| Phase 1 | [Phase1.docx](Phase1.docx) | [Review 1](Review1_Compiler_Design_Pipeline_DSL.pptx) |
| Phase 2 | [Phase2.docx](Phase2.docx) | [Review 2](Review2_Compiler_Design_Pipeline_DSL.pptx) |
| Phase 3 and complete project | [Phase3.docx](Phase3.docx) | [Review 3](Review3_Compiler_Design_Pipeline_DSL.pptx) |

## Run and explore

- [Open the live dashboard](https://ds-pipeline-compiler.streamlit.app/).
- [Local setup, deployment and troubleshooting](deployment.md).
- [Compiler architecture](architecture.md) and [language grammar](grammar.md).
- [Five-minute demonstration](demo.md) and [CLI examples](demo_outputs/).
- [Dashboard screenshots](screenshots/README.md).

## Results and historical evidence

- [test_results.txt](test_results.txt) records the current test suite. The dashboard reads this file for its saved passing-test count.
- [performance.md](performance.md) contains the saved 23 October 2026 benchmark displayed by the dashboard. Running `python benchmarks/benchmark.py` replaces it.
- The academic report records an earlier 267-test run and the 22 October 2026 benchmark. These historical results remain unchanged; the current suite has 268 tests.
- [evidence/pytest_v.txt](evidence/pytest_v.txt), [evidence/performance.md](evidence/performance.md) and [evidence/pipeline_data.json](evidence/pipeline_data.json) retain the original test log, benchmark and diagnostic specimens referenced in the complete report.

Phase 1 and Phase 2 materials describe their development stages. Use the source, tests, root README and technical documentation for the current implementation.
