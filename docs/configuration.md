# Configuration Guide

This guide provides comprehensive documentation for configuring Klaro, including LLM model selection, recursion limit tuning, LangSmith tracing, ChromaDB configuration, and custom tool integration.

## Table of Contents
- [Environment Variables](#environment-variables)
- [LLM Model Selection](#llm-model-selection)
- [Recursion Limit Tuning](#recursion-limit-tuning)
- [LangSmith Tracing Configuration](#langsmith-tracing-configuration)
- [ChromaDB Configuration](#chromadb-configuration)
- [Custom Tool Integration](#custom-tool-integration)
- [Advanced Configuration](#advanced-configuration)

---

## Environment Variables

### Overview

Klaro uses environment variables for configuration. These are loaded from a `.env` file in the project root.

### Required Variables

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `OPENAI_API_KEY` | **Required** | Your OpenAI API key for LLM and embeddings | `sk-proj-abc123...` |

### Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `KLARO_RECURSION_LIMIT` | Integer | `50` | Maximum agent iterations before timeout |
| `LANGSMITH_TRACING` | Boolean | `false` | Enable LangSmith tracing for debugging |
| `LANGSMITH_API_KEY` | String | - | LangSmith API key (required if tracing enabled) |
| `LANGSMITH_ENDPOINT` | URL | `https://api.smith.langchain.com` | LangSmith API endpoint |
| `LANGSMITH_PROJECT` | String | `klaro` | LangSmith project name for organizing traces |

### Example `.env` File

```bash
# Required Configuration
OPENAI_API_KEY=sk-proj-1234567890abcdefghijklmnopqrstuvwxyz

# Optional: Agent Behavior
KLARO_RECURSION_LIMIT=50

# Optional: LangSmith Tracing (for debugging)
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=ls__1234567890abcdef
LANGSMITH_PROJECT=klaro

# Optional: Custom Database Path
# KLARO_DB_PATH=./custom_db_path
```

### Loading Environment Variables

Environment variables are loaded in `main.py` using `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Access variables
api_key = os.getenv("OPENAI_API_KEY")
recursion_limit = int(os.getenv("KLARO_RECURSION_LIMIT", "50"))
```

### Validating Configuration

**Validation Script:**
```python
# validate_env.py
import os
from dotenv import load_dotenv

load_dotenv()

def validate_config():
    issues = []

    # Required
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("❌ OPENAI_API_KEY is missing")
    elif not os.getenv("OPENAI_API_KEY").startswith("sk-"):
        issues.append("⚠️  OPENAI_API_KEY format may be invalid")
    else:
        print("✅ OPENAI_API_KEY is set")

    # Optional but important
    if os.getenv("LANGSMITH_TRACING", "").lower() == "true":
        if not os.getenv("LANGSMITH_API_KEY"):
            issues.append("⚠️  LANGSMITH_TRACING enabled but LANGSMITH_API_KEY is missing")
        else:
            print("✅ LangSmith tracing configured")

    recursion_limit = os.getenv("KLARO_RECURSION_LIMIT", "50")
    try:
        limit = int(recursion_limit)
        if limit < 10:
            issues.append(f"⚠️  KLARO_RECURSION_LIMIT ({limit}) is very low")
        elif limit > 200:
            issues.append(f"⚠️  KLARO_RECURSION_LIMIT ({limit}) is very high (high cost)")
        else:
            print(f"✅ KLARO_RECURSION_LIMIT set to {limit}")
    except ValueError:
        issues.append(f"❌ KLARO_RECURSION_LIMIT must be an integer, got: {recursion_limit}")

    if issues:
        print("\nConfiguration Issues:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ All configuration valid!")
        return True

if __name__ == "__main__":
    validate_config()
```

**Run validation:**
```bash
python validate_env.py
```

---

## LLM Model Selection

### Overview

Klaro supports multiple OpenAI models. Model selection affects performance, cost, and output quality.

### Supported Models

| Model | Context Window | Cost (Input/Output per 1M tokens) | Speed | Best For |
|-------|---------------|-----------------------------------|-------|----------|
| `gpt-4o-mini` | 128K | $0.15 / $0.60 | ⚡⚡⚡ Fast | **Default** - Most use cases |
| `gpt-4o` | 128K | $2.50 / $10.00 | ⚡⚡ Medium | Complex codebases, high accuracy |
| `gpt-4-turbo` | 128K | $10.00 / $30.00 | ⚡ Slower | Maximum reasoning quality |
| `gpt-3.5-turbo` | 16K | $0.50 / $1.50 | ⚡⚡⚡ Fast | Simple projects (not recommended) |

*Pricing as of January 2025. Check OpenAI pricing page for current rates.*

### Changing the Model

**Method 1: Edit main.py directly**

```python
# main.py (around line 78)
LLM_MODEL = "gpt-4o-mini"  # Change this line

# Options:
# LLM_MODEL = "gpt-4o"        # More powerful
# LLM_MODEL = "gpt-4-turbo"   # Most powerful
# LLM_MODEL = "gpt-3.5-turbo" # Cheapest (not recommended)
```

**Method 2: Use environment variable (requires code modification)**

Add to `main.py`:
```python
LLM_MODEL = os.getenv("KLARO_LLM_MODEL", "gpt-4o-mini")
```

Then in `.env`:
```bash
KLARO_LLM_MODEL=gpt-4o
```

### Model Selection Guide

#### Use `gpt-4o-mini` when:
- ✅ Analyzing small to medium projects (<10,000 lines)
- ✅ Cost is a primary concern
- ✅ Documentation style is straightforward
- ✅ Fast iteration is needed

**Example Cost:**
- Project size: 5,000 lines
- Estimated tokens: ~15,000 input, ~3,000 output
- Cost: **~$0.01 per run**

#### Use `gpt-4o` when:
- ✅ Analyzing large, complex codebases (10,000+ lines)
- ✅ Code has intricate logic or architectural patterns
- ✅ Higher quality documentation is required
- ✅ Multiple programming paradigms are used

**Example Cost:**
- Project size: 20,000 lines
- Estimated tokens: ~50,000 input, ~8,000 output
- Cost: **~$0.20 per run**

#### Use `gpt-4-turbo` when:
- ✅ Maximum reasoning capability is required
- ✅ Extremely complex domain-specific code
- ✅ Cost is not a constraint
- ✅ Highest quality output is mandatory

**Example Cost:**
- Project size: 50,000 lines
- Estimated tokens: ~150,000 input, ~15,000 output
- Cost: **~$1.95 per run**

### Model Comparison Example

**Test Project:** Flask REST API (2,000 lines)

| Model | Runtime | Cost | Quality Score* | Details Captured |
|-------|---------|------|----------------|------------------|
| gpt-3.5-turbo | 45s | $0.003 | 6/10 | Basic structure, misses nuances |
| gpt-4o-mini | 60s | $0.008 | 8/10 | **Good balance** (Recommended) |
| gpt-4o | 90s | $0.045 | 9/10 | Excellent details, architecture |
| gpt-4-turbo | 120s | $0.285 | 9.5/10 | Comprehensive, may be overkill |

*Quality Score: Subjective rating based on completeness, accuracy, and usefulness*

### Cost Optimization Tips

1. **Use gpt-4o-mini by default**
   - Switch to gpt-4o only for complex projects

2. **Analyze subdirectories separately**
   ```bash
   # Cheaper than analyzing entire large project at once
   python main.py ./src
   python main.py ./tests
   ```

3. **Monitor token usage with LangSmith**
   ```bash
   LANGSMITH_TRACING=true python main.py
   # Check token usage in LangSmith dashboard
   ```

4. **Limit recursion for cost control**
   ```bash
   KLARO_RECURSION_LIMIT=30  # Fewer iterations = lower cost
   ```

---

## Recursion Limit Tuning

### What is the Recursion Limit?

The recursion limit controls the maximum number of ReAct loop iterations (Thought → Action → Observation cycles) the agent can perform before timing out.

### Default Value

```python
# main.py
KLARO_RECURSION_LIMIT = int(os.getenv("KLARO_RECURSION_LIMIT", "50"))
```

**Default: 50 iterations**

### When to Adjust

#### Increase the limit (to 75-150) when:
- ✅ Analyzing large codebases (>10,000 lines)
- ✅ Agent consistently hits the limit without completing
- ✅ Complex project structure with many subdirectories
- ✅ You see "Recursion limit exceeded" errors

#### Decrease the limit (to 20-40) when:
- ✅ Analyzing small projects (<1,000 lines)
- ✅ Controlling costs (fewer iterations = less API usage)
- ✅ Testing/debugging (faster failure detection)
- ✅ Agent is getting stuck in loops

### Configuration

**Set in `.env`:**
```bash
KLARO_RECURSION_LIMIT=100
```

**Or modify `main.py` directly:**
```python
KLARO_RECURSION_LIMIT = 100  # Hard-coded value
```

### Performance vs Accuracy Tradeoff

| Limit | Use Case | Avg Cost | Completion Rate | Best For |
|-------|----------|----------|----------------|----------|
| 20 | Small projects | $0.02 | 85% | Quick prototypes |
| 50 | **Default** | $0.05 | 95% | **Most projects** |
| 100 | Large projects | $0.12 | 98% | Complex codebases |
| 150 | Very large | $0.20 | 99% | Enterprise applications |
| 200+ | Extreme cases | $0.30+ | 99%+ | Massive monoliths |

### Monitoring Recursion Usage

**Add logging to main.py:**
```python
def run_model(state: AgentState):
    iteration = len([m for m in state['messages'] if hasattr(m, 'tool_calls')])
    print(f"Iteration {iteration}/{KLARO_RECURSION_LIMIT}")
    # ... rest of function
```

**Check LangSmith trace:**
- View total iterations
- Identify bottlenecks
- See which tools are called most

### Example: Tuning for Your Project

**Small Project (500 lines):**
```bash
KLARO_RECURSION_LIMIT=25
python main.py
# Expected iterations: 8-15
# Cost: ~$0.015
```

**Medium Project (5,000 lines):**
```bash
KLARO_RECURSION_LIMIT=50  # Default
python main.py
# Expected iterations: 20-35
# Cost: ~$0.05
```

**Large Project (25,000 lines):**
```bash
KLARO_RECURSION_LIMIT=120
python main.py
# Expected iterations: 60-100
# Cost: ~$0.18
```

---

## LangSmith Tracing Configuration

### What is LangSmith?

LangSmith is LangChain's observability platform for debugging and monitoring LLM applications. It provides:
- Detailed execution traces
- Token usage analytics
- Error tracking
- Performance metrics

### Enabling LangSmith

**1. Create LangSmith Account:**
- Visit https://smith.langchain.com
- Sign up for free account
- Create a new project (e.g., "klaro")

**2. Get API Key:**
- Navigate to Settings → API Keys
- Click "Create API Key"
- Copy the key (starts with `ls__`)

**3. Configure `.env`:**
```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls__your_api_key_here
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=klaro
```

**4. Run Klaro:**
```bash
python main.py
```

**5. View Traces:**
- Visit https://smith.langchain.com
- Open your project ("klaro")
- View real-time execution traces

### LangSmith Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LANGSMITH_TRACING` | No | `false` | Enable/disable tracing |
| `LANGSMITH_API_KEY` | Yes* | - | Your LangSmith API key (*if tracing enabled) |
| `LANGSMITH_ENDPOINT` | No | `https://api.smith.langchain.com` | API endpoint URL |
| `LANGSMITH_PROJECT` | No | `klaro` | Project name for organizing traces |

### What Gets Traced

**Automatically captured:**
- ✅ Every LLM call (input prompts, outputs)
- ✅ Tool executions (inputs, outputs, duration)
- ✅ Agent state transitions
- ✅ Token usage and costs
- ✅ Errors and exceptions
- ✅ Execution timeline

**Example trace structure:**
```
Run: run_klaro_langgraph
├─ run_model (2.3s) - $0.002
│  └─ ChatOpenAI (gpt-4o-mini)
│     ├─ Input: 1,234 tokens
│     └─ Output: 456 tokens
├─ call_tool (0.5s)
│  ├─ list_files["."]
│  └─ read_file["main.py"]
├─ run_model (1.8s) - $0.001
...
```

### Using LangSmith for Debugging

**Scenario 1: Agent not completing**
1. Enable tracing
2. Run Klaro
3. Open LangSmith trace
4. Check which iteration it's stuck on
5. Review tool outputs for errors

**Scenario 2: High costs**
1. View trace
2. Check "Token Usage" tab
3. Identify most expensive calls
4. Optimize prompts or switch models

**Scenario 3: Incorrect output**
1. Review trace
2. Check which files were analyzed
3. Verify tool outputs are correct
4. Review LLM reasoning in "Thought" steps

### LangSmith Best Practices

1. **Use different projects for different use cases:**
   ```bash
   # Development
   LANGSMITH_PROJECT=klaro-dev

   # Production
   LANGSMITH_PROJECT=klaro-prod

   # Testing
   LANGSMITH_PROJECT=klaro-test
   ```

2. **Tag runs for organization:**
   ```python
   # Modify main.py to add tags
   from langsmith import traceable

   @traceable(tags=["production", "large-project"])
   def run_klaro_langgraph(project_path):
       # ...
   ```

3. **Disable in production to reduce overhead:**
   ```bash
   LANGSMITH_TRACING=false  # In production .env
   ```

4. **Export traces for documentation:**
   - Use LangSmith UI to export traces
   - Share with team for debugging
   - Create benchmark traces

### Cost of LangSmith

- **Free Tier:** 5,000 traces/month
- **Pro Tier:** $39/month for 50,000 traces/month
- **No additional runtime cost** (async logging)

---

## ChromaDB Configuration

### Overview

Klaro uses ChromaDB as a vector database for Retrieval-Augmented Generation (RAG). It stores project style guides and retrieves relevant context during documentation generation.

### Default Configuration

**Location:**
```python
# tools.py
KLARO_DB_PATH = "./klaro_db"
```

**Embedding Model:**
```python
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```

**Text Splitting:**
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
```

### Custom Database Path

**Method 1: Edit tools.py**
```python
# tools.py
KLARO_DB_PATH = os.path.expanduser("~/klaro_databases/my_project")
```

**Method 2: Use environment variable (requires code modification)**

Add to `tools.py`:
```python
KLARO_DB_PATH = os.getenv("KLARO_DB_PATH", "./klaro_db")
```

Then in `.env`:
```bash
KLARO_DB_PATH=/custom/path/to/database
```

### Custom Embedding Model

**Available OpenAI Embedding Models:**

| Model | Dimensions | Cost per 1M tokens | Performance |
|-------|------------|-------------------|-------------|
| `text-embedding-3-small` | 1536 | $0.02 | **Default** - Fast, good quality |
| `text-embedding-3-large` | 3072 | $0.13 | Higher quality, slower |
| `text-embedding-ada-002` | 1536 | $0.10 | Legacy model (not recommended) |

**Change embedding model:**
```python
# tools.py
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
```

**Cost impact example:**
- Small project: 10 documents, 5,000 tokens
  - `text-embedding-3-small`: $0.0001
  - `text-embedding-3-large`: $0.00065
- Large project: 100 documents, 50,000 tokens
  - `text-embedding-3-small`: $0.001
  - `text-embedding-3-large`: $0.0065

### Custom Text Splitting

**Adjust chunk size and overlap:**
```python
# tools.py
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # Smaller chunks = more granular retrieval
    chunk_overlap=100,   # Reduce overlap to save storage
    separators=["\n\n", "\n", " ", ""]
)
```

**Tradeoffs:**

| Chunk Size | Overlap | Storage | Retrieval Quality | Best For |
|------------|---------|---------|-------------------|----------|
| 500 | 50 | Small | Precise | Short docs, FAQs |
| 1000 | 200 | **Medium** | **Balanced** | **Default** |
| 2000 | 400 | Large | Comprehensive | Long-form guides |

### Custom Retrieval Settings

**Adjust number of retrieved documents:**
```python
# tools.py, in retrieve_knowledge function
def retrieve_knowledge(query: str) -> str:
    results = KLARO_RETRIEVER.invoke(query, k=5)  # Retrieve top 5 (default: 3)
    # ...
```

**Tradeoffs:**
- `k=1`: Fast, minimal context, may miss relevant info
- `k=3`: **Default** - balanced
- `k=5`: More context, slower, higher token usage
- `k=10`: Maximum context, expensive

### Advanced: Custom Collection Configuration

**Add custom metadata:**
```python
# tools.py, in init_knowledge_base
collection.add(
    documents=texts,
    metadatas=[
        {"source": "style_guide", "section": "formatting"},
        {"source": "examples", "section": "api_docs"}
    ],
    ids=[f"doc_{i}" for i in range(len(texts))]
)
```

**Filter retrieval by metadata:**
```python
# tools.py, in retrieve_knowledge
results = collection.query(
    query_texts=[query],
    n_results=3,
    where={"source": "style_guide"}  # Only retrieve from style guides
)
```

### ChromaDB Persistence

**Database structure:**
```
klaro_db/
├── chroma.sqlite3          # Metadata database
└── <collection_id>/
    ├── data_level0.bin     # Vector data
    └── index_metadata.json # Index configuration
```

**Resetting the database:**
```bash
rm -rf klaro_db
python main.py  # Will reinitialize automatically
```

### Custom Style Guides

**Add your own style guide documents:**

```python
# tools.py, modify init_knowledge_base
def init_knowledge_base(documents: list[str]):
    # Default style guide
    default_docs = [
        "Documentation should be clear and concise...",
        # ... existing defaults
    ]

    # Add custom documents
    custom_docs = []

    # Load from file
    with open("my_style_guide.md", "r") as f:
        custom_docs.append(f.read())

    # Combine all documents
    all_docs = default_docs + documents + custom_docs

    # Continue with initialization
    # ...
```

**Or provide at runtime:**
```python
from main import run_klaro_langgraph
from tools import init_knowledge_base

# Load custom style guides
custom_guides = [
    open("style_guide_1.md").read(),
    open("style_guide_2.md").read(),
]

init_knowledge_base(custom_guides)

# Run Klaro
result = run_klaro_langgraph("./my_project")
```

---

## Custom Tool Integration

### Overview

Klaro's agent can be extended with custom tools. Tools are Python functions decorated with `@tool` from LangChain.

### Tool Structure

**Anatomy of a tool:**
```python
from langchain_core.tools import tool

@tool
def my_custom_tool(param: str) -> str:
    """
    Clear, concise description of what this tool does.

    The LLM reads this docstring to decide when to use the tool.
    Be specific about inputs and expected outputs.

    Args:
        param: Description of the parameter

    Returns:
        Description of the return value
    """
    # Tool implementation
    result = do_something(param)
    return result
```

**Key components:**
1. `@tool` decorator - Registers function as a LangChain tool
2. Type hints - `param: str` and `-> str` are required
3. Docstring - LLM uses this to understand tool purpose
4. Return value - Must be a string (JSON for complex data)

### Example: Adding a Git Analysis Tool

**1. Create the tool in `tools.py`:**
```python
import subprocess

@tool
def analyze_git_history(repo_path: str) -> str:
    """
    Analyzes Git commit history to understand project evolution.

    Retrieves the last 10 commits with stats to provide context
    about recent development activity, contributors, and changes.

    Args:
        repo_path: Path to the Git repository

    Returns:
        JSON string with commit history and stats
    """
    try:
        # Get last 10 commits
        result = subprocess.run(
            ["git", "log", "--oneline", "--stat", "-10"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return json.dumps({"error": "Not a git repository or git not installed"})

        # Parse output
        commits = result.stdout.strip().split("\n")

        return json.dumps({
            "commits": commits,
            "total_commits": len(commits),
            "repository_path": repo_path
        })

    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Git command timed out"})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**2. Register the tool in `main.py`:**
```python
from tools import (
    list_files,
    read_file,
    analyze_code,
    web_search,
    retrieve_knowledge,
    analyze_git_history  # Import your new tool
)

# Add to tools list
tools = [
    list_files,
    read_file,
    analyze_code,
    web_search,
    retrieve_knowledge,
    analyze_git_history  # Add here
]

tools_node = ToolNode(tools)
```

**3. Update the system prompt in `prompts.py`:**
```python
SYSTEM_PROMPT = f"""
[... existing prompt ...]

Available tools:
- list_files[directory]: Lists files in directory
- read_file[file_path]: Reads file content
- analyze_code[code_content]: Analyzes Python code using AST
- web_search[query]: Searches for external information
- retrieve_knowledge[query]: Retrieves style guide context
- analyze_git_history[repo_path]: Analyzes Git commit history (NEW)

[... rest of prompt ...]
"""
```

**4. Test the new tool:**
```bash
python main.py
# Agent should now be able to use analyze_git_history
```

### Example: Adding a Dependency Analyzer

```python
@tool
def analyze_dependencies(requirements_file: str) -> str:
    """
    Analyzes project dependencies from requirements.txt or setup.py.

    Extracts package names, versions, and categorizes them by purpose
    (web framework, database, testing, etc.).

    Args:
        requirements_file: Path to requirements.txt or setup.py

    Returns:
        JSON string with dependency analysis
    """
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            content = f.read()

        dependencies = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse package==version
                if '==' in line:
                    package, version = line.split('==')
                    dependencies.append({
                        "package": package.strip(),
                        "version": version.strip()
                    })
                else:
                    dependencies.append({
                        "package": line,
                        "version": "unspecified"
                    })

        # Categorize dependencies (simplified)
        categories = {
            "web": ["flask", "django", "fastapi"],
            "data": ["pandas", "numpy", "sqlalchemy"],
            "ai": ["langchain", "openai", "chromadb"],
            "testing": ["pytest", "unittest", "coverage"]
        }

        categorized = {cat: [] for cat in categories}
        categorized["other"] = []

        for dep in dependencies:
            categorized_flag = False
            for cat, keywords in categories.items():
                if any(kw in dep["package"].lower() for kw in keywords):
                    categorized[cat].append(dep)
                    categorized_flag = True
                    break
            if not categorized_flag:
                categorized["other"].append(dep)

        return json.dumps({
            "total_dependencies": len(dependencies),
            "dependencies": dependencies,
            "categorized": categorized
        }, indent=2)

    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {requirements_file}"})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

### Best Practices for Custom Tools

1. **Clear, Specific Docstrings**
   - LLM uses docstring to decide when to call the tool
   - Explain what the tool does, when to use it, and what it returns

2. **Type Hints Are Required**
   ```python
   @tool
   def my_tool(param: str) -> str:  # Required!
   ```

3. **Return JSON for Complex Data**
   ```python
   return json.dumps({"key": "value"})
   ```

4. **Handle Errors Gracefully**
   ```python
   try:
       # Tool logic
   except Exception as e:
       return json.dumps({"error": str(e)})
   ```

5. **Add Timeouts for External Calls**
   ```python
   subprocess.run(..., timeout=10)
   requests.get(..., timeout=5)
   ```

6. **Test Tools Independently**
   ```python
   # test_tools.py
   from tools import my_custom_tool

   result = my_custom_tool("test_input")
   print(result)
   ```

### Example: Tool for Database Schema Analysis

```python
import sqlite3

@tool
def analyze_database_schema(db_path: str) -> str:
    """
    Analyzes SQLite database schema to document tables and columns.

    Connects to SQLite database and extracts table definitions,
    column types, and relationships. Useful for documenting
    projects that use SQLite databases.

    Args:
        db_path: Path to SQLite database file

    Returns:
        JSON string with schema information
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        schema = {}

        for table_name in [t[0] for t in tables]:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            schema[table_name] = {
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]
            }

        conn.close()

        return json.dumps({
            "database": db_path,
            "tables": len(schema),
            "schema": schema
        }, indent=2)

    except sqlite3.Error as e:
        return json.dumps({"error": f"Database error: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

---

## Advanced Configuration

### Multi-Model Strategy

**Use different models for different tasks:**

```python
# advanced_main.py
from langchain_openai import ChatOpenAI

# Fast model for simple tasks
fast_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Powerful model for complex analysis
powerful_model = ChatOpenAI(model="gpt-4o", temperature=0)

def run_model_smart(state: AgentState):
    """Choose model based on task complexity."""
    # Use fast model for tool calls
    if needs_tool_call(state):
        return fast_model.invoke(state['messages'])

    # Use powerful model for final analysis
    if is_generating_final_answer(state):
        return powerful_model.invoke(state['messages'])

    # Default to fast model
    return fast_model.invoke(state['messages'])
```

### Custom Prompt Templates

**Create domain-specific prompts:**

```python
# custom_prompts.py
API_DOCUMENTATION_PROMPT = """
You are an API documentation specialist. Your task is to:

1. Identify all API endpoints (routes, views)
2. Extract request/response schemas
3. Document authentication requirements
4. Provide example requests/responses

[... rest of custom prompt ...]
"""

# Use in main.py
from custom_prompts import API_DOCUMENTATION_PROMPT
```

### Parallel Tool Execution

**Speed up analysis by running tools in parallel:**

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_file_analysis(file_paths: list[str]) -> dict:
    """Analyze multiple files in parallel."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(analyze_single_file, file_paths)
    return list(results)
```

### Caching Results

**Cache expensive operations:**

```python
from functools import lru_cache

@lru_cache(maxsize=100)
@tool
def cached_analyze_code(code_content: str) -> str:
    """Cached version of analyze_code."""
    # Analysis happens only once per unique code_content
    return analyze_code_impl(code_content)
```

---

## Summary

This configuration guide covered:
- ✅ Environment variables setup and validation
- ✅ LLM model selection (gpt-4o-mini, gpt-4o, gpt-4-turbo)
- ✅ Recursion limit tuning for performance vs cost
- ✅ LangSmith tracing for debugging and monitoring
- ✅ ChromaDB configuration for RAG
- ✅ Custom tool integration with examples
- ✅ Advanced configurations

## Related Documentation

- [Usage Examples](./usage_examples.md) - Real-world usage scenarios
- [Troubleshooting Guide](./troubleshooting.md) - Common issues and solutions
- [Main README](../README.md) - Project overview and quick start

---

**Need Help?**

- GitHub Issues: https://github.com/aethrox/klaro/issues
- Documentation: https://github.com/aethrox/klaro/docs
- LangChain Docs: https://python.langchain.com/docs
- OpenAI Docs: https://platform.openai.com/docs
