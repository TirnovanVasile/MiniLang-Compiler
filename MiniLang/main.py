import sys
import os
import subprocess
import argparse

from lexer import Lexer
from parser import Parser, print_ast
from semantic import SemanticAnalyzer
from ir_gen import IRGenerator
from optimizer import Optimizer
from codegen import CodeGenerator


def _find_tool(name: str, is_windows: bool) -> str:
    import shutil

    if is_windows:
        if name == "gcc":
            candidates = [
                "C:\\msys64\\mingw64\\bin\\gcc.exe",
                "C:\\TDM-GCC-64\\bin\\gcc.exe",
                "C:\\msys64\\usr\\bin\\gcc.exe",
            ]
        elif name == "nasm":
            candidates = [
                "C:\\Program Files\\NASM\\nasm.exe",
                "C:\\Program Files (x86)\\NASM\\nasm.exe",
                "C:\\NASM\\nasm.exe",
                "C:\\msys64\\mingw64\\bin\\nasm.exe",
            ]
        else:
            candidates = []

        for path in candidates:
            if os.path.exists(path):
                return path

        found = shutil.which(name)
        if found:
            return found
    else:
        found = shutil.which(name)
        if found:
            return found

    return None


def build_executable(asm_file: str, obj_file: str, exe_file: str, is_windows: bool) -> bool:
    nasm_format = "win64" if is_windows else "elf64"
    nasm_exe = _find_tool("nasm", is_windows)

    if not nasm_exe:
        print("  EROARE: NASM nu a fost gasit.")
        _print_install_instructions("nasm", is_windows)
        return False

    print(f"\n[ + ] Asamblare cu NASM (format {nasm_format})...")
    try:
        nasm_result = subprocess.run(
            [nasm_exe, "-f", nasm_format, "-o", obj_file, asm_file],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        print("  EROARE: NASM nu a fost gasit in PATH.")
        return False

    if nasm_result.returncode != 0:
        print(f"\n  EROARE NASM:\n{nasm_result.stderr}")
        return False
    print(f"  OK  Fisier obiect generat: '{obj_file}'")

    gcc_exe = _find_tool("gcc", is_windows)
    if not gcc_exe:
        print("  EROARE: GCC nu a fost gasit.")
        _print_install_instructions("gcc", is_windows)
        return False

    print(f"\n[ + ] Linkeditare cu GCC → '{exe_file}'...")
    if is_windows:
        gcc_cmd = [gcc_exe, "-o", exe_file, obj_file, "-nostartfiles", "-lmsvcrt", "-lkernel32"]
    else:
        gcc_cmd = [gcc_exe, "-no-pie", "-o", exe_file, obj_file]

    try:
        if is_windows:
            env = os.environ.copy()
            env["PATH"] = r"C:\msys64\mingw64\bin;C:\msys64\usr\bin;" + env.get("PATH", "")
            gcc_result = subprocess.run(gcc_cmd, capture_output=True, text=True, env=env)
        else:
            gcc_result = subprocess.run(gcc_cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("  EROARE: GCC nu a fost gasit in PATH.")
        return False

    if gcc_result.returncode != 0:
        print(f"\n  EROARE GCC:\n{gcc_result.stderr}")
        return False

    print(f"  OK  Executabil creat: '{exe_file}'")
    return True


def run_executable(exe_file: str, is_windows: bool):
    print(f"\n[ > ] Rulare '{exe_file}':\n" + "─" * 40)
    cmd = [exe_file] if is_windows else [f"./{exe_file}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print("stderr:", result.stderr)
    print("─" * 40 + f"\n  Cod de iesire: {result.returncode}")


def _print_install_instructions(tool: str, is_windows: bool):
    pass


def compile_source(source: str, filename: str, args) -> bool:
    is_windows = sys.platform == "win32"

    print("[ 1/5 ] Analiza lexicala...")
    try:
        tokens = Lexer(source).tokenize()
    except SyntaxError as e:
        print(f"\n  EROARE LEXICALA: {e}")
        return False
    print(f"  OK  {len(tokens)} tokeni generati")

    print("\n[ 2/5 ] Analiza sintactica (constructie AST)...")
    try:
        ast = Parser(tokens).parse()
    except SyntaxError as e:
        print(f"\n  EROARE SINTACTICA: {e}")
        return False
    print(f"  OK  AST construit ({len(ast.statements)} instructiuni la nivel superior)")

    print("\n[ 3/5 ] Analiza semantica...")
    errors = SemanticAnalyzer().analyze(ast)
    if errors:
        print(f"\n  {len(errors)} EROARE(I) SEMANTICA(E):")
        for err in errors:
            print(f"    - {err}")
        return False
    print("  OK  Nicio eroare semantica")

    print("\n[ 4/5 ] Generare cod intermediar si optimizare...")
    raw = IRGenerator().generate(ast)
    opt_instrs = Optimizer(raw).optimize()
    print(f"  OK  {len(raw)} → {len(opt_instrs)} instructiuni dupa optimizare")

    if args.ir or args.verbose:
        print("\n  IR optimizat:")
        for instr in opt_instrs:
            print(f"    {instr}")

    print("\n[ 5/5 ] Generare cod Assembly x86-64...")
    asm_code = CodeGenerator(opt_instrs, is_windows=is_windows).generate()
    base = os.path.splitext(filename)[0]
    asm_file = base + ".asm"
    obj_file = base + (".obj" if is_windows else ".o")
    exe_file = base + (".exe" if is_windows else "")

    with open(asm_file, "w") as f:
        f.write(asm_code)
    print(f"  OK  Assembly salvat in '{asm_file}'")

    if args.asm or args.verbose:
        print(f"\n  Continut '{asm_file}':\n  " + "\n  ".join(asm_code.splitlines()))

    if args.build or args.run:
        if not build_executable(asm_file, obj_file, exe_file, is_windows):
            return False
        if args.run:
            run_executable(exe_file, is_windows)

    print("\n  Compilare finalizata cu succes!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Compilator MiniLang - Assembly x86-64")
    parser.add_argument("input", help="Fisierul sursa .ml")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--ir", action="store_true")
    parser.add_argument("--asm", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--run", action="store_true")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Eroare: fisierul '{args.input}' nu exista.")
        sys.exit(1)

    with open(args.input, "r") as f:
        source = f.read()

    success = compile_source(source, args.input, args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()