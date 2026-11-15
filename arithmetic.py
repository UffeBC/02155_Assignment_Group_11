"""Arithmetic instructions"""


def execute(cpu, instruction):
    # I type aritmhetic instructions (opcode == 0x13)
    if instruction.opcode == 0x13:
        if instruction.funct3 == 0:
            return execute_addi(cpu, instruction)
        elif instruction.funct3 == 2:
            return execute_slti(cpu, instruction)
        elif instruction.funct3 == 3:
            return execute_sltiu(cpu, instruction)
        elif instruction.funct3 == 4:
            return execute_xori(cpu, instruction)
        elif instruction.funct3 == 6:
            return execute_ori(cpu, instruction)
        elif instruction.funct3 == 7:
            return execute_andi(cpu, instruction)
        elif instruction.funct3 == 1:
            return execute_slli(cpu, instruction)
        elif instruction.funct3 == 5:
            # funct7 differentiates between SRLI and SRAI
            if instruction.funct7 == 0:
                return execute_srli(cpu, instruction)
            elif instruction.funct7 == 0x20:
                return execute_srai(cpu, instruction)

    # R type arithmetic instructions (opcode == 0x33)
    elif instruction.opcode == 0x33:
        operation = (instruction.funct3, instruction.funct7)   
        if operation == (0, 0):
            return execute_add(cpu, instruction)
        elif operation == (0, 0x20):
            return execute_sub(cpu, instruction)
        elif operation == (1, 0):
            return execute_sll(cpu, instruction)
        elif operation == (2, 0):
            return execute_slt(cpu, instruction)
        elif operation == (3, 0):
            return execute_sltu(cpu, instruction)
        elif operation == (4, 0):
            return execute_xor(cpu, instruction)
        elif operation == (5, 0):
            return execute_srl(cpu, instruction)
        elif operation == (5, 0x20):
            return execute_sra(cpu, instruction)
        elif operation == (6, 0):
            return execute_or(cpu, instruction)
        elif operation == (7, 0):
            return execute_and(cpu, instruction)

    # U type arithmetic instructions (opcode == 0x37 for LUI, 0x17 for AUIPC)
    elif instruction.opcode == 0x37:
        return execute_lui(cpu, instruction)
    elif instruction.opcode == 0x17:
        return execute_auipc(cpu, instruction)

    # return False, None if the instruction is not handled by any functions in this file
    return False, None



def execute_addi(cpu, instruction):
    # read the source register value
    left = cpu.read_reg(instruction.rs1)

    # perform the addition with the immediate value
    result = left + instruction.imm_i

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None

def execute_add(cpu, instruction):
    # read the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # perform the addition operation
    result = left + right

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None

def execute_sub(cpu, instruction):
    # read the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # perform the subtraction operation
    result = left - right

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None

def execute_slt(cpu, instruction):
    # need to preserve the sign bit
    from cpu import signed32

    # read the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # perform the set less than operation by turning the values to an int and comparing them
    result = int(signed32(left) < signed32(right))

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None

def execute_sltu(cpu, instruction):
    # no need to preserve the sign bit since the values are unsigned
    # read the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # perform the set less than unsigned operation (1 if left < right else 0)
    result = 1 if left < right else 0

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None

def execute_xor(cpu, instruction):
    # read the the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # perform the XOR operation with python ^
    result = left ^ right

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_or(cpu, instruction):
    # read the the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # perform the OR operation with python |
    result = left | right

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_and(cpu, instruction):
    # read the the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # perform the AND operation with python &
    result = left & right

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_sll(cpu, instruction):
    # read the the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # get the shift amount from the lower 5 bits of the right register
    shift_amount = right & 0x1F

    # perform the shift left logical operation with python <<
    result = left << shift_amount

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_srl(cpu, instruction):
    # read the the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # get the shift amount from the lower 5 bits of the right register
    shift_amount = right & 0x1F

    # perform the shift right logical operation with python >>
    result = left >> right

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_sra(cpu, instruction):
    # need to preserve the sign bit
    from cpu import signed32

    # read the the two values from the registers
    left = cpu.read_reg(instruction.rs1)
    right = cpu.read_reg(instruction.rs2)

    # get the shift amount from the lower 5 bits of the right register
    shift_amount = right & 0x1F

    #perform the right shift arithmetic operation with python >>
    result = signed32(left) >> shift_amount

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)
    
    # return True, None
    return True, None


def execute_slti(cpu, instruction):
    # need to preserve the sign bit
    from cpu import signed32

    # read the source register value
    left = cpu.read_reg(instruction.rs1)

    # perform the set less than immediate operation by turning the values to an int and comparing them
    result = int(signed32(left) < instruction.imm_i)

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_sltiu(cpu, instruction):
    # no need to preserve the sign bit since the values are unsigned
    # read the source register value
    left = cpu.read_reg(instruction.rs1)

    # get the signes immediate value from the instruction and convert it to an unsigned 32-bit value
    imm_u = instruction.imm_i & 0xFFFFFFFF

    # perform the set less than immediate unsigned operation (1 if left < imm_u else 0)
    result = 1 if left < imm_u else 0

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_xori(cpu, instruction):
    # read the source register value
    left = cpu.read_reg(instruction.rs1)

    # perform the XOR immediate operation with python ^
    result = left ^ instruction.imm_i

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_ori(cpu, instruction):
    # read the source register value
    left = cpu.read_reg(instruction.rs1)

    # perform the OR immediate operation with python |
    result = left | instruction.imm_i

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_andi(cpu, instruction):
    # read the source register value
    left = cpu.read_reg(instruction.rs1)

    # perform the AND immediate operation with python &
    result = left & instruction.imm_i

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_slli(cpu, instruction):
    # read the source register value
    left = cpu.read_reg(instruction.rs1)
    
    # get the shift amount from the lower 5 bits of the immediate value
    shift_amount = instruction.imm_i & 0x1F

    # perform the shift left logical immediate operation with python <<
    result = left << shift_amount

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_srli(cpu, instruction):
    # read the source register value
    left = cpu.read_reg(instruction.rs1)
    
    # get the shift amount from the lower 5 bits of the immediate value
    shift_amount = instruction.imm_i & 0x1F

    # perform the shift right logical immediate operation with python >>
    result = left >> shift_amount

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_srai(cpu, instruction):
    # need to preserve the sign bit
    from cpu import signed32

    # read the source register value
    left = cpu.read_reg(instruction.rs1)
    
    # get the shift amount from the lower 5 bits of the immediate value
    shift_amount = instruction.imm_i & 0x1F

    # perform the shift right arithmetic immediate operation with python >>
    result = signed32(left) >> shift_amount

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_lui(cpu, instruction):
    # load the upper immediate value (top 20 bits, by & 0xFFFFF000) from the instruction
    result = instruction.word & 0xFFFFF000

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None


def execute_auipc(cpu, instruction):
    # load the upper immediate value (top 20 bits, by & 0xFFFFF000) from the instruction and add the current program counter value
    result = (instruction.word & 0xFFFFF000) + cpu.pc

    # write the result back to the destination register
    cpu.write_reg(instruction.rd, result)

    # return True, None
    return True, None
