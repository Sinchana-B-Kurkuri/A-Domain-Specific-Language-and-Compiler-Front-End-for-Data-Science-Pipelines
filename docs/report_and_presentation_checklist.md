# Academic report and presentation checklist

This checklist maps the completed project to the course manual's documentation structure. The preserved [final report](../final_report/Final_Report.pdf) and its [manual compliance audit](../final_report/manual_compliance.md) remain the academic deliverables. [Current verification](verification.md) records the later portfolio cleanup and one additional CLI test.

## Required report structure

| Manual chapter/topic | Project evidence |
|---|---|
| 1 Introduction | [README motivation and objectives](../README.md#why-this-project) |
| 2 Problem Statement | Source dependency validation and symbolic scope in the [architecture](architecture.md) |
| 3 Objectives | Original objectives and final status in the final report; implementation and tests linked from the README |
| 4 Literature Survey or Background Study | Final report Chapter 4 and bibliography |
| 5 System Design | [Architecture and data flow](architecture.md#data-flow) |
| 6 Methodology | Phase reports, Git history and regression discussion in final report Chapter 6 |
| 7 Compiler Design Concepts Used | [Grammar](grammar.md), [symbol table](architecture.md#symbol-table-and-validation), [IR and optimization](architecture.md#intermediate-representation) |
| 8 Implementation | [Compiler source](../src/ds_pipeline_dsl/), [dashboard](../dashboard/), [benchmark](../benchmarks/benchmark.py) |
| 9 Testing and Results | [Full test log](test_results.txt), [verification](verification.md), [saved benchmark](performance.md), [captured CLI outputs](demo_outputs/) |
| 10 Conclusion | Achievements and explicit scope limits in the final report |
| 11 Future Enhancements | [README limitations and next steps](../README.md#limitations-and-next-steps) and final report Chapter 11 |
| References | Final report bibliography; official deployment reference in [deployment guide](deployment.md) |
| Appendix | Final report appendices A–F: grammar, diagnostics, source, examples, reproduction and evolution |

## Phase 3 deliverables

- Working compiler, CLI and interactive dashboard.
- [Source](../src/ds_pipeline_dsl/) and [tests](../tests/).
- All [example programs](../examples/), captured outputs and current verified test results.
- Genuine [dashboard screenshots](screenshots/README.md) and terminal output evidence.
- Preserved final DOCX/PDF and earlier academic reports/review slides.
- [User instructions](deployment.md) and [five-minute demonstration](demo.md).
- Final Review 3 slides, live presentation and viva remain student responsibilities; an existing deck is not proof that those activities occurred.

## Detailed Review 3 allocation

| Criterion | Marks | Evidence |
|---|---:|---|
| Project completion | 6 | Integrated stages and objective status in final report |
| Functional correctness | 6 | Current tests and example outcomes |
| Technical complexity | 5 | Grammar, state constraints, IR and optimizer |
| Compiler concept integration | 4 | Full compilation flow |
| Testing | 4 | Unit, boundary, integration, equivalence and sensitivity cases |
| Demonstration | 4 | Live dashboard/CLI walkthrough |
| Viva | 4 | Explanation of implementation and limitations |
| Documentation | 2 | Report, current docs and reproduction instructions |
| Total | 35 | Detailed manual allocation |

The manual's summary and detailed allocations disagree; the original compliance audit records that ambiguity. Confirm administrative requirements and prior topic approval with the faculty rather than inferring them from project files.

## Claims to use accurately

- Current audit: 268 passing tests across 12 test modules, including 44 dashboard cases; the preserved report's earlier 267-test result is historical.
- One semantic traversal, ten SymbolTable fields and 21 explicit semantic raise sites. There are no `evaluations` or `statements_seen` fields.
- One pipeline declaration and seven executable body statement forms.
- Four ordered optimizer passes, with transformation safety defined by evaluation records.
- Saved benchmark sizes are 13, 99, 999 and 9999 statements; total times are 0.098, 0.671, 6.952 and 73.560 ms.
- No real dataset processing, numeric accuracy, memory-profile claim, universal strict-linear proof or preemptive benchmark timeout.

Historical Phase 1/2 reports and decks are retained as historical material. Use [report_todo.md](../final_report/report_todo.md) for student-specific submission and acknowledgement decisions; it is not a list of implemented compiler features.
