import argparse
import sys
from ds_pipeline_dsl.lexer import tokenize, LexicalError
from ds_pipeline_dsl.parser import Parser, SyntaxError_
from ds_pipeline_dsl.semantic import analyze, SemanticError
from ds_pipeline_dsl.ir import lower_to_ir
from ds_pipeline_dsl.optimizer import optimize
from ds_pipeline_dsl.executor import execute

def main():
    parser = argparse.ArgumentParser(description="DS Pipeline DSL Compiler")
    parser.add_argument("file", help="Path to the .pipe source file")
    parser.add_argument("--tokens", action="store_true", help="Print lexer token output")
    parser.add_argument("--ast", action="store_true", help="Print parsed AST")
    parser.add_argument("--ir", action="store_true", help="Print unoptimized IR")
    parser.add_argument("--optimized-ir", action="store_true", help="Print optimized IR")
    parser.add_argument("--trace", action="store_true", help="Print executor trace")
    
    args = parser.parse_args()
    
    # If no flags provided, set all to True
    if not (args.tokens or args.ast or args.ir or getattr(args, 'optimized_ir') or args.trace):
        args.tokens = True
        args.ast = True
        args.ir = True
        args.optimized_ir = True
        args.trace = True
        
    try:
        with open(args.file, "r") as f:
            code = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
        
    try:
        tokens = tokenize(code)
        if args.tokens:
            print("=== TOKENS ===")
            for tok in tokens:
                print(tok)
                
        ast = Parser(tokens).parse_pipeline()
        if args.ast:
            print("=== AST ===")
            print(ast)
            
        table = analyze(ast)
        
        ir = lower_to_ir(ast, table)
        if args.ir:
            print("=== IR ===")
            for i in ir:
                print(i)
                
        opt_ir = optimize(ir)
        if args.optimized_ir:
            print("=== OPTIMIZED IR ===")
            for i in opt_ir:
                print(i)
                
        trace = execute(opt_ir)
        if args.trace:
            print("=== TRACE ===")
            for line in trace:
                print(line)
                
    except LexicalError as e:
        print(e)
        sys.exit(1)
    except SyntaxError_ as e:
        print(e)
        sys.exit(1)
    except SemanticError as e:
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
