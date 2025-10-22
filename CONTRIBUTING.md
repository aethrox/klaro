# Contributing to Klaro

Thank you for your interest in contributing to Klaro! This document provides guidelines and instructions for contributing to this autonomous documentation agent project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Contribution Workflow](#contribution-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Be respectful and considerate in communication
- Accept constructive criticism gracefully
- Focus on what's best for the community and project
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or discriminatory language
- Publishing others' private information without permission
- Unprofessional conduct that disrupts the collaborative environment

---

## How Can I Contribute?

### 1. Report Bugs

Found a bug? Help us improve Klaro by reporting it:

**Before Submitting**:
- Check existing [GitHub Issues](https://github.com/aethrox/klaro/issues) to avoid duplicates
- Verify the bug exists in the latest version

**When Reporting**:
- **Use a clear, descriptive title** (e.g., "AST analyzer fails on async functions")
- **Provide reproduction steps**:
  ```
  1. Run `python main.py` on project with async functions
  2. Check output for errors
  3. Expected: Proper analysis of async functions
  4. Actual: SyntaxError in analyze_code
  ```
- **Include environment details**:
  - Python version (`python --version`)
  - Operating system
  - Relevant dependencies versions
- **Attach error logs or screenshots**

### 2. Suggest Enhancements

Have an idea to improve Klaro? We'd love to hear it!

**Feature Requests Should Include**:
- **Clear use case**: Why is this feature valuable?
- **Proposed solution**: How should it work?
- **Alternatives considered**: What other approaches did you think about?
- **Implementation thoughts**: Any technical ideas? (optional)

**Example**:
```markdown
### Feature: Support for TypeScript AST Analysis

**Use Case**: Many projects use TypeScript, and Klaro currently only supports Python.

**Proposed Solution**:
- Add a `TypeScriptAnalyzer` class using the `@babel/parser` library
- Extend `analyze_code` tool to detect file extension and route to appropriate analyzer
- Return unified JSON format matching Python AST output

**Alternatives**:
- Use LLM-only analysis (rejected: less accurate)
- Support only JavaScript ES6+ (rejected: TypeScript is widely used)

**Estimated Complexity**: Medium (requires new dependency, parser integration)
```

### 3. Contribute Code

Ready to implement a feature or fix a bug? Awesome!

**Good First Contributions**:
- Fix typos in documentation
- Add type hints to existing functions
- Improve error messages
- Add tests for existing functionality
- Implement small feature enhancements

**Priority Areas** (see [ARCHITECTURE.md](./ARCHITECTURE.md) for technical details):
- **Multi-language support**: Add AST analyzers for JavaScript, Java, Go, etc.
- **Tool development**: Create new tools (e.g., dependency graph extraction)
- **Smart model steering**: Implement cost-optimization routing
- **Testing infrastructure**: Expand test coverage
- **Error handling**: Improve agent recovery from edge cases

### 4. Improve Documentation

Documentation is as valuable as code! You can:
- Fix grammar, typos, or unclear explanations
- Add code examples or tutorials
- Translate documentation (future goal)
- Create video walkthroughs or blog posts

---

## Development Setup

### Prerequisites
- **Python 3.11+** (required for modern type hints)
- **Git** for version control
- **OpenAI API Key** (get free credits at [platform.openai.com](https://platform.openai.com))

### Setup Steps

1. **Fork the Repository**
   - Go to [https://github.com/aethrox/klaro](https://github.com/aethrox/klaro)
   - Click the "Fork" button in the top-right corner

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/klaro.git
   cd klaro
   ```

3. **Create a Virtual Environment** (recommended)
   ```bash
   # macOS/Linux
   python -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

6. **Verify Installation**
   ```bash
   python main.py
   ```

   Expected output:
   ```
   --- Launching Klaro LangGraph Agent (Stage 4 - gpt-4o-mini) ---
   📢 Initializing RAG Knowledge Base...
   ```

7. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Project Structure

Understanding the codebase:

```
klaro/
├── main.py                 # LangGraph agent orchestration & entry point
├── tools.py                # Custom tool implementations (AST, RAG, file ops)
├── prompts.py              # System prompts for agent behavior
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── docs/                   # Technical design documents
│   ├── klaro_project_plan.md
│   ├── tech_design_advanced_agent_langgraph.md
│   └── tech_design_custom_tools.md
├── assets/                 # Project assets (logo, etc.)
├── ARCHITECTURE.md         # Deep technical dive into system design
├── CONTRIBUTING.md         # This file
└── README.md               # Main project documentation
```

### Key Files to Understand

| File | Purpose | When to Edit |
|------|---------|--------------|
| `main.py` | Agent workflow, state machine | Modifying agent behavior, adding nodes/edges |
| `tools.py` | Tool implementations | Adding new tools, fixing tool bugs |
| `prompts.py` | System instructions for LLM | Improving agent reasoning, changing output format |
| `requirements.txt` | Dependencies | Adding new libraries |

---

## Contribution Workflow

### Step-by-Step Process

1. **Ensure Your Fork is Up-to-Date**
   ```bash
   git remote add upstream https://github.com/aethrox/klaro.git
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/add-javascript-support
   ```

3. **Make Your Changes**
   - Write code following [Coding Standards](#coding-standards)
   - Add tests if applicable
   - Update documentation

4. **Test Your Changes**
   ```bash
   # Run the agent
   python main.py

   # Run tests (if test suite exists)
   pytest tests/
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add JavaScript AST analyzer

   - Implement JavaScriptAnalyzer class using esprima
   - Extend analyze_code to detect .js files
   - Add tests for JS function/class extraction
   - Update documentation with JS support"
   ```

   **Good Commit Messages**:
   - Use imperative mood ("Add feature" not "Added feature")
   - Capitalize the first line
   - Keep first line under 50 characters
   - Add detailed explanation after blank line if needed
   - Reference issues: `Fixes #123` or `Closes #45`

6. **Push to Your Fork**
   ```bash
   git push origin feature/add-javascript-support
   ```

7. **Open a Pull Request**
   - Go to your fork on GitHub
   - Click "Compare & pull request"
   - Fill out the PR template:
     - **Title**: Clear, concise description
     - **Description**: What changes were made and why?
     - **Testing**: How did you verify the changes work?
     - **Related Issues**: Link to relevant issues

**PR Example**:
```markdown
## Description
Adds support for JavaScript code analysis using the esprima parser.

## Changes
- New `JavaScriptAnalyzer` class in `tools.py`
- Extended `analyze_code` to auto-detect language from file extension
- Added `esprima` to `requirements.txt`
- Updated README.md with JavaScript support documentation

## Testing
- Tested on React project with classes and arrow functions
- Verified JSON output matches Python AST format
- All existing Python tests still pass

## Related Issues
Closes #42 (JavaScript support feature request)
```

8. **Address Review Feedback**
   - Maintainers may request changes
   - Make updates in your branch and push again
   - PR updates automatically

9. **Merge**
   - Once approved, a maintainer will merge your PR
   - Your contribution is now part of Klaro!

---

## Coding Standards

### Python Style Guide

**Follow PEP 8** with these specific guidelines:

#### 1. Type Hints (Required)
```python
# Good ✅
def analyze_code(code_content: str) -> str:
    """Analyzes Python code using AST."""
    pass

# Bad ❌
def analyze_code(code_content):
    pass
```

#### 2. Docstrings (Required for Public Functions)
```python
def retrieve_knowledge(query: str) -> str:
    """
    Retrieves relevant information from the knowledge base.

    Args:
        query: Semantic search query to match against stored documents.

    Returns:
        Formatted string with top 3 most relevant document chunks.

    Raises:
        RuntimeError: If knowledge base not initialized.
    """
    pass
```

#### 3. Error Handling
```python
# Good ✅: Specific exceptions, informative messages
try:
    tree = ast.parse(code_content)
except SyntaxError as e:
    return json.dumps({"error": f"Invalid Python syntax: {e}"})

# Bad ❌: Bare except, vague error
try:
    tree = ast.parse(code_content)
except:
    return "Error"
```

#### 4. Import Organization
```python
# Standard library imports
import os
import json
from typing import TypedDict, Sequence

# Third-party imports
from langchain_core.messages import BaseMessage
from chromadb import Client

# Local imports
from tools import list_files, analyze_code
```

#### 5. Constants
```python
# Use UPPER_CASE for module-level constants
MAX_RECURSION_LIMIT = 50
DEFAULT_MODEL = "gpt-4o-mini"
VECTOR_DB_PATH = "./klaro_db"
```

### Code Review Checklist

Before submitting, ensure:
- [ ] All functions have type hints
- [ ] Public functions have docstrings
- [ ] No commented-out code (use git history instead)
- [ ] Error messages are clear and actionable
- [ ] No hardcoded values (use constants or config)
- [ ] Code follows single responsibility principle

---

## Testing Guidelines

### Current State
Klaro does not yet have a comprehensive test suite (contributions welcome!).

### When Adding Tests (Future)

**Test Structure**:
```
tests/
├── test_tools.py          # Unit tests for tool functions
├── test_agent.py          # Integration tests for agent workflow
├── fixtures/              # Sample code files for testing
│   ├── sample_python.py
│   └── sample_javascript.js
└── conftest.py            # Pytest configuration
```

**Example Test**:
```python
import pytest
from tools import analyze_code

def test_analyze_code_basic_function():
    """Test AST analysis on a simple function."""
    code = '''
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b
'''

    result = analyze_code(code)
    data = json.loads(result)

    assert len(data["components"]) == 1
    assert data["components"][0]["type"] == "function"
    assert data["components"][0]["name"] == "add"
    assert data["components"][0]["parameters"] == ["a", "b"]
    assert data["components"][0]["returns"] == "int"
```

**Testing Best Practices**:
- Test one behavior per test function
- Use descriptive test names (`test_analyze_code_handles_async_functions`)
- Mock external API calls (OpenAI, web searches)
- Test edge cases (empty input, malformed code, large files)

---

## Documentation

### Documentation Standards

When adding features, update:

1. **README.md**: User-facing features, installation steps
2. **ARCHITECTURE.md**: Technical implementation details, design decisions
3. **Docstrings**: In-code documentation for all public functions
4. **CHANGELOG.md**: Add entry under "Unreleased" section

### Documentation Style

- **Be clear and concise**: Avoid jargon unless necessary
- **Use examples**: Show don't just tell
- **Target audience**: Assume intermediate Python knowledge
- **Link to related docs**: Cross-reference when relevant

---

## Questions or Need Help?

- **Open an issue**: For questions about implementation
- **Start a discussion**: For architectural questions or design proposals
- **Reach out**: Contact the maintainers via GitHub

---

## License

By contributing to Klaro, you agree that your contributions will be licensed under the same **MIT License** that covers the project. See [LICENSE](./LICENSE) for details.

---

**Thank you for contributing to Klaro!** Every contribution, no matter how small, helps make documentation automation better for everyone. 🎉
