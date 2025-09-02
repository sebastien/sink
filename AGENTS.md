# Agent Development Guide for Sink

## Build/Lint/Test Commands
- `make prep` - Install dependencies (ruff, bandit, mypy, flake8)
- `make check` - Run all quality checks (security, linting, typing)
- `make fmt` - Format code with ruff
- `make compile` - Compile with mypyc for performance
- `python tests/unit-filter.py` - Run unit tests (single test file)
- `PYTHONPATH=src/py python tests/unit-filter.py` - Run tests with path setup

## Code Style Guidelines
- **Python**: Target 3.11+ with comprehensive type hints
- **Imports**: Group as stdlib → third-party → local; use absolute imports
- **Naming**: `camelCase()` functions, `UPPER_CASE` constants, `snake_case` variables, `PascalCase` classes
- **Types**: Use `Optional[T]`, `Union[T1, T2]`, `TypeVar`, `Generic`, `NamedTuple`, `cast()`
- **Structure**: dataclasses, context managers, pathlib.Path, compiled regex patterns
- **Error Handling**: Specific exception types, `finally` blocks, avoid bare `except:`
- **Security**: `subprocess.run(capture_output=False)`, `# nosec` comments, validate paths
- **Comments**: `# NOTE:` for implementation details, descriptive docstrings

## Development Workflow
1. `make prep` - Setup dependencies
2. Code changes following style guidelines
3. `make check` - Quality checks
4. Run specific test: `python tests/unit-filter.py`
5. `make fmt` - Format code
6. `make compile` - Performance compilation