from typing import List
from ds_pipeline_dsl.ir import IRInstruction

def optimize(ir_list: List[IRInstruction]) -> List[IRInstruction]:
    optimized = []
    has_eval = False

    for instr in ir_list:
        if has_eval:
            print(f"Warning: unreachable instruction after OP_EVAL removed: {instr.op}")
            continue

        if instr.op == "OP_EVAL":
            has_eval = True
            optimized.append(instr)
            continue

        if len(optimized) > 0:
            last_instr = optimized[-1]
            if instr.op == last_instr.op and instr.args == last_instr.args and instr.op in ("OP_CLEAN", "OP_SELECT"):
                # Collapse consecutive duplicates by skipping this instruction
                continue

        optimized.append(instr)

    return optimized
