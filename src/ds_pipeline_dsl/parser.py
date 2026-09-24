from typing import List
from ds_pipeline_dsl.lexer import Token
from ds_pipeline_dsl.ast_nodes import (
    PipelineNode, LoadStmt, CleanStmt, SelectStmt,
    SplitStmt, TrainStmt, EvaluateStmt
)

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
