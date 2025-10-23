# Klaro Code Style Guide

This document defines the code style standards for the Klaro project, ensuring consistency and maintainability across the codebase.

## Table of Contents

1. [Python Version and Standards](#python-version-and-standards)
2. [Naming Conventions](#naming-conventions)
3. [Docstring Format](#docstring-format)
4. [Comment Guidelines](#comment-guidelines)
5. [Import Organization](#import-organization)
6. [Type Hints Usage](#type-hints-usage)
7. [Line Length Limits](#line-length-limits)
8. [Code Organization](#code-organization)
9. [Error Handling](#error-handling)
10. [Testing Standards](#testing-standards)
11. [Tools and Automation](#tools-and-automation)

---

## Python Version and Standards

### Python Version

- **Minimum**: Python 3.10
- **Recommended**: Python 3.11+
- **Target**: Write code compatible with Python 3.10-3.12

### Standards Compliance

- **PEP 8**: Follow PEP 8 style guide
- **PEP 484**: Use type hints (PEP 484)
- **PEP 257**: Follow docstring conventions (PEP 257)

### Language Features

**Allowed**:
- Type hints (required)
- F-strings (preferred for string formatting)
- Dataclasses and TypedDict
- Context managers (`with` statements)
- List/dict comprehensions (when clear)
- Walrus operator `:=` (when improves readability)

**Avoid**:
- `eval()` and `exec()` (security risk)
- Global mutable state (except where necessary, e.g., KLARO_RETRIEVER)
- Bare `except:` clauses
- Import * (except in `__init__.py` if needed)

---

## Naming Conventions

### General Rules

- **Be descriptive**: Names should reveal intent
- **Avoid abbreviations**: Use `file_path` not `fp`
- **Be consistent**: Use same terms throughout project

### Specific Conventions

**Modules and Packages**:
```python
# Lowercase, short, single words preferred
tools.py
prompts.py
main.py
```

**Classes**:
```python
# PascalCase (CapWords)
class AgentState:
    pass

class ChromaVectorStore:
    pass

class FileSystemTool:
    pass
```

**Functions and Methods**:
```python
# snake_case
def list_files(directory: str) -> str:
    pass

def analyze_code(code_content: str) -> str:
    pass

def init_knowledge_base(documents: list) -> str:
    pass
```

**Variables**:
```python
# snake_case
file_path = "main.py"
code_content = read_file(file_path)
analysis_result = analyze_code(code_content)
```

**Constants**:
```python
# UPPER_SNAKE_CASE
LLM_MODEL = "gpt-4o-mini"
RECURSION_LIMIT = 50
VECTOR_DB_PATH = "./klaro_db"
DEFAULT_GUIDE_CONTENT = """..."""
```

**Private/Internal**:
```python
# Leading underscore
def _extract_docstring(node):
    pass

_internal_cache = {}

class MyClass:
    def __init__(self):
        self._private_attribute = None
```

**Type Variables**:
```python
# PascalCase with T suffix
from typing import TypeVar

T = TypeVar('T')
MessageT = TypeVar('MessageT', bound=BaseMessage)
```

### Examples from Klaro

```python
# ✅ Good
def read_file(file_path: str) -> str:
    """Reads file content."""
    return content

RECURSION_LIMIT = 50
agent_state: AgentState = {...}

# ❌ Bad
def ReadFile(FilePath: str) -> str:  # Wrong casing
    return content

recursionLimit = 50  # Should be UPPER_SNAKE_CASE
AgentState = {...}  # Variable shouldn't be PascalCase
```

---

## Docstring Format

### Required Docstrings

Docstrings are **required** for:
- All modules
- All public classes
- All public functions and methods
- Complex private functions

### Google-Style Docstrings

Klaro uses **Google-style** docstrings:

```python
def function_name(param1: str, param2: int) -> str:
    """One-line summary ending with a period.

    Longer description paragraph providing more details about
    the function's behavior, design decisions, and usage notes.

    Args:
        param1 (str): Description of param1. Include type info
            even though type hints are present.
        param2 (int): Description of param2. Explain constraints,
            valid ranges, or special values.

    Returns:
        str: Description of return value. Explain format,
            structure, or special return values.

    Raises:
        ValueError: When param1 is empty.
        IOError: When file cannot be read.

    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        Expected output

    Note:
        Additional notes, warnings, or design decisions.
    """
    pass
```

### Module Docstrings

```python
"""Module title in one line.

Longer module description explaining the module's purpose,
main components, and how it fits into the larger system.

This module provides X functionality for Y purpose. Key components:
    - Component1: Description
    - Component2: Description

Usage Example:
    >>> from module import function
    >>> result = function()

Technical Notes:
    - Important implementation details
    - Dependencies
    - Performance considerations
"""
```

### Class Docstrings

```python
class MyClass:
    """One-line summary of class purpose.

    Detailed description of the class, its responsibilities,
    and how it should be used.

    Attributes:
        attribute1 (str): Description of attribute1.
        attribute2 (int): Description of attribute2.

    Example:
        >>> obj = MyClass(param="value")
        >>> obj.method()
        Expected output
    """

    def __init__(self, param: str):
        """Initializes MyClass with given parameters.

        Args:
            param: Description of initialization parameter.
        """
        self.attribute1 = param
```

### Examples from Klaro

```python
def analyze_code(code_content: str) -> str:
    """Analyzes Python code structure using AST and returns structured JSON data.

    Performs programmatic code analysis by parsing Python source code into an
    Abstract Syntax Tree (AST) and extracting structured information about
    classes, functions, methods, parameters, return types, and docstrings.

    This is the core code analysis tool used by the Klaro agent. Unlike LLM-based
    analysis, AST extraction is deterministic and prevents hallucinations.

    Args:
        code_content (str): Raw Python source code to analyze. Must be syntactically
            valid Python code (will be parsed with ast.parse()).

    Returns:
        str: JSON-formatted string containing analysis results with structure:
            {
                "analysis_summary": "High-level summary",
                "components": [{"type": "function", "name": "...", ...}]
            }

    Raises:
        Returns JSON error object (doesn't raise exceptions) for:
        - Empty code_content: {"error": "Code content is empty."}
        - SyntaxError: {"error": "Code parsing error: <details>"}

    Example:
        >>> code = 'def greet(name: str) -> str:\\n    return f"Hello, {name}"'
        >>> result = analyze_code(code)
        >>> data = json.loads(result)
        >>> data["components"][0]["name"]
        'greet'
    """
```

---

## Comment Guidelines

### When to Use Comments

**DO comment**:
- Complex algorithms or logic
- Non-obvious design decisions
- Workarounds for known issues
- Performance optimizations
- Edge cases and why they're handled

**DON'T comment**:
- Obvious code (let code be self-documenting)
- Redundant information already in docstrings
- Version history (use git)

### Comment Style

```python
# Single-line comments use hash and space
# Multiple single-line comments for multiple lines

# NOT:
#No space after hash
#not capitalized

# YES:
# Proper spacing and capitalization
# Explains why, not what
```

### Inline Comments

```python
# Use inline comments sparingly
x = x + 1  # Increment x by 1  # ❌ Redundant

# Prefer:
# Compensate for border width
x = x + 1  # ✅ Explains why
```

### TODOs

```python
# TODO(username): Description of what needs to be done
# FIXME: Description of what's broken
# HACK: Description of workaround
# NOTE: Important note

# Example:
# TODO(kaand): Refactor to use async file reading for better performance
# FIXME: This breaks on Windows due to path separator issues
```

### Block Comments

```python
# Block comments explain larger code sections
# Use for complex algorithms or multi-step processes

# Step 1: Parse the .gitignore content into regex patterns
# This converts glob-style patterns (*.py, __pycache__/) into
# Python regex patterns that can be used with re.search()
patterns = []
for line in gitignore_content.splitlines():
    # Skip comments and empty lines
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    # Convert glob to regex...
```

---

## Import Organization

### Import Order

1. **Standard library imports**
2. **Related third-party imports**
3. **Local application imports**

Separate each group with a blank line.

```python
# Standard library
import os
import re
import json
from typing import TypedDict, Annotated, Sequence

# Third-party
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_community.vectorstores import Chroma

# Local
from prompts import SYSTEM_PROMPT
from tools import list_files, read_file, analyze_code
```

### Import Style

```python
# ✅ Preferred: Explicit imports
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# ❌ Avoid: Import *
from langchain_core.messages import *

# ✅ OK: Import module for many items
from langchain_core import messages

# ✅ OK: Alias for long names
from langchain_community.vectorstores import Chroma as ChromaDB
```

### Conditional Imports

```python
# For optional dependencies
try:
    import optional_module
except ImportError:
    optional_module = None

# For type checking only
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from expensive_module import ExpensiveClass
```

---

## Type Hints Usage

### Required Type Hints

Type hints are **required** for:
- All function signatures (parameters and return)
- Class attributes
- Complex variables

```python
# ✅ Function with type hints
def read_file(file_path: str) -> str:
    content: str = ""
    return content

# ✅ Class with type hints
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    error_log: str

# ✅ Variable type hints (when not obvious)
file_paths: list[str] = []
config: dict[str, Any] = {}
```

### Type Hint Patterns

**Basic Types**:
```python
def example(
    text: str,
    count: int,
    ratio: float,
    enabled: bool,
    data: bytes
) -> None:
    pass
```

**Collections**:
```python
def process(
    items: list[str],
    mapping: dict[str, int],
    unique: set[int],
    values: tuple[str, int, bool]
) -> list[dict[str, Any]]:
    pass
```

**Optional and Union**:
```python
from typing import Optional, Union

def get_value(key: str) -> Optional[str]:
    """Returns value or None."""
    pass

def flexible(input: Union[str, int]) -> str:
    """Accepts str or int."""
    pass

# Python 3.10+ syntax (preferred)
def get_value(key: str) -> str | None:
    pass
```

**Callable**:
```python
from typing import Callable

def apply_func(
    func: Callable[[int, int], int],
    a: int,
    b: int
) -> int:
    return func(a, b)
```

**Generic Types**:
```python
from typing import TypeVar, Generic

T = TypeVar('T')

def first_item(items: list[T]) -> T:
    return items[0]
```

---

## Line Length Limits

### Standard Limits

- **Code**: 100 characters
- **Comments/Docstrings**: 120 characters
- **Exception**: Long strings, URLs can exceed

### Line Breaking

```python
# ✅ Break long function calls
result = some_function(
    first_parameter="value1",
    second_parameter="value2",
    third_parameter="value3"
)

# ✅ Break long strings
message = (
    "This is a very long message that needs to be split "
    "across multiple lines for readability."
)

# ✅ Break long conditions
if (
    condition1
    and condition2
    and condition3
):
    pass

# ✅ Break imports
from module import (
    first_item,
    second_item,
    third_item,
)
```

---

## Code Organization

### File Structure

```python
"""Module docstring."""

# Imports
import standard_lib
from third_party import Module
from local import tool

# Constants
CONSTANT_NAME = "value"

# Helper functions (private)
def _private_helper():
    pass

# Main functions/classes
def public_function():
    pass

class MainClass:
    pass

# Entry point (if applicable)
if __name__ == "__main__":
    main()
```

### Function Length

- **Ideal**: 20-50 lines
- **Maximum**: 100 lines
- **Guideline**: If longer, consider breaking into smaller functions

### Class Organization

```python
class MyClass:
    """Class docstring."""

    # Class attributes
    class_var: str = "value"

    def __init__(self):
        """Constructor."""
        # Instance attributes
        self.attribute = None

    # Public methods
    def public_method(self):
        """Public method."""
        pass

    # Private methods
    def _private_method(self):
        """Private helper."""
        pass

    # Special methods
    def __str__(self):
        """String representation."""
        return f"MyClass({self.attribute})"
```

---

## Error Handling

### Exception Handling

```python
# ✅ Specific exceptions
try:
    result = risky_operation()
except FileNotFoundError:
    handle_missing_file()
except PermissionError:
    handle_permission_error()

# ❌ Bare except
try:
    result = risky_operation()
except:  # Never do this
    pass

# ✅ Catch-all with logging
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return error_response
```

### Klaro Pattern: Return Errors as Strings

```python
# In tools.py, don't raise exceptions - return error strings
def read_file(file_path: str) -> str:
    """Reads file content."""
    if not os.path.exists(file_path):
        return f"Error: File not found: '{file_path}'"

    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"
```

---

## Testing Standards

### Test File Organization

```python
"""Test module docstring."""

import pytest
from module import function_to_test

# Fixtures
@pytest.fixture
def sample_data():
    return "test data"

# Unit tests
@pytest.mark.unit
def test_function_normal_case(sample_data):
    """Test function with valid input."""
    result = function_to_test(sample_data)
    assert result == expected

@pytest.mark.unit
def test_function_error_case():
    """Test function error handling."""
    result = function_to_test(invalid_input)
    assert "Error" in result
```

### Test Naming

```python
# Pattern: test_<function>_<scenario>
test_read_file_existing_file()
test_read_file_nonexistent_file()
test_analyze_code_valid_python()
test_analyze_code_syntax_error()
```

---

## Tools and Automation

### Code Formatting: Black

```bash
# Format files
black main.py tools.py

# Check without modifying
black --check main.py

# Configuration in pyproject.toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311']
```

### Linting: Flake8

```bash
# Run flake8
flake8 main.py tools.py

# Configuration in .flake8
[flake8]
max-line-length = 100
ignore = E203, W503
exclude = .git,__pycache__,venv
```

### Import Sorting: isort

```bash
# Sort imports
isort main.py tools.py

# Configuration in pyproject.toml
[tool.isort]
profile = "black"
line_length = 100
```

### Type Checking: mypy

```bash
# Run type checker
mypy main.py tools.py

# Configuration in mypy.ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
```

---

## Quick Reference

### Checklist for New Code

- [ ] Follows naming conventions
- [ ] Has Google-style docstrings
- [ ] Uses type hints
- [ ] Lines under 100 characters
- [ ] Imports organized correctly
- [ ] Error handling in place
- [ ] Tests written and passing
- [ ] Formatted with Black
- [ ] Passes flake8 linting
- [ ] Passes mypy type checking

---

**Last Updated**: 2025-10-23
**Klaro Version**: 1.0
**Maintained by**: Klaro Development Team
