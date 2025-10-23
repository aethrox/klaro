# Project Structure and Extension Points

This document explains Klaro's architecture, project organization, and extension points for customization.

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Core Architecture](#core-architecture)
- [Data Flow](#data-flow)
- [Extension Points](#extension-points)
- [Module Dependencies](#module-dependencies)
- [Best Practices for Customization](#best-practices-for-customization)

---

## Overview

Klaro is a modular, autonomous AI documentation agent built on the LangGraph framework. The architecture follows a clear separation of concerns:

- **main.py** - Orchestration layer (LangGraph state machine)
- **tools.py** - Tool implementations (code analysis, RAG, file operations)
- **prompts.py** - System prompt configuration
- **tests/** - Test suite and fixtures

---

## Directory Structure

```
klaro/
├── main.py                     # LangGraph agent orchestration
├── tools.py                    # Custom tool implementations
├── prompts.py                  # System prompt definitions
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore patterns
│
├── docs/                       # Documentation directory
│   ├── ARCHITECTURE.md         # System architecture overview
│   ├── ADVANCED_CONFIG.md      # Advanced configuration guide
│   ├── PROJECT_STRUCTURE.md    # This file
│   ├── configuration.md        # Basic configuration guide
│   ├── usage_examples.md       # Usage examples
│   ├── troubleshooting.md      # Troubleshooting guide
│   ├── CODE_STYLE.md           # Code style guidelines
│   ├── TESTING.md              # Testing guide
│   └── DEVELOPMENT.md          # Development workflow
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_tools.py           # Tool unit tests
│   ├── test_main.py            # Agent integration tests
│   └── fixtures/               # Test data and sample projects
│       └── sample_project/
│
├── klaro_db/                   # ChromaDB vector database (generated)
│   └── (vector store files)
│
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── CLAUDE.md                   # Claude Code integration instructions
└── README.md                   # Project README
```

### Key Directories

- **`/` (root)**: Core Python modules and configuration files
- **`docs/`**: All documentation in Markdown format
- **`tests/`**: Test suite with unit and integration tests
- **`klaro_db/`**: Persisted ChromaDB vector database (auto-generated)

---

## Core Architecture

### 1. LangGraph State Machine (main.py)

Klaro uses a **StateGraph** to manage the agent's workflow:

```
┌─────────────┐
│  START      │
│ (HumanMsg)  │
└──────┬──────┘
       │
       v
┌─────────────┐
│ run_model   │ <──────────┐
│ (LLM Think) │            │
└──────┬──────┘            │
       │                   │
       v                   │
┌─────────────┐            │
│decide_next  │            │
│   _step     │            │
└──────┬──────┘            │
       │                   │
       ├───[tool_calls?]───┤
       │                   │
       v                   │
┌─────────────┐            │
│ call_tool   │────────────┘
│ (Execute)   │
└─────────────┘

       │
       v
┌─────────────┐
│     END     │
│ (Final Ans) │
└─────────────┘
```

**Components:**

- **AgentState** (main.py:106): TypedDict defining state schema
  - `messages`: Conversation history (append-only via reducer)
  - `error_log`: Execution error tracking

- **run_model** (main.py:157): Node for LLM invocation
  - Sends message history to LLM
  - Returns AIMessage with reasoning or tool calls

- **decide_next_step** (main.py:207): Conditional router
  - Error recovery → loop to run_model
  - "Final Answer" detected → END
  - Tool calls present → call_tool
  - Otherwise → continue to run_model

- **call_tool** (main.py:296): ToolNode for execution
  - Parses tool_calls from AIMessage
  - Executes requested tools
  - Returns ToolMessage results

### 2. Tool System (tools.py)

Tools provide the agent's capabilities:

| Tool Category | Tools | Purpose |
|--------------|-------|---------|
| **Codebase Exploration** | `list_files`, `read_file` | Navigate and read project files |
| **Code Analysis** | `analyze_code`, `_extract_docstring` | AST-based Python code extraction |
| **External Knowledge** | `web_search`, `init_knowledge_base`, `retrieve_knowledge` | RAG and external data |
| **Support Functions** | `get_gitignore_patterns`, `is_ignored` | .gitignore filtering |

**Key Design Patterns:**

- **Agent-Centric**: Tools are called incrementally (not bulk loading)
- **Error-Safe**: All tools return strings (never raise exceptions)
- **Hybrid Analysis**: AST extraction + LLM semantic interpretation

### 3. RAG System (tools.py)

**Vector Database Flow:**

```
Documents (style guides)
       │
       v
┌──────────────────┐
│ Text Splitting   │ chunk_size=1000, overlap=200
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ OpenAI Embedding │ text-embedding-3-small
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  ChromaDB Store  │ ./klaro_db (persisted)
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ KLARO_RETRIEVER  │ Global retriever (k=3)
└──────────────────┘
```

**Globals:**

- `KLARO_RETRIEVER` (tools.py:89): Global VectorStoreRetriever instance
- `VECTOR_DB_PATH` (tools.py:88): ChromaDB location (`./klaro_db`)
- `IGNORE_PATTERNS` (tools.py:319): Compiled .gitignore regex patterns

---

## Data Flow

### Complete Agent Execution Flow

```
1. Initialization (run_klaro_langgraph)
   ├── Load environment variables (.env)
   ├── Initialize RAG knowledge base (init_knowledge_base)
   │   ├── Split documents into chunks
   │   ├── Generate embeddings (OpenAI)
   │   └── Store in ChromaDB
   └── Create initial HumanMessage with task

2. Graph Execution (app.invoke)
   ├── Entry Point: run_model
   │   └── LLM receives: SYSTEM_PROMPT + task + message history
   │
   ├── Conditional Routing: decide_next_step
   │   ├── Check error_log → replan if needed
   │   ├── Check "Final Answer" → END if complete
   │   ├── Check tool_calls → execute if present
   │   └── Otherwise → continue thinking
   │
   ├── Tool Execution: call_tool (if needed)
   │   ├── Parse tool_calls from AIMessage
   │   ├── Execute tools (list_files, read_file, analyze_code, etc.)
   │   └── Return ToolMessage results
   │   └── Loop back to run_model
   │
   └── Termination: END
       └── Extract final documentation from last message

3. Output Processing
   ├── Strip "Final Answer:" prefix
   └── Print documentation to stdout
```

### ReAct Loop Pattern

Klaro implements the **ReAct (Reasoning and Acting)** paradigm:

```
Thought → Action → Observation → Thought → ... → Final Answer
```

**Example Sequence:**

1. **Thought**: "I need to explore the project structure"
2. **Action**: Call `list_files(".")`
3. **Observation**: Receive directory tree
4. **Thought**: "I should read main.py to understand the architecture"
5. **Action**: Call `read_file("main.py")`
6. **Observation**: Receive file contents
7. **Thought**: "I should analyze the code structure"
8. **Action**: Call `analyze_code(main_py_content)`
9. **Observation**: Receive JSON with classes/functions
10. **Thought**: "I need the style guide"
11. **Action**: Call `retrieve_knowledge("README style guidelines")`
12. **Observation**: Receive style guide chunks
13. **Final Answer**: Generate README.md documentation

---

## Extension Points

Klaro is designed for extensibility. Here are the key extension points:

### 1. Adding Custom Tools

**Location:** `tools.py`

**Steps:**

1. **Define the tool function:**

```python
# tools.py
def analyze_dependencies(file_path: str = "requirements.txt") -> str:
    """Analyzes project dependencies from requirements.txt.

    Args:
        file_path: Path to the dependency file.

    Returns:
        JSON string with dependency analysis.
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        deps = [line.strip() for line in lines if line.strip() and not line.startswith('#')]

        return json.dumps({
            "total": len(deps),
            "packages": deps
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
```

2. **Register in main.py:**

```python
# main.py
from tools import (
    list_files, read_file, analyze_code,
    web_search, init_knowledge_base, retrieve_knowledge,
    analyze_dependencies  # Add your tool
)

tools = [
    Tool(name="list_files", func=list_files, description=list_files.__doc__),
    # ... other tools ...
    Tool(name="analyze_dependencies", func=analyze_dependencies, description=analyze_dependencies.__doc__),
]
```

3. **Update system prompt (optional):**

```python
# prompts.py
SYSTEM_PROMPT = """
...
Available Tools:
...
6. analyze_dependencies[file_path] - Analyze project dependencies
"""
```

**Tool Design Guidelines:**

- Always return strings (never raise exceptions)
- Use JSON format for structured data
- Include detailed docstrings (LLM uses these)
- Keep execution time < 5 seconds
- Make tools idempotent (safe to call multiple times)

### 2. Modifying the System Prompt

**Location:** `prompts.py`

**Examples:**

```python
# Focus on API documentation
API_DOCS_PROMPT = """
You are Klaro, specialized in API documentation.

Focus on:
1. Endpoint routes and HTTP methods
2. Request/response schemas
3. Authentication requirements
4. Error codes and messages
"""

# Focus on tutorials
TUTORIAL_PROMPT = """
You are Klaro, a tutorial writer.

Create beginner-friendly guides with:
1. Step-by-step instructions
2. Annotated code examples
3. Common pitfalls section
"""
```

### 3. Customizing the LLM Model

**Location:** `main.py:78`

**Options:**

```python
# Cost-effective (default)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Higher quality
llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

# Alternative providers
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.2)
```

### 4. Modifying RAG Behavior

**Chunk Size:**

```python
# tools.py:763
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,   # Smaller chunks = more precise retrieval
    chunk_overlap=100
)
```

**Retrieval Count:**

```python
# tools.py:793
KLARO_RETRIEVER = vectorstore.as_retriever(search_kwargs={"k": 5})  # Return top 5 chunks
```

**Embedding Model:**

```python
# tools.py:773
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")  # Higher quality embeddings
```

### 5. Adding New Graph Nodes

**Location:** `main.py`

**Example: Add a validation node:**

```python
# main.py

def validate_output(state: AgentState):
    """Validates generated documentation before finalizing."""
    last_message = state["messages"][-1]

    if "Final Answer" in last_message.content:
        # Check if documentation meets criteria
        content = last_message.content.replace("Final Answer:", "").strip()

        if len(content) < 100:
            return {
                "messages": [],
                "error_log": "Documentation too short. Please expand."
            }

    return {"messages": [], "error_log": ""}

# Add to graph
workflow.add_node("validate", validate_output)

# Modify routing
def decide_next_step_with_validation(state: AgentState):
    if state.get("error_log"):
        return "run_model"

    last_message = state["messages"][-1]

    if "Final Answer" in last_message.content:
        return "validate"  # Route to validation first

    if last_message.tool_calls:
        return "call_tool"

    return "run_model"

# Update edges
workflow.add_conditional_edges(
    "run_model",
    decide_next_step_with_validation,
    {
        "call_tool": "call_tool",
        "validate": "validate",
        "run_model": "run_model"
    }
)

workflow.add_conditional_edges(
    "validate",
    lambda state: END if not state.get("error_log") else "run_model",
    {END: END, "run_model": "run_model"}
)
```

### 6. Custom State Management

**Location:** `main.py:106`

**Example: Add metadata tracking:**

```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    error_log: str
    # New fields
    files_analyzed: list[str]  # Track which files have been read
    total_tokens: int          # Track token usage
    analysis_depth: int        # Track recursion depth
```

Update nodes to populate new fields:

```python
def run_model(state: AgentState):
    response = model.invoke(state["messages"])

    # Track token usage (example)
    tokens = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)

    return {
        "messages": [response],
        "error_log": "",
        "total_tokens": state.get("total_tokens", 0) + tokens
    }
```

### 7. Alternative Output Formats

**Location:** `main.py:run_klaro_langgraph`

**Example: Save to file instead of printing:**

```python
def run_klaro_langgraph(project_path: str = ".", output_file: str = "README.md"):
    # ... existing code ...

    try:
        final_state = app.invoke(inputs, {"recursion_limit": RECURSION_LIMIT})
        final_message = final_state["messages"][-1].content

        if final_message.startswith("Final Answer:"):
            final_message = final_message.replace("Final Answer:", "").strip()

        # Save to file instead of printing
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_message)

        print(f"✅ Documentation saved to {output_file}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
```

### 8. Custom .gitignore Patterns

**Location:** `tools.py:92`

**Modify GITIGNORE_CONTENT or load from file:**

```python
# Load .gitignore from project directory
def get_project_gitignore(project_path: str) -> str:
    """Load .gitignore from the project being analyzed."""
    gitignore_path = os.path.join(project_path, ".gitignore")

    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            return f.read()

    return GITIGNORE_CONTENT  # Fallback to default
```

---

## Module Dependencies

### Import Graph

```
main.py
├── tools.py
│   ├── ast (stdlib)
│   ├── json (stdlib)
│   ├── langchain_openai.OpenAIEmbeddings
│   ├── langchain_community.vectorstores.Chroma
│   ├── langchain_text_splitters.RecursiveCharacterTextSplitter
│   └── langchain_core.documents.Document
├── prompts.py
├── langgraph.graph.StateGraph
├── langgraph.prebuilt.ToolNode
├── langchain_openai.ChatOpenAI
├── langchain_core.messages
└── langchain_core.tools.Tool
```

### External Dependencies (requirements.txt)

**Core:**
- `langchain` - LLM orchestration framework
- `langgraph` - State machine workflow engine
- `langchain-openai` - OpenAI LLM and embeddings integration
- `langchain-community` - Community integrations (ChromaDB)
- `chromadb` - Vector database for RAG
- `python-dotenv` - Environment variable management

**Development:**
- `pytest` - Testing framework
- `pytest-cov` - Test coverage
- `black` - Code formatter
- `ruff` - Linter

---

## Best Practices for Customization

### 1. Testing Custom Extensions

Always write tests for new tools:

```python
# tests/test_custom_tools.py
import pytest
from tools import analyze_dependencies

def test_analyze_dependencies():
    result = analyze_dependencies("tests/fixtures/requirements.txt")
    data = json.loads(result)

    assert "total" in data
    assert "packages" in data
    assert data["total"] > 0
```

### 2. Error Handling

All custom tools should return error strings:

```python
def my_custom_tool(param: str) -> str:
    try:
        # ... implementation ...
        return json.dumps(result)
    except FileNotFoundError as e:
        return json.dumps({"error": f"File not found: {e}"})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"})
```

### 3. Docstring Quality

LLM uses docstrings to decide when to call tools:

```python
def good_tool_docstring(param: str) -> str:
    """Analyzes the project's dependency graph and detects outdated packages.

    This tool reads requirements.txt and package-lock.json files, checks
    package versions against PyPI, and returns a JSON report with:
    - List of outdated packages
    - Available updates
    - Security vulnerabilities

    Args:
        param: Path to the project directory containing dependency files.

    Returns:
        JSON string with dependency analysis and recommendations.
    """
    # ... implementation ...
```

### 4. State Immutability

Always return new state objects (don't modify in place):

```python
# Good
def my_node(state: AgentState):
    new_files = state.get("files_analyzed", []) + ["new_file.py"]
    return {"files_analyzed": new_files}

# Bad (mutates state)
def my_node(state: AgentState):
    state["files_analyzed"].append("new_file.py")  # Don't do this!
    return state
```

### 5. Version Control

Track changes to configuration:

```bash
git commit -m "feat: add dependency analysis tool"
git commit -m "config: increase chunk size to 1500 for better context"
git commit -m "fix: handle missing .gitignore files gracefully"
```

---

## Related Documentation

- [Architecture Overview](architecture.md) - High-level system design
- [Advanced Configuration](advanced-config.md) - Performance tuning and integrations
- [Development Guide](development.md) - Contributing and development workflow
- [Code Style Guide](code-style.md) - Coding standards

---

**Last Updated:** 2025-10-23
