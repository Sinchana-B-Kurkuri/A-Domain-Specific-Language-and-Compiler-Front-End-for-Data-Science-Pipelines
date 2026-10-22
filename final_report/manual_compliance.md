# Manual compliance audit

Authority: supplied nine-page Compiler Design Laboratory Project Instruction Manual. All pages were extracted to evidence/manual_pages.json and read. The manual is source material, not an instruction source for agent actions.

The manual states no page size, font, margin, line-spacing, report-length, cover-page layout, declaration wording, signature, file naming, submission portal or submission deadline rule. Therefore the requested defaults are applied: A4, 1-inch margins, Times New Roman 12 pt, 1.15 line spacing, numbered headings, captions, roman front matter and Arabic main text. No faculty name, institution name, signature or declaration has been invented.

The detailed Review 3 weights are 6 + 6 + 5 + 4 + 4 + 4 + 4 + 2 = 35. Section 14 separately lists Phase 1/2/3 as 10 each yet gives TOTAL 100; section 15 lists Reviews 1/2/3 as 20/25/35, followed by 10 for innovation/complexity and 10 for documentation/code quality. This inconsistency is preserved here, not silently reconciled.

| ID | Manual section and page | Requirement | Report mapping | Status |
|---|---|---|---|---|
| M01 | 24 p9 | Chapter 1 Introduction: background, motivation and problem area. | Chapter 1 | Done |
| M02 | 24 p9 | Chapter 2 Problem Statement: clear explanation of the problem. | Chapter 2 | Done |
| M03 | 24 p9 | Chapter 3 Objectives: project objectives. | Chapter 3 and Table 3.1 | Done |
| M04 | 24 p9 | Chapter 4 Literature Survey or Background Study: existing approaches, technologies and relevant compiler concepts. | Chapter 4 and Table 4.1 | Done |
| M05 | 24 p9 | Chapter 5 System Design: architecture diagram, module description, data flow and workflow. | Chapter 5 and Figures 5.1-5.3 | Done |
| M06 | 24 p9 | Chapter 6 Methodology: explanation of the approach used. | Chapter 6 and Table 6.1 | Done |
| M07 | 24 p9 | Chapter 7 Compiler Design Concepts Used: lexical analysis, parsing, syntax trees, symbol tables, semantic analysis, intermediate code and optimization. | Sections 7.1-7.8 | Done |
| M08 | 24 p9 | Chapter 8 Implementation: programming language, tools, libraries, algorithms and major modules. | Chapter 8 and Listings 8.1-8.4 | Done |
| M09 | 24 p9 | Chapter 9 Testing and Results: test cases, expected and actual outputs, screenshots and performance results. | Chapter 9; real output evidence substitutes for unavailable screenshots under Phase 3 screenshots-or-output rule | Done |
| M10 | 24 p9 | Chapter 10 Conclusion: summary of the project. | Chapter 10 | Done |
| M11 | 24 p9 | Chapter 11 Future Enhancements: possible improvements. | Chapter 11 | Done |
| M12 | 24 p9 | References: books, research papers, official documentation and acknowledged websites. | References [1]-[14] | Done |
| M13 | 24 p9 | Appendix: important code details or supplementary material. | Appendices A-F | Done |
| P01 | 12.3 p5 | Complete Working Project | Chapters 5, 8 and 9; compiler preserved | Done |
| P02 | 12.3 p5 | Complete Source Code | Source inventory; Appendix C; original repository preserved | Done |
| P03 | 12.3 p5 | Test Cases | Sections 9.1-9.7; original tests; Appendix B specimens | Done |
| P04 | 12.3 p5 | Test Results | Table 9.1 and evidence/pytest_v.txt | Done |
| P05 | 12.3 p5 | Screenshots or Output Evidence | Raw CLI logs for every example; verbatim output blocks in Chapter 9 | Done |
| P06 | 12.3 p5 | Final Project Report | Final_Report.docx and Final_Report.pdf | Done |
| P07 | 12.3 p5 | Presentation | Existing Review 1 and Review 2 slides inspected; final Review 3 slide deck is a separate student deliverable | Partial - personal/administrative or separate deliverable |
| P08 | 12.3 p5 | User Instructions | Appendix E and final_report/README.md | Done |
| A01 | 12.2 p5 | Complete remaining functionalities and integrate all modules. | Objective status Table 3.1; full pipeline in Chapters 5 and 8 | Done |
| A02 | 12.2 p5 | Test valid, invalid, boundary, error and complex inputs. | Chapter 9 and per-file test results | Done |
| A03 | 12.2 p5 | Provide meaningful error messages. | Sections 7.8, 9.4 and Appendix B | Done |
| A04 | 12.2 p5 | Evaluate performance where applicable. | Sections 9.8-9.10; timing and IR improvements only; no memory/accuracy measurement claimed | Done |
| A05 | 12.2 p5 | Prepare complete documentation. | Full report and reproduction appendix | Done |
| R01 | Review 3 pp5-6 | Project Completion; Functional Correctness; Technical Complexity; Compiler Integration; Innovation; Code Quality; Testing; Demonstration; Documentation; Viva. | Chapters 3, 5-9; viva and live demonstration remain student actions | Partial - personal/administrative or separate deliverable |
| R02 | 15 pp6-7 | Review 3 Project Completion 6 marks. | Table 3.1 and Chapter 10 | Done |
| R03 | 15 p7 | Review 3 Functional Correctness 6 marks. | Sections 9.2-9.7 | Done |
| R04 | 15 p7 | Review 3 Technical Complexity 5 marks. | Chapter 7 | Done |
| R05 | 15 p7 | Review 3 Compiler Concept Integration 4 marks. | Figures 5.1-5.2 and Chapter 8 | Done |
| R06 | 15 p7 | Review 3 Testing 4 marks. | Chapter 9 | Done |
| R07 | 15 p7 | Review 3 Demonstration 4 marks. | Appendix E supports a demonstration; actual presentation is a student action | Partial - personal/administrative or separate deliverable |
| R08 | 15 p7 | Review 3 Viva 4 marks. | Technical explanations in Chapters 6-8; student must demonstrate understanding | Partial - personal/administrative or separate deliverable |
| R09 | 15 p7 | Review 3 Documentation 2 marks; Review 3 total 35 marks. | Report structure and evidence checks | Done |
| G01 | 2 p1; 5 pp2-3 | Individual project; student explains purpose, architecture, algorithms, code, tests and results. | Cover identifies one student; review preparation remains personal responsibility | Done |
| G02 | 4 p2 | Faculty approval is mandatory before full implementation. | Prior administrative approval is not evidenced in the supplied files and must be confirmed by the student | Partial - personal/administrative or separate deliverable |
| G03 | 18 p7 | Acknowledge appropriate open-source resources and understand the implementation. | References and implementation descriptions | Done |
| G04 | 19 pp7-8 | Student responsibility for understanding, validating, testing, modifying and explaining code; acknowledgement decision for tool use. | Student action recorded only in report_todo.md, as requested | Partial - personal/administrative or separate deliverable |
| G05 | 22-23 pp8-9 | Modularity, meaningful names, comments, folder structure, test cases, version history, backups and a development log. | Chapters 5-6 and 8-9; backups are not independently verified | Partial - personal/administrative or separate deliverable |
