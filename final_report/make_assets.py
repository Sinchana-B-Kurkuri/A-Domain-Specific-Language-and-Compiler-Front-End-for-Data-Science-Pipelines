"""Publication figures from serialized compiler structure and recorded measurements."""
from __future__ import annotations
import json
from pathlib import Path
import textwrap
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parent
ASSETS=OUT/'assets'
INK='#172B46'; TEAL='#087F8C'; PALE='#EAF3F5'; GREY='#627286'; LINE='#D5DEE6'
COLORS=['#173A5E','#087F8C','#46998F','#8AB9B2','#B0C5D4','#D0DEE7']
FONT=Path('C:/Windows/Fonts/arial.ttf')
BOLD=Path('C:/Windows/Fonts/arialbd.ttf')
MONO=Path('C:/Windows/Fonts/consola.ttf')

def font(size=32,bold=False,mono=False):
    path=MONO if mono else BOLD if bold else FONT
    return ImageFont.truetype(str(path),size) if path.exists() else ImageFont.load_default(size=size)

def canvas(height=1050):
    image=Image.new('RGB',(1800,height),'white')
    return image,ImageDraw.Draw(image)

def center(d,xy,text,size=32,fill=INK,bold=False,mono=False):
    d.multiline_text(xy,text,font=font(size,bold,mono),fill=fill,anchor='mm',align='center',spacing=10)

def box(d,rect,text,fill=PALE,size=32):
    d.rounded_rectangle(rect,radius=16,fill=fill,outline=LINE,width=3)
    center(d,((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),text,size)

def arrow(d,start,end,fill=TEAL):
    d.line([start,end],fill=fill,width=5)
    import math
    angle=math.atan2(end[1]-start[1],end[0]-start[0]);length=18
    points=[end,(end[0]-length*math.cos(angle-.5),end[1]-length*math.sin(angle-.5)),(end[0]-length*math.cos(angle+.5),end[1]-length*math.sin(angle+.5))]
    d.polygon(points,fill=fill)

def save(image,name):
    ASSETS.mkdir(parents=True,exist_ok=True)
    image.save(ASSETS/name,dpi=(300,300))

def architecture():
    im,d=canvas(1160)
    center(d,(900,58),'Compiler data flow',42,bold=True)
    nodes=[('Source text',100,140),('Lexer\nToken list',680,140),('Parser\nPipelineNode',1260,140),
           ('Optimizer\nFour ordered passes',100,480),('IR generator\nIRInstruction list',680,480),('Semantic analyzer\nSymbolTable',1260,480),
           ('Symbolic executor',100,820),('Trace strings',680,820)]
    for label,x,y in nodes:box(d,(x,y,x+440,y+180),label)
    arrow(d,(540,230),(680,230));arrow(d,(1120,230),(1260,230))
    arrow(d,(1480,320),(1480,480));arrow(d,(1260,570),(1120,570));arrow(d,(680,570),(540,570))
    arrow(d,(320,660),(320,820));arrow(d,(540,910),(680,910))
    center(d,(900,1090),'CLI and dashboard coordinate the same compiler modules',29,GREY)
    save(im,'architecture.png')

def error_flow():
    im,d=canvas(1050)
    center(d,(900,60),'First error terminates compilation',42,bold=True)
    stages=[('Lexical analysis','LexicalError'),('Syntax analysis','SyntaxError_'),('Semantic analysis','SemanticError')]
    for i,(name,error) in enumerate(stages):
        y=150+i*245
        box(d,(190,y,850,y+140),name)
        box(d,(1120,y,1680,y+140),error,fill='#FBECEC')
        arrow(d,(850,y+70),(1120,y+70),fill='#A23C3C')
        center(d,(980,y+36),'failure',26,'#A23C3C')
        if i<2:arrow(d,(520,y+140),(520,y+245))
    box(d,(190,885,850,1010),'IR / optimizer / executor',size=29)
    arrow(d,(520,780),(520,885))
    center(d,(1395,912),'Report the original message\nLater stages do not run',29,GREY)
    save(im,'error_flow.png')

def package_tree(stats):
    im,d=canvas(1100)
    center(d,(900,65),'Compiler package structure',42,bold=True)
    box(d,(540,135,1260,260),'src/ds_pipeline_dsl',size=37)
    d.line([(900,260),(900,310)],fill=TEAL,width=3)
    d.line([(310,310),(1490,310)],fill=TEAL,width=3)
    for x in (310,900,1490):d.line([(x,310),(x,905)],fill=TEAL,width=3)
    modules=[Path(s['path']).name for s in stats if s['path'].startswith('src/ds_pipeline_dsl/') and s['path'].endswith('.py')]
    for i,name in enumerate(modules):
        x=70+(i%3)*590;y=360+(i//3)*225
        box(d,(x,y,x+480,y+135),name,size=34)
    center(d,(900,1040),'Separate data models, analysis, lowering, optimization and execution',28,GREY)
    save(im,'package_structure.png')

def ast_diagram(program):
    im,d=canvas(1420)
    center(d,(900,55),'AST of valid_basic.pipe',42,bold=True)
    box(d,(420,125,1380,255),'PipelineNode: '+program['ast']['name'],size=34)
    d.line([(420,190),(165,190),(165,390)],fill=TEAL,width=4)
    for i,stmt in enumerate(program['ast']['statements']):
        y=330+i*165
        field_names=list(stmt)
        kind=['LoadStmt','CleanStmt','SelectStmt','SplitStmt','TrainStmt','EvaluateStmt'][i]
        details=', '.join(f'{k}={v!r}' for k,v in stmt.items() if k!='line')
        box(d,(300,y,1700,y+120),kind+'  |  line '+str(stmt['line'])+'\n'+details,size=32)
        d.line([(165,255),(165,y+60),(300,y+60)],fill=TEAL,width=4)
    save(im,'ast_basic.png')

def symbol_evolution(program):
    im,d=canvas(1050)
    center(d,(900,55),'Symbol table evolution for valid_basic.pipe',40,bold=True)
    columns=[100,450,670,900,1250,1710]
    headers=['After statement','Loaded','Cleaned','Splits','Models']
    for i,h in enumerate(headers):center(d,((columns[i]+columns[i+1])/2,170),h,29,bold=True)
    states=[{'after':0,'statement':'Initial','state':{'data_loaded':False,'data_cleaned':False,'splits':{},'models':{}}}]+program['symbol_evolution']
    for i,entry in enumerate(states):
        top=230+i*100
        d.rectangle((100,top,1710,top+100),fill='#F0F5F8' if i%2==0 else 'white')
        s=entry['state']
        values=[str(entry['after'])+' '+entry['statement'].replace('Stmt',''),str(s['data_loaded']),str(s['data_cleaned']),repr(s['splits']),repr(s['models'])]
        for j,v in enumerate(values):
            if j==4 and s['models']:v=v.replace(': ', ':\n')
            center(d,((columns[j]+columns[j+1])/2,top+50),v,32)
    save(im,'symbol_evolution.png')

def ir_comparison(program):
    im,d=canvas(1390)
    center(d,(900,55),'Optimizer demonstration from real IR',42,bold=True)
    for x,title,key in [(80,'Original IR','ir'),(970,'Optimized IR','optimized_ir')]:
        items=program[key]
        center(d,(x+370,160),f'{title}: {len(items)} instructions',33,bold=True)
        for i,instr in enumerate(items):
            y=225+i*95
            color=PALE
            if key=='ir' and instr['args'].get('line') in (4,10,12):color='#FBECEC'
            box(d,(x,y,x+740,y+76),f'{instr["op"]}  |  source line {instr["args"].get("line")}',fill=color,size=29)
    center(d,(1335,1040),'Source drops at lines 5 and 6\nmerge into one OP_DROP.\n\nEvaluation of model1 remains.',29,GREY)
    save(im,'ir_comparison.png')

def tests_chart(counts):
    files=list(counts['per_file'])
    im,d=canvas(1220)
    center(d,(900,55),'Executed tests by file',42,bold=True)
    maximum=max(sum(v.values()) for v in counts['per_file'].values())
    for i,name in enumerate(files):
        y=160+i*80;value=sum(counts['per_file'][name].values())
        d.text((90,y),Path(name).name,font=font(28),fill=INK,anchor='lm')
        width=value/maximum*1050
        d.rounded_rectangle((530,y-20,530+width,y+20),radius=5,fill=TEAL)
        d.text((550+width,y),str(value),font=font(28,True),fill=INK,anchor='lm')
    save(im,'test_distribution.png')

def benchmark_charts(rows):
    numeric=lambda r,k:float(r[k])
    for name,title in [('stage_times.png','Stage times from the recorded benchmark'),('microseconds.png','Recorded microseconds per statement'),('ir_sizes.png','Recorded IR size before and after optimization')]:
        im,d=canvas(1040)
        center(d,(900,55),title,40,bold=True)
        left,right,top,bottom=190,1670,210,850
        d.line([(left,top),(left,bottom),(right,bottom)],fill=LINE,width=3)
        if name=='stage_times.png':
            keys=['Lexer ms','Parser ms','Semantic ms','IR ms','Optimizer ms','Exec(opt) ms']
            maximum=max(sum(numeric(r,k) for k in keys) for r in rows)*1.1
        elif name=='microseconds.png':maximum=max(numeric(r,'us/stmt') for r in rows)*1.15
        else:maximum=max(numeric(r,'IR before') for r in rows)*1.15
        for tick in range(5):
            value=maximum*tick/4;y=bottom-(bottom-top)*tick/4
            d.line([(left,y),(right,y)],fill='#EEF1F4',width=2)
            d.text((left-20,y),f'{value:.1f}' if name!='ir_sizes.png' else f'{int(value)}',font=font(28),fill=GREY,anchor='rm')
        positions=[left+(i+.5)*(right-left)/len(rows) for i in range(len(rows))]
        points=[]
        for x,r in zip(positions,rows):
            center(d,(x,bottom+50),r['Statements'],28)
            if name=='stage_times.png':
                y=bottom
                for color,key in zip(COLORS,keys):
                    h=numeric(r,key)/maximum*(bottom-top)
                    d.rectangle((x-80,y-h,x+80,y),fill=color);y-=h
                center(d,(x,y-27),r['Total ms'],25)
            elif name=='microseconds.png':
                value=numeric(r,'us/stmt');y=bottom-value/maximum*(bottom-top);points.append((x,y))
                d.ellipse((x-10,y-10,x+10,y+10),fill=TEAL)
                center(d,(x,y-36),r['us/stmt'],29,bold=True)
            else:
                for offset,key,color in [(-48,'IR before',INK),(48,'IR after',TEAL)]:
                    y=bottom-numeric(r,key)/maximum*(bottom-top)
                    d.rectangle((x+offset-38,y,x+offset+38,bottom),fill=color)
                    center(d,(x+offset,y-28),r[key],25)
        if points:d.line(points,fill=TEAL,width=4)
        center(d,(925,955),'Statements (categorical program sizes)',27,GREY)
        if name=='stage_times.png':
            for i,(key,color) in enumerate(zip(keys,COLORS)):
                x=155+(i%3)*540;y=120+(i//3)*42
                d.rectangle((x,y-10,x+25,y+10),fill=color);d.text((x+37,y),key,font=font(28),fill=INK,anchor='lm')
        elif name=='ir_sizes.png':
            center(d,(640,135),'Original IR',27,INK,bold=True);center(d,(1160,135),'Optimized IR',27,TEAL,bold=True)
        save(im,name)

def make_all(data,counts,stats,rows):
    architecture();error_flow();package_tree(stats);ast_diagram(data['programs']['valid_basic.pipe'])
    symbol_evolution(data['programs']['valid_basic.pipe']);ir_comparison(data['programs']['optimizer_demo.pipe'])
    tests_chart(counts);benchmark_charts(rows)
