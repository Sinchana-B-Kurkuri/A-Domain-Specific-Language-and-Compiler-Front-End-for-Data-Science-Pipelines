import re
from dataclasses import dataclass
from typing import List

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
