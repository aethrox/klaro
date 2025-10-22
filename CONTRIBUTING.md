# Contributing to Klaro

Thank you for your interest in contributing to Klaro! This document provides guidelines and instructions for contributing to the project.

## 🎯 Ways to Contribute

### 1. Report Bugs

If you find a bug, please [open an issue](https://github.com/aethrox/klaro/issues) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (Python version, OS, dependencies)
- Relevant error messages or logs

### 2. Request Features

Feature requests are welcome! Please [open an issue](https://github.com/aethrox/klaro/issues) with:
- Clear description of the proposed feature
- Use case and motivation
- Potential implementation approach (optional)
- Any relevant examples or references

### 3. Improve Documentation

Documentation improvements are highly valued:
- Fix typos or unclear explanations
- Add code examples
- Improve setup instructions
- Create tutorials or guides
- Add diagrams for complex concepts

### 4. Submit Code Contributions

Code contributions should follow the guidelines below.

## 🚀 Development Setup

### Prerequisites

- Python 3.11+
- Git
- OpenAI API key (for testing)

### Setup Steps

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/klaro.git
   cd klaro
   ```

2. **Create Virtual Environment**
   ```bash
   python3.11 -m venv klaro-env
   source klaro-env/bin/activate  # Windows: klaro-env\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest black ruff mypy  # Dev dependencies
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

5. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-number-description
   ```

## 📝 Code Guidelines

### Code Style

Klaro follows [PEP 8](https://peps.python.org/pep-0008/) with these tools:

- **Black:** Code formatting (line length: 120)
  ```bash
  black --line-length 120 .
  ```

- **Ruff:** Fast linting
  ```bash
  ruff check .
  ```

- **MyPy:** Type checking (future)
  ```bash
  mypy main.py tools.py
  ```

### Code Standards

1. **Type Hints:** All function signatures must include type hints
   ```python
   def analyze_code(code_content: str) -> str:
       """Analyzes Python code using AST."""
       ...
   ```

2. **Docstrings:** All public functions must have docstrings
   ```python
   def my_function(param: str) -> int:
       """
       Brief description.

       Args:
           param: Description of parameter

       Returns:
           Description of return value
       """
       ...
   ```

3. **Error Handling:** Use try-except blocks for operations that may fail
   ```python
   try:
       result = risky_operation()
   except SpecificError as e:
       return f"Error: {e}"
   ```

4. **Imports:** Follow this order
   ```python
   # Standard library
   import os
   import sys

   # Third-party
   from langchain import ...

   # Local
   from tools import ...
   ```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_tools.py

# Run with coverage
pytest --cov=. tests/
```

### Writing Tests

1. **Location:** Place tests in `tests/` directory
2. **Naming:** Test files should be named `test_*.py`
3. **Structure:** Test functions should be named `test_*`

Example test:
```python
def test_analyze_code_basic():
    """Test basic code analysis functionality."""
    code = """
    def hello(name: str) -> str:
        return f"Hello {name}"
    """
    result = analyze_code(code)
    assert "hello" in result
    assert "function" in result
```

## 📋 Pull Request Process

### Before Submitting

1. **Ensure tests pass:** `pytest tests/`
2. **Format code:** `black --line-length 120 .`
3. **Lint code:** `ruff check .`
4. **Update documentation:** If adding features, update README.md
5. **Add tests:** Include tests for new functionality

### PR Guidelines

1. **Title:** Use clear, descriptive titles
   - ✅ "Add support for TypeScript AST analysis"
   - ✅ "Fix IndexError in _extract_docstring"
   - ❌ "Update code"

2. **Description:** Include:
   - What changed and why
   - Related issue number (if applicable)
   - Testing performed
   - Screenshots (for UI changes)

3. **Commits:** Write clear commit messages
   ```
   Add TypeScript AST analysis support

   - Implement TypeScript parser using @babel/parser
   - Add type extraction for interfaces and types
   - Update documentation with TypeScript examples

   Fixes #123
   ```

4. **Review:** Address review feedback promptly

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #(issue number)

## Changes Made
- Change 1
- Change 2

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing performed
- [ ] Documentation updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
```

## 🎨 Contribution Areas

### High Priority

| Area | Skills | Difficulty |
|------|--------|------------|
| Multi-language AST support | Parser design, TypeScript/Go/Rust | Advanced |
| Smart model steering | LangGraph, cost optimization | Intermediate |
| Test suite development | Pytest, integration testing | Intermediate |
| Error handling improvements | Python, defensive programming | Beginner |

### Medium Priority

| Area | Skills | Difficulty |
|------|--------|------------|
| RAG system enhancements | Vector DBs, embeddings | Intermediate |
| CLI improvements | Typer, Rich, UX design | Beginner |
| Documentation generation | Technical writing | Beginner |
| Web interface | FastAPI, React | Advanced |

### Good First Issues

Look for issues labeled `good-first-issue` in the [issue tracker](https://github.com/aethrox/klaro/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## 🤝 Code Review Process

### For Contributors

- Be patient; reviews may take a few days
- Be receptive to feedback
- Ask questions if feedback is unclear
- Push updates to the same branch

### For Reviewers

- Be respectful and constructive
- Explain the "why" behind suggestions
- Approve when ready; request changes if needed
- Test the changes locally when possible

## 📞 Communication

### GitHub Issues
- **Bug reports:** Use bug template
- **Feature requests:** Use feature template
- **Questions:** Use discussion template

### GitHub Discussions
- General questions
- Design discussions
- Show and tell (your Klaro use cases)

### Response Times
- Issues: Typically reviewed within 3-5 days
- PRs: Typically reviewed within 3-7 days
- Security issues: Within 24 hours

## 🔒 Security Issues

**Do NOT open public issues for security vulnerabilities.**

Instead, email security concerns to: [PROJECT MAINTAINER EMAIL]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## 📜 License

By contributing to Klaro, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

All contributors will be:
- Listed in the project's contributor graph
- Mentioned in release notes (for significant contributions)
- Added to CONTRIBUTORS.md (future)

## ❓ Questions?

If you have questions about contributing:
1. Check existing [documentation](docs/)
2. Search [closed issues](https://github.com/aethrox/klaro/issues?q=is%3Aissue+is%3Aclosed)
3. Ask in [Discussions](https://github.com/aethrox/klaro/discussions)
4. Open a new issue with the "question" label

---

**Thank you for contributing to Klaro!** 🎉

Your contributions help make technical documentation accessible to everyone.
