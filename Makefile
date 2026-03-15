.PHONY: fix check check-backend check-docs artifacts

# Refresh the checked-in machine-readable docs and API artifacts only.
artifacts:
	uv run python scripts/generate_machine_artifacts.py

# Auto-fix formatting and generated files, then run the full validation loop.
fix:
	uv run python scripts/repo_loop.py fix

# Run the same read-only validation path used by CI.
check:
	uv run python scripts/repo_loop.py check

# Run only the backend validation path.
check-backend:
	uv run python scripts/repo_loop.py check --scope backend

# Run docs/site validation plus generated artifact checks.
check-docs:
	uv run python scripts/repo_loop.py check --scope docs