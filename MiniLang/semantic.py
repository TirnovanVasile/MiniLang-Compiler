from parser import (
    Program, Assign, IfStmt, WhileStmt, PrintStmt,
    BinaryOp, UnaryOp, IntLiteral, FloatLiteral,
    BoolLiteral, Identifier, Node
)


class Type:
    INT   = "int"
    FLOAT = "float"
    BOOL  = "bool"
    VOID  = "void"


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent  = parent

    def define(self, name: str, type_: str):
        self.symbols[name] = type_

    def lookup(self, name: str):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def __repr__(self):
        return f"SymbolTable({self.symbols})"


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self):
        self.scope = SymbolTable()
        self.errors = []

    def analyze(self, program: Program):
        for stmt in program.statements:
            self.check_statement(stmt)
        return self.errors

    def check_statement(self, node: Node):
        if isinstance(node, Assign):
            self.check_assign(node)
        elif isinstance(node, IfStmt):
            self.check_if(node)
        elif isinstance(node, WhileStmt):
            self.check_while(node)
        elif isinstance(node, PrintStmt):
            self.check_print(node)
        else:
            self.errors.append(f"Nod necunoscut: {type(node)}")

    def check_assign(self, node: Assign):
        value_type = self.infer_type(node.value)

        if value_type is None:
            return

        existing_type = self.scope.lookup(node.name)
        if existing_type and existing_type != value_type:
            if set([existing_type, value_type]) == {Type.INT, Type.FLOAT}:
                self.scope.define(node.name, Type.FLOAT)
            else:
                self.errors.append(
                    f"Eroare tip: variabila '{node.name}' era '{existing_type}', "
                    f"acum se atribuie '{value_type}'"
                )
        else:
            self.scope.define(node.name, value_type)

        node.inferred_type = value_type

    def check_if(self, node: IfStmt):
        cond_type = self.infer_type(node.condition)

        if cond_type and cond_type != Type.BOOL:
            self.errors.append(
                f"Eroare tip: conditia 'if' trebuie sa fie bool, "
                f"nu '{cond_type}'"
            )

        saved_scope  = self.scope
        self.scope   = SymbolTable(parent=saved_scope)

        for stmt in node.body:
            self.check_statement(stmt)

        self.scope = saved_scope

    def check_while(self, node: WhileStmt):
        cond_type = self.infer_type(node.condition)

        if cond_type and cond_type != Type.BOOL:
            self.errors.append(
                f"Eroare tip: conditia 'while' trebuie sa fie bool, "
                f"nu '{cond_type}'"
            )

        saved_scope  = self.scope
        self.scope   = SymbolTable(parent=saved_scope)

        for stmt in node.body:
            self.check_statement(stmt)

        self.scope = saved_scope

    def check_print(self, node: PrintStmt):
        expr_type = self.infer_type(node.expression)
        if expr_type:
            node.inferred_type = expr_type

    def infer_type(self, node: Node) -> str:
        if isinstance(node, IntLiteral):
            node.type = Type.INT
            return Type.INT

        if isinstance(node, FloatLiteral):
            node.type = Type.FLOAT
            return Type.FLOAT

        if isinstance(node, BoolLiteral):
            node.type = Type.BOOL
            return Type.BOOL

        if isinstance(node, Identifier):
            var_type = self.scope.lookup(node.name)
            if var_type is None:
                self.errors.append(
                    f"Eroare: variabila '{node.name}' folosita fara sa fie declarata"
                )
                return None
            node.type = var_type
            return var_type

        if isinstance(node, BinaryOp):
            return self.infer_binary_op(node)

        if isinstance(node, UnaryOp):
            return self.infer_unary_op(node)

        self.errors.append(f"Nod de expresie necunoscut: {type(node)}")
        return None

    def infer_binary_op(self, node: BinaryOp) -> str:
        left_type  = self.infer_type(node.left)
        right_type = self.infer_type(node.right)

        if left_type is None or right_type is None:
            return None

        op = node.op

        if op in ('+', '-', '*', '/', '%'):
            if left_type not in (Type.INT, Type.FLOAT):
                self.errors.append(
                    f"Eroare tip: operatorul '{op}' nu se poate aplica pe '{left_type}'"
                )
                return None
            if right_type not in (Type.INT, Type.FLOAT):
                self.errors.append(
                    f"Eroare tip: operatorul '{op}' nu se poate aplica pe '{right_type}'"
                )
                return None

            if op == '/' and isinstance(node.right, IntLiteral) and node.right.value == 0:
                self.errors.append("Eroare: impartire la zero detectata!")
                return None
            if op == '/' and isinstance(node.right, FloatLiteral) and node.right.value == 0.0:
                self.errors.append("Eroare: impartire la zero detectata!")
                return None

            result_type = Type.FLOAT if Type.FLOAT in (left_type, right_type) else Type.INT
            node.type = result_type
            return result_type

        if op in ('==', '!=', '<', '>', '<=', '>='):
            numeric = {Type.INT, Type.FLOAT}
            if left_type in numeric and right_type in numeric:
                node.type = Type.BOOL
                return Type.BOOL
            if left_type == right_type:
                node.type = Type.BOOL
                return Type.BOOL
            self.errors.append(
                f"Eroare tip: nu poti compara '{left_type}' cu '{right_type}'"
            )
            return None

        if op in ('&&', '||'):
            if left_type != Type.BOOL:
                self.errors.append(
                    f"Eroare tip: '&&'/'||' necesita bool, nu '{left_type}'"
                )
                return None
            if right_type != Type.BOOL:
                self.errors.append(
                    f"Eroare tip: '&&'/'||' necesita bool, nu '{right_type}'"
                )
                return None
            node.type = Type.BOOL
            return Type.BOOL

        self.errors.append(f"Operator necunoscut: '{op}'")
        return None

    def infer_unary_op(self, node: UnaryOp) -> str:
        operand_type = self.infer_type(node.operand)
        if operand_type is None:
            return None

        if node.op == '!':
            if operand_type != Type.BOOL:
                self.errors.append(
                    f"Eroare tip: '!' necesita bool, nu '{operand_type}'"
                )
                return None
            node.type = Type.BOOL
            return Type.BOOL

        if node.op == '-':
            if operand_type not in (Type.INT, Type.FLOAT):
                self.errors.append(
                    f"Eroare tip: negatie unara necesita numeric, nu '{operand_type}'"
                )
                return None
            node.type = operand_type
            return operand_type

        self.errors.append(f"Operator unar necunoscut: '{node.op}'")
        return None