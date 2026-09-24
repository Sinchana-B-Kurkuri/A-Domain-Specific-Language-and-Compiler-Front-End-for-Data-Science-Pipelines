from dataclasses import dataclass, field
from typing import List

@dataclass
class LoadStmt:
    filename: str
    line: int

@dataclass
class CleanStmt:
    strategy: str
    line: int

@dataclass
class SelectStmt:
    columns: List[str]
    line: int

@dataclass
class SplitStmt:
    name: str
    percent: float
    line: int

@dataclass
class TrainStmt:
    model_name: str
    algorithm: str
    line: int

@dataclass
class EvaluateStmt:
    model_name: str
    line: int

@dataclass
class PipelineNode:
    name: str
    statements: List = field(default_factory=list)
    line: int = 0
