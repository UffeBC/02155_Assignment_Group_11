"""Arithmetic instructions. Extend execute() with the remaining RV32I operations."""


def execute(cpu, instruction):
    if instruction.opcode == 0x13 and instruction.funct3 == 0:  # ADDI
        cpu.write_reg(instruction.rd,
                      cpu.read_reg(instruction.rs1) + instruction.imm_i)
        return True, None
    return False, None
