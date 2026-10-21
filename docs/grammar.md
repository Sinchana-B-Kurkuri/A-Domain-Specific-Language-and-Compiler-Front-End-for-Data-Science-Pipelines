# Language Grammar & Lexical Specification

This document provides the formal grammar specification and lexical analysis definition for the Data Science Pipeline Domain-Specific Language (`ds_pipeline_dsl`). The grammar matches [`src/ds_pipeline_dsl/parser.py`](../src/ds_pipeline_dsl/parser.py) and [`src/ds_pipeline_dsl/lexer.py`](../src/ds_pipeline_dsl/lexer.py) exactly.

---

## 1. Lexical Specification

### 1.1 Keywords
The following 8 words are reserved keywords. When encountered by the scanner as whole words, they emit their corresponding token types rather than generic `IDENT` tokens:

| Keyword | Token Type | Purpose |
|:---|:---|:---|
| `pipeline` | `PIPELINE` | Declares the top-level pipeline block |
| `load` | `LOAD` | Loads a dataset source file |
| `clean` | `CLEAN` | Applies a data cleaning strategy |
| `select` | `SELECT` | Specifies feature columns |
| `drop` | `DROP` | Removes columns from the pipeline |
| `split` | `SPLIT` | Defines data partition percentages |
| `train` | `TRAIN` | Trains a model with a specified algorithm |
| `evaluate` | `EVALUATE` | Evaluates a trained model |

> **Contextual Keyword Exception**: In a `split` statement, the split name accepts either an `IDENT` or the `TRAIN` keyword (`split_name ::= IDENT | 'train'`). This allows statements such as `split train = 80%;` without ambiguity. In all other contexts, keywords are reserved and cannot be used as column, dataset, or model identifiers.

### 1.2 Token Specification
Tokens are matched using Python regular expressions compiled into a single master pattern scanning from left to right:

| Token Name | Regular Expression | Description / Semantic Value |
|:---|:---|:---|
| `STRING` | `"[^"\n]*"` | Double-quoted ASCII/UTF-8 string without linebreaks. The parser strips enclosing quotes. |
| `BAD_STRING` | `"[^"\n]*` | Unterminated string literal reaching a newline or EOF. Raises `LexicalError`. |
| `PERCENT` | `\d+(\.\d+)?%` | Numeric percentage value followed immediately by `%`. Stripped and parsed as a `float`. |
| `NUMBER` | `\d+(\.\d+)?` | Raw numeric literal. Used to provide precise syntax diagnostics when `%` is omitted. |
| `LBRACE` | `\{` | Left opening brace `{` |
| `RBRACE` | `\}` | Right closing brace `}` |
| `EQUALS` | `=` | Assignment operator `=` |
| `SEMI` | `;` | Statement terminator `;` |
| `COMMA` | `,` | Delimiter `,` separating column identifiers |
| `IDENT` | `[A-Za-z_][A-Za-z0-9_]*` | Identifier starting with a letter or underscore, followed by alphanumeric characters or underscores |
| `SKIP` | `[ \t\r\n]+` | Whitespace (spaces, tabs, carriage returns `\r`, and line feeds `\n`), silently skipped |
| `COMMENT` | `//[^\n]*` | Single-line comment starting with `//` and extending to end of line, silently skipped |
| `MISMATCH` | `.` | Any other character not matched by above rules. Raises `LexicalError`. |
| `EOF` | `""` | Synthetic End-Of-File marker appended when scanner reaches the end of the input string |

### 1.3 Lexical Error Rules
The lexer is strict and fails immediately upon encountering the first invalid token:
1. **Unterminated String**: If an opening quote `"` is not closed on the same line, `LexicalError` is raised:
   ```text
   Lexical Error at line {line_num}, col {col}: unterminated string literal
   ```
2. **Unexpected Character**: Any character outside the recognized alphabet (e.g. `@`, `#`, `$`, `-`, or non-ASCII characters outside comments and strings) raises `LexicalError`:
   ```text
   Lexical Error at line {line_num}, col {col}: unexpected character {value!r}
   ```

---

## 2. Syntactic Grammar (EBNF)

The language syntax is formally specified in Extended Backus-Naur Form (EBNF):

```ebnf
(* Top-level Program: exactly one pipeline per file *)
pipeline_decl    ::= 'pipeline' IDENT '{' statement* '}'

(* Statements *)
statement        ::= load_stmt
                   | clean_stmt
                   | select_stmt
                   | drop_stmt
                   | split_stmt
                   | train_stmt
                   | evaluate_stmt

(* Statement Definitions *)
load_stmt        ::= 'load' STRING ';'
clean_stmt       ::= 'clean' IDENT ';'
select_stmt      ::= 'select' IDENT (',' IDENT)* ';'
drop_stmt        ::= 'drop' IDENT (',' IDENT)* ';'
split_stmt       ::= 'split' split_name '=' PERCENT ';'
split_name       ::= IDENT | 'train'
train_stmt       ::= 'train' IDENT '=' IDENT ';'
evaluate_stmt    ::= 'evaluate' IDENT ';'
```

---

## 3. Syntactic Constraints & Parsing Rules

The recursive-descent parser enforces the following structural constraints:
1. **Single Pipeline per File**: Only one `pipeline` declaration is permitted per source file. Any trailing tokens or secondary pipeline blocks after the closing `}` raise `SyntaxError_`.
2. **Mandatory Block Delimiters**: The pipeline body must be enclosed in `{` and `}`. Missing braces or an unexpected EOF within the body raise `SyntaxError_`.
3. **Mandatory Statement Semicolons**: Every statement inside the pipeline body must end with a semicolon `;`. Standalone empty semicolons are prohibited.
4. **Comma-Separated Identifiers**: In `select` and `drop` statements, identifiers must be separated by commas `,`. Trailing commas (e.g. `select c1, ;`) or missing column names raise `SyntaxError_`.
5. **Mandatory Percentage Sign**: The `split` percentage must include the `%` suffix. A bare number (e.g. `80`) raises a syntax error:
   ```text
   Syntax Error at line {line}: expected PERCENT, found NUMBER ('80')
   ```
6. **Identifiers and Strategy/Algorithm Free Names**: Strategy names in `clean` and algorithm names in `train` are free identifiers conforming to `[A-Za-z_][A-Za-z0-9_]*`.
