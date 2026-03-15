from __future__ import annotations

import argparse
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[1]
WEBSITE_DIR: Final = ROOT / "website"


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...]
    cwd: Path


FIX_STEPS: Final[tuple[Step, ...]] = (
    Step(
        name="Generate machine-readable artifacts",
        command=("uv", "run", "python", "scripts/generate_machine_artifacts.py"),
        cwd=ROOT,
    ),
    Step(
        name="Format Python",
        command=("uv", "run", "ruff", "format", "."),
        cwd=ROOT,
    ),
    Step(
        name="Format docs site",
        command=("npm", "run", "format"),
        cwd=WEBSITE_DIR,
    ),
    Step(
        name="Regenerate artifacts after formatting",
        command=("uv", "run", "python", "scripts/generate_machine_artifacts.py"),
        cwd=ROOT,
    ),
)


CHECK_STEPS: Final[tuple[Step, ...]] = (
    Step(
        name="Lint Python",
        command=("uv", "run", "ruff", "check", "."),
        cwd=ROOT,
    ),
    Step(
        name="Check Python formatting",
        command=("uv", "run", "ruff", "format", "--check", "."),
        cwd=ROOT,
    ),
    Step(
        name="Run tests",
        command=("uv", "run", "pytest"),
        cwd=ROOT,
    ),
    Step(
        name="Check generated artifacts",
        command=("uv", "run", "python", "scripts/generate_machine_artifacts.py", "--check"),
        cwd=ROOT,
    ),
    Step(
        name="Check docs formatting",
        command=("npm", "run", "format:check"),
        cwd=WEBSITE_DIR,
    ),
    Step(
        name="Typecheck docs site",
        command=("npm", "run", "typecheck"),
        cwd=WEBSITE_DIR,
    ),
    Step(
        name="Build docs site",
        command=("npm", "run", "build"),
        cwd=WEBSITE_DIR,
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the repo automation loop in fix or check mode."
    )
    parser.add_argument(
        "mode",
        choices=("fix", "check"),
        help="fix updates generated files and formatting before validating; check only validates.",
    )
    return parser.parse_args()


def run_step(step: Step) -> None:
    command_preview = shlex.join(step.command)
    print(f"[{step.name}] {command_preview}")
    subprocess.run(step.command, cwd=step.cwd, check=True)


def main() -> int:
    args = parse_args()
    steps = CHECK_STEPS if args.mode == "check" else (*FIX_STEPS, *CHECK_STEPS)
    for step in steps:
        run_step(step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
