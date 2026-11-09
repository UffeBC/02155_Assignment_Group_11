"""Focused baseline tests; run with python3 -m unittest -v."""
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cpu import CPU, Instruction, SimulatorError, sign_extend
from memory import Memory, MemoryAccessError

ROOT = Path(__file__).resolve().parent


def program(*words):
    return struct.pack("<" + "I" * len(words), *words)


def addi(rd, rs1, immediate):
    return ((immediate & 0xFFF) << 20) | (rs1 << 15) | (rd << 7) | 0x13


def beq(rs1, rs2, offset):
    return (((offset >> 12) & 1) << 31 | ((offset >> 5) & 63) << 25
            | rs2 << 20 | rs1 << 15 | ((offset >> 1) & 15) << 8
            | ((offset >> 11) & 1) << 7 | 0x63)


class BaselineTests(unittest.TestCase):
    def test_register_arithmetic(self):
        # Literal instruction encodings: ADD, SUB, SLT, SLTU x3, x1, x2.
        cases = (
            (0x002081B3, 5, 6, 11),
            (0x002081B3, 0xFFFFFFFF, 1, 0),
            (0x402081B3, 5, 6, 0xFFFFFFFF),
            (0x402081B3, 0x80000000, 1, 0x7FFFFFFF),
            (0x0020A1B3, 0xFFFFFFFF, 1, 1),
            (0x0020A1B3, 0x80000000, 0x7FFFFFFF, 1),
            (0x0020A1B3, 7, 7, 0),
            (0x0020B1B3, 0xFFFFFFFF, 1, 0),
            (0x0020B1B3, 1, 0xFFFFFFFF, 1),
            (0x0020B1B3, 7, 7, 0),
        )
        for word, left, right, expected in cases:
            with self.subTest(word=hex(word), left=left, right=right):
                cpu = CPU(program(word))
                cpu.write_reg(1, left)
                cpu.write_reg(2, right)
                cpu.run()
                self.assertEqual(cpu.read_reg(3), expected)
                self.assertEqual(cpu.pc, 4)

    def test_register_arithmetic_zero_and_overlapping_destination(self):
        for word in (0x002081B3, 0x402081B3, 0x0020A1B3, 0x0020B1B3):
            with self.subTest(word=hex(word)):
                cpu = CPU(program(word & ~(31 << 7)))  # rd = x0
                cpu.write_reg(1, 5)
                cpu.write_reg(2, 6)
                cpu.run()
                self.assertEqual(cpu.read_reg(0), 0)
        cpu = CPU(program(0x002080B3))  # ADD x1, x1, x2
        cpu.write_reg(1, 5)
        cpu.write_reg(2, 6)
        cpu.run()
        self.assertEqual(cpu.read_reg(1), 11)

    def test_unsupported_register_arithmetic_encoding(self):
        # MUL shares ADD's funct3 but has funct7=1; it is not implemented.
        with self.assertRaisesRegex(SimulatorError, "Unsupported"):
            CPU(program(0x022081B3)).run()

    def test_addi_negative_wrap_and_zero(self):
        cpu = CPU(program(addi(1, 0, -1), addi(2, 1, 1), addi(0, 0, 9)))
        self.assertEqual(cpu.run(), 3)
        self.assertEqual(cpu.registers[:3], [0, 0xFFFFFFFF, 0])
        self.assertEqual(cpu.pc, 12)

    def test_taken_and_untaken_branch(self):
        cpu = CPU(program(addi(1, 0, 1), beq(0, 0, 8), addi(2, 0, 99),
                          beq(0, 1, 8), addi(3, 0, 7)))
        self.assertEqual(cpu.run(), 4)
        self.assertEqual(cpu.read_reg(2), 0)
        self.assertEqual(cpu.read_reg(3), 7)

    def test_backward_branch(self):
        cpu = CPU(program(addi(1, 1, 1), beq(0, 0, -4)))
        cpu.step()
        cpu.step()
        self.assertEqual(cpu.pc, 0)
        cpu.step()
        self.assertEqual(cpu.read_reg(1), 2)

    def test_immediates(self):
        for offset in (-4096, -2048, -4, 0, 2048, 4094):
            self.assertEqual(Instruction.decode(beq(1, 2, offset)).imm_b, offset)
        self.assertEqual(sign_extend(0x800, 12), -2048)
        self.assertEqual(Instruction.decode(addi(1, 0, 2047)).imm_i, 2047)

    def test_lw_negative_offset_and_unaligned_data(self):
        lw = (0xFFC << 20) | (1 << 15) | (2 << 12) | (2 << 7) | 0x03
        cpu = CPU(program(lw))
        cpu.write_reg(1, 105)
        cpu.memory.write_word(101, 0x89ABCDEF)
        cpu.run()
        self.assertEqual(cpu.read_reg(2), 0x89ABCDEF)
        self.assertEqual(cpu.memory.read_byte(101), 0xEF)

    def test_lw_out_of_bounds_even_with_zero_destination(self):
        cpu = CPU(program((1 << 15) | (2 << 12) | 0x03))
        cpu.write_reg(1, 1024 * 1024 - 3)
        with self.assertRaises(MemoryAccessError):
            cpu.run()

    def test_memory_bounds_and_width(self):
        memory = Memory()
        memory.write_byte(0, 0x1FF)
        self.assertEqual(memory.read_byte(0), 255)
        memory.write_word(len(memory.data) - 4, -1)
        self.assertEqual(memory.read_word(len(memory.data) - 4), 0xFFFFFFFF)
        for address in (-1, len(memory.data) - 3):
            with self.assertRaises(MemoryAccessError):
                memory.read_word(address)

    def test_errors_and_execution_limit(self):
        with self.assertRaises(SimulatorError):
            CPU(b"abc")
        with self.assertRaises(MemoryAccessError):
            CPU(bytes(1024 * 1024 + 4))
        with self.assertRaisesRegex(SimulatorError, "Unsupported.*PC"):
            CPU(program(0x00000073)).run()
        with self.assertRaisesRegex(SimulatorError, "Execution limit"):
            CPU(program(beq(0, 0, 0))).run(max_steps=3)
        with self.assertRaisesRegex(SimulatorError, "Invalid instruction address"):
            CPU(program(beq(0, 0, 2))).run()

    def test_empty_program(self):
        cpu = CPU(b"")
        self.assertEqual(cpu.run(), 0)
        self.assertEqual(cpu.register_dump(), bytes(128))

    def test_dump_matches_supplied_format(self):
        expected = (ROOT / "task1" / "addpos.res").read_bytes()
        self.assertEqual(len(expected), 128)
        cpu = CPU(b"")
        for index, value in ((10, 5), (11, 6), (12, 11), (17, 10)):
            cpu.write_reg(index, value)
        self.assertEqual(cpu.register_dump(), expected)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "demo.bin"
            output = Path(directory) / "demo.res"
            source.write_bytes(program(addi(1, 0, 42)))
            result = subprocess.run(
                [sys.executable, str(ROOT / "main.py"), str(source), str(output)],
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("x01: 0x0000002a (42)", result.stdout)
            expected = [0] * 32
            expected[1] = 42
            self.assertEqual(output.read_bytes(), struct.pack("<32I", *expected))


if __name__ == "__main__":
    unittest.main()
