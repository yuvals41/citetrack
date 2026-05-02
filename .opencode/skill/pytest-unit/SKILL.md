---
name: pytest-unit
description: "pytest Python test framework with fixtures, coverage, parametrized tests, mocking, and UV runtime integration"
license: MIT
metadata:
  author: solara-ai
  version: "1.0"
---

# Pytest Unit Testing Skill

## When to Use

Use this skill when:
- Writing unit tests for Python services (agentflow, visual-content-generator, researcher)
- Creating pytest fixtures for test setup/teardown
- Mocking external dependencies (APIs, databases, message queues)
- Running tests with coverage requirements
- Writing async tests with pytest-asyncio
- Parametrizing tests for multiple input scenarios

## Quick Start

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest path/to/test_file.py

# Run specific test function
uv run pytest path/to/test_file.py::test_function_name

# Run with markers (exclude slow tests)
uv run pytest -m "not slow"

# Run only unit tests (exclude integration)
uv run pytest -m "not integration"

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run with coverage and fail under threshold
uv run pytest --cov=src --cov-fail-under=95
```

## Test File Structure

```
service/
├── src/
│   └── module/
│       └── feature.py
├── tests/
│   ├── conftest.py          # Shared fixtures
│   ├── unit/
│   │   ├── conftest.py      # Unit-specific fixtures
│   │   └── test_feature.py
│   └── integration/
│       ├── conftest.py      # Integration-specific fixtures
│       └── test_feature_integration.py
├── pyproject.toml
└── pytest.ini               # Or in pyproject.toml
```

### pytest.ini / pyproject.toml Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
asyncio_mode = "auto"
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

## Examples

### Basic Test with Fixtures

```python
# tests/conftest.py
import pytest
from src.models import User

@pytest.fixture
def sample_user() -> User:
    """Provide a sample user for testing."""
    return User(id="user_123", name="Test User", email="test@example.com")

@pytest.fixture
def user_list(sample_user: User) -> list[User]:
    """Provide a list of users, demonstrating fixture composition."""
    return [sample_user, User(id="user_456", name="Another User", email="another@example.com")]


# tests/unit/test_user_service.py
import pytest
from src.services.user_service import UserService

class TestUserService:
    """Test suite for UserService."""

    def test_get_user_by_id_returns_user(self, sample_user):
        """Test that get_user_by_id returns the correct user."""
        service = UserService()
        
        result = service.get_user_by_id(sample_user.id)
        
        assert result is not None
        assert result.id == sample_user.id
        assert result.name == sample_user.name

    def test_get_user_by_id_not_found_raises(self):
        """Test that get_user_by_id raises when user not found."""
        service = UserService()
        
        with pytest.raises(UserNotFoundError) as exc_info:
            service.get_user_by_id("nonexistent_id")
        
        assert "nonexistent_id" in str(exc_info.value)
```

### Async Test with pytest-asyncio

```python
# tests/unit/test_async_service.py
import pytest
from src.services.content_generator import ContentGenerator

@pytest.fixture
async def content_generator():
    """Async fixture for ContentGenerator with cleanup."""
    generator = ContentGenerator()
    await generator.initialize()
    yield generator
    await generator.cleanup()


class TestContentGenerator:
    """Test suite for async ContentGenerator."""

    @pytest.mark.asyncio
    async def test_generate_content_returns_valid_response(self, content_generator):
        """Test async content generation."""
        result = await content_generator.generate(prompt="Test prompt")
        
        assert result is not None
        assert result.content != ""
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_generate_content_handles_timeout(self, content_generator):
        """Test that timeout is handled gracefully."""
        with pytest.raises(TimeoutError):
            await content_generator.generate(prompt="slow", timeout=0.001)
```

### Mocking with pytest-mock

```python
# tests/unit/test_external_api.py
import pytest
from unittest.mock import AsyncMock
from src.services.research_service import ResearchService

class TestResearchService:
    """Test ResearchService with mocked external APIs."""

    def test_fetch_data_calls_external_api(self, mocker):
        """Test that external API is called correctly."""
        # Mock only external APIs, not internal services
        mock_response = {"data": "test_data", "status": "success"}
        mock_get = mocker.patch(
            "src.services.research_service.httpx.get",
            return_value=mocker.Mock(json=lambda: mock_response, status_code=200)
        )
        
        service = ResearchService()
        result = service.fetch_data("query")
        
        mock_get.assert_called_once()
        assert result["data"] == "test_data"

    @pytest.mark.asyncio
    async def test_async_fetch_with_mock(self, mocker):
        """Test async method with mocked async dependency."""
        mock_client = AsyncMock()
        mock_client.get.return_value.json.return_value = {"result": "success"}
        mocker.patch(
            "src.services.research_service.get_http_client",
            return_value=mock_client
        )
        
        service = ResearchService()
        result = await service.async_fetch("test_query")
        
        assert result["result"] == "success"
        mock_client.get.assert_awaited_once()
```

### Parametrized Tests

```python
# tests/unit/test_validators.py
import pytest
from src.validators import validate_email, validate_content_length

class TestValidators:
    """Test suite for validation functions."""

    @pytest.mark.parametrize("email,expected", [
        ("valid@example.com", True),
        ("also.valid@sub.domain.com", True),
        ("invalid-email", False),
        ("missing@domain", False),
        ("@nodomain.com", False),
        ("", False),
    ])
    def test_validate_email(self, email: str, expected: bool):
        """Test email validation with multiple inputs."""
        assert validate_email(email) == expected

    @pytest.mark.parametrize("content,min_len,max_len,expected", [
        ("hello", 1, 10, True),
        ("", 1, 10, False),
        ("x" * 100, 1, 50, False),
        ("valid", 5, 5, True),
    ])
    def test_validate_content_length(self, content, min_len, max_len, expected):
        """Test content length validation."""
        assert validate_content_length(content, min_len, max_len) == expected
```

## Markers

```python
# Mark slow tests
@pytest.mark.slow
def test_heavy_computation():
    """This test takes a long time."""
    pass

# Mark integration tests
@pytest.mark.integration
def test_database_connection():
    """This test requires real database."""
    pass

# Mark unit tests (optional, unit is default)
@pytest.mark.unit
def test_pure_function():
    """Fast, isolated unit test."""
    pass

# Combine markers
@pytest.mark.slow
@pytest.mark.integration
def test_full_pipeline():
    """Slow integration test."""
    pass
```

## Coverage Requirements

- **Target: 95% coverage** for all touched code areas
- Run coverage check before committing:

```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Fail if coverage is below threshold
uv run pytest --cov=src --cov-fail-under=95

# Coverage for specific module
uv run pytest --cov=src/services --cov-report=term-missing tests/unit/test_services.py
```

## Guidelines

1. **Mock only external APIs** - Do not mock internal services; use real implementations
2. **Use fixtures for setup** - Avoid repetitive setup code in tests
3. **One assertion concept per test** - Keep tests focused and readable
4. **Use descriptive names** - `test_create_user_with_invalid_email_raises_validation_error`
5. **Organize by feature** - Mirror source structure in test directory
6. **Clean up resources** - Use fixture teardown or context managers
7. **Avoid test interdependence** - Each test should run in isolation
8. **Use `pytest.raises`** - For expected exceptions, not try/except

## Commands

| Command | Description |
|---------|-------------|
| `uv run pytest` | Run all tests |
| `uv run pytest -v` | Verbose output |
| `uv run pytest -x` | Stop on first failure |
| `uv run pytest --lf` | Run last failed tests |
| `uv run pytest -k "keyword"` | Run tests matching keyword |
| `uv run pytest -m "not slow"` | Exclude slow tests |
| `uv run pytest --cov=src` | Run with coverage |
| `uv run pytest --tb=short` | Short traceback format |
| `uv run pytest -n auto` | Parallel execution (pytest-xdist) |

## Reference Files

- Service tests: `apps/api/tests/`, `apps/api/tests/`
- Shared fixtures: `repos/*/tests/conftest.py`
- pytest config: `repos/*/pyproject.toml` (tool.pytest section)
- Coverage config: `repos/*/.coveragerc` or `pyproject.toml`
