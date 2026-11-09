"""Processor state, instruction decoding, and the execution loop."""
from dataclasses import dataclass
import struct
import arithmetic
import control_flow
from memory import Memory, execute_load_store

MASK32 = 0xFFFFFFFF


class SimulatorError(Exception):
    """Invalid or unsupported execution."""


def sign_extend(value, bits):
    value &= (1 << bits) - 1
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def signed32(value):
    return sign_extend(value, 32)


@dataclass(frozen=True)
class Instruction:
    word: int
    opcode: int
    rd: int
    funct3: int
    rs1: int
    rs2: int
    funct7: int
    imm_i: int
    imm_b: int

    @classmethod
    def decode(cls, word):
        branch = (((word >> 31) & 1) << 12
                  | ((word >> 7) & 1) << 11
                  | ((word >> 25) & 63) << 5
                  | ((word >> 8) & 15) << 1)
        return cls(word, word & 127, (word >> 7) & 31,
                   (word >> 12) & 7, (word >> 15) & 31,
                   (word >> 20) & 31, (word >> 25) & 127,
                   sign_extend(word >> 20, 12), sign_extend(branch, 13))


class CPU:
    def __init__(self, program):
        if len(program) % 4:
            raise SimulatorError("Program size must be a multiple of 4 bytes")
        self.memory = Memory()
        self.memory.load_program(program)
        self.program_size = len(program)
        self.registers = [0] * 32
        self.pc = 0

    def read_reg(self, index):
        return 0 if index == 0 else self.registers[index]

    def write_reg(self, index, value):
        if index != 0:
            self.registers[index] = value & MASK32

    def step(self):
        """Execute once; return False if PC has passed the program."""
        if self.pc >= self.program_size:
            return False
        if self.pc < 0 or self.pc % 4:
            raise SimulatorError(f"Invalid instruction address 0x{self.pc:08x}")
        instruction = Instruction.decode(self.memory.read_word(self.pc))
        # Handlers return (handled, next_pc). None selects the default PC + 4.
        for handler in (arithmetic.execute, control_flow.execute, execute_load_store):
            handled, next_pc = handler(self, instruction)
            if handled:
                self.pc = ((self.pc + 4) if next_pc is None else next_pc) & MASK32
                return True
        raise SimulatorError(
            f"Unsupported instruction 0x{instruction.word:08x} at PC 0x{self.pc:08x}")

    def run(self, max_steps=1_000_000, trace=False):
        steps = 0
        while self.pc < self.program_size:
            if steps >= max_steps:
                raise SimulatorError(f"Execution limit reached ({max_steps} instructions)")
            self.step()
            steps += 1
            if trace:
                print(f"After instruction {steps}, PC=0x{self.pc:08x}")
                print(self.format_registers())
        return steps

    def register_dump(self):
        return struct.pack("<32I", *(self.read_reg(i) for i in range(32)))

    def format_registers(self):
        return "\n".join(
            f"x{i:02d}: 0x{self.read_reg(i):08x} ({signed32(self.read_reg(i))})"
            for i in range(32))
