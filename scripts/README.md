# Scripts

This folder contains the repo automation entrypoints that keep the backend, docs, and machine-readable artifacts aligned.

## Purpose

The scripts here exist to make the repo follow a single repeatable loop:

1. Generate machine-readable artifacts from source.
2. Apply formatting in the correct order.
3. Re-generate artifacts if formatting changed docs.
4. Run validation so the repo finishes in a clean state.

That loop is important because docs formatting can change generated summaries, which means a naive `generate once, then format, then check` flow can leave generated files stale.

## Scripts

### `generate_machine_artifacts.py`

Generates the checked-in machine-readable files used for ingestion and tool-building:

- `website/static/openapi.json`
- `website/static/docs-index.json`
- `website/static/llms.txt`

It derives those files from the FastAPI app and the Markdown docs under `website/docs/`.

Commands:

```bash
uv run python scripts/generate_machine_artifacts.py
uv run python scripts/generate_machine_artifacts.py --check
```

Use `--check` in automation when you want drift detection without writing files.

### `repo_loop.py`

Runs the full repo loop in one of two modes:

- `fix`: mutate files into the expected state, then validate.
- `check`: validate only.

Commands:

```bash
uv run python scripts/repo_loop.py fix
uv run python scripts/repo_loop.py check
uv run python scripts/repo_loop.py check --scope backend
uv run python scripts/repo_loop.py check --scope docs
```

## Repo integration

### Local development

Top-level shortcuts are provided by the repo `Makefile`:

```bash
make fix
make check
make artifacts
make check-backend
make check-docs
```

Recommended usage:

- Run `make fix` before pushing when you changed docs, metadata, or API routes.
- Run `make check` when you want the same read-only validation path used by CI.
- Run `make check-backend` or `make check-docs` when you want to match a single CI job locally.

### CI and GitHub Actions

The repo uses two different workflow roles:

- `.github/workflows/ci.yml` is read-only validation. It should fail on drift, not rewrite the branch.
- `.github/workflows/autofix.yml` is the write-enabled automation loop. It runs on pushes to `main`, applies the fix loop, and opens or updates an automation pull request with the resulting changes.

This split is deliberate. Validation workflows should stay predictable, while write-enabled automation should be isolated so it does not mutate pull request branches or create confusing side effects during review.

The generated artifact drift check lives with the docs/site validation path because `docs-index.json` and `llms.txt` are derived from documentation content as well as API metadata. That keeps docs-originated failures out of the backend-only job.

### Deployment relationship

The docs deployment workflow continues to build from repository state. Once an autofix PR is merged, those generated files and normalized docs changes become the new source of truth and will be picked up by the normal docs deployment workflow.