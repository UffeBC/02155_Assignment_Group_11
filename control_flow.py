"""Control flow instructions. Branch offsets use the current PC as their base."""

#B type, conditional branches, opcode 0x63
def execute(cpu, instruction):
    if instruction.opcode == 0x63: 
         if instruction.funct3 == 0:  # BEQ
            return execute_beq(cpu,instruction)
         elif instruction.funct3 == 1: #BNE
             return execute_bne(cpu,instruction)
         elif instruction.funct3 == 4: #BLT
             return execute_blt(cpu, instruction)
         elif instruction.funct3 == 5: #BGE
            return execute_bge(cpu, instruction)
         elif instruction.funct3 == 6: #BLT unsigned
            return execute_bltu(cpu, instruction)
         elif instruction.funct3 == 7: #BGE unsigned
            return execute_bgeu(cpu, instruction)
    
    elif instruction.opcode == 0x6F:       #J type
        return execute_jal(cpu, instruction)  
    elif instruction.opcode == 0x67 and instruction.funct3 == 0:
        return execute_jalr(cpu,instruction)   # I type  
    elif instruction.opcode == 0x73 and instruction.funct3 == 0 and instruction.imm_i == 0: #Ecall and Ebreak have the same opcode, so imm_b(12-bit immediate field) tells them appart
        return execute_ecall(cpu, instruction)     #         
  
    return False, None

def branch(cpu,instruction,held):

    return True, (cpu.pc + instruction.imm_b) if held else None #if true jumps to PC + offset, else continues with PC + 4

def JAL_offset(instruction): #calculates offset, bit 20 is the signed bit of the 21 bit offset
    offset = (((instruction.word >> 31) & 1) <<20
              | ((instruction.word >> 12) & 0xFF) << 12
              | ((instruction.word >> 20) & 1) << 11
              | ((instruction.word >> 21) & 0x3FF) << 1
    )
    return offset - (1 << 21) if offset & (1 << 20) else offset
                  
                  
               
            

def execute_beq(cpu,instruction):
    return branch(cpu,instruction, cpu.read_reg(instruction.rs1) == cpu.read_reg(instruction.rs2))

def execute_bne(cpu, instruction):
    return branch(cpu,instruction,  cpu.read_reg(instruction.rs1) != cpu.read_reg(instruction.rs2))


def execute_blt(cpu, instruction):
    from cpu import signed32 #is used for blt and bge to keep the sign bit

    return branch(cpu,instruction, signed32(cpu.read_reg(instruction.rs1)) < signed32(cpu.read_reg(instruction.rs2))) 


def execute_bge(cpu, instruction):
    from cpu import signed32 

    return branch(cpu,instruction, signed32(cpu.read_reg(instruction.rs1)) >= signed32(cpu.read_reg(instruction.rs2))) 



def execute_bltu(cpu, instruction):
    return branch(cpu,instruction, cpu.read_reg(instruction.rs1) < cpu.read_reg(instruction.rs2))



def execute_bgeu(cpu, instruction):
    return branch(cpu,instruction, cpu.read_reg(instruction.rs1) >= cpu.read_reg(instruction.rs2))



def execute_jal(cpu, instruction):
   cpu.write_reg(instruction.rd, cpu.pc + 4) #saves the return address in rd then jumps to PC + offset
   return True, cpu.pc + JAL_offset(instruction)


def execute_jalr(cpu, instruction):
    jump = (cpu.read_reg(instruction.rs1) + instruction.imm_i) & ~1 #reads rs1 before writing rd, because rd and rs1 could be in the same register
    cpu.write_reg(instruction.rd, cpu.pc + 4)
    return True, jump


def execute_ecall(cpu, instruction):
    call = cpu.read_reg(17)
    if call == 10: #10 = exit
        cpu.halted = True
        return True, None
    from cpu import SimulatorError
    raise SimulatorError