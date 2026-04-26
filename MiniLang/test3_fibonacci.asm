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
    sub rsp, 96      ; aloca 96 bytes pe stiva

;     n = 8
    mov rax, 8
    mov [rbp - 8], rax

;     a = 0
    mov rax, 0
    mov [rbp - 16], rax

;     b = 1
    mov rax, 1
    mov [rbp - 24], rax

;     i = 0
    mov rax, 0
    mov [rbp - 32], rax

;     PRINT 0
    mov rdx, 0
    lea rcx, [rel fmt_int]     ; primul argument: format string
    call printf                ; apel printf Windows

;     PRINT 1
    mov rdx, 1
    lea rcx, [rel fmt_int]     ; primul argument: format string
    call printf                ; apel printf Windows

while_start_0:

;     t5 = n - 2
    mov rax, [rbp - 8]
    mov rbx, 2
    sub rax, rbx
    mov [rbp - 40], rax

;     t6 = i < t5
    mov rax, [rbp - 32]
    mov rbx, [rbp - 40]
    cmp rax, rbx
    setl al
    movzx rax, al
    mov [rbp - 48], rax

;     IF_FALSE t6 GOTO while_end_1
    mov rax, [rbp - 48]
    cmp rax, 0
    je while_end_1

;     t7 = a + b
    mov rax, [rbp - 16]
    mov rbx, [rbp - 24]
    add rax, rbx
    mov [rbp - 56], rax

;     PRINT t7
    mov rdx, [rbp - 56]
    lea rcx, [rel fmt_int]     ; primul argument: format string
    call printf                ; apel printf Windows

;     a = b
    mov rax, [rbp - 24]
    mov [rbp - 16], rax

;     b = t7
    mov rax, [rbp - 56]
    mov [rbp - 24], rax

;     t9 = i + 1
    mov rax, [rbp - 32]
    mov rbx, 1
    add rax, rbx
    mov [rbp - 64], rax

;     i = t9
    mov rax, [rbp - 64]
    mov [rbp - 32], rax

;     GOTO while_start_0
    jmp while_start_0

while_end_1:

    ; Epilogue
    xor rcx, rcx             ; exit code = 0
    call ExitProcess