# GitHub presentation

## About fields

**Description** (200 characters):

```text
Python compiler front-end for a data science pipeline DSL, with lexical and semantic validation, a four-pass IR optimizer, symbolic execution, a Streamlit playground, and tested transformation safety.
```

**Website**:

```text
https://ds-pipeline-compiler.streamlit.app/
```

**Topics**:

```text
compiler-design domain-specific-language python streamlit code-optimization lexical-analysis recursive-descent-parser semantic-analysis abstract-syntax-tree intermediate-representation
```

No installed/authenticated GitHub CLI or token-backed GitHub connector was available. Remote metadata was read through the public API; no remote write was attempted. At audit time the repository had its earlier description, no website value and no topics.

## Manual update

1. Open the [repository](https://github.com/Sinchana-B-Kurkuri/A-Domain-Specific-Language-and-Compiler-Front-End-for-Data-Science-Pipelines) while signed in as an owner.
2. Click the gear beside **About** on the repository's Code page.
3. Paste the description and website above, add the topics, then save.

If an authenticated GitHub CLI is available on another machine, the equivalent command is:

```powershell
gh repo edit Sinchana-B-Kurkuri/A-Domain-Specific-Language-and-Compiler-Front-End-for-Data-Science-Pipelines --description "Python compiler front-end for a data science pipeline DSL, with lexical and semantic validation, a four-pass IR optimizer, symbolic execution, a Streamlit playground, and tested transformation safety." --homepage "https://ds-pipeline-compiler.streamlit.app/" --add-topic "compiler-design,domain-specific-language,python,streamlit,code-optimization,lexical-analysis,recursive-descent-parser,semantic-analysis,abstract-syntax-tree,intermediate-representation"
```

## Review and publish local changes

These commands are supplied for the owner; the audit did not stage, commit, push or rewrite history.

```powershell
git status --short
git branch --show-current
git diff --check
git diff --stat
git diff -- README.md pyproject.toml requirements-dashboard.txt requirements.txt .gitignore .streamlit/config.toml src/ds_pipeline_dsl/cli.py benchmarks/benchmark.py tests/
python -m pytest -q
```

After reviewing additions and generated-preview deletions:

```powershell
git add README.md pyproject.toml requirements.txt requirements-dashboard.txt .gitignore .streamlit/config.toml src/ds_pipeline_dsl/cli.py benchmarks/benchmark.py tests/test_cli.py tests/test_executor.py tests/test_integration.py tests/test_ir.py tests/test_lexer.py dashboard/app.py docs/ examples/data/README.md final_report/rendered/
git diff --cached --stat
git diff --cached --check
git commit -m "Polish portfolio documentation and verify compiler deployment"
git push origin main
```

The `final_report/rendered/` staging path records deletions of tracked preview images; retained final DOCX/PDF, report sources, figures and evidence are unchanged. Confirm that the current branch is `main` before pushing. Select a project license personally if you intend to grant reuse rights; no license was invented during this audit.
