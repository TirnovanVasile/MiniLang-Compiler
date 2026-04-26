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

;     n = 5
    mov rax, 5
    mov [rbp - 8], rax

;     i = 0
    mov rax, 0
    mov [rbp - 16], rax

;     sum = 0
    mov rax, 0
    mov [rbp - 24], rax

while_start_0:

;     t3 = i < n
    mov rax, [rbp - 16]
    mov rbx, [rbp - 8]
    cmp rax, rbx
    setl al
    movzx rax, al
    mov [rbp - 32], rax

;     IF_FALSE t3 GOTO while_end_1
    mov rax, [rbp - 32]
    cmp rax, 0
    je while_end_1

;     t4 = sum + i
    mov rax, [rbp - 24]
    mov rbx, [rbp - 16]
    add rax, rbx
    mov [rbp - 40], rax

;     sum = t4
    mov rax, [rbp - 40]
    mov [rbp - 24], rax

;     t6 = i + 1
    mov rax, [rbp - 16]
    mov rbx, 1
    add rax, rbx
    mov [rbp - 48], rax

;     i = t6
    mov rax, [rbp - 48]
    mov [rbp - 16], rax

;     GOTO while_start_0
    jmp while_start_0

while_end_1:

;     t8 = sum == 10
    mov rax, [rbp - 24]
    mov rbx, 10
    cmp rax, rbx
    sete al
    movzx rax, al
    mov [rbp - 56], rax

;     IF_FALSE t8 GOTO if_end_2
    mov rax, [rbp - 56]
    cmp rax, 0
    je if_end_2

;     PRINT 999
    mov rdx, 999
    lea rcx, [rel fmt_int]     ; primul argument: format string
    call printf                ; apel printf Windows

if_end_2:

;     t11 = sum != 10
    mov rax, [rbp - 24]
    mov rbx, 10
    cmp rax, rbx
    setne al
    movzx rax, al
    mov [rbp - 64], rax

;     IF_FALSE t11 GOTO if_end_3
    mov rax, [rbp - 64]
    cmp rax, 0
    je if_end_3

;     PRINT 404
    mov rdx, 404
    lea rcx, [rel fmt_int]     ; primul argument: format string
    call printf                ; apel printf Windows

if_end_3:

;     PRINT sum
    mov rdx, [rbp - 24]
    lea rcx, [rel fmt_int]     ; primul argument: format string
    call printf                ; apel printf Windows

    ; Epilogue
    xor rcx, rcx             ; exit code = 0
    call ExitProcess