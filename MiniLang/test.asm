section .data
    fmt_int   db "%lld", 10, 0  ; format pentru intregi (Windows foloseste %lld)
    fmt_float db "%f",   10, 0  ; format pentru reali

section .text
    global main
    extern printf
    extern ExitProcess

main:
    ; Prologue
    push rbp
    mov rbp, rsp
    sub rsp, 48      ; aloca 48 bytes pe stiva

;     y = 25
    mov rax, 25
    mov [rbp - 8], rax

;     t6 = 1
    mov rax, 1
    mov [rbp - 16], rax

;     IF_FALSE t6 GOTO if_end_0
    mov rax, [rbp - 16]
    cmp rax, 0
    je if_end_0

;     PRINT y
    mov rdx, [rbp - 8]
    lea rcx, [rel fmt_int]     ; primul argument: format string
    call printf                ; apel printf Windows

if_end_0:

    ; Epilogue
    xor rcx, rcx             ; exit code = 0
    call ExitProcess