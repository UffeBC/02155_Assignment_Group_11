"""Run supplied binaries in isolated processes and compare their register dumps."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folders", nargs="*", type=Path, help="defaults to task1 through task4")
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    folders = args.folders or [ROOT / f"task{i}" for i in range(1, 5)]
    programs = sorted({p for folder in folders for p in folder.rglob("*.bin")})
    if not programs:
        print("No .bin programs found.", file=sys.stderr)
        return 1
    passed = 0
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "registers.res"
        for source in programs:
            expected = source.with_suffix(".res")
            if not expected.is_file():
                print(f"ERROR {source}: missing .res file")
                continue
            try:
                result = subprocess.run(
                    [sys.executable, str(ROOT / "main.py"), str(source), str(output)],
                    capture_output=True, text=True, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                print(f"ERROR {source}: timed out after {args.timeout}s")
                continue
            if result.returncode:
                print(f"ERROR {source}: {result.stderr.strip()}")
            elif output.read_bytes() != expected.read_bytes():
                print(f"FAIL  {source}: register dump differs")
            else:
                print(f"PASS  {source}")
                passed += 1
    print(f"{passed}/{len(programs)} passed")
    return 0 if passed == len(programs) else 1


if __name__ == "__main__":
    sys.exit(main())
