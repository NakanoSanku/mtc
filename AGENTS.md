# Repository Guidelines

## Project Structure & Module Organization

- Root `pyproject.toml` defines a `uv` workspace and ties together the `mtc-*` packages (`mtc-base`, `mtc-adb`, `mtc-maatouch`, `mtc-minitouch`, `mtc-mumu`, `mtc-utils`).
- Each package is a standalone Python project using the `src/mtc` layout (for example `mtc-base/src/mtc/touch.py`); keep new modules under the appropriate package.
- CLI helpers and binaries live under `src/mtc/bin` in each package (for example `mtc-minitouch/src/mtc/bin/minitouch`).

## Build, Test, and Development Commands

- `uv sync` – install all workspace dependencies from `pyproject.toml` and `uv.lock`.
- `uv run pytest` – run the full test suite (add `pytest` to dev dependencies if you introduce tests).
- `uv run python -m mtc.mumu` – run a module directly for local experiments; adjust the module path as needed.
- `uv build` – build all workspace packages with `hatchling`.

## Coding Style & Naming Conventions

- Python 3.9+ with 4-space indentation and PEP 8–style formatting; use type hints for public interfaces.
- Use `snake_case` for functions and variables, `PascalCase` for classes (for example `MuMuTouch`, `CommandBuilder`).
- Prefer clear docstrings and comments (Chinese or English are both fine), mirroring existing modules like `touch.py` and `utils.py`.

## Testing Guidelines

- Use `pytest` for new tests; place them under `<package>/tests/` (for example `mtc-utils/tests/test_utils.py`).
- Name tests `test_<feature>.py` and keep one logical concern per file.
- Ensure `uv run pytest` passes before opening a pull request.

## Commit & Pull Request Guidelines

- Follow the existing history: short, action-oriented commit summaries (optionally with prefixes like `FIX:`), in English or Chinese.
- For pull requests, include: a clear description, affected packages (`mtc-base`, `mtc-minitouch`, etc.), test strategy (such as `uv run pytest`), and any relevant screenshots or logs.

## Agent-Specific Instructions

- When using automated tools or agents, keep diffs small and focused; avoid large refactors that cross package boundaries in a single change.
- If you add a new `mtc-*` package, update the root `pyproject.toml` `[tool.uv.workspace.members]` and `[tool.uv.sources]` sections to keep the workspace consistent.

