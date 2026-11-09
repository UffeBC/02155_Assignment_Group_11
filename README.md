# RV32I simulator — Group 11

This is the agreed team baseline, using Python 3.9+ and only its standard library.
It implements **ADDI, BEQ, and LW**. The full assignment instruction set remains
team work; supplied programs will currently report unsupported instructions.

## Run

On Ubuntu:

```sh
python3 main.py examples/baseline.bin registers.res
python3 main.py examples/baseline.bin registers.res --trace
python3 -m unittest -v
python3 run_all_tests.py
python3 run_all_tests.py task1 --timeout 10
```

On Windows, use `py -3` in place of `python3`.

```
py -3 main.py examples/baseline.bin registers.res
py -3 main.py examples/baseline.bin registers.res --trace
py -3 -m unittest -v
py -3 run_all_tests.py
py -3 run_all_tests.py task1 --timeout 10
```

The example uses all three baseline instructions and finishes with x1=16,
x2=0x02a00213, x3=0, x4=42. Its last instruction is also loaded as data by LW.
Compare its output with `examples/baseline.res`.
The simulator stops when PC reaches or passes the loaded program's end.
Exit ECALL is deliberately left for the control-flow contributor.

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
- `Instruction.decode(word)` provides opcode, rd, rs1, rs2, funct3, funct7,
  signed I-immediate, and signed B-immediate. Add other immediate formats as
  their instructions are implemented. `sign_extend` and `signed32` are in cpu.py.
- Each handler receives `(cpu, instruction)` and returns
  `(handled, next_pc)`. Return `(False, None)` for instructions you do not handle,
  `(True, None)` for normal PC+4, or `(True, target)` for a jump/taken branch.
  Only CPU updates PC, wrapping it to 32 bits. Branch targets use the current PC.
- Unsupported instructions raise an error showing the word and PC.
  The control-flow owner should add an explicit halted state for exit ECALL,
  then make the execution loop honor it.
- Modules avoid importing CPU at runtime to prevent circular imports. For signed
  comparisons, a local import of `signed32` inside the handler is sufficient.

## Contribution plan

| Owner | Files / remaining work |
| --- | --- |
| Baseline owner | main.py, cpu.py, shared memory helpers, tests, integration |
| Arithmetic owner | arithmetic.py: remaining ALU instructions, LUI, AUIPC |
| Control/memory owner | control_flow.py: other branches, JAL/JALR, exit ECALL; memory.py: other loads and stores |
| Everyone | Tests for owned instructions, full-program checks, report, Ubuntu check, TA demo |

Arithmetic remaining: ADD, SUB, SLT, SLTU, XOR, OR, AND, SLL, SRL, SRA,
SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI, LUI, AUIPC.

Control/memory remaining: BNE, BLT, BGE, BLTU, BGEU, JAL, JALR, exit ECALL,
LB, LH, LBU, LHU, SB, SH, SW.

The supplied-program runner discovers .bin/.res pairs, uses a subprocess timeout,
reports mismatches and execution errors, and exits nonzero unless all pass.
Unsupported instructions are reported as errors, not skipped.
Task4 is included as extra validation; the instructions describe Tasks 1–3.
