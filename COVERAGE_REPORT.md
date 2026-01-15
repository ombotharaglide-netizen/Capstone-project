# Test Coverage Report

## Overview

This document describes the test coverage for the `resolution.py` API route and how to generate/view coverage reports.

## Test Results

### Test Suite: `test_resolution_api.py`

**Status**: ✅ All 10 tests passing

**Coverage**: 100% for `app/api/v1/routes/resolution.py`

### Test Cases Covered

1. ✅ **test_resolve_error_with_log_id_success** - Successful resolution with existing log_id
2. ✅ **test_resolve_error_with_log_text_success** - Successful ad-hoc resolution with log_text
3. ✅ **test_resolve_error_log_id_not_found** - 404 error when log_id doesn't exist
4. ✅ **test_resolve_error_missing_both_log_id_and_log_text** - 400 error when neither parameter provided
5. ✅ **test_resolve_error_rag_error** - RAGError exception handling
6. ✅ **test_resolve_error_general_exception** - General exception handling
7. ✅ **test_resolve_error_with_default_top_k** - Default top_k value usage
8. ✅ **test_resolve_error_similar_logs_without_id** - Handling similar logs without id
9. ✅ **test_resolve_error_similar_logs_invalid_id** - Handling similar logs with invalid id
10. ✅ **test_resolve_error_custom_top_k** - Custom top_k value usage

## Generating Coverage Reports

### Prerequisites

Ensure you have the required packages installed:
```bash
pip install pytest pytest-cov pytest-asyncio
```

### Running Tests with Coverage

#### Terminal Report Only
```bash
pytest app/tests/integration/test_resolution_api.py --cov=app.api.v1.routes.resolution --cov-report=term-missing
```

#### HTML Report (Recommended)
```bash
pytest app/tests/integration/test_resolution_api.py --cov=app.api.v1.routes.resolution --cov-report=html --cov-report=term
```

#### Both Terminal and HTML Reports
```bash
pytest app/tests/integration/test_resolution_api.py --cov=app.api.v1.routes.resolution --cov-report=term-missing --cov-report=html
```

### Viewing the HTML Coverage Report

1. After running tests with `--cov-report=html`, navigate to the `htmlcov` directory
2. Open `htmlcov/index.html` in your web browser
3. Click on `app/api/v1/routes/resolution.py` to see detailed line-by-line coverage

### Coverage Configuration

The project uses `pyproject.toml` for pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = ["app/tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=70"
```

This configuration:
- Sets test paths to `app/tests`
- Requires minimum 70% coverage for the entire app
- Generates both terminal and HTML reports by default

## Coverage Statistics

### Resolution API Route (`app/api/v1/routes/resolution.py`)

- **Statements**: 48
- **Missing**: 0
- **Coverage**: 100%

### Test File (`app/tests/integration/test_resolution_api.py`)

- **Statements**: 236
- **Missing**: 1
- **Coverage**: 99%

## Test Structure

The test suite uses:
- **FastAPI TestClient** for making HTTP requests
- **Mock objects** for database sessions and resolver services
- **Dependency overrides** to inject test dependencies
- **AsyncMock** for testing async resolver methods

## Key Testing Patterns

1. **Database Mocking**: Uses `setup_db_query_mocks()` helper to simulate database queries
2. **Dependency Injection**: Overrides FastAPI dependencies using `app.dependency_overrides`
3. **Async Testing**: Uses `AsyncMock` for async resolver methods
4. **Error Handling**: Tests both expected errors (404, 400) and unexpected errors (500)

## Running All Tests

To run all tests in the project:

```bash
pytest app/tests/ -v
```

To run with coverage for the entire app:

```bash
pytest app/tests/ --cov=app --cov-report=html --cov-report=term-missing
```

## Notes

- The HTML coverage report is generated in the `htmlcov/` directory
- The report includes interactive features to drill down into specific files
- Green lines indicate covered code, red lines indicate uncovered code
- Yellow lines indicate partial coverage (e.g., in conditional statements)
