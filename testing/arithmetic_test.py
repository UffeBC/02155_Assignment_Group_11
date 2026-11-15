import unittest
import sys
import os

# adding the parent directory to the path to import the arithmetic module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import arithmetic

# Create a mask for 32-bit unsigned integers
MASK32 = 0xFFFFFFFF

# A lightweight CPU class for testing purposes is created
class TestCPU:
    def __init__(self):
        self.registers = {0: 0}  
        self.written = {}
        self.pc = 0x1000 # Dummy value for AUIPC test

    def read_reg(self, index):
        # return 0 for register 0, otherwise return the value in the register 
        return 0 if index == 0 else self.registers.get(index, 0)

    def write_reg(self, index, value):
        # mirror the real cpu behavior, mask to 32 bits, ignore writes to x0
        if index != 0:
            self.written[index] = value & MASK32


# A fake instruction class for testing purposes is created, holding the necessary fields for the arithmetic operations
class TestInstruction:
    def __init__(self, opcode=0, funct3=0, funct7=0, rs1=0, rs2=0, rd=0, imm_i=0, word=0):
        self.opcode = opcode
        self.funct3 = funct3
        self.funct7 = funct7     
        self.rs1 = rs1
        self.rs2 = rs2
        self.rd = rd
        self.imm_i = imm_i
        self.word = word

class TestArithmetic(unittest.TestCase):
    # create a new instance of the TestCPU class for each test
    def setUp(self):
        self.cpu = TestCPU()

    # I type tests
    def test_addi(self):
        self.cpu.registers[1] = 10
        inst=TestInstruction(rs1=1, rd=2, imm_i=-3)
        arithmetic.execute_addi(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 7)  # 10 + (-3) = 7

    def test_slti(self):
        self.cpu.registers[1] = 0xFFFFFFFF  # -1 in signed 32-bit representation
        inst=TestInstruction(rs1=1, rd=2, imm_i=5)
        arithmetic.execute_slti(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 1)  # -1 < 5, so rd should be set to 1

    def test_sltiu(self):
        self.cpu.registers[1] = 0xFFFFFFFF  # -1 in signed, but 4294967295 in unsigned
        inst=TestInstruction(rs1=1, rd=2, imm_i=5)
        arithmetic.execute_sltiu(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 0)  # 4294967295 > 5, so rd should be set to 0

    def test_xori(self):
        self.cpu.registers[1] = 0b1010
        inst=TestInstruction(rs1=1, rd=2, imm_i=0b1100)
        arithmetic.execute_xori(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 0b0110)  # 0b0110 XOR 0b1100 = 0b0110

    def test_ori(self):
        self.cpu.registers[1] = 0b1010
        inst=TestInstruction(rs1=1, rd=2, imm_i=0b1100)
        arithmetic.execute_ori(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 0b1110)  # 0b1010 OR 0b1100 = 0b1110

    def test_andi(self):
        self.cpu.registers[1] = 0b1010
        inst=TestInstruction(rs1=1, rd=2, imm_i=0b1100)
        arithmetic.execute_andi(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 0b1000)  # 0b1010 AND 0b1100 = 0b1000

    def test_slli(self):
        self.cpu.registers[1] = 1
        inst=TestInstruction(rs1=1, rd=2, imm_i=5)
        arithmetic.execute_slli(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 32)  # 1 << 5 = 32

    def test_srli(self):
        self.cpu.registers[1] = 0xFFFFFFFF  # all 1
        inst=TestInstruction(rs1=1, rd=2, imm_i=4)
        arithmetic.execute_srli(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 0x0FFFFFFF)  # zeros shifted in from the left

    def test_srai(self):
        self.cpu.registers[1] = 0xFFFFFFFF  # -1 in signed,
        inst=TestInstruction(rs1=1, rd=2, imm_i=4)
        arithmetic.execute_srai(self.cpu, inst)
        self.assertEqual(self.cpu.written[2], 0xFFFFFFFF)  # 1 shifted in, sign bit preserved

    # R type tests
    def test_add(self):
        self.cpu.registers[1] = 15
        self.cpu.registers[2] = 20
        inst=TestInstruction(rs1=1, rs2=2, rd=3)
        arithmetic.execute_add(self.cpu, inst)
        self.assertEqual(self.cpu.written[3], 35)  # 15 + 20 = 35

    def test_sub(self):
        self.cpu.registers[1] = 10
        self.cpu.registers[2] = 15
        inst=TestInstruction(rs1=1, rs2=2, rd=3)
        arithmetic.execute_sub(self.cpu, inst)
        self.assertEqual(self.cpu.written[3], 0xFFFFFFFB)  # 10 - 15 = -5 wrapped to 32 bits

    def test_sll(self):
        self.cpu.registers[1] = 1
        self.cpu.registers[2] = 4
        inst=TestInstruction(rs1=1, rs2=2, rd=3)
        arithmetic.execute_sll(self.cpu, inst)
        self.assertEqual(self.cpu.written[3], 16)  # 1 << 4 = 16

    def test_slt(self):
        self.cpu.registers[1] = 0xFFFFFFFF  # -1 in signed
        self.cpu.registers[2] = 10
        inst=TestInstruction(rs1=1, rs2=2, rd=3)
        arithmetic.execute_slt(self.cpu, inst)
        self.assertEqual(self.cpu.written[3], 1)  # -1 < 10, so rd should be set to 1

    def test_sltu(self):
        self.cpu.registers[1] = 0xFFFFFFFF  # 4294967295 in unsigned
        self.cpu.registers[2] = 10
        inst=TestInstruction(rs1=1, rs2=2, rd=3)
        arithmetic.execute_sltu(self.cpu, inst)
        self.assertEqual(self.cpu.written[3], 0)  # 4294967295 > 10, so rd should be set to 0

    # U type tests
    def test_lui(self):
        inst=TestInstruction(rd=1, word=0x12345000) # simulate the u type raw instruction (upper 20 bits)
        arithmetic.execute_lui(self.cpu, inst)
        self.assertEqual(self.cpu.written[1], 0x12345000)  # upper immediate value loaded

    def test_auipc(self):
        self.cpu.pc = 0x1000  # Set a dummy program counter value
        inst=TestInstruction(rd=1, word=0x00004000) # simulate the u type raw instruction (upper 20 bits)
        arithmetic.execute_auipc(self.cpu, inst)
        self.assertEqual(self.cpu.written[1], 0x00005000)  # 0x00004000 + 0x1000 = 0x00005000

    # Dispather test
    def test_execute_dispatcher(self):
        # test if the dispatcher correctly routs the ADD instruction
        self.cpu.registers[1] = 10
        self.cpu.registers[2] = 30
        inst=TestInstruction(opcode=0x33, funct3=0, funct7=0, rs1=1, rs2=2, rd=3)  # ADD instruction

        handled, next_pc = arithmetic.execute(self.cpu, inst)

        self.assertTrue(handled)
        self.assertIsNone(next_pc)
        self.assertEqual(self.cpu.written[3], 40)  # 10 + 30 = 40

if __name__ == '__main__':
    unittest.main()