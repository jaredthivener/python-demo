import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

repo_loop = importlib.import_module("scripts.repo_loop")


def _step_names(steps: tuple[repo_loop.Step, ...]) -> list[str]:
    return [step.name for step in steps]


def test_backend_check_scope_only_runs_backend_validation() -> None:
    steps = repo_loop.steps_for(mode="check", scope="backend")

    assert _step_names(steps) == [
        "Lint Python",
        "Check Python formatting",
        "Run tests",
    ]


def test_docs_check_scope_includes_artifact_verification() -> None:
    steps = repo_loop.steps_for(mode="check", scope="docs")

    assert _step_names(steps) == [
        "Check generated artifacts",
        "Check docs formatting",
        "Typecheck docs site",
        "Build docs site",
    ]


def test_full_fix_scope_runs_fix_then_all_checks() -> None:
    steps = repo_loop.steps_for(mode="fix", scope="full")
    names = _step_names(steps)

    assert names[:4] == [
        "Generate machine-readable artifacts",
        "Format Python",
        "Format docs site",
        "Regenerate artifacts after formatting",
    ]
    assert names[-4:] == [
        "Check generated artifacts",
        "Check docs formatting",
        "Typecheck docs site",
        "Build docs site",
    ]
