from typing import List, Optional
from ds_pipeline_dsl.ir import IRInstruction

def _note(notes: Optional[list], msg: str) -> None:
    if notes is not None:
        notes.append(msg)

def _remove_unreachable(ir_list: List[IRInstruction], notes: Optional[list] = None) -> List[IRInstruction]:
    """Pass 1: Removes instructions appearing after the last OP_EVAL.
    Safety: Pipeline records are produced only at OP_EVAL points, so any instructions
    after the final evaluation cannot affect any observable evaluation records."""
    last_eval_idx = None
    for idx in range(len(ir_list) - 1, -1, -1):
        if ir_list[idx].op == "OP_EVAL":
            last_eval_idx = idx
            break

    if last_eval_idx is None:
        return [IRInstruction(i.op, dict(i.args)) for i in ir_list]

    for instr in ir_list[last_eval_idx + 1:]:
        line = instr.args.get("line", "?") if instr.args else "?"
        _note(notes, f"unreachable: removed {instr.op} (line {line}) after last OP_EVAL")

    return [IRInstruction(i.op, dict(i.args)) for i in ir_list[:last_eval_idx + 1]]

def _remove_dead_trains(ir_list: List[IRInstruction], notes: Optional[list] = None) -> List[IRInstruction]:
    """Pass 2: Removes OP_TRAIN instructions whose models are never evaluated.
    Policy: A pipeline with no evaluation is left untouched (this is a conservative policy,
    not a correctness requirement).
    Safety: OP_TRAIN writes only models[name], which is read only at OP_EVAL. Models that
    are never evaluated have no observable effect."""
    has_eval = any(i.op == "OP_EVAL" for i in ir_list)
    if not has_eval:
        # Conservative policy: a pipeline with no evaluation is left untouched
        return [IRInstruction(i.op, dict(i.args)) for i in ir_list]

    # Robustness: if any OP_EVAL lacks model_name, treat all models as live (change nothing)
    for instr in ir_list:
        if instr.op == "OP_EVAL":
            if not instr.args or "model_name" not in instr.args:
                return [IRInstruction(i.op, dict(i.args)) for i in ir_list]

    live = set()
    kept_reversed = []
    dead_notes_reversed = []

    for instr in reversed(ir_list):
        if instr.op == "OP_EVAL":
            mname = instr.args.get("model_name")
            if mname is not None:
                live.add(mname)
            kept_reversed.append(IRInstruction(instr.op, dict(instr.args)))
        elif instr.op == "OP_TRAIN":
            mname = instr.args.get("model_name") if instr.args else None
            if mname is None or mname in live:
                if mname is not None:
                    live.discard(mname)
                kept_reversed.append(IRInstruction(instr.op, dict(instr.args)))
            else:
                line = instr.args.get("line", "?") if instr.args else "?"
                dead_notes_reversed.append(
                    f"dead-train: removed OP_TRAIN '{mname}' (line {line}); model is never evaluated"
                )
        else:
            kept_reversed.append(IRInstruction(instr.op, dict(instr.args)))

    kept_reversed.reverse()
    dead_notes_reversed.reverse()
    for note_msg in dead_notes_reversed:
        _note(notes, note_msg)

    return kept_reversed

def _merge_adjacent_drops(ir_list: List[IRInstruction], notes: Optional[list] = None) -> List[IRInstruction]:
    """Pass 3: Merges immediately adjacent runs of >= 2 OP_DROP instructions.
    Safety: Dropping columns is set union/difference with no observable state
    between adjacent drop statements."""
    result = []
    i = 0
    n = len(ir_list)

    while i < n:
        instr = ir_list[i]
        if instr.op == "OP_DROP" and instr.args and "columns" in instr.args and isinstance(instr.args["columns"], list):
            run = [instr]
            j = i + 1
            while j < n and ir_list[j].op == "OP_DROP" and ir_list[j].args and "columns" in ir_list[j].args and isinstance(ir_list[j].args["columns"], list):
                run.append(ir_list[j])
                j += 1

            if len(run) >= 2:
                seen = set()
                merged_cols = []
                lines = []
                for d in run:
                    line_val = d.args.get("line", "?")
                    lines.append(str(line_val))
                    for col in d.args.get("columns", []):
                        if col not in seen:
                            seen.add(col)
                            merged_cols.append(col)

                new_args = dict(run[0].args)
                new_args["columns"] = merged_cols
                result.append(IRInstruction(op="OP_DROP", args=new_args))

                lines_str = ", ".join(lines)
                _note(notes, f"drop-merge: merged {len(run)} adjacent OP_DROP (lines {lines_str}) into one")
                i = j
            else:
                result.append(IRInstruction(instr.op, dict(instr.args)))
                i += 1
        else:
            args = dict(instr.args) if instr.args else {}
            result.append(IRInstruction(instr.op, args))
            i += 1

    return result

def _args_match_excluding_line(args1: dict, args2: dict) -> bool:
    k1 = {k: v for k, v in args1.items() if k != "line"}
    k2 = {k: v for k, v in args2.items() if k != "line"}
    return k1 == k2

def _collapse_duplicates(ir_list: List[IRInstruction], notes: Optional[list] = None) -> List[IRInstruction]:
    """Pass 4: Collapses consecutive duplicate OP_CLEAN or OP_SELECT instructions.
    Safety: An immediately repeated clean with identical strategy is idempotent under A1.
    An immediately repeated select with identical columns is also idempotent."""
    result = []
    for instr in ir_list:
        args = dict(instr.args) if instr.args else {}
        if instr.op in ("OP_CLEAN", "OP_SELECT") and len(result) > 0:
            last_kept = result[-1]
            last_args = last_kept.args if last_kept.args else {}
            if instr.op == last_kept.op and _args_match_excluding_line(args, last_args):
                line = args.get("line", "?")
                _note(notes, f"duplicate: removed repeated {instr.op} (line {line})")
                continue
        result.append(IRInstruction(instr.op, args))
    return result

def optimize(ir_list: List[IRInstruction], notes: Optional[list] = None) -> List[IRInstruction]:
    """Optimizes the IR instructions through four independent passes:
    1. _remove_unreachable: removes dead tail instructions after the final evaluation.
    2. _remove_dead_trains: removes training of models that are never evaluated.
    3. _merge_adjacent_drops: combines runs of adjacent drop instructions.
    4. _collapse_duplicates: eliminates consecutive duplicate clean and select instructions.

    Note on order: Order of passes is chosen for readability; the passes are independent
    because all data-preparation statements precede the first train (F1).
    """
    ir = _remove_unreachable(ir_list, notes)
    ir = _remove_dead_trains(ir, notes)
    ir = _merge_adjacent_drops(ir, notes)
    ir = _collapse_duplicates(ir, notes)
    return ir
