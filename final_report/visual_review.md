# Final report verification record

Reviewed on 22 October 2026. The delivered PDF contains 62 physical pages: eight front-matter pages and 54 pages numbered from Chapter 1 through Appendix F. The cover suppresses its page number. Front matter uses roman numbering; the main text restarts at 1.

Microsoft Word automation updated the TOC, figure list, table list and caption fields before PDF export. All 90 TOC entries were compared with Word's actual adjusted page numbers, with zero mismatches. The PDF was rendered with Poppler at 110 dpi. The packaged DOCX renderer was also attempted; its log identifies the unavailable LibreOffice executable. The delivered PDF is a native Word export, not a placeholder conversion.

All 62 pages were inspected as original-resolution page-image pairs during the final formatting review. After the last layout refinements, the pages with changed text flow and the updated diagram/chart pages were inspected again. This included the cover, all contents/list pages, every chapter, all ten figures, all appendices, multi-page tables and the landscape benchmark table. No unresolved clipping, overlap, blank page, detached heading or figure-caption issue was found. Long source lines wrap within code blocks; their source characters remain unchanged. The landscape benchmark page retains all 15 columns. Its intentional remaining space avoids reducing the original table to illegible type.

The review corrected the stock Word title border and theme-font overrides, sparse text continuations, an orphaned code-block introduction, narrow table labels, and small diagram labels. Code and actual output use shaded monospace blocks; headings and running headers are black. Repeated table headers, roman/Arabic numbering, A4 page sizes and one-inch margins were checked structurally as well as visually. The prose received a manual consistency and grammar pass.

## Content and execution checks

| Check | Result |
|---|---|
| Fresh full pytest run | 267 passed, 0 failed, 0 skipped |
| Supplied examples executed | 20, including 7 accepted and 13 rejected |
| Recorded benchmark statement sizes | 13, 99, 999 and 9999 |
| Benchmark handling | Copied and parsed; not rerun by the report build |
| Compiler opcodes and optimizer passes | All seven opcodes and all four passes described |
| Semantic raise sites | All 21 exercised by real trigger programs |
| Explicit compiler diagnostic patterns | All 29 checked against report text |
| Source excerpts/listings | All eight matched verbatim against cited source ranges |
| Abstract | 219 words |
| Figures and tables | 10 figures and 25 tables, captioned and referenced |
| Claims ledger | 608 narrative/data entries matched to delivered DOCX text; sources recorded per section |
| Cached TOC page numbers | 90 entries checked, zero mismatches |
| PDF blank pages | None |
| Existing project files | 76 baseline files audited; no unexpected changes |

The ledger's text-matching check establishes that the recorded claims appear in the delivered document. Behavioral verification additionally relies on source inspection, fresh execution, the serialized pipeline evidence, exact diagnostics, snippets and benchmark-cell comparisons; text matching alone is not treated as proof of behavior.

## Preservation and scope limitations

The overall repository was already dirty before report work. README.md and docs/performance.md were modified, and dashboard/configuration/test files were untracked. Those files were not cleaned or reverted. A further change to docs/performance.md was observed during the task outside the report scripts. Both captured versions and exact hashes are retained. The latest captured benchmark is used consistently throughout the report. A clean overall Git status or empty overall diff is therefore not claimed. Final status/diff logs are under evidence/.

No numeric ML accuracy, real dataset execution, memory profile or cross-machine evaluation is claimed. Coverage was not measured because pytest-cov was absent. Genuine dashboard screenshots were unavailable; real compiler outputs satisfy the manual's screenshots-or-output-evidence requirement. Earlier DOCX embedded images were inspected and are historical architecture diagrams, not dashboard screenshots; the final report supplies an updated generated architecture figure.

Faculty approval, institution-specific submission requirements, the final live presentation, viva performance and the student's acknowledgement decision remain personal actions in report_todo.md. No project files were staged, committed or pushed.

Machine-readable checks, final artifact hashes and the reviewed-page list are in evidence/verification.json, evidence/toc_page_check.json, evidence/visual_review.json and evidence/final_artifact_hashes.json. Regeneration after content, screenshot or layout changes requires another visual review.
