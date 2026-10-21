from typing import List, Tuple, Any, Optional
from ds_pipeline_dsl.lexer import tokenize
from ds_pipeline_dsl.parser import Parser
from ds_pipeline_dsl.semantic import analyze
from ds_pipeline_dsl.ir import lower_to_ir, IRInstruction

def compile_to_ir(source: str) -> List[IRInstruction]:
    tokens = tokenize(source)
    ast = Parser(tokens).parse_pipeline()
    table = analyze(ast)
    return lower_to_ir(ast, table)

def _snapshot_state(cleaning_history: List[str],
                    selected_columns: Optional[Tuple[str, ...]],
                    dropped_columns: set,
                    splits: dict) -> Tuple[Tuple[str, ...], Optional[Tuple[str, ...]], frozenset, Tuple[Tuple[str, float], ...]]:
    return (
        tuple(cleaning_history),
        selected_columns,
        frozenset(dropped_columns),
        tuple(sorted(splits.items()))
    )

def evaluation_records(ir: List[IRInstruction]) -> List[Tuple[Any, Any, Any, Any]]:
    records = []
    cleaning_history: List[str] = []
    selected_columns: Optional[Tuple[str, ...]] = None
    dropped_columns: set = set()
    splits: dict = {}
    trained_models: dict = {}
    
    last_op = None
    last_clean_strategy = None

    for instr in ir:
        op = instr.op
        args = instr.args if instr.args is not None else {}

        if op == "OP_CLEAN":
            strat = args.get("strategy")
            # Appends UNLESS immediately preceding interpreted instruction was OP_CLEAN with same strategy
            if not (last_op == "OP_CLEAN" and last_clean_strategy == strat):
                if strat is not None:
                    cleaning_history.append(strat)
            last_clean_strategy = strat

        elif op == "OP_SELECT":
            cols = args.get("columns", [])
            selected_columns = tuple(cols)

        elif op == "OP_DROP":
            cols = args.get("columns", [])
            dropped_columns.update(cols)
            if selected_columns is not None:
                drop_set = set(cols)
                selected_columns = tuple(c for c in selected_columns if c not in drop_set)

        elif op == "OP_SPLIT":
            name = args.get("name")
            pct = args.get("percent")
            if name is not None:
                splits[name] = pct

        elif op == "OP_TRAIN":
            mname = args.get("model_name")
            algo = args.get("algorithm")
            train_st = _snapshot_state(cleaning_history, selected_columns, dropped_columns, splits)
            if mname is not None:
                trained_models[mname] = (algo, train_st)

        elif op == "OP_EVAL":
            mname = args.get("model_name")
            eval_st = _snapshot_state(cleaning_history, selected_columns, dropped_columns, splits)
            if mname in trained_models:
                algo, train_st = trained_models[mname]
            else:
                algo, train_st = None, None
            records.append((mname, algo, train_st, eval_st))

        last_op = op

    return records

def assert_order_preserving(unopt: List[IRInstruction], opt: List[IRInstruction]) -> None:
    u_idx = 0
    u_len = len(unopt)
    
    for opt_idx, opt_instr in enumerate(opt):
        found = False
        while u_idx < u_len:
            curr_u = unopt[u_idx]
            
            # Check 1: exact instruction match (same op and args)
            if opt_instr.op == curr_u.op and opt_instr.args == curr_u.args:
                u_idx += 1
                found = True
                break
                
            # Check 2: merged OP_DROP
            if opt_instr.op == "OP_DROP" and curr_u.op == "OP_DROP":
                # Check run of contiguous OP_DROP starting at u_idx
                run_cols = []
                run_seen = set()
                run_k = 0
                while (u_idx + run_k) < u_len and unopt[u_idx + run_k].op == "OP_DROP":
                    for c in unopt[u_idx + run_k].args.get("columns", []):
                        if c not in run_seen:
                            run_seen.add(c)
                            run_cols.append(c)
                    run_k += 1
                    # If columns match opt_instr.args["columns"], we matched the run!
                    if opt_instr.args.get("columns") == run_cols:
                        u_idx += run_k
                        found = True
                        break
                if found:
                    break

            u_idx += 1

        assert found, (
            f"Instruction at opt[{opt_idx}] ({opt_instr}) does not map to a strictly increasing "
            f"position in unopt after index {u_idx}"
        )
