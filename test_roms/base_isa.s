;;; A test rom that will check all opcodes defined in base-isa.md
;;; Expects MMIO output stream connected at address 3
.set OUTPUT 3
;;; Addresses 0x0020 to 0x7FFF should be RAM
;;; This ROM should be placed at 0x8000.


.macro putc 1
            mov %rx0, {0}
            stx %rx0, OUTPUT
.endmacro

.macro trap 0
            putc    '?'
            hlt
.endmacro

;;; The very first test we do is that `movs`, `slo` and `store` work to output stuff.
;;; If these don't work, we are going to have a hard time running the rest of the tests.
test_fundamental:
            putc    'T'
            putc    'E'
            putc    'S'
            putc    'T'
            putc    ' '
            putc    'E'
            putc    'T'
            putc    'C'
            putc    'a'
            putc    '\n'
.next_test:

;;; Next we test that unconditional forward jumps work
test_forward_jmp:
            putc    'J'
            jmp     .letter_m
            trap
.letter_m:
            putc    'U'
            putc    'M'
            jmp     .letter_p
            trap
            trap
            trap
            trap
.letter_p:
            putc    'P'
            putc    '\n'
            jmp     .next_test
            trap
            trap
.next_test:

;;; And now unconditional backward jumps
test_backward_jmp:
            jmp     .letter_p
.letter_j:
            putc    'J'
            putc    '\n'
            jmp     .next_test
            trap
.letter_m:
            putc    'M'
            putc    'U'
            jmp     .letter_j
            trap
            trap
            trap
.letter_p:
            putc    'P'
            jmp     .letter_m
            trap
            trap
.next_test:

;;; Now we are actually ready for the main test suite
main_test_suite:
            jmp     test_conditions
return_test_conditions:
final:
            putc    'S'
            putc    'U'
            putc    'C'
            putc    'C'
            putc    'E'
            putc    'S'
            putc    'S'
            putc    '\n'
            hlt

test_conditions:
            jmp     return_test_conditions