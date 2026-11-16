"""Shared little-endian memory and RV32I load/store instructions."""


class MemoryAccessError(ValueError):
    # Raised when any part of a read or write falls outside the memory array.
    pass


class Memory:
    def __init__(self, size=1024 * 1024):
        # Start with 1 MiB of memory filled with zeros.
        self.data = bytearray(size)

    def _check(self, address, size):
        # Check the full range before reading or writing, so an invalid store
        # cannot change the first few bytes and then fail halfway through.
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

    def read_halfword(self, address):
        self._check(address, 2)
        # Combine two bytes, with the least significant byte at the lower address.
        return int.from_bytes(self.data[address:address + 2], "little")

    def write_halfword(self, address, value):
        self._check(address, 2)
        # A halfword only has room for the lowest 16 bits of the register value.
        self.data[address:address + 2] = (value & 0xFFFF).to_bytes(2, "little")

    def write_word(self, address, value):
        self._check(address, 4)
        # Keep 32 bits and split them into 4 little-endian bytes.
        self.data[address:address + 4] = (value & 0xFFFFFFFF).to_bytes(4, "little")


def execute_load_store(cpu, instruction):
    # The opcode selects loads or stores. funct3 selects the size and, for
    # loads, whether the value should be treated as signed or unsigned.
    if instruction.opcode == 0x03:
        if instruction.funct3 == 0:
            return execute_lb(cpu, instruction)
        elif instruction.funct3 == 1:
            return execute_lh(cpu, instruction)
        elif instruction.funct3 == 2:
            return execute_lw(cpu, instruction)
        elif instruction.funct3 == 4:
            return execute_lbu(cpu, instruction)
        elif instruction.funct3 == 5:
            return execute_lhu(cpu, instruction)
    elif instruction.opcode == 0x23:
        if instruction.funct3 == 0:
            return execute_sb(cpu, instruction)
        elif instruction.funct3 == 1:
            return execute_sh(cpu, instruction)
        elif instruction.funct3 == 2:
            return execute_sw(cpu, instruction)
    # Let the CPU try other handlers or report an unsupported instruction.
    return False, None


def load_address(cpu, instruction):
    # The decoder already gives us a signed I-type offset. Add it to the base
    # register and keep 32 bits, just like a 32-bit CPU address calculation.
    return (cpu.read_reg(instruction.rs1) + instruction.imm_i) & 0xFFFFFFFF


def store_address(cpu, instruction):
    # Stores use an S-type offset: join bits 31:25 and 11:7 into 12 bits.
    offset = ((instruction.word >> 25) << 5) | ((instruction.word >> 7) & 0x1F)
    if offset & 0x800:
        # Bit 11 is the sign bit. Subtract 4096 to get a negative Python value.
        offset -= 0x1000
    return (cpu.read_reg(instruction.rs1) + offset) & 0xFFFFFFFF


def execute_lb(cpu, instruction):
    value = cpu.memory.read_byte(load_address(cpu, instruction))
    # Bit 7 is the sign bit. For example, byte 0xFF represents -1 for LB.
    if value & 0x80:
        value -= 0x100
    cpu.write_reg(instruction.rd, value)
    # write_reg converts negative results to 32 bits and ignores writes to x0.
    # None means the CPU should advance PC by 4, as for all loads and stores.
    return True, None


def execute_lh(cpu, instruction):
    value = cpu.memory.read_halfword(load_address(cpu, instruction))
    # Sign-extend the 16-bit value: 0xFFFF should become 0xFFFFFFFF in rd.
    if value & 0x8000:
        value -= 0x10000
    cpu.write_reg(instruction.rd, value)
    return True, None


def execute_lw(cpu, instruction):
    # A word already fills the 32-bit register, so no sign conversion is needed.
    value = cpu.memory.read_word(load_address(cpu, instruction))
    cpu.write_reg(instruction.rd, value)
    return True, None


def execute_lbu(cpu, instruction):
    # Unsigned load: keep the byte as 0..255, leaving the upper register bits zero.
    value = cpu.memory.read_byte(load_address(cpu, instruction))
    cpu.write_reg(instruction.rd, value)
    return True, None


def execute_lhu(cpu, instruction):
    # Unsigned halfwords stay in the range 0..65535, even if bit 15 is set.
    value = cpu.memory.read_halfword(load_address(cpu, instruction))
    cpu.write_reg(instruction.rd, value)
    return True, None


def execute_sb(cpu, instruction):
    # Store the lowest byte of rs2 at base register rs1 + the signed offset.
    cpu.memory.write_byte(store_address(cpu, instruction), cpu.read_reg(instruction.rs2))
    return True, None


def execute_sh(cpu, instruction):
    # write_halfword keeps the lowest two bytes of rs2 and writes them in order.
    cpu.memory.write_halfword(store_address(cpu, instruction), cpu.read_reg(instruction.rs2))
    return True, None


def execute_sw(cpu, instruction):
    # Store all four bytes of rs2. Stores change memory, not the registers.
    cpu.memory.write_word(store_address(cpu, instruction), cpu.read_reg(instruction.rs2))
    return True, None
