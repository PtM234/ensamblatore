addi sp, sp, 0x700
addi a0, zero, 0x120
jal ra, strlen
addi s0, a0, 0
addi a0, zero, 0x200
jal ra, strlen
addi s1, a0, 0
addi a0, zero, 0x250
jal ra, strlen
addi s2, a0, 0
eternal: beq zero, zero, eternal
strlen:
    addi t0, zero, 0
loop:
    add  t1, t0, a0
    lb   t1, 0(t1)
    beq  t1, zero, end
    addi t0, t0, 1
    jal  zero, loop
end:
    addi a0, t0, 0
    jalr zero, ra, 0
