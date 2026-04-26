from ir_gen import (
    Instruction, BinOpInstr, UnaryInstr, CopyInstr,
    LabelInstr, GotoInstr, IfFalseGotoInstr, PrintInstr
)


class Optimizer:
    def __init__(self, instructions: list):
        self.instructions = instructions

    def optimize(self) -> list:
        MAX_PASSES = 10

        for pass_num in range(MAX_PASSES):
            before = len(self.instructions)
            old_repr = [repr(i) for i in self.instructions]

            self.instructions = self.constant_folding(self.instructions)
            self.instructions = self.copy_propagation(self.instructions)
            self.instructions = self.dead_code_elimination(self.instructions)

            new_repr = [repr(i) for i in self.instructions]

            if old_repr == new_repr:
                print(f"  [Optimizer] Stabil dupa {pass_num + 1} pas(i). "
                      f"{before} → {len(self.instructions)} instructiuni.")
                break

        return self.instructions

    def constant_folding(self, instructions: list) -> list:
        result = []
        for instr in instructions:
            if isinstance(instr, BinOpInstr):
                folded = self._try_fold(instr)
                result.append(folded)
            else:
                result.append(instr)
        return result

    def _try_fold(self, instr: BinOpInstr) -> Instruction:
        left = instr.left
        right = instr.right
        op = instr.op

        if not (self._is_const(left) and self._is_const(right)):
            return instr

        l = float(left) if '.' in str(left) else int(left)
        r = float(right) if '.' in str(right) else int(right)

        try:
            if op == '+': val = l + r
            elif op == '-': val = l - r
            elif op == '*': val = l * r
            elif op == '/':
                if r == 0: return instr
                val = l / r if isinstance(l, float) or isinstance(r, float) else l // r
            elif op == '%':
                if r == 0: return instr
                val = l % r
            elif op == '>': val = 1 if l > r else 0
            elif op == '<': val = 1 if l < r else 0
            elif op == '>=': val = 1 if l >= r else 0
            elif op == '<=': val = 1 if l <= r else 0
            elif op == '==': val = 1 if l == r else 0
            elif op == '!=': val = 1 if l != r else 0
            else: return instr
        except Exception:
            return instr

        if isinstance(val, float) and val == int(val):
            val = int(val)

        return CopyInstr(instr.result, val)

    def _is_const(self, val) -> bool:
        try:
            float(str(val))
            return True
        except ValueError:
            return False

    def copy_propagation(self, instructions: list) -> list:
        copies = {}
        result = []

        for instr in instructions:
            if isinstance(instr, (LabelInstr, GotoInstr, IfFalseGotoInstr)):
                copies.clear()
                result.append(instr)
                continue

            instr = self._substitute(instr, copies)

            if isinstance(instr, CopyInstr):
                src = instr.source
                if self._is_const(src) or (isinstance(src, str) and src.isidentifier()):
                    copies[instr.result] = src
                else:
                    copies.pop(instr.result, None)
            else:
                dest = self._get_dest(instr)
                if dest:
                    copies.pop(dest, None)

            result.append(instr)

        return result

    def _substitute(self, instr: Instruction, copies: dict) -> Instruction:
        def sub(val):
            if isinstance(val, str) and val in copies:
                return copies[val]
            return val

        if isinstance(instr, BinOpInstr):
            return BinOpInstr(instr.result, sub(instr.left), instr.op, sub(instr.right))

        if isinstance(instr, UnaryInstr):
            return UnaryInstr(instr.result, instr.op, sub(instr.operand))

        if isinstance(instr, CopyInstr):
            return CopyInstr(instr.result, sub(instr.source))

        if isinstance(instr, IfFalseGotoInstr):
            return IfFalseGotoInstr(sub(instr.condition), instr.label)

        if isinstance(instr, PrintInstr):
            return PrintInstr(sub(instr.operand))

        return instr

    def _get_dest(self, instr: Instruction):
        if isinstance(instr, (BinOpInstr, UnaryInstr, CopyInstr)):
            return instr.result
        return None

    def dead_code_elimination(self, instructions: list) -> list:
        live = self._collect_live_vars(instructions)

        result = []
        for instr in instructions:
            dest = self._get_dest(instr)

            if dest is None:
                result.append(instr)
                continue

            if dest in live:
                result.append(instr)

        return result

    def _collect_live_vars(self, instructions: list) -> set:
        live = set()

        for instr in instructions:
            if isinstance(instr, BinOpInstr):
                if isinstance(instr.left, str): live.add(instr.left)
                if isinstance(instr.right, str): live.add(instr.right)

            elif isinstance(instr, UnaryInstr):
                if isinstance(instr.operand, str): live.add(instr.operand)

            elif isinstance(instr, CopyInstr):
                if isinstance(instr.source, str): live.add(instr.source)

            elif isinstance(instr, IfFalseGotoInstr):
                if isinstance(instr.condition, str): live.add(instr.condition)

            elif isinstance(instr, PrintInstr):
                if isinstance(instr.operand, str): live.add(instr.operand)

        return live

    @staticmethod
    def print_comparison(before: list, after: list):
        print(f"\n{'─'*25} INAINTE {'─'*25}")
        for instr in before:
            print(instr)
        print(f"\n{'─'*25} DUPA    {'─'*25}")
        for instr in after:
            print(instr)
        eliminated = len(before) - len(after)
        print(f"\n  Instructiuni eliminate: {eliminated} "
              f"({100*eliminated//len(before) if before else 0}% reducere)")