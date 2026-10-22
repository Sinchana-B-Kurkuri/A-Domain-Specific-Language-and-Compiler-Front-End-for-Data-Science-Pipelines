"""Run under the project interpreter to serialize actual compiler outputs."""
from dataclasses import asdict, is_dataclass
import ast as pyast
import inspect
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'dashboard')]
from ds_pipeline_dsl.lexer import tokenize, TOKEN_SPEC, KEYWORDS
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze
from ds_pipeline_dsl.ir import lower_to_ir
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute
from tests.helpers import evaluation_records

def encode(value):
    if is_dataclass(value): return asdict(value)
    if isinstance(value,(set,frozenset)): return sorted(value)
    return repr(value)

data={'token_spec':TOKEN_SPEC,'keywords':sorted(KEYWORDS),'programs':{},'signatures':{f.__name__:str(inspect.signature(f)) for f in (tokenize,analyze,lower_to_ir,optimize,execute)}}
for path in sorted((ROOT/'examples').glob('*.pipe')):
    source=path.read_text(encoding='utf-8')
    program={'source':source}
    try:
        tokens=tokenize(source)
        program['tokens']=[asdict(t) for t in tokens]
        tree=Parser(tokens).parse_pipeline()
        program['ast']=asdict(tree)
        program['ast_repr']=repr(tree)
        table=analyze(tree)
        program['symbol_table']=vars(table)
        ir=lower_to_ir(tree,table)
        notes=[]
        optimized=optimize(ir,notes)
        program.update(ir=[asdict(i) for i in ir],optimized_ir=[asdict(i) for i in optimized],
                       ir_repr=[repr(i) for i in ir], optimized_ir_repr=[repr(i) for i in optimized],notes=notes,
                       trace=execute(optimized),unoptimized_trace=execute(ir),
                       evaluation_records_equal=evaluation_records(ir)==evaluation_records(optimized))
        states=[]
        for i,stmt in enumerate(tree.statements,1):
            prefix=type(tree)(name=tree.name,statements=tree.statements[:i],line=tree.line)
            states.append({'after':i,'statement':type(stmt).__name__,'line':stmt.line,'state':vars(analyze(prefix))})
        program['symbol_evolution']=states
    except Exception as exc:
        program['error']={'class':type(exc).__name__,'message':str(exc)}
    data['programs'][path.name]=program
errors=[]
for name in ('lexer.py','parser.py','semantic.py'):
    path=ROOT/'src'/'ds_pipeline_dsl'/name
    source=path.read_text(encoding='utf-8')
    tree=pyast.parse(source)
    for node in pyast.walk(tree):
        if isinstance(node,pyast.Raise) and isinstance(node.exc,pyast.Call):
            argument=node.exc.args[0] if node.exc.args else None
            if argument is not None:
                def pattern(n):
                    if isinstance(n,pyast.Constant):return str(n.value)
                    if isinstance(n,pyast.JoinedStr):return ''.join(pattern(v) for v in n.values)
                    if isinstance(n,pyast.FormattedValue):return '{'+pyast.unparse(n.value)+('!'+chr(n.conversion) if n.conversion!=-1 else '')+(':'+pattern(n.format_spec) if n.format_spec else '')+'}'
                    return pyast.unparse(n)
                errors.append({'module':name,'line':node.lineno,'class':pyast.unparse(node.exc.func),'pattern':pattern(argument)})
data['error_catalogue']=sorted(errors,key=lambda e:(e['module'],e['line']))
semantic_bodies=[
    ('Duplicate load','load "a.csv"; load "b.csv";'),
    ('Empty load filename','load "";'),
    ('Clean before load','clean missing;'),
    ('Clean after training','load "d.csv"; split train = 80%; train m = dt; clean missing;'),
    ('Select before load','select a;'),
    ('Select after training','load "d.csv"; split train = 80%; train m = dt; select a;'),
    ('Duplicate selected column','load "d.csv"; select a, a;'),
    ('Select previously dropped column','load "d.csv"; drop a; select a;'),
    ('Drop before load','drop a;'),
    ('Drop after training','load "d.csv"; split train = 80%; train m = dt; drop a;'),
    ('Duplicate column in one drop','load "d.csv"; drop a, a;'),
    ('Drop previously dropped column','load "d.csv"; drop a; drop a;'),
    ('Drop outside current selection','load "d.csv"; select a, b; drop c;'),
    ('Drop every selected column','load "d.csv"; select a; drop a;'),
    ('Split before load','split train = 80%;'),
    ('Split percentage outside bounds','load "d.csv"; split train = 100%;'),
    ('Duplicate split name','load "d.csv"; split train = 80%; split train = 10%;'),
    ('Cumulative split total over limit','load "d.csv"; split train = 80%; split test = 30%;'),
    ('Train without train split','load "d.csv"; train m = dt;'),
    ('Duplicate model name','load "d.csv"; split train = 80%; train m = dt; train m = rf;'),
    ('Evaluation before training','evaluate m;'),
]
semantic_cases=[]
for i,(name,body) in enumerate(semantic_bodies,1):
    source='pipeline rule_case { '+body+' }'
    try:analyze(Parser(tokenize(source)).parse_pipeline())
    except Exception as exc:
        tb=exc.__traceback__
        while tb.tb_next:tb=tb.tb_next
        semantic_cases.append({'id':f'S{i:02}','name':name,'source':source,'message':str(exc),'raise_line':tb.tb_lineno,'class':type(exc).__name__})
    else:raise AssertionError('Semantic case unexpectedly passed: '+name)
assert [c['raise_line'] for c in semantic_cases]==[e['line'] for e in data['error_catalogue'] if e['module']=='semantic.py']
data['semantic_cases']=semantic_cases
data['edge_cases']={}
for name,source in [('empty_pipeline','pipeline empty {}'),('free_identifiers','pipeline p { load "missing.csv"; clean custom_strategy; split train = 80%; train m = custom_algorithm; evaluate m; }'),('no_eval_duplicates','pipeline p { load "d.csv"; clean x; clean x; }')]:
    tree=Parser(tokenize(source)).parse_pipeline();table=analyze(tree);ir=lower_to_ir(tree,table);notes=[];opt=optimize(ir,notes)
    data['edge_cases'][name]={'source':source,'ir_before':len(ir),'ir_after':len(opt),'notes':notes,'trace':execute(opt)}
app=ROOT/'dashboard'/'app.py'
if app.exists():
    module=pyast.parse(app.read_text(encoding='utf-8'))
    for node in module.body:
        if isinstance(node,pyast.Assign):
            for target in node.targets:
                if isinstance(target,pyast.Name) and target.id in ('PAGES','STAGE_INFO','PASSES'):
                    try:data['dashboard_'+target.id.lower()]=pyast.literal_eval(node.value)
                    except (ValueError,TypeError):pass
print('Serialized compiler stages, error catalogue and symbol-table evolution.')
(ROOT/'final_report'/'evidence'/'pipeline_data.json').write_text(json.dumps(data,indent=2,ensure_ascii=False,default=encode),encoding='utf-8')
