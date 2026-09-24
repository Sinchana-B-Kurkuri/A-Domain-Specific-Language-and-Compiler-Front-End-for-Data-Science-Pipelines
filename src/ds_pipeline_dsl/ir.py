from dataclasses import dataclass
from typing import List
from ds_pipeline_dsl.ast_nodes import (
    PipelineNode, LoadStmt, CleanStmt, SelectStmt,
    SplitStmt, TrainStmt, EvaluateStmt
)
from ds_pipeline_dsl.semantic import SymbolTable

@dataclass
class IRInstruction:
    op: str
    args: dict

def lower_to_ir(pipeline_ast: PipelineNode, symbol_table: SymbolTable) -> List[IRInstruction]:
    ir = []
    for stmt in pipeline_ast.statements:
        if isinstance(stmt, LoadStmt):
            ir.append(IRInstruction(op="OP_LOAD", args={"filename": stmt.filename, "line": stmt.line}))
        elif isinstance(stmt, CleanStmt):
            ir.append(IRInstruction(op="OP_CLEAN", args={"strategy": stmt.strategy, "line": stmt.line}))
        elif isinstance(stmt, SelectStmt):
            ir.append(IRInstruction(op="OP_SELECT", args={"columns": stmt.columns, "line": stmt.line}))
        elif isinstance(stmt, SplitStmt):
            ir.append(IRInstruction(op="OP_SPLIT", args={"name": stmt.name, "percent": stmt.percent, "line": stmt.line}))
        elif isinstance(stmt, TrainStmt):
            ir.append(IRInstruction(op="OP_TRAIN", args={"model_name": stmt.model_name, "algorithm": stmt.algorithm, "line": stmt.line}))
        elif isinstance(stmt, EvaluateStmt):
            ir.append(IRInstruction(op="OP_EVAL", args={"model_name": stmt.model_name, "line": stmt.line}))
    return ir
