"""Run local validation and unit tests without network or live adapters."""

from __future__ import annotations

from pathlib import Path
from subprocess import run
from datetime import datetime, timezone
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, help="optional local JSON report")
    args = parser.parse_args()
    commands = ([sys.executable, "scripts/build_registry.py"],
                [sys.executable, "scripts/validate.py"],
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"])
    results = []
    for command in commands:
        process = run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        results.append({"command": command[1:], "status": "PASS" if process.returncode == 0 else "FAIL",
                        "exit_code": process.returncode, "stdout": process.stdout.strip(), "stderr": process.stderr.strip()})
    report = {"product": "F.R.I.D.A.Y.", "author": "RogueKI",
              "checked_at": datetime.now(timezone.utc).isoformat(), "results": results}
    if args.report:
        target = args.report.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(f"{result['status']}: {' '.join(result['command'])}")
        if result["status"] == "FAIL":
            print(result["stderr"] or result["stdout"], file=sys.stderr)
    return 0 if all(result["status"] == "PASS" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
