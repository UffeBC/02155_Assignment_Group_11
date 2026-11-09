"""Command-line entry point for the baseline RV32I simulator."""
import argparse
from pathlib import Path
import sys
from cpu import CPU, SimulatorError
from memory import MemoryAccessError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("program", type=Path, help="raw RISC-V binary")
    parser.add_argument("output", type=Path, help="binary register dump destination")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--max-steps", type=int, default=1_000_000)
    args = parser.parse_args()
    if args.max_steps <= 0:
        parser.error("--max-steps must be positive")
    if args.program.resolve() == args.output.resolve():
        parser.error("input and output must be different files")
    try:
        cpu = CPU(args.program.read_bytes())
        cpu.run(max_steps=args.max_steps, trace=args.trace)
        args.output.write_bytes(cpu.register_dump())
        print(cpu.format_registers())
    except (OSError, SimulatorError, MemoryAccessError) as error:
        print(f"Simulator error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
