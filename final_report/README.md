# Final project report build

The final deliverables are `Final_Report.docx` and `Final_Report.pdf`. Supporting scripts, raw evidence, diagrams, compliance audit, claims ledger and student actions are stored in this directory. Existing compiler, dashboard, tests and documentation are not build outputs.

## Rebuild on this Windows machine

Microsoft Word is installed on this machine. The verified build uses the bundled report Python and the existing project Python, which already has pytest and Streamlit. Run this single PowerShell command from any directory:

```powershell
& 'C:\Users\sinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\sinch\Desktop\CD Project\final_report\build_report.py' --project-python 'C:\Users\sinch\AppData\Local\Python\pythoncore-3.14-64\python.exe'
```

This collects fresh tests and example outputs, verifies source preservation, reads the saved benchmark, draws the figures, builds the DOCX, updates Word fields, exports the PDF, renders page PNGs and runs structural/content checks. It does not run Git mutations or start the dashboard server. Test execution disables bytecode and pytest cache writes. An existing benchmark is copied without rerunning or overwriting it.

To rebuild the document using the previously captured evidence, append `--reuse-evidence`. This is useful for formatting changes, but does not refresh project results. `--skip-render` omits the page PNG generation; visual review remains necessary before delivery after a content or layout change.

## Requirements and portability

The report Python needs the packages listed in `requirements-report.txt`. The separate project interpreter needs the existing package, pytest and, for this project's dashboard tests, Streamlit. No report dependencies were added to the project configuration.

For a separate report environment, use an explicit report interpreter path to install `final_report/requirements-report.txt`, then invoke `build_report.py --project-python <existing-project-interpreter>`. Installing report packages is not necessary in the bundled runtime used above.

The default input paths are relative to this directory: Phase reports under `../docs/`, the repository under `../`, and the supplied manual PDF in the repository's parent directory. Change `MANUAL` in `collect_evidence.py` if relocating the supplied manual. The fonts use the standard Windows Arial and Consolas files, with a Pillow fallback.

PDF and field update use Microsoft Word COM on Windows. Word opens invisibly and closes its own automation instance after export. A configured `REPORT_SOFFICE` executable is a fallback when Word export is unavailable. Poppler is resolved from the bundled runtime or `PATH`. The packaged DOCX renderer is attempted and its diagnostics retained; this machine lacks LibreOffice, so the delivered PDF and PNGs use Word export followed by Poppler. A machine without either converter cannot regenerate the delivered PDF or populated fields automatically.

## Evidence and verification

- `evidence/pytest_v.txt`, `test_counts.json` and `pytest_command.json`: fresh verbose suite output, exact invocation and derived counts.
- `evidence/cli/` and `examples.json`: every supplied example's output, diagnostics and exit status.
- `evidence/pipeline_data.json`: actual stage structures, equivalence records, all diagnostic patterns, and executed triggers for every semantic raise site.
- `evidence/performance.md` and `benchmark_parsed.json`: the saved benchmark, retaining every original numeric string. Charts use these values only.
- `evidence/document_manifest.json`: source-verbatim snippets, captions and headings.
- `evidence/claims_check.json`, `toc_page_check.json` and `verification.json`: content, cached TOC page comparisons and structural results.
- `rendered/page-*.png`: rendered final PDF pages for visual inspection; `visual_review.md` records the review.
- `manual_compliance.md`: manual rules, exact chapter list, Review 3 weights and completion mapping.
- `report_todo.md`: student decisions and administrative work outside this report task.

## Preservation boundary

The repository already had tracked modifications in README.md and docs/performance.md, plus untracked dashboard/configuration/test files, before report work began. Those changes were preserved. During this task, docs/performance.md also changed outside these report scripts; the initial and latest captures and their hashes are retained in `evidence/performance_initial_snapshot.md` and `evidence/observed_external_changes.json`. The report uses the latest captured benchmark. Consequently, a clean overall Git status and empty overall Git diff cannot truthfully be asserted.

The baseline manifest contains 76 existing files. Subsequent checks accept only the explicitly recorded benchmark change and fail on any other changed baseline hash. See `evidence/preservation_check.json`, `git_status_before.txt` and the final status evidence. No commit, push, staging, stash, reset or checkout was performed.

## Optional genuine screenshots

Place genuine PNG captures in `assets/screenshots/` using the filenames and subjects in `report_todo.md`, then rebuild. Existing PNGs are embedded automatically with captions. When none exists, the report supplies real compiler output and no empty screenshot section.
