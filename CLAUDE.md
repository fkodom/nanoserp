# Development Playbook

This document outlines the development guidelines, architecture, and best practices for this FastAPI CRUD repository.

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

The application is structured into four distinct layers: **DB**, **Services**, **API**, and **Client**.

### Shared & Custom Types
- **Shared Types:** Any types shared across the codebase should be placed in `nanoserp/models.py`.
  - Use `sqlmodel` for any types that also correspond to a Database table.
- **Custom Types:** You may create custom types within submodules for clarity and consistency.
  - **API Types:** Factor API endpoints into `views.py` and `schemas.py` files.
    - Define schemas independently in `schemas.py` and import them into `views.py`.
    - This ensures they are accessible at the top-level of the repository without circular imports, allowing the Client SDK to use the same type definitions as the API.

### 1. DB Layer
- **Location:** `nanoserp/db`
- **Structure:** Generally, each file corresponds to a separate table in the DB for organization and simplicity.
  - *Exception:* This rule can be modified if multiple tables effectively deal with the same underlying object.

### 2. Services Layer
- **Location:** `nanoserp/services` (Create if needed)
- **Responsibility:**
  - Leverage the DB layer for CRUD interactions.
  - Perform aggregate actions (e.g., "pull top 5 items from table X, then generate a text summary") that do not conceptually fit into the API or DB layers.
  - **Note:** Any non-trivial functions or interactions should be factored out of the API and into this layer.

### 3. API Layer
- **Location:** `nanoserp/api`
- **Structure:**
  - Group API endpoints by name into routers.
  - Import routers into the main API in `nanoserp/api/main.py`.
- **Responsibility:** Primarily responsible for authentication checks and request/response typing. Logic should be delegated to the Services layer.

### 4. Client Layer
- **Location:** `nanoserp/client.py` (or `nanoserp/client/` for complex APIs)
- **Responsibility:** The client SDK must be fully separable from the FastAPI endpoints themselves.
  - It typically shares request/response schema definitions with the API.

## 3. Testing Standards

Strict testing requirements apply to each layer of the application.

- **DB Tests:** Every DB function must have a unit test.
  - **Fixture:** Use `database_url` from `tests/conftest.py` to test against a temporary database.
- **Service Tests:** Every public-facing service method must have a unit test.
  - **Location:** `tests/services/`
  - **Strategy:** You may mock underlying DB methods entirely if needed, assuming they are verified by DB unit tests.
- **API Tests:** Every API endpoint must have a unit test.
  - **Fixture:** Use `mock_app` from `tests/conftest.py` to test against a temporary, local FastAPI server.
  - **Reference:** See `tests/api/test_example.py`.
- **Client Tests:** Every client method must have a unit test.
  - **Fixture:** Use `mock_client` from `tests/conftest.py` to test against a temporary, fully-functional FastAPI client.

## 4. General Guidelines

### Git Operations
- Write clear, concise commit messages.
- Ensure all local checks (tests, types) pass before pushing.
