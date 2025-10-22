# Contributing to Klaro

Thank you for your interest in contributing to Klaro! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style Guidelines](#code-style-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Expected Behavior

- Be respectful and considerate
- Use welcoming and inclusive language
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment, trolling, or discriminatory comments
- Personal attacks or inflammatory language
- Publishing others' private information
- Other conduct that would be inappropriate in a professional setting

### Enforcement

Violations of the code of conduct should be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.11 or higher
- Git installed and configured
- OpenAI API key (for testing agent functionality)
- Familiarity with:
  - Python type hints and modern syntax
  - LangChain and LangGraph frameworks
  - Git workflow (branching, pull requests)

### Find Something to Work On

1. **Check existing issues:** https://github.com/aethrox/klaro/issues
   - Look for issues labeled `good first issue` or `help wanted`
   - Comment on the issue to indicate you're working on it

2. **Propose new features:**
   - Open an issue first to discuss the feature
   - Wait for maintainer feedback before starting work
   - Ensure the feature aligns with project goals

3. **Fix bugs:**
   - Bugs are labeled with `bug` tag
   - Include test cases demonstrating the fix

---

## Development Environment Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork:
git clone https://github.com/YOUR_USERNAME/klaro.git
cd klaro

# Add upstream remote
git remote add upstream https://github.com/aethrox/klaro.git
```

### 2. Create Virtual Environment

```bash
python -m venv klaro-env
source klaro-env/bin/activate  # On Windows: klaro-env\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 5. Verify Setup

```bash
# Run the agent
python main.py

# Run tests (when available)
pytest tests/

# Check code style
black --check .
flake8 .
```

---

## How to Contribute

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes:**
   - Follow code style guidelines (see below)
   - Add tests for new functionality
   - Update documentation as needed
   - Keep commits atomic and focused

3. **Test your changes:**
   ```bash
   pytest tests/
   black .
   flake8 .
   mypy .
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new tool for X"
   # See commit message guidelines below
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   # Then create PR on GitHub
   ```

---

## Code Style Guidelines

### Python Style (PEP 8)

We follow [PEP 8](https://pep8.org/) with some modifications:

**Line Length:**
- Maximum 100 characters (not 79)
- Break long lines at logical points

**Formatting:**
- Use Black for automatic formatting: `black .`
- 4 spaces for indentation (no tabs)
- 2 blank lines between top-level definitions
- 1 blank line between method definitions

**Naming Conventions:**
```python
# Functions and variables: snake_case
def analyze_code(code_content: str) -> str:
    result_data = process_content(code_content)

# Classes: PascalCase
class AgentState(TypedDict):
    messages: list[str]

# Constants: UPPER_SNAKE_CASE
LLM_MODEL = "gpt-4o-mini"
RECURSION_LIMIT = 50

# Private functions: leading underscore
def _extract_docstring(node):
    pass
```

### Type Hints

**Always use type hints for function signatures:**

```python
# Good
def list_files(directory: str = '.') -> str:
    pass

# Bad
def list_files(directory='.'):
    pass
```

**Use modern type hint syntax (Python 3.11+):**

```python
# Good (modern)
def process_items(items: list[str]) -> dict[str, int]:
    pass

# Avoid (legacy)
from typing import List, Dict
def process_items(items: List[str]) -> Dict[str, int]:
    pass
```

### Docstrings (Google Style)

**All public functions must have docstrings:**

```python
def analyze_code(code_content: str) -> str:
    """
    Analyzes Python code using AST and returns JSON-formatted results.

    Extracts functions, classes, parameters, and docstrings from Python source code
    without executing it. Uses Abstract Syntax Tree parsing for perfect accuracy.

    Args:
        code_content (str): Raw Python source code to analyze. Must be syntactically
            valid Python code.

    Returns:
        str: JSON-formatted string containing analysis results with structure:
            {
                "analysis_summary": "File contains X classes and Y functions",
                "components": [...]
            }

            Returns error JSON on failure: {"error": "description"}

    Example:
        >>> code = "def foo():\\n    pass"
        >>> result = analyze_code(code)
        >>> data = json.loads(result)
        >>> data["components"][0]["name"]
        'foo'

    Note:
        Only supports Python code. Other languages will fail with syntax error.
    """
    pass
```

### Import Organization

**Group imports in this order:**
1. Standard library imports
2. Third-party library imports
3. Local application imports

**Use absolute imports, not relative:**

```python
# Good
from tools import list_files, read_file
from prompts import SYSTEM_PROMPT

# Avoid
from .tools import list_files
from ..prompts import SYSTEM_PROMPT
```

---

## Pull Request Process

### Before Submitting PR

1. **Update your branch:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run full test suite:**
   ```bash
   pytest tests/ --cov=.
   black --check .
   flake8 .
   mypy .
   ```

3. **Update documentation:**
   - Add/update docstrings for new functions
   - Update README.md if adding features
   - Update CHANGELOG.md with your changes

### PR Description Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to break)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran to verify your changes.

## Checklist
- [ ] My code follows the project's code style
- [ ] I have added tests covering my changes
- [ ] All new and existing tests pass
- [ ] I have updated the documentation
- [ ] I have added an entry to CHANGELOG.md
- [ ] My commits follow the commit message guidelines

## Related Issues
Closes #123
```

### PR Review Process

1. **Automated checks** will run (when CI/CD is set up)
2. **Maintainer review:** Usually within 1-3 days
3. **Address feedback:** Make requested changes
4. **Approval and merge:** Once approved, maintainers will merge

---

## Testing Requirements

### Writing Tests

**Test file structure:**
```
tests/
├── test_tools.py      # Tests for tools.py functions
├── test_main.py       # Tests for main.py components
├── test_integration.py # End-to-end tests
└── fixtures/          # Test data
    └── sample_project/
```

**Test naming convention:**
```python
def test_function_name_expected_behavior():
    """Test that function_name does X when given Y."""
    pass
```

**Example test:**
```python
def test_list_files_returns_tree_structure():
    """Test that list_files returns a formatted tree structure."""
    result = list_files("./tests/fixtures/sample_project")

    assert "main.py" in result
    assert "utils.py" in result
    assert "__pycache__" not in result  # Should be filtered
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_tools.py

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_tools.py::test_list_files_returns_tree_structure
```

### Test Coverage Requirements

- **New code:** Minimum 80% coverage
- **Bug fixes:** Must include test reproducing the bug
- **Critical functions:** Aim for 100% coverage

---

## Documentation Standards

### When to Update Documentation

**README.md:** Update when:
- Adding new features visible to users
- Changing installation/setup process
- Modifying usage examples
- Adding new configuration options

**Code documentation:** Always update:
- Docstrings for new functions
- Module-level docstrings for new files
- Inline comments for complex logic

**Architecture docs:** Update when:
- Changing core architecture (main.py)
- Adding new design patterns
- Modifying data flow

### Documentation Style

- **Be concise:** Users scan, don't read every word
- **Use examples:** Show, don't just tell
- **Be accurate:** Test all code examples
- **Link related docs:** Help users navigate

---

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature change)
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)

### Examples

```
feat(tools): add support for JavaScript AST analysis

Add `analyze_js_code` function using esprima parser to extract
JavaScript code structure similar to Python analyze_code.

Closes #45
```

```
fix(main): handle ChromaDB initialization errors gracefully

Previously, ChromaDB errors would crash the agent. Now returns
error message allowing agent to continue with degraded functionality.

Fixes #67
```

```
docs(README): update installation instructions for Windows

Clarify virtual environment activation commands for Windows users
and add troubleshooting section for common Windows-specific issues.
```

### Rules

- Use present tense: "add feature" not "added feature"
- Keep subject line under 50 characters
- Capitalize subject line
- No period at end of subject line
- Blank line between subject and body
- Wrap body at 72 characters
- Reference issues/PRs in footer

---

## Bug Reports

### Before Reporting

1. **Search existing issues:** Your bug may already be reported
2. **Verify it's reproducible:** Can you reproduce it consistently?
3. **Check latest version:** Update to latest main branch

### Bug Report Template

```markdown
**Describe the Bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run '...'
2. Call function '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Error Output**
```
[Paste full error message and stack trace]
```

**Environment:**
- OS: [e.g., Ubuntu 22.04, Windows 11, macOS 13]
- Python version: [e.g., 3.11.5]
- Klaro version/commit: [e.g., main branch, commit abc123]
- Relevant dependencies: [e.g., langchain==0.1.0]

**Additional Context**
Any other relevant information (screenshots, logs, related issues).
```

---

## Feature Requests

### Before Requesting

1. **Check existing issues:** Feature may already be planned
2. **Align with project goals:** Does it fit Klaro's vision?
3. **Consider alternatives:** Can existing features solve your need?

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem. Ex. "I'm frustrated when..."

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Any other context, mockups, or examples.

**Are you willing to implement this?**
- [ ] Yes, I can submit a PR
- [ ] Yes, with guidance
- [ ] No, but I can test
- [ ] No
```

---

## Getting Help

- **GitHub Issues:** https://github.com/aethrox/klaro/issues
- **Documentation:** https://github.com/aethrox/klaro/tree/main/docs
- **Email maintainers:** (if specified in README)

---

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md (if created)
- Credited in release notes
- Mentioned in project README (for significant contributions)

Thank you for contributing to Klaro! 🚀
