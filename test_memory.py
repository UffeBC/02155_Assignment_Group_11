"""Run with: py -3 -m unittest -v test_memory"""
import unittest

from cpu import CPU, SimulatorError
from memory import Memory, MemoryAccessError
from test_simulator import addi, beq, program


def load(funct3, rd=2, rs1=1, offset=0):
    # Build a real I-type instruction so the tests also exercise CPU decoding.
    # Masking the offset gives its 12-bit encoding, including negative offsets.
    return ((offset & 0xFFF) << 20 | rs1 << 15 | funct3 << 12
            | rd << 7 | 0x03)


def store(funct3, rs2=2, rs1=1, offset=0):
    # S-type instructions split the offset around the register and funct3 fields.
    offset &= 0xFFF
    return ((offset >> 5) << 25 | rs2 << 20 | rs1 << 15
            | funct3 << 12 | (offset & 31) << 7 | 0x23)


class MemoryTests(unittest.TestCase):
    def test_halfword_helpers(self):
        # Use a small memory so the final valid address is easy to check.
        memory = Memory(8)
        memory.write_halfword(1, 0x123AB)
        # Only 0x23AB fits in 16 bits; little-endian order puts 0xAB first.
        self.assertEqual(memory.data[1:3], bytes([0xAB, 0x23]))
        self.assertEqual(memory.read_halfword(1), 0x23AB)
        memory.write_halfword(6, -1)
        # A two-byte write at address 6 exactly fills the remaining space.
        self.assertEqual(memory.read_halfword(6), 0xFFFF)

    def test_loads(self):
        # These cases are LB, LH, LW, LBU and LHU, in that order.
        # LB/LH must fill the upper bits with ones when the loaded sign bit is set.
        cases = [(0, 0xFFFFFF80), (1, 0xFFFF8180), (2, 0x12348180),
                 (4, 0x80), (5, 0x8180)]
        for funct3, expected in cases:
            for offset in (-2048, -4, 0, 2047):
                # Include both limits of a signed 12-bit offset and a small negative.
                with self.subTest(funct3=funct3, offset=offset):
                    cpu = CPU(program(load(funct3, offset=offset)))
                    cpu.write_reg(1, 4097 - offset)
                    # Every case should reach 4097. This also checks unaligned loads.
                    cpu.memory.write_word(4097, 0x12348180)
                    cpu.run()
                    self.assertEqual(cpu.read_reg(2), expected)
                    self.assertEqual(cpu.pc, 4)

    def test_positive_signed_loads(self):
        # The largest positive byte/halfword must stay positive for LB and LH.
        for funct3, value in ((0, 0x7F), (1, 0x7FFF)):
            with self.subTest(funct3=funct3):
                cpu = CPU(program(load(funct3)))
                cpu.write_reg(1, 100)
                cpu.memory.write_word(100, value)
                cpu.run()
                self.assertEqual(cpu.read_reg(2), value)

    def test_stores(self):
        # SB, SH and SW should write exactly 1, 2 and 4 bytes respectively.
        for funct3, width in ((0, 1), (1, 2), (2, 4)):
            for offset in (-2048, -4, 0, 2047):
                with self.subTest(funct3=funct3, offset=offset):
                    cpu = CPU(program(store(funct3, offset=offset)))
                    cpu.write_reg(1, 4097 - offset)
                    cpu.write_reg(2, 0x89ABCDEF)
                    cpu.memory.data[4096:4102] = b'\x55' * 6
                    # Surround the target with a known value to detect extra writes.
                    cpu.run()
                    expected = b'\xEF\xCD\xAB\x89'[:width]
                    # Check the stored bytes in little-endian order and both neighbours.
                    self.assertEqual(cpu.memory.data[4097:4097 + width], expected)
                    self.assertEqual(cpu.memory.read_byte(4096), 0x55)
                    self.assertEqual(cpu.memory.read_byte(4097 + width), 0x55)
                    self.assertEqual(cpu.pc, 4)

    def test_bounds_and_no_partial_store(self):
        # Reuse the same checks for byte, halfword and word helpers.
        # getattr(memory, read/write) selects the method named by each string.
        for width, read, write in ((1, 'read_byte', 'write_byte'),
                                   (2, 'read_halfword', 'write_halfword'),
                                   (4, 'read_word', 'write_word')):
            memory = Memory(8)
            getattr(memory, write)(8 - width, -1)
            # This access ends exactly at the last byte and must succeed.
            self.assertEqual(getattr(memory, read)(8 - width), (1 << (8 * width)) - 1)
            for address in (-1, 9 - width):
                # Try below address zero and one byte beyond the valid end.
                with self.subTest(width=width, address=address):
                    before = bytes(memory.data)
                    with self.assertRaises(MemoryAccessError):
                        getattr(memory, read)(address)
                    with self.assertRaises(MemoryAccessError):
                        getattr(memory, write)(address, 0)
                    self.assertEqual(bytes(memory.data), before)
                    # Failed writes must leave the entire memory unchanged.

    def test_zero_register_and_address_wrap(self):
        # Loading into x0 discards the result; storing x0 must write a zero byte.
        cpu = CPU(program(load(4, rd=0), store(0, rs2=0)))
        cpu.write_reg(1, 100)
        cpu.memory.write_byte(100, 255)
        cpu.run()
        self.assertEqual(cpu.read_reg(0), 0)
        self.assertEqual(cpu.memory.read_byte(100), 0)
        for word in (load(4, offset=1), store(0, offset=1)):
            # 0xFFFFFFFF + 1 wraps to address 0 for both loads and stores.
            cpu = CPU(program(word))
            cpu.write_reg(1, 0xFFFFFFFF)
            cpu.run()  # Address wraps to zero, which is valid memory.
            self.assertEqual(cpu.pc, 4)

    def test_invalid_access_even_when_loading_x0(self):
        # Discarding the result does not make an out-of-bounds load valid.
        for funct3, width in ((0, 1), (1, 2), (2, 4), (4, 1), (5, 2)):
            cpu = CPU(program(load(funct3, rd=0)))
            cpu.write_reg(1, len(cpu.memory.data) - width + 1)
            with self.assertRaises(MemoryAccessError):
                cpu.run()
        for funct3, width in ((0, 1), (1, 2), (2, 4)):
            # Each store extends one byte past the end of memory and must fail.
            cpu = CPU(program(store(funct3)))
            cpu.write_reg(1, len(cpu.memory.data) - width + 1)
            with self.assertRaises(MemoryAccessError):
                cpu.run()

    def test_unsupported_memory_instructions(self):
        # These funct3 values are not supported RV32I loads/stores. The CPU
        # should report them instead of silently treating them as another size.
        for word in (load(3), load(6), load(7), store(3), store(4)):
            with self.subTest(word=hex(word)):
                with self.assertRaisesRegex(SimulatorError, 'Unsupported'):
                    CPU(program(word)).run()

    def test_memory_with_arithmetic_and_branch(self):
        # Run a small program through the real CPU to check that the three
        # instruction modules work together and advance the PC correctly.
        cpu = CPU(program(
            addi(1, 0, 101),       # Base address (unaligned).
            addi(2, 0, -5),
            store(2),             # SW x2, 0(x1).
            load(2, rd=3),        # LW x3, 0(x1).
            addi(3, 3, 5),        # Loaded -5 becomes zero.
            beq(3, 0, 8),         # Skip the next instruction.
            addi(4, 0, 99),
            addi(4, 0, 7)))
        self.assertEqual(cpu.run(), 7)
        # Eight instructions were loaded, but the taken branch skips one.
        self.assertEqual(cpu.read_reg(3), 0)
        self.assertEqual(cpu.read_reg(4), 7)
        self.assertEqual(cpu.memory.read_word(101), 0xFFFFFFFB)


if __name__ == '__main__':
    unittest.main()
