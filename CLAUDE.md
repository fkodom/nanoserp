# Development Playbook

This document outlines the development guidelines and best practices for the nanoserp Python library.

## 1. Development Workflow

### Verification (Manual)
Before committing code, you must ensure the following pass:
- **Linting & Formatting:** Always perform safe `ruff` fixes and formatting:
  ```bash
  uv run ruff check --fix . && uv run ruff format .
  ```
  These have no negative side effects and can be run frequently.
- **Type Checking:** `uv run ty check .` to verify type safety.  These are generally fast and can be run for the whole codebase frequently.  `ty` cannot auto-fix issues, though, so you must address any reported problems manually.
- **Testing:** Run `uv run pytest`.
  - *Tip:* Run targeted tests (e.g., `uv run pytest tests/test_specific.py`) to avoid unnecessary delays during development, but ensure the full suite passes before finishing.

### Automated Hooks
This project also uses `pre-commit` hooks to enforce code quality. If a commit fails, simply fix any issues (if needed), stage the changes, and commit again.

### Adding Dependencies

To add a new dependency, use `uv` to ensure it is added to the correct dependency group(s):
```bash
uv add <package-name>             # For regular dependencies
uv add <package-name> --dev       # For development dependencies
```
The regular dependency group should only include packages required for the main `nanoserp` module to function. All other packages (e.g., testing, linting, formatting tools) should go into the development group, unless otherwise specified.

## 2. Project Architecture

nanoserp is a simple Python library. The package layout is:

- **`nanoserp/models.py`**: Shared Pydantic data models used throughout the library.
- **`nanoserp/settings.py`**: Configuration via `pydantic-settings` (reads from environment / `.env` files).
- **`nanoserp/exceptions.py`**: Exception hierarchy for the library.

Runtime dependencies: `httpx`, `pydantic`, `pydantic-settings`.

## 3. Testing Standards

- Every public-facing function or class should have a unit test.
- Tests live under the `tests/` directory, mirroring the package structure.
- Run `uv run pytest` to execute the full test suite.

## 4. General Guidelines

### Git Operations
- Write clear, concise commit messages.
- Ensure all local checks (tests, types) pass before pushing.
