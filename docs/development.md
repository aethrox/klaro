# Klaro Development Guide

This guide provides comprehensive information for developers working on Klaro, covering environment setup, development workflows, debugging, and best practices.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Running Code in Development Mode](#running-code-in-development-mode)
3. [Debugging with LangSmith](#debugging-with-langsmith)
4. [Code Structure and Module Organization](#code-structure-and-module-organization)
5. [Adding New Tools](#adding-new-tools)
6. [Extending Agent Capabilities](#extending-agent-capabilities)
7. [Performance Profiling](#performance-profiling)
8. [Logging and Debugging](#logging-and-debugging)
9. [Working with Dependencies](#working-with-dependencies)
10. [Release Process](#release-process)

---

## Development Environment Setup

### Prerequisites

- **Python**: 3.10+ (3.11+ recommended)
- **Git**: For version control
- **Virtual Environment**: venv or virtualenv
- **OpenAI API Key**: Required for LLM and embeddings
- **IDE**: VS Code, PyCharm, or your preferred editor

For basic installation, see the [README.md installation guide](../README.md#installation).

This guide covers development-specific setup:

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/klaro.git
cd klaro

# Install development dependencies (after following README.md installation)
pip install -r requirements-dev.txt
```

### Development Dependencies

Create `requirements-dev.txt`:

```txt
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
pytest-xdist>=3.3.1

# Code Quality
black>=23.7.0
flake8>=6.1.0
mypy>=1.5.0
isort>=5.12.0

# Documentation
sphinx>=7.1.0
sphinx-rtd-theme>=1.3.0

# Development Tools
ipython>=8.14.0
jupyter>=1.0.0
pre-commit>=3.3.3

# Debugging
pdbpp>=0.10.3
```

### Environment Configuration

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**.env Template**:

```ini
# Required
OPENAI_API_KEY=your-api-key-here

# Optional
KLARO_RECURSION_LIMIT=50
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=klaro-development
LLM_MODEL=gpt-4o-mini
```

### IDE Configuration

**VS Code Settings** (`.vscode/settings.json`):

```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "editor.formatOnSave": true,
    "editor.rulers": [100],
    "[python]": {
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

**PyCharm Configuration**:
- Preferences → Python Interpreter → Select venv interpreter
- Preferences → Tools → Python Integrated Tools → Testing: pytest
- Preferences → Editor → Code Style → Python → Line length: 100

---

## Running Code in Development Mode

### Basic Execution

```bash
# Run the agent on current directory
python main.py

# Run with custom project path
python -c "from main import run_klaro_langgraph; run_klaro_langgraph('./my_project')"
```

### Development Mode with Debugging

```python
# dev_run.py - Development script with extra logging
import os
from dotenv import load_dotenv
load_dotenv()

# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

from main import run_klaro_langgraph

# Run with debugging enabled
run_klaro_langgraph(project_path=".")
```

### Interactive Development

```python
# Start IPython or Jupyter for interactive testing
ipython

# Load modules
from tools import list_files, read_file, analyze_code
from main import AgentState, run_model, decide_next_step

# Test individual components
result = list_files(".")
print(result)

code = read_file("main.py")
analysis = analyze_code(code)
```

### Running with Different Models

```python
# test_different_models.py
import os
os.environ["LLM_MODEL"] = "gpt-4o"  # or "claude-3-5-sonnet-20241022"

from main import run_klaro_langgraph
run_klaro_langgraph(".")
```

---

## Debugging with LangSmith

LangSmith provides detailed tracing for LangChain/LangGraph applications.

### Setup LangSmith

1. **Sign up** at https://smith.langchain.com/

2. **Get API Key** from Settings → API Keys

3. **Configure Environment**:
   ```bash
   export LANGSMITH_TRACING=true
   export LANGSMITH_API_KEY=your-key-here
   export LANGSMITH_PROJECT=klaro-dev
   ```

4. **Run Agent with Tracing**:
   ```bash
   python main.py
   ```

5. **View Traces** at https://smith.langchain.com/

### What LangSmith Shows

- **Trace Timeline**: Complete execution flow
- **LLM Calls**: Prompts, responses, token counts
- **Tool Executions**: Tool inputs, outputs, timing
- **State Changes**: How agent state evolves
- **Errors**: Stack traces and error details

### LangSmith Best Practices

```python
# Add custom metadata to runs
from langsmith import traceable

@traceable(run_type="tool", name="custom_tool")
def my_tool(input_data):
    # Your tool logic
    return result

# Add tags for filtering
os.environ["LANGSMITH_TAGS"] = "development,feature-x"
```

### Debugging Specific Runs

```python
# Add run name for easy identification
from langchain.callbacks import tracing_v2_enabled

with tracing_v2_enabled(project_name="klaro-debug", run_name="test-run-1"):
    run_klaro_langgraph(".")
```

---

## Code Structure and Module Organization

### Project Structure

```
klaro/
├── main.py                 # LangGraph agent orchestration
├── tools.py                # Custom tools (file ops, AST, RAG)
├── prompts.py              # System prompts and instructions
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── .env.example            # Environment variable template
├── README.md               # Project overview
├── CONTRIBUTING.md         # Contribution guidelines
├── CLAUDE.md               # Claude Code instructions
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # System architecture
│   ├── TESTING.md          # Testing guide
│   ├── DEVELOPMENT.md      # This file
│   ├── CODE_STYLE.md       # Code style standards
│   └── ...                 # Other docs
│
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Shared fixtures
│   ├── test_tools.py       # Tool unit tests
│   ├── test_main.py        # Agent unit tests
│   ├── test_integration.py # Integration tests
│   └── fixtures/           # Test data
│       ├── sample_code.py
│       └── sample_project/
│
└── klaro_db/               # ChromaDB vector store (gitignored)
```

### Module Responsibilities

**main.py**:
- LangGraph StateGraph definition
- Agent state management
- Node implementations (run_model, call_tool)
- Routing logic (decide_next_step)
- Execution function (run_klaro_langgraph)

**tools.py**:
- Codebase exploration (list_files, read_file)
- Code analysis (analyze_code, AST parsing)
- Knowledge retrieval (init_knowledge_base, retrieve_knowledge)
- Helper functions (.gitignore filtering)

**prompts.py**:
- System prompt definition
- ReAct format instructions
- Tool usage guidelines
- Output format requirements

### Design Patterns

**1. Tool Pattern**:
```
Define Python Function → Wrap as LangChain Tool → Bind to LLM → ToolNode Executes
```

**2. State Management Pattern**:
```
Initial State → Node Updates State → Reducer Merges Changes → Next Node Receives Updated State
```

**3. Error Handling Pattern**:
```
Tool Error → Return Error String → Log to error_log → Router Detects Error → Replan
```

---

## Adding New Tools

### Step-by-Step Guide

**1. Define Tool Function in `tools.py`**:

```python
def my_new_tool(parameter: str) -> str:
    """Clear, concise description of what this tool does.

    This docstring is crucial - it's shown to the LLM to help it
    decide when to use this tool.

    Args:
        parameter (str): Description of the parameter.
            Include type information and constraints.

    Returns:
        str: Description of return value.
            Explain the format (plain text, JSON, etc.)

    Example:
        >>> result = my_new_tool("test input")
        >>> print(result)
        Expected output format
    """
    try:
        # Tool implementation
        result = process_parameter(parameter)
        return result
    except Exception as e:
        # Return errors as strings (don't raise)
        return f"Error in my_new_tool: {e}"
```

**2. Register Tool in `main.py`**:

```python
from tools import my_new_tool

tools = [
    Tool(name="list_files", func=list_files, description=list_files.__doc__),
    Tool(name="read_file", func=read_file, description=read_file.__doc__),
    Tool(name="analyze_code", func=analyze_code, description=analyze_code.__doc__),
    Tool(name="my_new_tool", func=my_new_tool, description=my_new_tool.__doc__),
    # ... other tools
]
```

**3. Update System Prompt in `prompts.py`**:

```python
SYSTEM_PROMPT = """
...
Available Tools (Tools) and Their Functions:
- list_files(directory: str): Lists files and folders...
- read_file(file_path: str): Reads and returns the content...
- my_new_tool(parameter: str): [Description from docstring]
...
"""
```

**4. Write Tests in `tests/test_tools.py`**:

```python
@pytest.mark.unit
def test_my_new_tool_normal_case():
    """Test my_new_tool with valid input."""
    result = my_new_tool("valid input")
    assert "expected output" in result

@pytest.mark.unit
def test_my_new_tool_error_handling():
    """Test my_new_tool handles errors gracefully."""
    result = my_new_tool("invalid input")
    assert "Error" in result
```

**5. Document in README/Docs**:
- Add tool description to README.md
- Update ARCHITECTURE.md if tool changes system behavior
- Add usage examples

### Tool Design Best Practices

- **Return strings**: Always return `str`, never raise exceptions
- **Error handling**: Catch all exceptions, return error messages
- **Descriptive docstrings**: LLM uses these to decide when to call
- **Deterministic**: Same input → same output (when possible)
- **Fast execution**: Avoid long-running operations
- **Clear parameters**: Simple, well-typed parameters

---

## Extending Agent Capabilities

### Modifying Agent Behavior

**1. Change Routing Logic** (`decide_next_step`):

```python
def decide_next_step(state: AgentState):
    """Add custom routing conditions."""
    last_message = state["messages"][-1]

    # Custom condition: check for specific keyword
    if "pause execution" in last_message.content.lower():
        return "pause_node"  # New custom node

    # Existing conditions...
    if state.get("error_log"):
        return "run_model"
    # ...
```

**2. Add Custom Node**:

```python
def custom_processing_node(state: AgentState):
    """Custom node for specialized processing."""
    # Custom logic
    processed_data = process_state(state)

    return {
        "messages": [AIMessage(content=processed_data)],
        "error_log": ""
    }

# Register node
workflow.add_node("custom_node", custom_processing_node)
workflow.add_edge("run_model", "custom_node")
```

**3. Modify System Prompt**:

```python
# prompts.py
SYSTEM_PROMPT = """
You are Klaro, enhanced with new capabilities:
- Custom processing for X
- Special handling for Y
...
"""
```

### Adding New State Fields

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    error_log: str
    # New field
    analysis_cache: dict  # Cache analyzed files
```

### Customizing LLM Settings

```python
# main.py
LLM_MODEL = "gpt-4o"  # Upgrade model
llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=0.2,
    max_tokens=4000,  # Increase output length
    timeout=60,       # API timeout
    max_retries=3     # Retry on errors
)
```

---

## Performance Profiling

### Timing Analysis

```python
# profile_agent.py
import time
from main import run_klaro_langgraph

start_time = time.time()
run_klaro_langgraph(".")
end_time = time.time()

print(f"Total execution time: {end_time - start_time:.2f} seconds")
```

### Memory Profiling

```bash
# Install memory_profiler
pip install memory_profiler

# Add @profile decorator to functions
# Run with:
python -m memory_profiler main.py
```

### LangSmith Performance Analysis

- View token usage per LLM call
- Identify slow tool executions
- Analyze agent iteration counts
- Track API costs

### Optimization Tips

1. **Reduce LLM Calls**:
   - Cache repeated analyses
   - Batch similar operations
   - Use more specific prompts

2. **Optimize Tool Execution**:
   - Cache file reads
   - Lazy load large files
   - Use streaming for large outputs

3. **RAG Optimization**:
   - Adjust chunk size (balance context vs. specificity)
   - Tune retrieval count (k parameter)
   - Use smaller embedding models

---

## Logging and Debugging

### Python Logging Setup

```python
# debug_main.py
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('klaro_debug.log'),
        logging.StreamHandler()
    ]
)

# Add logging to modules
logger = logging.getLogger(__name__)

def run_model(state: AgentState):
    logger.debug(f"run_model called with {len(state['messages'])} messages")
    response = model.invoke(state["messages"])
    logger.debug(f"LLM response: {response.content[:100]}...")
    return {"messages": [response], "error_log": ""}
```

### Debugging Techniques

**1. Print State at Each Step**:

```python
def debug_run_model(state: AgentState):
    print(f"=== run_model ===")
    print(f"Message count: {len(state['messages'])}")
    print(f"Last message: {state['messages'][-1].content[:100]}")
    result = run_model(state)
    print(f"Response: {result['messages'][0].content[:100]}")
    return result
```

**2. Step Through with Debugger**:

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use IDE debugger breakpoints
```

**3. Save State History**:

```python
state_history = []

def track_state(state: AgentState):
    state_history.append(state.copy())
    return state

# After execution, inspect history
for i, state in enumerate(state_history):
    print(f"Step {i}: {state['messages'][-1].content[:50]}")
```

### Debugging Common Issues

**Issue: Agent loops infinitely**
- Check decide_next_step logic
- Verify "Final Answer" detection
- Reduce RECURSION_LIMIT for testing

**Issue: Tool execution fails**
- Add try-except in tool functions
- Log tool inputs and outputs
- Check error_log field

**Issue: LLM doesn't use tools correctly**
- Improve tool docstrings
- Add examples in system prompt
- Check tool parameter types

---

## Working with Dependencies

### Adding New Dependencies

```bash
# Install package
pip install new-package

# Add to requirements.txt
pip freeze | grep new-package >> requirements.txt

# Or manually edit requirements.txt
echo "new-package>=1.2.3" >> requirements.txt
```

### Dependency Management Best Practices

- Pin major/minor versions: `package>=1.2.0,<2.0.0`
- Use `requirements-dev.txt` for dev-only dependencies
- Document why each dependency is needed
- Regularly update dependencies: `pip list --outdated`

### Updating Dependencies

```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade langchain

# Check for security issues
pip install safety
safety check
```

---

## Release Process

### Version Numbering

Follow **Semantic Versioning** (SemVer):
- `MAJOR.MINOR.PATCH`
- Example: `1.2.3`

Increment:
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. **Update Version**:
   ```python
   # __init__.py or version.py
   __version__ = "1.2.0"
   ```

2. **Update CHANGELOG.md**:
   ```markdown
   ## [1.2.0] - 2025-10-23
   ### Added
   - New PDF reading tool
   - Support for custom style guides

   ### Fixed
   - Bug in AST analysis for async functions
   ```

3. **Run Full Test Suite**:
   ```bash
   pytest tests/ --cov=. --cov-report=term
   ```

4. **Update Documentation**:
   - README.md with new features
   - ARCHITECTURE.md if structure changed
   - Add migration guide for breaking changes

5. **Create Git Tag**:
   ```bash
   git tag -a v1.2.0 -m "Release version 1.2.0"
   git push origin v1.2.0
   ```

6. **Create GitHub Release**:
   - Go to Releases → Draft a new release
   - Select tag, add release notes
   - Upload any build artifacts

---

## Additional Resources

- **LangChain Docs**: https://python.langchain.com/docs/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangSmith**: https://docs.smith.langchain.com/
- **OpenAI API**: https://platform.openai.com/docs/
- **Python Packaging**: https://packaging.python.org/

---

## Getting Help

- **Issues**: Search or create GitHub issues
- **Discussions**: GitHub Discussions for questions
- **Documentation**: Check docs/ directory
- **Code Review**: Request review from maintainers

---

**Last Updated**: 2025-10-23
**Klaro Version**: 1.0
**Maintained by**: Klaro Development Team
