# Contributing to Klaro

Thank you for your interest in contributing to Klaro! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

1. [How to Contribute](#how-to-contribute)
2. [Development Environment Setup](#development-environment-setup)
3. [Code Style Guidelines](#code-style-guidelines)
4. [Pull Request Process](#pull-request-process)
5. [Commit Message Guidelines](#commit-message-guidelines)
6. [Testing Requirements](#testing-requirements)
7. [Documentation Standards](#documentation-standards)
8. [Reporting Issues](#reporting-issues)
9. [Community Guidelines](#community-guidelines)

---

## How to Contribute

We welcome contributions in many forms:

- 🐛 **Bug Reports**: Report bugs via GitHub Issues
- ✨ **Feature Requests**: Suggest new features or improvements
- 📝 **Documentation**: Improve or add documentation
- 🧪 **Tests**: Add or improve test coverage
- 💻 **Code**: Submit bug fixes or new features
- 🔍 **Code Review**: Review pull requests from other contributors

### Good First Issues

Look for issues tagged with `good first issue` for beginner-friendly contributions.

---

## Development Environment Setup

### Prerequisites

- **Python**: 3.10 or higher
- **Git**: For version control
- **OpenAI API Key**: Required for LLM and embeddings

### Step 1: Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/klaro.git
cd klaro

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/klaro.git
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install project dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### Step 4: Configure Environment

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your-api-key-here
```

### Step 5: Verify Setup

```bash
# Run tests to verify installation
pytest tests/

# Run the agent to ensure everything works
python main.py
```

---

## Code Style Guidelines

Klaro follows **PEP 8** standards with some project-specific conventions. For detailed style guidelines, see [docs/CODE_STYLE.md](docs/CODE_STYLE.md).

### Quick Reference

**Python Version**: 3.10+

**Formatting**:
- Line length: 100 characters (120 for comments)
- Indentation: 4 spaces (no tabs)
- String quotes: Double quotes `"` (single quotes for dict keys)

**Naming Conventions**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

**Docstrings**:
- Use Google-style docstrings
- Required for all public functions, classes, and modules

**Type Hints**:
- Use type hints for function signatures
- Example: `def read_file(file_path: str) -> str:`

### Code Formatting Tools

```bash
# Format code with Black
black main.py tools.py prompts.py

# Check style with flake8
flake8 main.py tools.py prompts.py

# Type checking with mypy
mypy main.py tools.py
```

### Pre-commit Hooks

We recommend using pre-commit hooks to automatically format and check code:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

---

## Pull Request Process

### 1. Create a Branch

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a new feature branch
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/issue-description
```

**Branch Naming**:
- Features: `feature/description`
- Bug fixes: `fix/description`
- Documentation: `docs/description`
- Tests: `test/description`

### 2. Make Changes

- Write clear, concise code
- Follow code style guidelines
- Add tests for new functionality
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. --cov-report=term-missing tests/

# Run linting
flake8 .

# Format code
black .
```

### 4. Commit Changes

Follow our [commit message guidelines](#commit-message-guidelines):

```bash
git add .
git commit -m "feat: add support for custom style guides"
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Go to GitHub and create a Pull Request
```

### 6. PR Requirements

Before submitting, ensure:

- ✅ All tests pass
- ✅ Code follows style guidelines
- ✅ New code has test coverage (80%+ for new files)
- ✅ Documentation is updated
- ✅ Commit messages follow guidelines
- ✅ PR description explains changes clearly

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new features
- [ ] Coverage maintained or improved

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## Commit Message Guidelines

We follow **Conventional Commits** format for clear, semantic commit history.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring (no feature change)
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build config)
- **perf**: Performance improvements

### Examples

```bash
# Feature addition
git commit -m "feat(tools): add PDF file reading support"

# Bug fix
git commit -m "fix(main): handle empty message history in decide_next_step"

# Documentation
git commit -m "docs: add architecture diagrams to ARCHITECTURE.md"

# Test addition
git commit -m "test(tools): add edge case tests for analyze_code"

# Refactoring
git commit -m "refactor(tools): extract gitignore pattern matching to separate function"

# With body and footer
git commit -m "feat(rag): add multi-document indexing support

- Support multiple document sources
- Add document metadata tracking
- Improve retrieval accuracy

Closes #42"
```

### Best Practices

- Use present tense ("add feature" not "added feature")
- Keep subject line under 72 characters
- Capitalize subject line
- Don't end subject with period
- Use body to explain what and why (not how)
- Reference issues in footer (e.g., `Closes #123`)

---

## Testing Requirements

All code contributions must include appropriate tests.

### Test Coverage Requirements

- **New Files**: 90%+ coverage
- **Modified Files**: Maintain or improve existing coverage
- **Overall Project**: 80%+ coverage

### Test Types Required

1. **Unit Tests**:
   - Test individual functions in isolation
   - Mock external dependencies
   - Fast execution (< 1 second)

2. **Integration Tests** (for significant features):
   - Test component interactions
   - Use mocked LLM responses
   - Cover end-to-end workflows

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. --cov-report=html tests/

# Run specific test types
pytest tests/ -m unit           # Unit tests only
pytest tests/ -m integration    # Integration tests only
pytest tests/ -m "not rag"      # Skip RAG tests (avoid API calls)
```

### Test Guidelines

- Write clear test names describing what is tested
- Use AAA pattern (Arrange-Act-Assert)
- Test edge cases and error conditions
- Use fixtures from `conftest.py`
- Mock external API calls (LLM, embeddings)
- Clean up resources in test teardown

For detailed testing guidelines, see [docs/TESTING.md](docs/TESTING.md).

---

## Documentation Standards

Good documentation is crucial for project maintainability.

### Documentation Requirements

When contributing code, update:

1. **Docstrings**: Add/update Google-style docstrings for:
   - All public functions
   - All classes
   - All modules
   - Complex private functions

2. **README.md**: Update if:
   - New features are added
   - Usage instructions change
   - Installation requirements change

3. **ARCHITECTURE.md**: Update if:
   - System architecture changes
   - New components are added
   - Data flows change

4. **Code Comments**: Add comments for:
   - Complex algorithms
   - Non-obvious design decisions
   - Workarounds for known issues

### Docstring Format

Use **Google-style** docstrings:

```python
def analyze_code(code_content: str) -> str:
    """Analyzes Python code structure using AST.

    Performs programmatic code analysis by parsing Python source code
    into an Abstract Syntax Tree and extracting structured information.

    Args:
        code_content (str): Raw Python source code to analyze.
            Must be syntactically valid Python code.

    Returns:
        str: JSON-formatted string containing analysis results with
            structure including analysis_summary and components list.

    Raises:
        Returns JSON error object for:
        - Empty code_content
        - SyntaxError in code
        - Other parsing exceptions

    Example:
        >>> code = 'def greet(name): return f"Hello, {name}"'
        >>> result = analyze_code(code)
        >>> data = json.loads(result)
        >>> data["components"][0]["name"]
        'greet'
    """
```

### Documentation Files

When adding major features, consider creating:
- Tutorial in `docs/`
- Usage examples
- Architecture diagrams
- API reference updates

---

## Reporting Issues

### Bug Reports

When reporting bugs, include:

1. **Environment Information**:
   - OS and version
   - Python version
   - Klaro version/commit

2. **Steps to Reproduce**:
   - Clear, numbered steps
   - Minimal reproducible example

3. **Expected Behavior**: What should happen

4. **Actual Behavior**: What actually happens

5. **Error Messages**: Full error traceback

6. **Additional Context**: Screenshots, logs, etc.

### Bug Report Template

```markdown
**Environment**
- OS: [e.g., Windows 11]
- Python: [e.g., 3.11.4]
- Klaro: [e.g., commit abc123]

**Steps to Reproduce**
1. Run `python main.py`
2. Wait for file analysis
3. Error occurs at...

**Expected Behavior**
Should generate README successfully

**Actual Behavior**
Throws SyntaxError during code analysis

**Error Message**
```
Traceback (most recent call last):
  ...
```

**Additional Context**
Happens only with files containing f-strings
```

### Feature Requests

When requesting features:

1. **Use Case**: Describe the problem you're solving
2. **Proposed Solution**: Your suggested approach
3. **Alternatives**: Other solutions you've considered
4. **Additional Context**: Examples, mockups, etc.

---

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on collaboration
- Respect differing viewpoints

### Communication

- **GitHub Issues**: Bug reports, feature requests, discussions
- **Pull Requests**: Code review and feedback
- **Commit Messages**: Clear description of changes

### Review Process

- Maintainers will review PRs within 1-2 weeks
- Address feedback promptly
- Be open to suggestions
- Changes may be requested before merging

---

## Development Workflow

### Typical Contribution Flow

```
1. Find or create issue
   ↓
2. Fork repository
   ↓
3. Create feature branch
   ↓
4. Make changes
   ↓
5. Write tests
   ↓
6. Update documentation
   ↓
7. Run tests locally
   ↓
8. Commit with clear message
   ↓
9. Push to your fork
   ↓
10. Create Pull Request
    ↓
11. Address review feedback
    ↓
12. PR merged!
```

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge into your local main
git checkout main
git merge upstream/main

# Push to your fork
git push origin main

# Rebase your feature branch
git checkout feature/your-feature
git rebase main
```

---

## Additional Resources

- **Development Guide**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Code Style Guide**: [docs/CODE_STYLE.md](docs/CODE_STYLE.md)
- **Testing Guide**: [docs/TESTING.md](docs/TESTING.md)
- **Architecture Documentation**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search closed issues for similar questions
3. Create a new issue with the `question` label

---

## License

By contributing to Klaro, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

## Thank You!

Thank you for contributing to Klaro! Your efforts help make this project better for everyone.

---

**Last Updated**: 2025-10-23
**Klaro Version**: 1.0
**Maintained by**: Klaro Development Team
