"""Shared little-endian memory and the initial load instruction handler."""


class MemoryAccessError(ValueError):
    pass


class Memory:
    def __init__(self, size=1024 * 1024):
        self.data = bytearray(size)

    def _check(self, address, size):
        if address < 0 or address + size > len(self.data):
            raise MemoryAccessError(
                f"Memory access outside memory: address={address}, size={size}")

    def load_program(self, program):
        self._check(0, len(program))
        self.data[:len(program)] = program

    def read_byte(self, address):
        self._check(address, 1)
        return self.data[address]

    def write_byte(self, address, value):
        self._check(address, 1)
        self.data[address] = value & 0xFF

    def read_word(self, address):
        self._check(address, 4)
        return int.from_bytes(self.data[address:address + 4], "little")

    def write_word(self, address, value):
        self._check(address, 4)
        self.data[address:address + 4] = (value & 0xFFFFFFFF).to_bytes(4, "little")


def execute_load_store(cpu, instruction):
    if instruction.opcode == 0x03 and instruction.funct3 == 2:  # LW
        address = (cpu.read_reg(instruction.rs1) + instruction.imm_i) & 0xFFFFFFFF
        cpu.write_reg(instruction.rd, cpu.memory.read_word(address))
        return True, None
    # TODO: other loads and all stores.
    return False, None
