# Raw binary counterpart is baseline.bin; no ECALL is needed for this baseline.
addi x1, x0, 16
lw   x2, 0(x1)
beq  x0, x0, 8
addi x3, x0, 99
addi x4, x0, 42
# LW reads the last instruction's encoding, 0x02a00213, into x2.
