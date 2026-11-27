# Learning Notes: Test Runner Configuration, Environment Management, and LLM Observability

## 1. Test Discovery and Python Path Configuration

When running `pytest` in subfolders (e.g. `cd backend; pytest`), Python by default imports modules relative to the current directory unless `sys.path` contains the root of the project package. 

- **Problem:** Running `pytest` raised `ModuleNotFoundError: No module named 'app'`.
- **Solution:** Configure `pythonpath = .` in `pytest.ini`. This instructs pytest to add the directory containing `pytest.ini` (`backend/`) to `sys.path`, enabling clean `from app.x import y` imports across all test suites.

## 2. Decoupling Model Imports from Database Connection Requirements

In SQLAlchemy applications, models inherit from a common `Base = DeclarativeBase()`. If the file defining `Base` immediately inspects `os.getenv("DATABASE_URL")` and raises an exception at import time:

- Importing any model (even in unit tests that mock the database session or services) causes immediate failure if `DATABASE_URL` is not set in the shell environment.
- **Solution:** 
  1. Add `load_dotenv()` to `database.py` so `.env` is automatically picked up during development.
  2. Provide a safe `conftest.py` setting `os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")` so unit test suites and CI can collect tests without requiring an active database server.
  3. When connecting to SQLite in threaded environments like FastAPI, set `connect_args={"check_same_thread": False}` to prevent thread-safety errors.

## 3. Package Structure and Python Init Conventions

- A typo such as `__inti__.py` instead of `__init__.py` prevents standard package discovery.
- Explicit `__init__.py` files in subdirectories (`app/api`, `app/core`, `app/repositories`, `app/services/llm`) ensure unambiguous packaging across linters, static analyzers, and test runners.

## 4. Privacy-Safe LLM Observability

Production and development observability for LLM features (blueprints, adaptive interviews, evaluation scorecards) must never leak sensitive information:

- **What to log:** Monotonic stage timings (`provider_wait_ms`, `json_parse_ms`, `pydantic_validation_ms`, `grounding_validation_ms`), safe non-sensitive configuration (model name, context size, timeout), and structured error categories (`GenerationFailureCategory`).
- **What never to log:** Prompts, candidate answers, raw resumes, or model response text.
