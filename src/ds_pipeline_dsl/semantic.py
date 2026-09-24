from ds_pipeline_dsl.ast_nodes import (
    PipelineNode, LoadStmt, CleanStmt, SelectStmt,
    SplitStmt, TrainStmt, EvaluateStmt
)

class SemanticError(Exception):
    pass

class SymbolTable:
    """Tracks pipeline state so dependency-based semantic rules can be
    verified, e.g. 'train' cannot appear before 'split' has produced
    training data."""
    def __init__(self):
        self.data_loaded = False
        self.data_cleaned = False
        self.splits: dict = {}
        self.models: dict = {}

def analyze(pipeline: PipelineNode) -> SymbolTable:
    table = SymbolTable()
    for stmt in pipeline.statements:
        if isinstance(stmt, LoadStmt):
            table.data_loaded = True

        elif isinstance(stmt, CleanStmt):
            if not table.data_loaded:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'clean' used before "
                    f"any 'load' statement. No dataset is available."
                )
            table.data_cleaned = True

        elif isinstance(stmt, SelectStmt):
            if not table.data_loaded:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'select' used before "
                    f"any 'load' statement."
                )

        elif isinstance(stmt, SplitStmt):
            if not table.data_loaded:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'split' used before "
                    f"any 'load' statement."
                )
            table.splits[stmt.name] = stmt.percent

        elif isinstance(stmt, TrainStmt):
            if "train" not in table.splits:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: training data has not "
                    f"been defined. A 'split train = <percent>%;' statement must "
                    f"appear before 'train {stmt.model_name} = {stmt.algorithm};'."
                )
            table.models[stmt.model_name] = stmt.algorithm

        elif isinstance(stmt, EvaluateStmt):
            if stmt.model_name not in table.models:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: model '{stmt.model_name}' "
                    f"is evaluated before it has been trained."
                )
    return table
