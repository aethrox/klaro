# Klaro Testing Guide

This document provides comprehensive testing guidelines for the Klaro project, covering test execution, test organization, coverage requirements, and contribution standards.

## Table of Contents

1. [Test Suite Overview](#test-suite-overview)
2. [Running Tests](#running-tests)
3. [Test Organization](#test-organization)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [Mocking Strategy](#mocking-strategy)
7. [Test Data and Fixtures](#test-data-and-fixtures)
8. [CI/CD Integration](#cicd-integration)
9. [Troubleshooting](#troubleshooting)

---

## Test Suite Overview

Klaro's test suite is organized into three main categories:

### Unit Tests
- **Location**: `tests/test_tools.py`, `tests/test_main.py`
- **Purpose**: Test individual functions and components in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Mocked external dependencies (LLM, embeddings)
- **Coverage**: ~80%+ of codebase

### Integration Tests
- **Location**: `tests/test_integration.py`
- **Purpose**: Test complete workflows and component interactions
- **Speed**: Moderate (1-5 seconds per test)
- **Dependencies**: Mocked LLM with realistic responses
- **Coverage**: End-to-end scenarios

### Test Fixtures
- **Location**: `tests/fixtures/`
- **Contents**:
  - `sample_code.py`: Sample Python code for AST testing
  - `sample_project/`: Complete sample project structure
- **Purpose**: Provide consistent test data across test modules

---

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_tools.py

# Run specific test function
pytest tests/test_tools.py::test_list_files_current_directory

# Run specific test class
pytest tests/test_tools.py::TestListFiles
```

### Running by Category

```bash
# Run only unit tests (fast)
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run tests requiring RAG/embeddings
pytest tests/ -m rag

# Skip slow tests
pytest tests/ -m "not integration"
```

### Output Formats

```bash
# Verbose output with test names
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Short summary
pytest tests/ --tb=short

# Quiet mode (only show failures)
pytest tests/ -q

# Show detailed failure info
pytest tests/ -vv
```

---

## Test Organization

### Test File Structure

```
tests/
├── __init__.py                  # Test suite package
├── conftest.py                  # Shared fixtures and configuration
├── test_tools.py                # Unit tests for tools.py
├── test_main.py                 # Unit tests for main.py
├── test_integration.py          # End-to-end integration tests
└── fixtures/                    # Test data and sample projects
    ├── sample_code.py           # Sample Python code
    └── sample_project/          # Complete sample project
        ├── main.py
        ├── tools.py
        ├── README.md
        └── requirements.txt
```

### Test Naming Conventions

**Test Files**: `test_<module>.py`
- Example: `test_tools.py`, `test_main.py`

**Test Functions**: `test_<feature>_<scenario>()`
- Example: `test_list_files_current_directory()`
- Example: `test_read_file_nonexistent_file()`

**Test Classes** (optional): `Test<Feature>`
- Example: `TestListFiles`, `TestAnalyzeCode`

### Test Markers

Tests are marked with pytest markers for categorization:

```python
@pytest.mark.unit          # Fast unit test
@pytest.mark.integration   # Slower integration test
@pytest.mark.rag           # Requires RAG/embeddings
```

**Usage**:
```bash
pytest -m unit             # Run only unit tests
pytest -m "not rag"        # Skip RAG tests (avoid API calls)
```

---

## Writing Tests

### Test Structure (AAA Pattern)

Follow the **Arrange-Act-Assert** pattern:

```python
def test_read_file_existing_file(temp_dir):
    # Arrange: Set up test data
    file_path = os.path.join(temp_dir, "test.txt")
    content = "Test content"
    with open(file_path, 'w') as f:
        f.write(content)

    # Act: Execute the function under test
    result = read_file(file_path)

    # Assert: Verify expected behavior
    assert result == content
    assert "Test content" in result
```

### Unit Test Template

```python
@pytest.mark.unit
def test_function_name_scenario(fixture1, fixture2):
    """Test that function_name does X when Y."""
    # Arrange
    input_data = "test input"

    # Act
    result = function_name(input_data)

    # Assert
    assert result == expected_output
    assert "expected substring" in result
```

### Integration Test Template

```python
@pytest.mark.integration
def test_workflow_name(mock_env_vars):
    """Test complete workflow from A to B."""
    # Mock external dependencies
    with patch('main.model') as mock_model:
        mock_model.invoke = Mock(return_value=expected_response)

        # Execute workflow
        result = run_klaro_langgraph(project_path=".")

        # Verify behavior
        assert mock_model.invoke.called
        assert "expected output" in result
```

### Testing Error Conditions

Always test error handling:

```python
@pytest.mark.unit
def test_read_file_nonexistent_file():
    """Test read_file handles missing files gracefully."""
    result = read_file("/nonexistent/path.txt")

    assert "Error" in result
    assert "not found" in result.lower()
```

### Testing Edge Cases

```python
@pytest.mark.unit
def test_analyze_code_empty_input():
    """Test analyze_code handles empty input."""
    result = analyze_code("")
    data = json.loads(result)

    assert "error" in data
    assert "empty" in data["error"].lower()
```

---

## Test Coverage

### Running Coverage Reports

```bash
# Run tests with coverage
pytest --cov=. tests/

# Generate HTML coverage report
pytest --cov=. --cov-report=html tests/

# View HTML report
open htmlcov/index.html  # macOS/Linux
start htmlcov\index.html # Windows

# Show missing lines
pytest --cov=. --cov-report=term-missing tests/

# Generate XML report (for CI)
pytest --cov=. --cov-report=xml tests/
```

### Coverage Requirements

**Minimum Coverage Standards**:
- **Overall**: 80%
- **tools.py**: 85%
- **main.py**: 80%
- **New code**: 90%+

**Excluded from Coverage**:
- `__init__.py` files
- Test files (`tests/`)
- Configuration files

### Coverage Configuration

Create `.coveragerc` in project root:

```ini
[run]
source = .
omit =
    tests/*
    setup.py
    *__init__.py
    .venv/*
    venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

### Checking Coverage Before Commit

```bash
# Run tests with coverage and fail if below 80%
pytest --cov=. --cov-fail-under=80 tests/
```

---

## Mocking Strategy

### Mocking LLM Calls

**Why**: Avoid expensive API calls and ensure deterministic tests.

```python
@pytest.mark.unit
def test_run_model_node_invokes_llm():
    """Test run_model without actual LLM API call."""
    mock_response = AIMessage(content="Test response", tool_calls=[])

    with patch('main.model') as mock_model:
        mock_model.invoke = Mock(return_value=mock_response)

        state = {"messages": [HumanMessage(content="Task")], "error_log": ""}
        result = run_model(state)

        assert result["messages"][0].content == "Test response"
        mock_model.invoke.assert_called_once()
```

### Mocking Embeddings

**Why**: Avoid OpenAI API calls for RAG tests.

```python
@pytest.fixture
def mock_embeddings():
    """Mock OpenAI embeddings."""
    mock = Mock()
    mock.embed_documents = Mock(return_value=[[0.1, 0.2, 0.3] * 512])
    mock.embed_query = Mock(return_value=[0.1, 0.2, 0.3] * 512)
    return mock

@pytest.mark.rag
def test_init_knowledge_base(sample_documents, mock_embeddings):
    """Test RAG initialization without API calls."""
    with patch('tools.OpenAIEmbeddings', return_value=mock_embeddings):
        result = init_knowledge_base(sample_documents)
        assert "successfully" in result.lower()
```

### Mocking ChromaDB

```python
@pytest.mark.rag
def test_retrieve_knowledge(mock_chroma):
    """Test knowledge retrieval with mocked vector store."""
    mock_retriever = Mock()
    mock_retriever.invoke = Mock(return_value=[
        MagicMock(page_content="Result 1"),
        MagicMock(page_content="Result 2")
    ])

    with patch('tools.KLARO_RETRIEVER', mock_retriever):
        result = retrieve_knowledge("test query")
        assert "Result 1" in result
```

### Mocking File System

Use `temp_dir` fixture for isolated file operations:

```python
def test_list_files_current_directory(temp_dir):
    """Test with temporary directory."""
    # Create test structure
    Path(temp_dir / "test.py").touch()

    result = list_files(temp_dir)
    assert "test.py" in result
```

---

## Test Data and Fixtures

### Shared Fixtures (conftest.py)

**Available Fixtures**:

1. **`temp_dir`**: Temporary directory (auto-cleanup)
   ```python
   def test_example(temp_dir):
       file_path = os.path.join(temp_dir, "test.txt")
       # Use temp_dir for file operations
   ```

2. **`sample_python_code`**: Valid Python code string
   ```python
   def test_analyze(sample_python_code):
       result = analyze_code(sample_python_code)
       # Test AST analysis
   ```

3. **`invalid_python_code`**: Code with syntax errors
   ```python
   def test_error_handling(invalid_python_code):
       result = analyze_code(invalid_python_code)
       # Verify error handling
   ```

4. **`sample_project_path`**: Path to fixtures/sample_project
   ```python
   def test_integration(sample_project_path):
       result = list_files(str(sample_project_path))
       # Test on complete project
   ```

5. **`mock_llm`**: Mocked ChatOpenAI instance
6. **`mock_embeddings`**: Mocked OpenAIEmbeddings
7. **`mock_env_vars`**: Pre-configured environment variables
8. **`sample_documents`**: LangChain Document objects

### Using Fixtures

```python
# Single fixture
def test_example(temp_dir):
    pass

# Multiple fixtures
def test_complex(temp_dir, sample_python_code, mock_llm):
    pass

# Fixture with scope
@pytest.fixture(scope="module")
def expensive_setup():
    # Runs once per module
    return setup_data
```

### Creating Custom Fixtures

Add to `conftest.py`:

```python
@pytest.fixture
def custom_fixture():
    """Description of fixture."""
    # Setup
    data = setup_test_data()

    yield data

    # Teardown (optional)
    cleanup(data)
```

---

## CI/CD Integration

### GitHub Actions Configuration

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests with coverage
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term tests/

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        fail_ci_if_error: true
```

### Pre-commit Hooks

Install pre-commit hooks to run tests before commits:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml <<EOF
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest tests/ -m "not integration"
        language: system
        pass_filenames: false
        always_run: true
EOF

# Install hooks
pre-commit install
```

### Running Tests in Docker

```dockerfile
# Dockerfile.test
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt pytest pytest-cov

COPY . .

CMD ["pytest", "tests/", "--cov=.", "--cov-report=term"]
```

```bash
# Build and run
docker build -f Dockerfile.test -t klaro-test .
docker run --env OPENAI_API_KEY=$OPENAI_API_KEY klaro-test
```

---

## Troubleshooting

### Common Issues

**1. Import Errors**

```bash
# Error: ModuleNotFoundError: No module named 'tools'
# Solution: Run pytest from project root
cd /path/to/klaro
pytest tests/

# Or install package in editable mode
pip install -e .
```

**2. Fixture Not Found**

```bash
# Error: fixture 'temp_dir' not found
# Solution: Ensure conftest.py is in tests/ directory
ls tests/conftest.py
```

**3. Tests Pass Locally but Fail in CI**

- Check environment variables (OPENAI_API_KEY)
- Verify dependencies in requirements.txt
- Check Python version compatibility

**4. RAG Tests Failing**

```bash
# Error: OpenAI API key required
# Solution: Set environment variable
export OPENAI_API_KEY="your-key-here"

# Or use mocked embeddings
pytest tests/ -m "not rag"
```

**5. Slow Test Execution**

```bash
# Run unit tests only (skip integration)
pytest tests/ -m unit

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto
```

### Debugging Tests

```bash
# Drop into debugger on failure
pytest tests/ --pdb

# Show print statements
pytest tests/ -s

# Increase verbosity
pytest tests/ -vv

# Show local variables on failure
pytest tests/ -l
```

### Test Isolation Issues

If tests affect each other:

```python
# Ensure proper cleanup
@pytest.fixture
def my_fixture():
    setup()
    yield data
    teardown()  # Always cleanup

# Reset global state
import tools
tools.KLARO_RETRIEVER = None  # Reset after test
```

---

## Best Practices

### DO:
- ✅ Write tests for all new features
- ✅ Test both success and error cases
- ✅ Use descriptive test names
- ✅ Keep tests independent and isolated
- ✅ Mock external dependencies (LLM, APIs)
- ✅ Use fixtures for shared setup
- ✅ Run tests before committing
- ✅ Maintain 80%+ code coverage

### DON'T:
- ❌ Make API calls in tests (mock them)
- ❌ Depend on test execution order
- ❌ Use hardcoded paths (use fixtures)
- ❌ Skip writing tests for "simple" functions
- ❌ Commit failing tests
- ❌ Test implementation details (test behavior)

---

## Additional Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Pytest Fixtures**: https://docs.pytest.org/en/stable/fixture.html
- **Python unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **Coverage.py**: https://coverage.readthedocs.io/
- **Testing Best Practices**: https://docs.python-guide.org/writing/tests/

---

## Contributing Tests

When contributing code to Klaro:

1. **Write tests for new features**
   - Add unit tests in `tests/test_tools.py` or `tests/test_main.py`
   - Add integration tests in `tests/test_integration.py` if needed

2. **Run test suite before submitting PR**
   ```bash
   pytest tests/ --cov=. --cov-report=term-missing
   ```

3. **Ensure coverage doesn't decrease**
   ```bash
   pytest --cov=. --cov-fail-under=80 tests/
   ```

4. **Update fixtures if needed**
   - Add new fixtures to `conftest.py`
   - Update `fixtures/sample_project` for integration tests

5. **Document complex tests**
   - Add clear docstrings
   - Explain mocking strategy
   - Document any special setup

---

**Last Updated**: 2025-10-23
**Klaro Version**: 1.0
**Maintained by**: Klaro Development Team
