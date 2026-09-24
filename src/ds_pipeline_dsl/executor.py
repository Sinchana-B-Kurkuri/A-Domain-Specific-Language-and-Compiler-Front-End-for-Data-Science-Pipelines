from typing import List
from ds_pipeline_dsl.ir import IRInstruction

def execute(ir_list: List[IRInstruction]) -> List[str]:
    trace = []
    for instr in ir_list:
        if instr.op == "OP_LOAD":
            trace.append(f"Loaded {instr.args['filename']}")
        elif instr.op == "OP_CLEAN":
            trace.append(f"Cleaned using {instr.args['strategy']}")
        elif instr.op == "OP_SELECT":
            cols = ", ".join(instr.args["columns"])
            trace.append(f"Selected columns: {cols}")
        elif instr.op == "OP_SPLIT":
            percent = instr.args["percent"]
            if percent == int(percent):
                percent = int(percent)
            trace.append(f"Defined split '{instr.args['name']}' = {percent}%")
        elif instr.op == "OP_TRAIN":
            trace.append(f"Trained model '{instr.args['model_name']}' using {instr.args['algorithm']}")
        elif instr.op == "OP_EVAL":
            trace.append(f"Evaluated model '{instr.args['model_name']}' (simulated accuracy trace)")
        else:
            trace.append(f"Unknown instruction: {instr.op}")
    return trace
