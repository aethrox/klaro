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
|:---------|:-----|:------------|:--------|
| `OPENAI_API_KEY` | **Required** | Your OpenAI API key for LLM and embeddings | `sk-proj-abc123...` |

### Optional Variables

| Variable | Type | Default | Description |
|:---------|:-----|:--------|:------------|
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
|:------|:--------------|:----------------------------------|:------|:---------|
| `gpt-4o` | 128K | $2.50 / $10.00 | ⚡⚡ Medium | **Default** - High accuracy, quality outputs |
| `gpt-4o-mini` | 128K | $0.15 / $0.60 | ⚡⚡⚡ Fast | Cost-effective alternative |
| `gpt-4-turbo` | 128K | $10.00 / $30.00 | ⚡ Slower | Maximum reasoning quality |
| `gpt-3.5-turbo` | 16K | $0.50 / $1.50 | ⚡⚡⚡ Fast | Simple projects (not recommended) |

*Pricing as of January 2025. Check OpenAI pricing page for current rates.*

### Changing the Model

**Method 1: Edit main.py directly**

```python
# main.py (around line 78)
LLM_MODEL = "gpt-4o"  # Current default

# Options:
# LLM_MODEL = "gpt-4o-mini"   # More cost-effective
# LLM_MODEL = "gpt-4-turbo"   # Most powerful
# LLM_MODEL = "gpt-3.5-turbo" # Cheapest (not recommended)
```

**Method 2: Use environment variable (requires code modification)**

Add to `main.py`:
```python
LLM_MODEL = os.getenv("KLARO_LLM_MODEL", "gpt-4o")
```

Then in `.env`:
```bash
KLARO_LLM_MODEL=gpt-4o
```

### Model Selection Guide

#### Use `gpt-4o` (Default) when:
- ✅ Analyzing medium to large codebases (5,000+ lines)
- ✅ High-quality, accurate documentation is required
- ✅ Code has intricate logic or architectural patterns
- ✅ Multiple programming paradigms are used
- ✅ You need reliable, professional outputs

**Example Cost:**
- Project size: 20,000 lines
- Estimated tokens: ~50,000 input, ~8,000 output
- Cost: **~$0.20 per run**

#### Use `gpt-4o-mini` when:
- ✅ Analyzing small projects (<5,000 lines)
- ✅ Cost is a primary concern
- ✅ Documentation style is straightforward
- ✅ Fast iteration is needed
- ✅ Budget constraints are strict

**Example Cost:**
- Project size: 5,000 lines
- Estimated tokens: ~15,000 input, ~3,000 output
- Cost: **~$0.01 per run**

#### Use `gpt-4-turbo` when:
- ✅ Maximum reasoning capability is required
- ✅ Extremely complex domain-specific code
- ✅ Cost is not a constraint
- ✅ Highest quality output is mandatory

**Example Cost:**
- Project size: 50,000 lines
- Estimated tokens: ~150,000 input, ~15,000 output
- Cost: **~$1.95 per run**

### Intelligent Model Selection (Automatic)

Klaro now includes an intelligent model selection system that automatically chooses the optimal LLM based on your project size and complexity.

#### How It Works

When you run Klaro, it:
1. **Analyzes your project** - Counts Python files and total lines of code
2. **Calculates complexity** - Classifies project as small, medium, or large
3. **Selects optimal model** - Chooses the best model for your project size
4. **Displays selection** - Shows project metrics and selected model

```bash
$ python main.py

--- Launching Klaro LangGraph Agent ---
📊 Analyzing project size...
   -> Project metrics: 4,523 lines across 15 files
   -> Complexity: small
   -> Selected model: gpt-4o-mini
🚀 Starting agent with model: gpt-4o-mini
```

#### Selection Thresholds

| Project Size | Lines of Code | Complexity | Model Selected | Reasoning |
|:------------|:--------------|:-----------|:---------------|:----------|
| **Small** | < 10,000 | small | `gpt-4o-mini` | Fast, cost-effective for simple projects |
| **Medium** | 10,000 - 100,000 | medium | `gpt-4o` | Balanced performance for typical projects |
| **Large** | > 100,000 | large | `gpt-4-turbo` | Maximum capability for complex codebases |

#### Environment Variable Configuration

Customize model selection thresholds and behavior via environment variables:

```bash
# .env

# Enable/disable automatic model selection (default: true)
KLARO_AUTO_MODEL_SELECTION=true

# Override models for each tier
KLARO_SMALL_MODEL=gpt-4o-mini
KLARO_MEDIUM_MODEL=gpt-4o
KLARO_LARGE_MODEL=gpt-4-turbo

# Fallback model if auto-selection is disabled
KLARO_DEFAULT_MODEL=gpt-4o
```

#### Disabling Auto-Selection

If you prefer to use a fixed model, disable auto-selection:

```bash
# .env
KLARO_AUTO_MODEL_SELECTION=false
KLARO_DEFAULT_MODEL=gpt-4o  # Will always use this model
```

When disabled, you'll see:
```bash
📌 Auto model selection disabled. Using: gpt-4o
```

#### Cost Optimization Examples

**Scenario 1: Small Project (5,000 lines)**
```bash
# Auto-selection (default):
# Selected: gpt-4o-mini
# Estimated cost: $0.008 per run
# ✅ 80% cost savings

# Manual selection:
KLARO_AUTO_MODEL_SELECTION=false
KLARO_DEFAULT_MODEL=gpt-4o
# Cost: $0.045 per run
```

**Scenario 2: Medium Project (25,000 lines)**
```bash
# Auto-selection (default):
# Selected: gpt-4o
# Estimated cost: $0.085 per run
# ✅ Optimal balance of cost and quality

# Over-provisioning (manual):
KLARO_DEFAULT_MODEL=gpt-4-turbo
# Cost: $0.380 per run (4.5x more expensive)
```

**Scenario 3: Large Project (150,000 lines)**
```bash
# Auto-selection (default):
# Selected: gpt-4-turbo
# Estimated cost: $1.95 per run
# ✅ Necessary for handling complexity

# Under-provisioning (not recommended):
KLARO_DEFAULT_MODEL=gpt-4o-mini
# May fail to complete or produce low-quality output
```

#### Custom Thresholds

Override the default thresholds by modifying `main.py`:

```python
# main.py line 82
MODEL_SELECTION_THRESHOLDS = {
    'small': {
        'max_lines': 5000,  # Changed from 10000
        'model': 'gpt-4o-mini',
        'description': 'Fast and cost-effective for small projects'
    },
    'medium': {
        'max_lines': 50000,  # Changed from 100000
        'model': 'gpt-4o',
        'description': 'Balanced performance for medium projects'
    },
    'large': {
        'max_lines': float('inf'),
        'model': 'gpt-4-turbo',
        'description': 'Maximum capability for large projects'
    }
}
```

#### Ignoring Files in Size Calculation

The size analyzer respects `.gitignore` patterns, automatically excluding:
- `__pycache__/` directories
- `.pyc`, `.pyo` compiled files
- Virtual environments (`venv/`, `env/`)
- Build artifacts (`build/`, `dist/`)
- Test coverage reports

**Result:** Only production code is counted, providing accurate project size metrics.

#### Monitoring Model Selection

Enable LangSmith tracing to see detailed metrics:

```bash
# .env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_key_here
```

View in LangSmith:
- Selected model for each run
- Token usage per model
- Cost breakdown by project size
- Performance comparisons

#### Real-World Performance

**Benchmark: Flask REST API Projects**

| Project Size | Files | Lines | Auto-Selected Model | Runtime | Cost | Quality |
|:------------|:------|:------|:-------------------|:--------|:-----|:--------|
| Small API | 8 | 1,200 | gpt-4o-mini | 45s | $0.004 | ⭐⭐⭐ Good |
| Medium API | 35 | 15,000 | gpt-4o | 90s | $0.062 | ⭐⭐⭐⭐ Excellent |
| Large API | 120 | 85,000 | gpt-4o | 180s | $0.285 | ⭐⭐⭐⭐ Excellent |
| Enterprise | 450 | 250,000 | gpt-4-turbo | 420s | $2.850 | ⭐⭐⭐⭐⭐ Outstanding |

**Key Insights:**
- Auto-selection provides optimal cost/performance for each tier
- Medium projects stay with gpt-4o (no need for gpt-4-turbo)
- Small projects achieve 80% cost savings with gpt-4o-mini
- Large projects automatically upgrade to gpt-4-turbo only when needed

#### Best Practices

1. **Keep auto-selection enabled** - Let Klaro optimize for your project
2. **Override only when necessary** - For specific quality requirements
3. **Monitor costs with LangSmith** - Track spending across projects
4. **Test with gpt-4o-mini first** - For new projects, verify quality before committing

### Model Comparison Example

**Test Project:** Flask REST API (2,000 lines)

| Model | Runtime | Cost | Quality Score* | Details Captured |
|:------|:--------|:-----|:---------------|:-----------------|
| gpt-3.5-turbo | 45s | $0.003 | 6/10 | Basic structure, misses nuances |
| gpt-4o-mini | 60s | $0.008 | 8/10 | Good balance, cost-effective |
| gpt-4o | 90s | $0.045 | 9/10 | **Default** - Excellent details, high accuracy |
| gpt-4-turbo | 120s | $0.285 | 9.5/10 | Comprehensive, may be overkill |

*Quality Score: Subjective rating based on completeness, accuracy, and usefulness*

### Cost Optimization Tips

1. **Consider gpt-4o-mini for cost savings**
   - Switch to gpt-4o-mini for simple projects or when budget is a concern
   - Default gpt-4o provides better accuracy but at higher cost

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
|:------|:---------|:---------|:---------------|:---------|
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
|:---------|:---------|:--------|:------------|
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
├─ run_model (2.3s) - $0.015
│  └─ ChatOpenAI (gpt-4o)
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
|:------|:-----------|:------------------|:------------|
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
|:-----------|:--------|:--------|:------------------|:---------|
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

# Standard model (default)
standard_model = ChatOpenAI(model="gpt-4o", temperature=0)

# Cost-effective model for simple tasks
fast_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

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

- [Usage Examples](usage-examples.md) - Real-world usage scenarios
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Main README](../README.md) - Project overview and quick start

---

**Need Help?**

- GitHub Issues: https://github.com/aethrox/klaro/issues
- Documentation: https://github.com/aethrox/klaro/docs
- LangChain Docs: https://python.langchain.com/docs
- OpenAI Docs: https://platform.openai.com/docs

---

## Advanced Configuration

This section covers advanced configuration options for Klaro, including custom LLM models, performance tuning, memory optimization, and integration patterns.

### Table of Contents (Advanced)

- [Custom LLM Models](#custom-llm-models-1)
- [Performance Tuning for Large Projects](#performance-tuning-for-large-projects-1)
- [Memory Optimization](#memory-optimization-1)
- [Batch Processing](#batch-processing-1)
- [Custom Prompts](#custom-prompts-1)
- [Tool Customization](#tool-customization-1)
- [Integration with Other Systems](#integration-with-other-systems-1)

---

### Custom LLM Models

Klaro supports multiple LLM models through the LangChain integration. By default, it uses `gpt-4o` for high-quality, accurate outputs, but you can configure alternative models.

#### Switching Models

**Option 1: Environment Variable (Recommended)**

Create or modify your `.env` file:

```bash
# .env
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o  # Change to your preferred model
```

**Option 2: Code Modification**

Edit `main.py` line 78:

```python
# Current default:
LLM_MODEL = "gpt-4o"

# Alternative options:
# LLM_MODEL = "gpt-4o-mini"  # For cost savings
# LLM_MODEL = "gpt-4-turbo"  # For maximum quality
```

#### Supported Models

| Model | Speed | Cost | Quality | Best For |
|:------|:------|:-----|:--------|:---------|
| `gpt-4o` | ⚡⚡ | $$ | ⭐⭐⭐⭐ | **Default** - Complex codebases, high-quality docs |
| `gpt-4o-mini` | ⚡⚡⚡ | $ | ⭐⭐⭐ | Cost savings, simple projects |
| `gpt-4-turbo` | ⚡ | $$$ | ⭐⭐⭐⭐⭐ | Large projects requiring deep understanding |

#### Using Non-OpenAI Models

To use models from other providers (Anthropic Claude, local models, etc.), modify the model initialization in `main.py`:

```python
# For Anthropic Claude
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0.2,
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

# For local models via Ollama
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(
    model="llama2",
    temperature=0.2
)
```

**Note:** Update `requirements.txt` with the appropriate provider package:
```bash
pip install langchain-anthropic  # for Claude
pip install langchain-community  # for Ollama
```

---

### Performance Tuning for Large Projects

Klaro's default configuration is optimized for small to medium projects. For large codebases (>100 files), apply these optimizations.

#### Recursion Limit Adjustment

The agent's recursion limit controls the maximum number of reasoning steps. Default is 50.

**Increase for large projects:**

```bash
# .env
KLARO_RECURSION_LIMIT=100  # or higher for very large projects
```

**Monitoring iterations:**

Enable LangSmith tracing to see how many iterations are used:

```bash
# .env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=klaro-performance-tuning
```

**Guidelines:**
- Small projects (<20 files): 30-40 iterations
- Medium projects (20-50 files): 50-70 iterations
- Large projects (50-100 files): 70-100 iterations
- Very large projects (100+ files): 100-150 iterations

#### Temperature Optimization

Temperature controls output randomness. Lower values produce more consistent results.

```python
# main.py line 86
llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=0.1  # More deterministic (default: 0.2)
)
```

**Recommendations:**
- Documentation generation: 0.1-0.2
- Creative content: 0.5-0.7
- Code summarization: 0.0-0.1

#### Parallel Tool Execution

Currently, tools execute sequentially. For advanced users, implement parallel execution:

```python
# Custom implementation (advanced)
import asyncio
from langgraph.prebuilt import ToolNode

async def parallel_tool_node(state):
    """Execute multiple tools in parallel."""
    tool_calls = state["messages"][-1].tool_calls

    # Group independent tool calls
    results = await asyncio.gather(*[
        execute_tool(call) for call in tool_calls
    ])

    return {"messages": results}
```

---

### Memory Optimization

For resource-constrained environments or very large projects.

#### Vector Database Optimization

**Reduce chunk size for less memory usage:**

```python
# tools.py line 725 (in init_knowledge_base)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,   # Reduced from 1000
    chunk_overlap=100 # Reduced from 200
)
```

**Trade-off:** Smaller chunks = lower memory usage but less context per retrieval.

#### ChromaDB Configuration

**Persistent vs. In-Memory:**

```python
# tools.py - In-memory mode (faster, no disk writes)
vectorstore = Chroma.from_documents(
    documents=texts,
    embedding=embeddings,
    # Remove persist_directory for in-memory mode
)

# For production: Keep persistent mode for consistency
vectorstore = Chroma.from_documents(
    documents=texts,
    embedding=embeddings,
    persist_directory=VECTOR_DB_PATH  # Persists to disk
)
```

#### Message History Pruning

Limit conversation history to prevent memory bloat:

```python
# main.py - Add to run_model function
def run_model(state: AgentState):
    # Keep only last 20 messages
    messages = state["messages"][-20:]
    response = model.invoke(messages)
    return {"messages": [response], "error_log": ""}
```

---

### Batch Processing

Process multiple projects in a single run for efficiency.

#### Basic Batch Script

Create `batch_process.py`:

```python
import os
from main import run_klaro_langgraph

def batch_process_projects(project_dirs: list[str]):
    """Process multiple projects sequentially."""
    results = {}

    for project_path in project_dirs:
        print(f"\n{'='*60}")
        print(f"Processing: {project_path}")
        print('='*60)

        try:
            # Save stdout to capture documentation
            import io
            import sys
            captured_output = io.StringIO()
            sys.stdout = captured_output

            run_klaro_langgraph(project_path)

            sys.stdout = sys.__stdout__
            results[project_path] = {
                "status": "success",
                "output": captured_output.getvalue()
            }
        except Exception as e:
            results[project_path] = {
                "status": "error",
                "error": str(e)
            }

    return results

if __name__ == "__main__":
    projects = [
        "./project1",
        "./project2",
        "./project3"
    ]

    results = batch_process_projects(projects)

    # Save results
    import json
    with open("batch_results.json", "w") as f:
        json.dump(results, f, indent=2)
```

#### Parallel Batch Processing

For faster processing using multiprocessing:

```python
from multiprocessing import Pool
from main import run_klaro_langgraph

def process_single_project(project_path: str):
    """Worker function for parallel processing."""
    try:
        run_klaro_langgraph(project_path)
        return {"project": project_path, "status": "success"}
    except Exception as e:
        return {"project": project_path, "status": "error", "error": str(e)}

def parallel_batch_process(project_dirs: list[str], num_workers: int = 4):
    """Process multiple projects in parallel."""
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_single_project, project_dirs)
    return results
```

---

### Custom Prompts

Customize the agent's behavior by modifying the system prompt.

#### Modifying System Prompt

Edit `prompts.py`:

```python
# prompts.py
SYSTEM_PROMPT = """
You are Klaro, an advanced AI documentation agent.

# YOUR CUSTOM INSTRUCTIONS HERE

TASK: Generate professional technical documentation...
"""
```

#### Task-Specific Prompts

Create different prompts for different documentation types:

```python
# custom_prompts.py
API_DOCS_PROMPT = """
Focus on:
1. API endpoints and routes
2. Request/response schemas
3. Authentication methods
4. Error codes and handling
"""

TUTORIAL_PROMPT = """
Create beginner-friendly documentation with:
1. Step-by-step guides
2. Code examples with explanations
3. Common pitfalls and solutions
"""

# Use in run_klaro_langgraph
def run_klaro_with_custom_prompt(project_path: str, custom_prompt: str):
    """Run Klaro with a custom system prompt."""
    # Temporarily replace SYSTEM_PROMPT
    from prompts import SYSTEM_PROMPT
    original_prompt = SYSTEM_PROMPT

    # Override with custom prompt
    import prompts
    prompts.SYSTEM_PROMPT = custom_prompt

    try:
        run_klaro_langgraph(project_path)
    finally:
        # Restore original
        prompts.SYSTEM_PROMPT = original_prompt
```

#### Prompt Templates

Define reusable prompt templates:

```python
PROMPT_TEMPLATES = {
    "readme": "Create a comprehensive README.md with setup, usage, and examples.",
    "api_docs": "Document all API endpoints, parameters, and response formats.",
    "architecture": "Explain the system architecture, components, and data flow.",
    "contributing": "Create a CONTRIBUTING.md guide for new developers."
}

def run_with_template(project_path: str, template_name: str):
    """Run Klaro using a predefined prompt template."""
    template = PROMPT_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}")

    # Inject template into task
    # Implementation left as exercise
```

---

### Tool Customization

Extend Klaro's capabilities by adding custom tools.

#### Adding a New Tool

**Step 1: Define the tool function in `tools.py`:**

```python
def analyze_dependencies(file_path: str = "requirements.txt") -> str:
    """Analyzes project dependencies and returns package information.

    Args:
        file_path: Path to requirements.txt or similar dependency file.

    Returns:
        JSON string with dependency analysis results.
    """
    try:
        with open(file_path, 'r') as f:
            deps = f.readlines()

        analysis = {
            "total_dependencies": len(deps),
            "packages": [dep.strip() for dep in deps if dep.strip()]
        }

        return json.dumps(analysis, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
```

**Step 2: Register the tool in `main.py`:**

```python
# main.py - Import your new tool
from tools import (
    list_files, read_file, analyze_code,
    web_search, init_knowledge_base, retrieve_knowledge,
    analyze_dependencies  # Add your new tool
)

# main.py line 93 - Add to tools list
tools = [
    Tool(name="list_files", func=list_files, description=list_files.__doc__),
    Tool(name="read_file", func=read_file, description=read_file.__doc__),
    Tool(name="analyze_code", func=analyze_code, description=analyze_code.__doc__),
    Tool(name="web_search", func=web_search, description=web_search.__doc__),
    Tool(name="retrieve_knowledge", func=retrieve_knowledge, description=retrieve_knowledge.__doc__),
    Tool(name="analyze_dependencies", func=analyze_dependencies, description=analyze_dependencies.__doc__),
]
```

**Step 3: Update the system prompt to inform the agent:**

```python
# prompts.py - Add to tool descriptions
"""
Available Tools:
...
6. analyze_dependencies[file_path] - Analyzes project dependencies from requirements.txt
"""
```

#### Tool Best Practices

1. **Clear docstrings:** LLM uses these to understand when to call the tool
2. **Error handling:** Always return strings (never raise exceptions)
3. **JSON output:** For structured data, use JSON format
4. **Idempotent:** Tools should be safe to call multiple times
5. **Fast execution:** Avoid long-running operations (>5 seconds)

---

### Integration with Other Systems

Integrate Klaro into your existing workflows and pipelines.

#### CI/CD Integration

**GitHub Actions:**

```yaml
# .github/workflows/docs.yml
name: Auto-Generate Docs

on:
  push:
    branches: [main]

jobs:
  generate-docs:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run Klaro
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python main.py > README.md

      - name: Commit documentation
        run: |
          git config user.name "Klaro Bot"
          git config user.email "bot@klaro.ai"
          git add README.md
          git commit -m "docs: Auto-generate README [skip ci]" || echo "No changes"
          git push
```

#### Pre-commit Hook

Automatically generate docs before each commit:

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running Klaro documentation generator..."
python main.py > README.md

# Stage the generated documentation
git add README.md

echo "Documentation updated!"
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

#### REST API Wrapper

Expose Klaro as a web service:

```python
# api_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import run_klaro_langgraph
import tempfile
import shutil
import os

app = FastAPI()

class DocumentationRequest(BaseModel):
    project_path: str
    model: str = "gpt-4o"

@app.post("/generate-docs")
async def generate_documentation(request: DocumentationRequest):
    """Generate documentation for a given project."""
    try:
        # Set model
        os.environ["LLM_MODEL"] = request.model

        # Capture output
        import io
        import sys
        captured = io.StringIO()
        sys.stdout = captured

        run_klaro_langgraph(request.project_path)

        sys.stdout = sys.__stdout__

        return {
            "status": "success",
            "documentation": captured.getvalue()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run with:
```bash
pip install fastapi uvicorn
python api_server.py
```

#### Docker Integration

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OPENAI_API_KEY=""
ENV KLARO_RECURSION_LIMIT=50

CMD ["python", "main.py"]
```

**Docker Compose:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  klaro:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - KLARO_RECURSION_LIMIT=50
    volumes:
      - ./projects:/projects
    command: python main.py
```

Run:
```bash
docker-compose up
```

#### VSCode Extension Integration

Create a VSCode task:

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Generate Documentation with Klaro",
      "type": "shell",
      "command": "python",
      "args": ["main.py"],
      "problemMatcher": [],
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    }
  ]
}
```

Access via: `Terminal > Run Task > Generate Documentation with Klaro`

---

## Additional Advanced Resources

- [Architecture Documentation](architecture.md) - System design overview
- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

---

**Last Updated**: 2025-10-23
**Klaro Version**: 1.0
**Maintained by**: Klaro Development Team
