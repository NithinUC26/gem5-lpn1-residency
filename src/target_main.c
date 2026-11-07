/* Bare RV32 program for gem5 user-mode simulation: no C library, Linux syscalls only. */
#include "node.h"

static long sys3(long n, long a, long b, long c) {
    register long a7 __asm__("a7") = n;
    register long a0 __asm__("a0") = a;
    register long a1 __asm__("a1") = b;
    register long a2 __asm__("a2") = c;
    __asm__ volatile("ecall" : "+r"(a0) : "r"(a7), "r"(a1), "r"(a2) : "memory");
    return a0;
}

void _start(void) {
    unsigned r = run();
    char msg[18] = {'c','h','e','c','k','s','u','m',' ','0','0','0','0','0','0','0','0','\n'};
    for (int i = 0; i < 8; i++) {
        unsigned d = (r >> (28 - 4 * i)) & 0xF;
        msg[9 + i] = (char)(d < 10 ? '0' + d : 'a' + d - 10);
    }
    sys3(64, 1, (long)msg, 18);   /* write(1, msg, 18) */
    sys3(93, 0, 0, 0);            /* exit(0) */
    for (;;) {}
}
