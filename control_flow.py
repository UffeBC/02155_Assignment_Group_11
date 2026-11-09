"""Control flow instructions. Branch offsets use the current PC as their base."""


def execute(cpu, instruction):
    if instruction.opcode == 0x63 and instruction.funct3 == 0:  # BEQ
        # Take the branch if the two registers have the same value.
        if cpu.read_reg(instruction.rs1) == cpu.read_reg(instruction.rs2):
            # The offset is added to the address of this instruction.
            return True, cpu.pc + instruction.imm_b
        # None lets the CPU move to the next instruction (PC + 4).
        return True, None
    # TODO: remaining branches, JAL, JALR, and exit ECALL.
    return False, None


# TODO: Implement these handlers and call them from execute().
# Use the existing (handled, next_pc) return convention when implementing them.
# These placeholders are not connected to instruction dispatch yet.


def execute_bne(cpu, instruction):
    pass


def execute_blt(cpu, instruction):
    pass


def execute_bge(cpu, instruction):
    pass


def execute_bltu(cpu, instruction):
    pass


def execute_bgeu(cpu, instruction):
    pass


def execute_jal(cpu, instruction):
    pass


def execute_jalr(cpu, instruction):
    pass


def execute_ecall(cpu, instruction):
    pass
