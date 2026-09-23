"""
PipeLang Prototype - Phase 1
A minimal Lexer + Parser + AST + Semantic Dependency Checker for the
Data Science Pipeline DSL described in the Phase 1 proposal.

This is an INITIAL PROTOTYPE only (per Section 8.2, Activity 8 of the
project manual). Intermediate representation generation, optimization,
and the execution engine are Phase 2 / Phase 3 deliverables.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# 1. LEXICAL ANALYSIS
# ---------------------------------------------------------------------------

KEYWORDS = {
    "pipeline", "load", "clean", "select", "split", "train", "evaluate"
}

TOKEN_SPEC = [
    ("STRING",    r'"[^"]*"'),
    ("PERCENT",   r'\d+(\.\d+)?%'),
    ("NUMBER",    r'\d+(\.\d+)?'),
    ("LBRACE",    r'\{'),
    ("RBRACE",    r'\}'),
    ("EQUALS",    r'='),
    ("SEMI",      r';'),
    ("COMMA",     r','),
    ("IDENT",     r'[A-Za-z_][A-Za-z0-9_]*'),
    ("SKIP",      r'[ \t\n]+'),
    ("COMMENT",   r'//[^\n]*'),
    ("MISMATCH",  r'.'),
]

MASTER_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC)
)


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int


class LexicalError(Exception):
    pass


def tokenize(source: str) -> List[Token]:
    tokens = []
    line_num = 1
    line_start = 0
    for match in MASTER_PATTERN.finditer(source):
        kind = match.lastgroup
        value = match.group()
        col = match.start() - line_start

        if kind == "SKIP" or kind == "COMMENT":
            line_num += value.count("\n")
            if "\n" in value:
                line_start = match.end() - len(value.split("\n")[-1])
            continue
        if kind == "MISMATCH":
            raise LexicalError(
                f"Lexical Error at line {line_num}, col {col}: "
                f"unexpected character {value!r}"
            )
        if kind == "IDENT" and value in KEYWORDS:
            kind = value.upper()

        tokens.append(Token(kind, value, line_num, col))

    tokens.append(Token("EOF", "", line_num, 0))
    return tokens


# ---------------------------------------------------------------------------
# 2. ABSTRACT SYNTAX TREE (AST) NODE DEFINITIONS
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 3. RECURSIVE-DESCENT PARSER
# ---------------------------------------------------------------------------

class SyntaxError_(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, ttype: str) -> Token:
        tok = self.peek()
        if tok.type != ttype:
            raise SyntaxError_(
                f"Syntax Error at line {tok.line}: expected {ttype}, "
                f"found {tok.type} ({tok.value!r})"
            )
        return self.advance()

    def parse_pipeline(self) -> PipelineNode:
        self.expect("PIPELINE")
        name_tok = self.expect("IDENT")
        self.expect("LBRACE")
        stmts = []
        while self.peek().type != "RBRACE":
            stmts.append(self.parse_statement())
        self.expect("RBRACE")
        return PipelineNode(name=name_tok.value, statements=stmts, line=name_tok.line)

    def parse_statement(self):
        tok = self.peek()
        if tok.type == "LOAD":
            self.advance()
            fname = self.expect("STRING").value.strip('"')
            self.expect("SEMI")
            return LoadStmt(fname, tok.line)

        if tok.type == "CLEAN":
            self.advance()
            strategy = self.expect("IDENT").value
            self.expect("SEMI")
            return CleanStmt(strategy, tok.line)

        if tok.type == "SELECT":
            self.advance()
            cols = [self.expect("IDENT").value]
            while self.peek().type == "COMMA":
                self.advance()
                cols.append(self.expect("IDENT").value)
            self.expect("SEMI")
            return SelectStmt(cols, tok.line)

        if tok.type == "SPLIT":
            self.advance()
            # 'train' and 'test' are common split names; accept the TRAIN
            # keyword here as a contextual identifier as well as IDENT.
            name_tok = self.peek()
            if name_tok.type in ("IDENT", "TRAIN"):
                name = self.advance().value
            else:
                raise SyntaxError_(
                    f"Syntax Error at line {name_tok.line}: expected split "
                    f"name, found {name_tok.type} ({name_tok.value!r})"
                )
            self.expect("EQUALS")
            pct_tok = self.expect("PERCENT")
            pct = float(pct_tok.value.rstrip("%"))
            self.expect("SEMI")
            return SplitStmt(name, pct, tok.line)

        if tok.type == "TRAIN":
            self.advance()
            model = self.expect("IDENT").value
            self.expect("EQUALS")
            algo = self.expect("IDENT").value
            self.expect("SEMI")
            return TrainStmt(model, algo, tok.line)

        if tok.type == "EVALUATE":
            self.advance()
            model = self.expect("IDENT").value
            self.expect("SEMI")
            return EvaluateStmt(model, tok.line)

        raise SyntaxError_(
            f"Syntax Error at line {tok.line}: unexpected token {tok.type} ({tok.value!r})"
        )


# ---------------------------------------------------------------------------
# 4. SYMBOL TABLE + SEMANTIC DEPENDENCY ANALYSIS
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 5. DEMONSTRATION
# ---------------------------------------------------------------------------

VALID_PROGRAM = '''
pipeline student_prediction {
    load "students.csv";
    clean missing_values;
    select cgpa, attendance, study_hours;
    split train = 80%;
    train model = decision_tree;
    evaluate model;
}
'''

INVALID_PROGRAM = '''
pipeline student_prediction {
    load "students.csv";
    clean missing_values;
    select cgpa, attendance, study_hours;
    train model = decision_tree;
    evaluate model;
}
'''


def run_demo(source: str, label: str):
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}")
    tokens = tokenize(source)
    print(f"\n[LEXER OUTPUT] {len(tokens) - 1} tokens generated:")
    print(", ".join(f"{t.type}({t.value})" for t in tokens if t.type != "EOF"))

    ast = Parser(tokens).parse_pipeline()
    print(f"\n[PARSER OUTPUT] AST for pipeline '{ast.name}':")
    for s in ast.statements:
        print("   ", s)

    print("\n[SEMANTIC ANALYSIS]")
    try:
        table = analyze(ast)
        print("    No semantic errors found. Symbol table state:")
        print(f"    data_loaded={table.data_loaded}, "
              f"data_cleaned={table.data_cleaned}, "
              f"splits={table.splits}, models={table.models}")
    except SemanticError as e:
        print(f"    {e}")


if __name__ == "__main__":
    run_demo(VALID_PROGRAM, "DEMO 1: VALID PIPELINE (train after split)")
    run_demo(INVALID_PROGRAM, "DEMO 2: INVALID PIPELINE (train before split)")
