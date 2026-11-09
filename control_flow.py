"""Control flow instructions. Branch offsets use the current PC as their base."""


def execute(cpu, instruction):
    if instruction.opcode == 0x63 and instruction.funct3 == 0:  # BEQ
        if cpu.read_reg(instruction.rs1) == cpu.read_reg(instruction.rs2):
            return True, cpu.pc + instruction.imm_b
        return True, None
    # TODO: remaining branches, JAL, JALR, and exit ECALL.
    return False, None
