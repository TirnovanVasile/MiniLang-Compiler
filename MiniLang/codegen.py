import sys

from ir_gen import (
    BinOpInstr, UnaryInstr, CopyInstr,
    LabelInstr, GotoInstr, IfFalseGotoInstr, PrintInstr
)


class CodeGenerator:
    def __init__(self, instructions: list, is_windows: bool = None):
        self.instructions = instructions
        self.asm_lines    = []
        self.var_offsets  = {}
        self.stack_size   = 0

        if is_windows is None:
            self.is_windows = sys.platform == "win32"
        else:
            self.is_windows = is_windows


    def emit(self, line: str):
        self.asm_lines.append(line)

    def get_offset(self, var_name) -> int:
        if var_name not in self.var_offsets:
            self.stack_size += 8
            self.var_offsets[var_name] = self.stack_size
        return self.var_offsets[var_name]

    def addr(self, var_name) -> str:
        offset = self.get_offset(var_name)
        return f"[rbp - {offset}]"

    def load(self, val, reg="rax"):
        if self._is_const(val):
            int_val = int(float(str(val)))
            self.emit(f"    mov {reg}, {int_val}")
        else:
            self.emit(f"    mov {reg}, {self.addr(val)}")

    def store(self, reg, var_name):
        self.emit(f"    mov {self.addr(var_name)}, {reg}")

    def _is_const(self, val) -> bool:
        try:
            float(str(val))
            return True
        except (ValueError, TypeError):
            return False


    def generate(self) -> str:
        self._scan_variables()

        aligned_size = ((self.stack_size + 15) // 16) * 16

        if self.is_windows:
            aligned_size += 32

        aligned_size = ((aligned_size + 15) // 16) * 16

        self.emit("section .data")
        self.emit('    fmt_int   db "%lld", 10, 0  ; format pentru intregi (Windows foloseste %lld)')
        self.emit('    fmt_float db "%f",   10, 0  ; format pentru reali')
        self.emit("")

        self.emit("section .text")

        self.emit("    global main")
        self.emit("    extern printf")
        if self.is_windows:
            self.emit("    extern ExitProcess")
        self.emit("")

        self.emit("main:")
        self.emit("    ; Prologue")
        self.emit("    push rbp")
        self.emit("    mov rbp, rsp")
        self.emit(f"    sub rsp, {aligned_size}      ; aloca {aligned_size} bytes pe stiva")
        self.emit("")

        for instr in self.instructions:
            self.emit(f"    ; {instr}".strip())
            self._gen_instruction(instr)
            self.emit("")

        self.emit("    ; Epilogue")
        if self.is_windows:
            self.emit("    xor rcx, rcx             ; exit code = 0")
            self.emit("    call ExitProcess")
        else:
            self.emit("    xor rax, rax")
            self.emit("    mov rsp, rbp")
            self.emit("    pop rbp")
            self.emit("    ret")

        return "\n".join(self.asm_lines)

    def _scan_variables(self):
        for instr in self.instructions:
            if isinstance(instr, (BinOpInstr, UnaryInstr, CopyInstr)):
                self.get_offset(instr.result)
                if isinstance(instr, BinOpInstr):
                    if not self._is_const(instr.left):  self.get_offset(instr.left)
                    if not self._is_const(instr.right): self.get_offset(instr.right)
                elif isinstance(instr, UnaryInstr):
                    if not self._is_const(instr.operand): self.get_offset(instr.operand)
                elif isinstance(instr, CopyInstr):
                    if not self._is_const(instr.source): self.get_offset(instr.source)
            elif isinstance(instr, IfFalseGotoInstr):
                if not self._is_const(instr.condition): self.get_offset(instr.condition)
            elif isinstance(instr, PrintInstr):
                if not self._is_const(instr.operand): self.get_offset(instr.operand)


    def _gen_instruction(self, instr):
        if isinstance(instr, CopyInstr):
            self._gen_copy(instr)
        elif isinstance(instr, BinOpInstr):
            self._gen_binop(instr)
        elif isinstance(instr, UnaryInstr):
            self._gen_unary(instr)
        elif isinstance(instr, LabelInstr):
            self._gen_label(instr)
        elif isinstance(instr, GotoInstr):
            self._gen_goto(instr)
        elif isinstance(instr, IfFalseGotoInstr):
            self._gen_if_false_goto(instr)
        elif isinstance(instr, PrintInstr):
            self._gen_print(instr)

    def _gen_copy(self, instr: CopyInstr):
        self.load(instr.source, "rax")
        self.store("rax", instr.result)

    def _gen_binop(self, instr: BinOpInstr):
        op = instr.op
        self.load(instr.left,  "rax")
        self.load(instr.right, "rbx")

        if op == '+':
            self.emit("    add rax, rbx")
        elif op == '-':
            self.emit("    sub rax, rbx")
        elif op == '*':
            self.emit("    imul rax, rbx")
        elif op == '/':
            self.emit("    cqo")
            self.emit("    idiv rbx")
        elif op == '%':
            self.emit("    cqo")
            self.emit("    idiv rbx")
            self.emit("    mov rax, rdx")
        elif op in ('==', '!=', '<', '>', '<=', '>='):
            self._gen_comparison(op)

        self.store("rax", instr.result)

    def _gen_comparison(self, op: str):
        set_map = {
            '==': 'sete',  '!=': 'setne',
            '<':  'setl',  '>':  'setg',
            '<=': 'setle', '>=': 'setge',
        }
        self.emit("    cmp rax, rbx")
        self.emit(f"    {set_map[op]} al")
        self.emit("    movzx rax, al")

    def _gen_unary(self, instr: UnaryInstr):
        self.load(instr.operand, "rax")
        if instr.op == '-':
            self.emit("    neg rax")
        elif instr.op == '!':
            self.emit("    cmp rax, 0")
            self.emit("    sete al")
            self.emit("    movzx rax, al")
        self.store("rax", instr.result)

    def _gen_label(self, instr: LabelInstr):
        self.asm_lines.pop()
        self.emit(f"{instr.name}:")

    def _gen_goto(self, instr: GotoInstr):
        self.emit(f"    jmp {instr.label}")

    def _gen_if_false_goto(self, instr: IfFalseGotoInstr):
        self.load(instr.condition, "rax")
        self.emit("    cmp rax, 0")
        self.emit(f"    je {instr.label}")

    def _gen_print(self, instr: PrintInstr):
        if self.is_windows:
            self.load(instr.operand, "rdx")
            self.emit("    lea rcx, [rel fmt_int]     ; primul argument: format string")
            self.emit("    call printf                ; apel printf Windows")
        else:
            self.load(instr.operand, "rsi")
            self.emit("    lea rdi, [rel fmt_int]     ; primul argument: format string")
            self.emit("    xor rax, rax               ; rax=0: fara registre SSE")
            self.emit("    call printf                ; apel printf Linux")

