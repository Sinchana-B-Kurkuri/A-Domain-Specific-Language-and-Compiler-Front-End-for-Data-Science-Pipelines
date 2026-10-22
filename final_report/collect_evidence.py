"""Read-only project audit. Every generated file stays inside final_report/."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from contextlib import redirect_stdout
from dataclasses import asdict, is_dataclass
from datetime import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'final_report'
EVIDENCE = OUT / 'evidence'
MANUAL = ROOT.parent / 'FALLSEM2026-27_VL_BCSE307P_00100_LO_2026-09-03_Compiler-lab-project-instruction.pdf'


def write(name, value):
    target = EVIDENCE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        target.write_text(value, encoding='utf-8')
    else:
        target.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


def run(args, *, env=None):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace', env=env)
    return {'command': args, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def source_files():
    for folder in ('src/ds_pipeline_dsl', 'tests', 'examples', 'docs', 'benchmarks', 'dashboard', '.streamlit'):
        for path in sorted((ROOT / folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix not in {'.pyc'}:
                yield path
    for name in ('README.md', 'pyproject.toml', '.gitignore', 'requirements-dashboard.txt'):
        path = ROOT / name
        if path.exists():
            yield path


def snapshot():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files()}


def extract_documents():
    from docx import Document
    from pypdf import PdfReader
    reader = PdfReader(MANUAL)
    pages = [{'page': i, 'text': p.extract_text()} for i, p in enumerate(reader.pages, 1)]
    write('manual_pages.json', pages)
    write('manual.txt', '\n\n'.join(f'PAGE {p["page"]}\n{p["text"]}' for p in pages))
    phases = {}
    for name in ('Phase1.docx', 'Phase2.docx'):
        doc = Document(ROOT / 'docs' / name)
        content = []
        for block in doc.iter_inner_content():
            if hasattr(block, 'text'):
                content.append({'type': 'paragraph', 'style': block.style.name, 'text': block.text,
                                'runs': [{'text': r.text, 'font': r.font.name, 'size': r.font.size.pt if r.font.size else None} for r in block.runs]})
            else:
                content.append({'type': 'table', 'rows': [[c.text for c in row.cells] for row in block.rows]})
        phases[name] = content
        write(name.replace('.docx', '.txt'), '\n'.join(b['text'] if b['type']=='paragraph' else '\n'.join(' | '.join(row) for row in b['rows']) for b in content))
        with ZipFile(ROOT / 'docs' / name) as z:
            media = [n for n in z.namelist() if n.startswith('word/media/')]
            write(name.replace('.docx', '_media.json'), media)
    write('phase_reports.json', phases)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-python', default=shutil.which('python') or sys.executable)
    args = parser.parse_args()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    baseline_file = EVIDENCE / 'preservation_baseline.json'
    if not baseline_file.exists():
        write('preservation_baseline.json', snapshot())
        write('git_status_before.txt', run(['git','status','--short'])['stdout'])
        write('git_diff_before.txt', run(['git','diff','--stat'])['stdout'])
    extract_documents()
    text_sources = []
    statistics = []
    for path in source_files():
        if path.suffix in {'.py','.md','.txt','.pipe','.toml','.svg'} or path.name=='.gitignore':
            text = path.read_text(encoding='utf-8')
            lines = text.splitlines()
            rel = path.relative_to(ROOT).as_posix()
            text_sources.append(f'FILE {rel}\n'+'\n'.join(f'{i:04}: {line}' for i,line in enumerate(lines,1)))
            statistics.append({'path':rel,'physical_lines':len(lines),'nonblank_lines':sum(bool(l.strip()) for l in lines)})
    write('source_inventory.txt', '\n\n'.join(text_sources))
    write('source_statistics.json', statistics)
    history = run(['git','log','--reverse','--format=%h%x09%s'])
    write('git_history.txt', history['stdout'])
    write('git_history.json', [dict(zip(('hash','subject'), l.split('\t',1))) for l in history['stdout'].splitlines()])
    write('git_optimizer_evolution.txt', run(['git','show','ab9fe03:src/ds_pipeline_dsl/optimizer.py'])['stdout'])
    write('git_optimizer_fix.txt', run(['git','show','--stat','5d490ed'])['stdout'])
    environment_script = "import sys,platform,importlib.metadata as m,importlib.util,json; print(json.dumps({'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'os':platform.system(),'pytest':m.version('pytest'),'streamlit':m.version('streamlit') if importlib.util.find_spec('streamlit') else None,'pytest_cov':bool(importlib.util.find_spec('pytest_cov'))},indent=2))"
    environment = run([args.project_python,'-c',environment_script])
    write('environment.json', json.loads(environment['stdout']))
    test_env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    tests = run([args.project_python,'-B','-m','pytest','-v','-p','no:cacheprovider'],env=test_env)
    write('pytest_v.txt', tests['stdout']+tests['stderr'])
    write('pytest_command.json', {k:v for k,v in tests.items() if k not in {'stdout','stderr'}})
    per_file = {}
    for path, outcome in re.findall(r'^(tests[/\\][^\s:]+\.py)::.*?\s+(PASSED|FAILED|SKIPPED|XFAIL|XPASS|ERROR)(?:\s|$)',tests['stdout'],re.M):
        per_file.setdefault(path.replace('\\','/'), Counter())[outcome.lower()] += 1
    totals = Counter()
    for counts in per_file.values(): totals.update(counts)
    write('test_counts.json', {'per_file':per_file,'totals':totals,'exit_code':tests['exit_code']})
    if json.loads(environment['stdout'])['pytest_cov']:
        coverage = run([args.project_python,'-B','-m','pytest','-q','-p','no:cacheprovider','--cov=ds_pipeline_dsl','--cov-report=term-missing','--cov-report=json:'+str(EVIDENCE/'coverage.json')], env=dict(test_env,COVERAGE_FILE=str(EVIDENCE/'.coverage')))
        write('coverage.txt',coverage['stdout']+coverage['stderr'])
    else:
        write('coverage.txt','Coverage was not measured: pytest-cov was not installed. No coverage plugin was installed for this report.\n')
    examples=[]
    for path in sorted((ROOT/'examples').glob('*.pipe')):
        result=run([args.project_python,'-B','-m','ds_pipeline_dsl.cli',str(path.relative_to(ROOT))],env=test_env)
        category = 'valid'
        if result['exit_code']:
            kind=re.search(r'(Lexical|Syntax|Semantic) Error',result['stdout']+result['stderr'])
            category='invalid ('+(kind[1].lower() if kind else 'other')+')'
        elif path.name.startswith('optimizer_'): category='optimization'
        elif path.name.startswith('complex_'): category='complex'
        write('cli/'+path.stem+'.txt',result['stdout'])
        write('cli/'+path.stem+'.stderr.txt',result['stderr'])
        examples.append({'name':path.name,'category':category,**result})
    write('examples.json',examples)
    pipeline_script=OUT/'extract_pipeline.py'
    extracted=run([args.project_python,'-B',str(pipeline_script)],env=test_env)
    write('pipeline_extraction.log',extracted['stdout']+extracted['stderr'])
    if extracted['exit_code']: raise RuntimeError(extracted['stderr'])
    perf=ROOT/'docs'/'performance.md'
    if perf.exists():
        shutil.copyfile(perf,EVIDENCE/'performance.md')
    else:
        bench=run([args.project_python,'-B','-c',"import importlib.util; from pathlib import Path; p=Path('benchmarks/benchmark.py'); s=importlib.util.spec_from_file_location('bench',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); results,seconds=m.run_benchmark(); print(m.generate_report(results,seconds))"],env=test_env)
        write('performance.md',bench['stdout'])
        write('benchmark_rerun.json',bench)
    before=json.loads(baseline_file.read_text(encoding='utf-8'))
    after=snapshot()
    delta=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
    observed_path=EVIDENCE/'observed_external_changes.json'
    observed=json.loads(observed_path.read_text(encoding='utf-8')) if observed_path.exists() else {}
    unexpected=[p for p in delta if p not in observed or after.get(p)!=observed[p]['observed_sha256']]
    write('preservation_check.json',{'unchanged':not delta,'changed_existing_files':delta,'recorded_external_changes':observed,'unexpected_changes':unexpected,'baseline_files':len(before),'current_files':len(after)})
    if unexpected: raise RuntimeError(f'Unexpected existing project file changes: {unexpected}')
    print(f'Evidence collected: {dict(totals)}, {len(examples)} examples; {len(unexpected)} unexpected project changes; {len(delta)} recorded changes since baseline.')


if __name__=='__main__': main()
