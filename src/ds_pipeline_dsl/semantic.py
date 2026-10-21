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
        self.load_line = None
        self.split_lines: dict = {}
        self.model_lines: dict = {}
        self.first_train = None

def analyze(pipeline: PipelineNode) -> SymbolTable:
    table = SymbolTable()
    for stmt in pipeline.statements:
        if isinstance(stmt, LoadStmt):
            if table.data_loaded:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'load' used more than once; "
                    f"a dataset was already loaded at line {table.load_line}."
                )
            if stmt.filename.strip() == "":
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'load' requires a non-empty filename."
                )
            table.data_loaded = True
            table.load_line = stmt.line

        elif isinstance(stmt, CleanStmt):
            if not table.data_loaded:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'clean' used before "
                    f"any 'load' statement. No dataset is available."
                )
            if table.first_train:
                m, t = table.first_train
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'clean' used after model '{m}' "
                    f"was trained at line {t}; data-preparation statements must appear before any 'train'."
                )
            table.data_cleaned = True

        elif isinstance(stmt, SelectStmt):
            if not table.data_loaded:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'select' used before "
                    f"any 'load' statement."
                )
            if table.first_train:
                m, t = table.first_train
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'select' used after model '{m}' "
                    f"was trained at line {t}; data-preparation statements must appear before any 'train'."
                )
            seen_cols = set()
            for col in stmt.columns:
                if col in seen_cols:
                    raise SemanticError(
                        f"Semantic Error at line {stmt.line}: column '{col}' appears more than once in 'select'."
                    )
                seen_cols.add(col)

        elif isinstance(stmt, SplitStmt):
            if not table.data_loaded:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: 'split' used before "
                    f"any 'load' statement."
                )
            if not (0 < stmt.percent < 100):
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: split percentage must be strictly between 0 and 100."
                )
            if stmt.name in table.splits:
                m = table.split_lines[stmt.name]
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: split '{stmt.name}' is already defined at line {m}."
                )
            total = sum(table.splits.values()) + stmt.percent
            if total > 100 + 1e-9:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: cumulative split total would be {total:g}%, which exceeds 100%."
                )
            table.splits[stmt.name] = stmt.percent
            table.split_lines[stmt.name] = stmt.line

        elif isinstance(stmt, TrainStmt):
            if "train" not in table.splits:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: training data has not "
                    f"been defined. A 'split train = <percent>%;' statement must "
                    f"appear before 'train {stmt.model_name} = {stmt.algorithm};'."
                )
            if stmt.model_name in table.models:
                m = table.model_lines[stmt.model_name]
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: model '{stmt.model_name}' is already defined at line {m}."
                )
            if table.first_train is None:
                table.first_train = (stmt.model_name, stmt.line)
            table.models[stmt.model_name] = stmt.algorithm
            table.model_lines[stmt.model_name] = stmt.line

        elif isinstance(stmt, EvaluateStmt):
            if stmt.model_name not in table.models:
                raise SemanticError(
                    f"Semantic Error at line {stmt.line}: model '{stmt.model_name}' "
                    f"is evaluated before it has been trained."
                )
    return table
