from enum import Enum, auto


class TokenType(Enum):
    INT_LIT   = auto()
    FLOAT_LIT = auto()
    BOOL_LIT  = auto()

    IDENTIFIER = auto()
    IF         = auto()
    WHILE      = auto()
    PRINT      = auto()

    PLUS   = auto()
    MINUS  = auto()
    STAR   = auto()
    SLASH  = auto()
    PERCENT = auto()

    EQ     = auto()
    NEQ    = auto()
    LT     = auto()
    GT     = auto()
    LTE    = auto()
    GTE    = auto()

    AND    = auto()
    OR     = auto()
    NOT    = auto()

    ASSIGN = auto()

    LPAREN    = auto()
    RPAREN    = auto()
    LBRACE    = auto()
    RBRACE    = auto()
    SEMICOLON = auto()

    EOF = auto()


class Token:
    def __init__(self, type: TokenType, value, line: int, col: int):
        self.type  = type
        self.value = value
        self.line  = line
        self.col   = col

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.col})"


KEYWORDS = {
    "if":    TokenType.IF,
    "while": TokenType.WHILE,
    "print": TokenType.PRINT,
    "true":  TokenType.BOOL_LIT,
    "false": TokenType.BOOL_LIT,
}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.col    = 1

    def current_char(self):
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return None

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def make_token(self, type: TokenType, value):
        return Token(type, value, self.line, self.col)

    def skip_whitespace(self):
        while self.current_char() and self.current_char() in ' \t\r\n':
            self.advance()

    def skip_comment(self):
        if self.current_char() == '/' and self.peek() == '/':
            while self.current_char() and self.current_char() != '\n':
                self.advance()

    def read_number(self):
        start_line, start_col = self.line, self.col
        num_str = ""

        while self.current_char() and self.current_char().isdigit():
            num_str += self.advance()

        if self.current_char() == '.' and self.peek() and self.peek().isdigit():
            num_str += self.advance()
            while self.current_char() and self.current_char().isdigit():
                num_str += self.advance()
            return Token(TokenType.FLOAT_LIT, float(num_str), start_line, start_col)

        return Token(TokenType.INT_LIT, int(num_str), start_line, start_col)

    def read_identifier(self):
        start_line, start_col = self.line, self.col
        name = ""

        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            name += self.advance()

        token_type = KEYWORDS.get(name, TokenType.IDENTIFIER)

        if name == "true":
            return Token(token_type, True, start_line, start_col)
        if name == "false":
            return Token(token_type, False, start_line, start_col)

        return Token(token_type, name, start_line, start_col)

    def next_token(self) -> Token:
        while True:
            self.skip_whitespace()
            if self.current_char() == '/' and self.peek() == '/':
                self.skip_comment()
            else:
                break

        if self.current_char() is None:
            return self.make_token(TokenType.EOF, None)

        ch = self.current_char()
        line, col = self.line, self.col

        if ch.isdigit():
            return self.read_number()

        if ch.isalpha() or ch == '_':
            return self.read_identifier()

        two = ch + (self.peek() or '')

        if two == '==': self.advance(); self.advance(); return Token(TokenType.EQ,  '==', line, col)
        if two == '!=': self.advance(); self.advance(); return Token(TokenType.NEQ, '!=', line, col)
        if two == '<=': self.advance(); self.advance(); return Token(TokenType.LTE, '<=', line, col)
        if two == '>=': self.advance(); self.advance(); return Token(TokenType.GTE, '>=', line, col)
        if two == '&&': self.advance(); self.advance(); return Token(TokenType.AND, '&&', line, col)
        if two == '||': self.advance(); self.advance(); return Token(TokenType.OR,  '||', line, col)

        self.advance()

        single = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.STAR,
            '/': TokenType.SLASH,
            '%': TokenType.PERCENT,
            '=': TokenType.ASSIGN,
            '<': TokenType.LT,
            '>': TokenType.GT,
            '!': TokenType.NOT,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            ';': TokenType.SEMICOLON,
        }

        if ch in single:
            return Token(single[ch], ch, line, col)

        raise SyntaxError(f"[Linia {line}, Col {col}] Caracter necunoscut: '{ch}'")

    def tokenize(self) -> list:
        tokens = []
        while True:
            tok = self.next_token()
            if tok.type == TokenType.EOF:
                break
            tokens.append(tok)
        return tokens