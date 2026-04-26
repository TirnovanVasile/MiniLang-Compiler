from lexer import Lexer, Token, TokenType


class Node:
    pass


class IntLiteral(Node):
    def __init__(self, value: int):
        self.value = value

    def __repr__(self):
        return f"Int({self.value})"


class FloatLiteral(Node):
    def __init__(self, value: float):
        self.value = value

    def __repr__(self):
        return f"Float({self.value})"


class BoolLiteral(Node):
    def __init__(self, value: bool):
        self.value = value

    def __repr__(self):
        return f"Bool({self.value})"


class Identifier(Node):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"Var({self.name})"


class BinaryOp(Node):
    def __init__(self, left: Node, op: str, right: Node):
        self.left  = left
        self.op    = op
        self.right = right

    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


class UnaryOp(Node):
    def __init__(self, op: str, operand: Node):
        self.op      = op
        self.operand = operand

    def __repr__(self):
        return f"UnaryOp({self.op}{self.operand})"


class Assign(Node):
    def __init__(self, name: str, value: Node):
        self.name  = name
        self.value = value

    def __repr__(self):
        return f"Assign({self.name} = {self.value})"


class IfStmt(Node):
    def __init__(self, condition: Node, body: list):
        self.condition = condition
        self.body      = body

    def __repr__(self):
        return f"If({self.condition}, body={len(self.body)} stmts)"


class WhileStmt(Node):
    def __init__(self, condition: Node, body: list):
        self.condition = condition
        self.body      = body

    def __repr__(self):
        return f"While({self.condition}, body={len(self.body)} stmts)"


class PrintStmt(Node):
    def __init__(self, expression: Node):
        self.expression = expression

    def __repr__(self):
        return f"Print({self.expression})"


class Program(Node):
    def __init__(self, statements: list):
        self.statements = statements

    def __repr__(self):
        return f"Program({len(self.statements)} statements)"


class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos    = 0

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, None, 0, 0)

    def peek(self, offset=1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TokenType.EOF, None, 0, 0)

    def advance(self) -> Token:
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, type: TokenType) -> Token:
        tok = self.current()
        if tok.type != type:
            raise SyntaxError(
                f"[L{tok.line}:C{tok.col}] "
                f"Asteptam '{type.name}', am gasit '{tok.type.name}' ('{tok.value}')"
            )
        return self.advance()

    def check(self, *types) -> bool:
        return self.current().type in types

    def parse(self) -> Program:
        statements = []
        while not self.check(TokenType.EOF):
            stmt = self.parse_statement()
            statements.append(stmt)
        return Program(statements)

    def parse_statement(self) -> Node:
        tok = self.current()

        if tok.type == TokenType.IF:
            return self.parse_if()

        if tok.type == TokenType.WHILE:
            return self.parse_while()

        if tok.type == TokenType.PRINT:
            return self.parse_print()

        if tok.type == TokenType.IDENTIFIER:
            return self.parse_assign()

        raise SyntaxError(
            f"[L{tok.line}:C{tok.col}] "
            f"Instructiune neasteptata: '{tok.value}'"
        )

    def parse_assign(self) -> Assign:
        name_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return Assign(name_tok.value, value)

    def parse_if(self) -> IfStmt:
        self.expect(TokenType.IF)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)

        body = []
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            body.append(self.parse_statement())

        self.expect(TokenType.RBRACE)
        return IfStmt(condition, body)

    def parse_while(self) -> WhileStmt:
        self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)

        body = []
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            body.append(self.parse_statement())

        self.expect(TokenType.RBRACE)
        return WhileStmt(condition, body)

    def parse_print(self) -> PrintStmt:
        self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        return PrintStmt(expr)

    def parse_expression(self) -> Node:
        left = self.parse_comparison()

        while self.check(TokenType.AND, TokenType.OR):
            op  = self.advance().value
            right = self.parse_comparison()
            left  = BinaryOp(left, op, right)

        return left

    def parse_comparison(self) -> Node:
        left = self.parse_addition()

        cmp_ops = {
            TokenType.EQ, TokenType.NEQ,
            TokenType.LT, TokenType.GT,
            TokenType.LTE, TokenType.GTE
        }
        while self.check(*cmp_ops):
            op    = self.advance().value
            right = self.parse_addition()
            left  = BinaryOp(left, op, right)

        return left

    def parse_addition(self) -> Node:
        left = self.parse_multiplication()

        while self.check(TokenType.PLUS, TokenType.MINUS):
            op    = self.advance().value
            right = self.parse_multiplication()
            left  = BinaryOp(left, op, right)

        return left

    def parse_multiplication(self) -> Node:
        left = self.parse_unary()

        while self.check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op    = self.advance().value
            right = self.parse_unary()
            left  = BinaryOp(left, op, right)

        return left

    def parse_unary(self) -> Node:
        if self.check(TokenType.NOT):
            op      = self.advance().value
            operand = self.parse_unary()
            return UnaryOp(op, operand)

        if self.check(TokenType.MINUS):
            op      = self.advance().value
            operand = self.parse_unary()
            return UnaryOp(op, operand)

        return self.parse_primary()

    def parse_primary(self) -> Node:
        tok = self.current()

        if tok.type == TokenType.INT_LIT:
            self.advance()
            return IntLiteral(tok.value)

        if tok.type == TokenType.FLOAT_LIT:
            self.advance()
            return FloatLiteral(tok.value)

        if tok.type == TokenType.BOOL_LIT:
            self.advance()
            return BoolLiteral(tok.value)

        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(tok.name if hasattr(tok, 'name') else tok.value)

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        raise SyntaxError(
            f"[L{tok.line}:C{tok.col}] "
            f"Expresie neasteptata: '{tok.value}'"
        )


def print_ast(node: Node, indent: int = 0):
    prefix = "  " * indent

    if isinstance(node, Program):
        print(f"{prefix}Program")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)

    elif isinstance(node, Assign):
        print(f"{prefix}Assign: {node.name} =")
        print_ast(node.value, indent + 2)

    elif isinstance(node, IfStmt):
        print(f"{prefix}If:")
        print(f"{prefix}  Conditie:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Corp:")
        for stmt in node.body:
            print_ast(stmt, indent + 2)

    elif isinstance(node, WhileStmt):
        print(f"{prefix}While:")
        print(f"{prefix}  Conditie:")
        print_ast(node.condition, indent + 2)
        print(f"{prefix}  Corp:")
        for stmt in node.body:
            print_ast(stmt, indent + 2)

    elif isinstance(node, PrintStmt):
        print(f"{prefix}Print:")
        print_ast(node.expression, indent + 2)

    elif isinstance(node, BinaryOp):
        print(f"{prefix}BinOp '{node.op}'")
        print_ast(node.left,  indent + 1)
        print_ast(node.right, indent + 1)

    elif isinstance(node, UnaryOp):
        print(f"{prefix}UnaryOp '{node.op}'")
        print_ast(node.operand, indent + 1)

    elif isinstance(node, (IntLiteral, FloatLiteral, BoolLiteral)):
        print(f"{prefix}{node}")

    elif isinstance(node, Identifier):
        print(f"{prefix}{node}")

    else:
        print(f"{prefix}{node}")