# Installation and deployment

## Local setup

From the repository root, use Python 3.12 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dashboard,test]"
python -m pytest -v
python -m streamlit run dashboard/app.py
```

On macOS/Linux, use `source .venv/bin/activate` instead of PowerShell activation. The compiler alone needs only `python -m pip install -e .`. Optional dependencies are declared once in [pyproject.toml](../pyproject.toml): `dashboard` installs Streamlit, while `test` installs pytest. Pandas and the Python graphviz package are Streamlit dependencies; a system Graphviz executable is not needed for `st.graphviz_chart`.

Open [localhost:8501](http://localhost:8501) and keep the server process running. A refused connection usually means no server is listening. If the port is occupied, use `python -m streamlit run dashboard/app.py --server.port 8502` and open [localhost:8502](http://localhost:8502). Ctrl+C stops the server.

If PowerShell blocks activation, activation can be avoided entirely:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dashboard,test]"
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

## Streamlit Community Cloud

- Repository: [project repository](https://github.com/Sinchana-B-Kurkuri/A-Domain-Specific-Language-and-Compiler-Front-End-for-Data-Science-Pipelines)
- Branch: `main`
- Entrypoint: `dashboard/app.py`
- Public URL: [ds-pipeline-compiler.streamlit.app](https://ds-pipeline-compiler.streamlit.app/)
- Dependency entry point: root [requirements.txt](../requirements.txt), which includes [requirements-dashboard.txt](../requirements-dashboard.txt) and installs the local package with its dashboard extra.
- Select a Python version supported by Community Cloud that satisfies the declared Python requirement. Local verification used 3.14.7; the deployed interpreter version was not independently inspected.

Community Cloud recognizes `requirements.txt` in the root or entrypoint directory. A custom `requirements-dashboard.txt` filename alone is not its standard discovery entry point. See the [official dependency guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

The shared [Streamlit config](../.streamlit/config.toml) contains the theme and disables usage statistics. It does not force a host-specific bind address; hosting controls its own server binding. For an explicitly loopback-only local listener, append `--server.address 127.0.0.1`.

Paths to `src`, `examples`, `docs/performance.md` and the logo are derived from `__file__`, not the caller's working directory. The dashboard inserts its sibling `src/` directory into the import path. Deployment also installs the package explicitly. No datasets, API keys, external model services, or secrets are required.

The live deployment was exercised during the audit. Local changes in this polishing pass do not change the deployed app until the user commits/pushes and the deployment updates. See [verification](verification.md) for the tested cases and limits.

## Reproducing results

```powershell
python -m ds_pipeline_dsl.cli examples/valid_basic.pipe
python -m ds_pipeline_dsl.cli examples/invalid_train_before_split.pipe --trace
python -m ds_pipeline_dsl.cli examples/optimizer_demo.pipe --ir --optimized-ir
python -m pytest -v
python benchmarks/benchmark.py
```

The invalid example intentionally exits 1. The benchmark command overwrites `docs/performance.md`; do not run it if preserving the saved dashboard measurements. Audit timings were recorded separately in [verification_results.json](verification_results.json).

The final academic report has its own [build instructions](../final_report/README.md) and report-only dependencies. It is an archival deliverable and was not rebuilt during this audit.

## Secrets and repository hygiene

`.gitignore` excludes environments, caches, build products, editor-local files, `.env` files, `.streamlit/secrets.toml`, private-key files and generated report previews. Ignore rules do not remove files already tracked or rewrite Git history. No secrets are needed to run this app. The audit retained academic deliverables and report evidence exactly as supplied; those materials include student identity and historical workstation paths, so review their public visibility personally.
