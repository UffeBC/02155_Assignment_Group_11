"""Arithmetic instructions. Extend execute() with the remaining RV32I operations."""


def execute(cpu, instruction):
    if instruction.opcode == 0x13 and instruction.funct3 == 0:  # ADDI
        # Add the signed immediate to rs1 and save it in rd.
        cpu.write_reg(instruction.rd,
                      cpu.read_reg(instruction.rs1) + instruction.imm_i)
        return True, None
    if instruction.opcode == 0x33:
        # These instructions use two register values.
        left = cpu.read_reg(instruction.rs1)
        right = cpu.read_reg(instruction.rs2)
        # Together these fields tell us which operation to use.
        operation = (instruction.funct3, instruction.funct7)
        if operation == (0, 0):  # ADD
            result = left + right
        elif operation == (0, 0x20):  # SUB
            result = left - right
        elif operation == (2, 0):  # SLT: compare signed 32-bit values
            # Convert to signed values; int turns True/False into 1/0.
            from cpu import signed32
            result = int(signed32(left) < signed32(right))
        elif operation == (3, 0):  # SLTU: register values are already unsigned
            result = int(left < right)
        else:
            return False, None
        # write_reg keeps the result within 32 bits and protects x0.
        cpu.write_reg(instruction.rd, result)
        return True, None
    # False means this file did not handle the instruction.
    return False, None


# TODO: Implement these handlers and call them from execute().
# Use the existing (handled, next_pc) return convention when implementing them.
# These placeholders are not connected to instruction dispatch yet.


def execute_xor(cpu, instruction):
    pass


def execute_or(cpu, instruction):
    pass


def execute_and(cpu, instruction):
    pass


def execute_sll(cpu, instruction):
    pass


def execute_srl(cpu, instruction):
    pass


def execute_sra(cpu, instruction):
    pass


def execute_slti(cpu, instruction):
    pass


def execute_sltiu(cpu, instruction):
    pass


def execute_xori(cpu, instruction):
    pass


def execute_ori(cpu, instruction):
    pass


def execute_andi(cpu, instruction):
    pass


def execute_slli(cpu, instruction):
    pass


def execute_srli(cpu, instruction):
    pass


def execute_srai(cpu, instruction):
    pass


def execute_lui(cpu, instruction):
    pass


def execute_auipc(cpu, instruction):
    pass
