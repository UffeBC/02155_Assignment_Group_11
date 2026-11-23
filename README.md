# RV32I simulator — Group 11

This simulator implements the RV32I subset required by the assignment using
Python 3.9+ and its standard library. It supports integer arithmetic, logic,
shifts, comparisons, LUI and AUIPC, all six conditional branches, JAL and JALR,
all eight load/store instructions, and exit via `ecall 10`.

## Run

On Ubuntu:

```sh
python3 main.py examples/baseline.bin registers.res
python3 main.py examples/baseline.bin registers.res --trace
python3 -m unittest -v
python3 -m unittest -v testing.arithmetic_test
python3 run_all_tests.py
python3 run_all_tests.py task1 --timeout 10
```

On Windows, use `py -3` in place of `python3`.

```
py -3 main.py examples/baseline.bin registers.res
py -3 main.py examples/baseline.bin registers.res --trace
py -3 -m unittest -v
py -3 -m unittest -v testing.arithmetic_test
py -3 -m unittest -v test_memory
py -3 run_all_tests.py
py -3 run_all_tests.py task1 --timeout 10
```

The example finishes with x1=16,
x2=0x02a00213, x3=0, x4=42. Its last instruction is also loaded as data by LW.
Compare its output with `examples/baseline.res`.
The simulator stops when the PC reaches or passes the end of the loaded program
or when it executes an `ecall` with `a7` (`x17`) set to 10.

Input is raw little-endian 32-bit instructions, loaded at address zero.
Output is exactly 128 bytes: x0–x31 as unsigned little-endian 32-bit words,
matching the supplied .res files. Final registers are also printed.
The default execution limit is 1,000,000 instructions; change it with
`--max-steps N`. Errors return a nonzero exit status without writing a new dump.

## Shared contracts

- CPU owns PC and register state. Registers start at zero, including SP.
  Use `read_reg(index)` and `write_reg(index, value)`; writes mask to 32 bits
  and ignore x0. Do not modify the register list directly in handlers.
- Memory is a shared, zero-initialized 1 MiB byte array. Program bytes occupy its
  beginning. The separate `program_size` determines the execution boundary.
- Memory helpers check bounds and use little-endian byte order. Unaligned data
  accesses are supported (the supplied width test uses them); instruction
  fetch requires four-byte alignment.
- Memory tests are in `test_memory.py`. They cover all eight load/store instructions,
  signed values, offsets, bounds, and a program using arithmetic and BEQ together.
  Store handlers decode the signed S-immediate from `instruction.word` in memory.py.
- `Instruction.decode(word)` provides opcode, rd, rs1, rs2, funct3, funct7,
  signed I-immediate, and signed B-immediate. Handlers extract other immediate
  formats from the instruction word. `sign_extend` and `signed32` are in `cpu.py`.
- Each handler receives `(cpu, instruction)` and returns
  `(handled, next_pc)`. Return `(False, None)` for instructions you do not handle,
  `(True, None)` for normal PC+4, or `(True, target)` for a jump/taken branch.
  Only CPU updates PC, wrapping it to 32 bits. Branch targets use the current PC.
- Unsupported instructions raise an error showing the word and PC.
  Exit ECALL sets the CPU's halted state, which ends the execution loop.
- Modules avoid importing CPU at runtime to prevent circular imports. For signed
  comparisons, a local import of `signed32` inside the handler is sufficient.

## Tests

The supplied-program runner discovers .bin/.res pairs, uses a subprocess timeout,
reports mismatches and execution errors, and exits nonzero unless all pass.
Unsupported instructions are reported as errors, not skipped.
On Windows, all 14 programs for Tasks 1–3 and all 15 extra Task 4 programs
matched their expected register dumps byte for byte. The baseline example and
all 40 unit tests also passed.
