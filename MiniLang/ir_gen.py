from parser import (
    Program, Assign, IfStmt, WhileStmt, PrintStmt,
    BinaryOp, UnaryOp, IntLiteral, FloatLiteral,
    BoolLiteral, Identifier, Node
)


class Instruction:
    pass


class BinOpInstr(Instruction):

    def __init__(self, result, left, op, right):
        self.result = result
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"    {self.result} = {self.left} {self.op} {self.right}"


class UnaryInstr(Instruction):

    def __init__(self, result, op, operand):
        self.result = result
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"    {self.result} = {self.op}{self.operand}"


class CopyInstr(Instruction):

    def __init__(self, result, source):
        self.result = result
        self.source = source

    def __repr__(self):
        return f"    {self.result} = {self.source}"


class LabelInstr(Instruction):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.name}:"


class GotoInstr(Instruction):

    def __init__(self, label):
        self.label = label

    def __repr__(self):
        return f"    GOTO {self.label}"


class IfFalseGotoInstr(Instruction):

    def __init__(self, condition, label):
        self.condition = condition
        self.label = label

    def __repr__(self):
        return f"    IF_FALSE {self.condition} GOTO {self.label}"


class PrintInstr(Instruction):

    def __init__(self, operand):
        self.operand = operand

    def __repr__(self):
        return f"    PRINT {self.operand}"


class IRGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self) -> str:
        name = f"t{self.temp_count}"
        self.temp_count += 1
        return name

    def new_label(self, prefix="label") -> str:
        name = f"{prefix}_{self.label_count}"
        self.label_count += 1
        return name

    def emit(self, instr: Instruction):
        self.instructions.append(instr)

    def generate(self, program: Program) -> list:
        for stmt in program.statements:
            self.gen_statement(stmt)
        return self.instructions

    def gen_statement(self, node: Node):
        if isinstance(node, Assign):
            self.gen_assign(node)
        elif isinstance(node, IfStmt):
            self.gen_if(node)
        elif isinstance(node, WhileStmt):
            self.gen_while(node)
        elif isinstance(node, PrintStmt):
            self.gen_print(node)

    def gen_assign(self, node: Assign):
        value_var = self.gen_expr(node.value)
        self.emit(CopyInstr(node.name, value_var))

    def gen_if(self, node: IfStmt):
        cond_var = self.gen_expr(node.condition)
        end_label = self.new_label("if_end")

        self.emit(IfFalseGotoInstr(cond_var, end_label))

        for stmt in node.body:
            self.gen_statement(stmt)

        self.emit(LabelInstr(end_label))

    def gen_while(self, node: WhileStmt):
        start_label = self.new_label("while_start")
        end_label = self.new_label("while_end")

        self.emit(LabelInstr(start_label))

        cond_var = self.gen_expr(node.condition)

        self.emit(IfFalseGotoInstr(cond_var, end_label))

        for stmt in node.body:
            self.gen_statement(stmt)

        self.emit(GotoInstr(start_label))

        self.emit(LabelInstr(end_label))

    def gen_print(self, node: PrintStmt):
        expr_var = self.gen_expr(node.expression)
        self.emit(PrintInstr(expr_var))

    def gen_expr(self, node: Node) -> str:

        if isinstance(node, IntLiteral):
            t = self.new_temp()
            self.emit(CopyInstr(t, node.value))
            return t

        if isinstance(node, FloatLiteral):
            t = self.new_temp()
            self.emit(CopyInstr(t, node.value))
            return t

        if isinstance(node, BoolLiteral):
            t = self.new_temp()
            self.emit(CopyInstr(t, 1 if node.value else 0))
            return t

        if isinstance(node, Identifier):
            return node.name

        if isinstance(node, BinaryOp):
            return self.gen_binary_op(node)

        if isinstance(node, UnaryOp):
            return self.gen_unary_op(node)

        raise ValueError(f"Nod de expresie necunoscut: {type(node)}")

    def gen_binary_op(self, node: BinaryOp) -> str:
        left_var = self.gen_expr(node.left)
        right_var = self.gen_expr(node.right)

        t = self.new_temp()
        self.emit(BinOpInstr(t, left_var, node.op, right_var))
        return t

    def gen_unary_op(self, node: UnaryOp) -> str:
        operand_var = self.gen_expr(node.operand)
        t = self.new_temp()
        self.emit(UnaryInstr(t, node.op, operand_var))
        return t

    def print_ir(self):
        print("=== Cod Intermediar (TAC) ===")
        for instr in self.instructions:
            print(instr)