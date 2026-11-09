"""Shared little-endian memory and the initial load instruction handler."""


class MemoryAccessError(ValueError):
    pass


class Memory:
    def __init__(self, size=1024 * 1024):
        # Start with 1 MiB of memory filled with zeros.
        self.data = bytearray(size)

    def _check(self, address, size):
        # The whole access must fit inside memory.
        if address < 0 or address + size > len(self.data):
            raise MemoryAccessError(
                f"Memory access outside memory: address={address}, size={size}")

    def load_program(self, program):
        self._check(0, len(program))
        # Put the program at address 0.
        self.data[:len(program)] = program

    def read_byte(self, address):
        self._check(address, 1)
        return self.data[address]

    def write_byte(self, address, value):
        self._check(address, 1)
        # Only keep the lowest 8 bits.
        self.data[address] = value & 0xFF

    def read_word(self, address):
        self._check(address, 4)
        # A word is 4 bytes; the lowest byte comes first in memory.
        return int.from_bytes(self.data[address:address + 4], "little")

    def write_word(self, address, value):
        self._check(address, 4)
        # Keep 32 bits and split them into 4 little-endian bytes.
        self.data[address:address + 4] = (value & 0xFFFFFFFF).to_bytes(4, "little")


def execute_load_store(cpu, instruction):
    if instruction.opcode == 0x03 and instruction.funct3 == 2:  # LW
        # The address is the base register plus the signed offset.
        address = (cpu.read_reg(instruction.rs1) + instruction.imm_i) & 0xFFFFFFFF
        # Read a word from that address into the destination register.
        cpu.write_reg(instruction.rd, cpu.memory.read_word(address))
        return True, None
    # TODO: other loads and all stores.
    return False, None


# TODO: Implement these handlers and call them from execute_load_store().
# Use the existing (handled, next_pc) return convention when implementing them.
# These placeholders are not connected to instruction dispatch yet.


def execute_lb(cpu, instruction):
    pass


def execute_lh(cpu, instruction):
    pass


def execute_lbu(cpu, instruction):
    pass


def execute_lhu(cpu, instruction):
    pass


def execute_sb(cpu, instruction):
    pass


def execute_sh(cpu, instruction):
    pass


def execute_sw(cpu, instruction):
    pass
