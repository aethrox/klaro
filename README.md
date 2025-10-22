<div align="center">
  <img src="assets/logo_transparent.png" alt="Klaro Logo" width="150"/>
  <h1>Klaro</h1>
  <strong>From Code to Clarity. Instantly.</strong>
</div>

<br />

<p align="center">
  <a href="https://github.com/aethrox/klaro/actions/workflows/main.yml"><img alt="Build Status" src="https://img.shields.io/github/actions/workflow/status/aethrox/klaro/main.yml?style=for-the-badge"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/github/license/aethrox/klaro?style=for-the-badge&color=blue"></a>
  <a href="#"><img alt="Python Version" src="https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python"></a>
</p>

---

## Overview

**Klaro** is an advanced autonomous AI agent that transforms complex codebases into clear, professional documentation. Built on cutting-edge agentic architecture, Klaro autonomously navigates your codebase, performs deep structural analysis, and generates comprehensive technical documentation (README files, API references) with minimal human intervention.

### The Problem

Documentation is a critical yet time-consuming aspect of software development that's often neglected. This leads to:
- Accumulated technical debt
- Slow onboarding for new team members
- Reduced project maintainability
- Decreased developer productivity

### The Solution

Klaro automates the entire documentation process using a sophisticated multi-stage architecture:
- **Stateful Agent System**: Built on LangGraph for robust, error-tolerant operation
- **Structural Code Analysis**: Uses Python's AST (Abstract Syntax Tree) for semantic understanding
- **Quality Assurance**: RAG (Retrieval-Augmented Generation) enforces style guide consistency

---

## Key Features

### 1. Autonomous Code Analysis
**AST-Powered Intelligence**: Unlike text-based analysis, Klaro uses Python's Abstract Syntax Tree to extract structured data from code:
- Identifies classes, functions, and their relationships
- Extracts parameters, return types, and docstrings
- Builds a semantic understanding of code architecture

### 2. Style Guide Enforcement (RAG)
**Retrieval-Augmented Generation**: Ensures documentation quality through a vector database (ChromaDB) that:
- Stores project-specific style guides
- Enforces consistent tone and formatting
- Retrieves relevant examples during generation
- **Mandatory step**: Agent must query style guide before producing final output

### 3. Stateful Agent Architecture
**LangGraph State Machine**: Advanced orchestration replacing traditional ReAct loops:
- **Robustness**: Handles tool failures gracefully with automatic retry logic
- **Stateful Memory**: Maintains context across complex multi-step workflows
- **Error Recovery**: Routes back to planning phase when tools fail
- **Cycle Support**: Iteratively gathers information until task completion

### 4. Multi-Tool Orchestration
Custom tools providing specialized capabilities:
- `list_files`: Navigate project structure with .gitignore awareness
- `read_file`: Read specific files on-demand
- `analyze_code`: AST-based structural analysis producing JSON output
- `web_search`: Gather external library/framework information
- `retrieve_knowledge`: Query RAG system for style guidelines

---

## Architectural Deep Dive

### Why LangGraph? The Evolution from ReAct

Klaro's architecture evolved through 4 distinct stages, culminating in a **LangGraph State Machine** (Stage 4):

**The Limitations of ReAct (Stages 1-3)**:
- **Stateless**: No memory between action steps
- **Fragile**: Tool failures caused immediate termination
- **Linear**: Difficult to implement complex branching logic

**LangGraph Advantages (Stage 4 - Current)**:
```
┌─────────────────┐
│   run_model     │  ← Agent's "Thinking" node (LLM invocation)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ decide_next_step │  ← Conditional router (Error? Tool call? Done?)
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌─────────┐  ┌────────────┐
│call_tool│  │    END     │
└────┬────┘  └────────────┘
     │
     ↓ (Returns observation)
┌─────────────┐
│ run_model   │ ← Processes result, decides next action
└─────────────┘
```

**Key Innovation**: The `decide_next_step` conditional edge enables:
1. **Error Handling**: Tool failures route back to `run_model` for replanning
2. **Iterative Refinement**: Loops until sufficient information gathered
3. **Graceful Termination**: Only exits when "Final Answer" detected

### AST: Structural Intelligence

Traditional documentation tools rely on text parsing, leading to:
- Hallucinations about code structure
- Missed dependencies
- Inaccurate parameter descriptions

**Klaro's AST Approach**:
```python
# Input: Python code
def format_user_data(user_id: int, data: dict) -> dict:
    """Formats user data for API."""
    return {"id": user_id, "data": data}

# Output: Structured JSON
{
  "type": "function",
  "name": "format_user_data",
  "parameters": ["user_id (int)", "data (dict)"],
  "returns": "dict",
  "docstring": "Formats user data for API.",
  "lineno": 1
}
```

This structural data is then semantically processed by the LLM, ensuring accurate documentation.

### RAG: Enforcing Quality Standards

**Challenge**: LLMs can produce inconsistent documentation styles.

**Solution**: Vector database (ChromaDB) with embedded style guides:
1. Style guide chunked and embedded using OpenAI's `text-embedding-3-small`
2. Agent **must** use `retrieve_knowledge` tool before generating final output
3. Retrieved guidelines inform tone, structure, and formatting

**Result**: Professional, consistent documentation every time.

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.11+ | Core implementation |
| **Agent Framework** | LangChain + LangGraph | Orchestration and tool management |
| **Agent Architecture** | LangGraph State Machine | Stateful, error-tolerant workflows |
| **LLM** | OpenAI GPT-4o / GPT-4o mini | Reasoning and text generation |
| **Vector Database** | ChromaDB | RAG style guide storage |
| **Embeddings** | OpenAI text-embedding-3-small | Semantic search in vector DB |
| **Code Analysis** | Python `ast` module | Structural code parsing |

---

## Setup & Installation

### Prerequisites
- **Python**: 3.11 or higher
- **OpenAI API Key**: Required for LLM and embeddings

### Installation Steps

1. **Clone the Repository**
```bash
git clone https://github.com/aethrox/klaro.git
cd klaro
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

**Primary Dependencies**:
- `langchain==1.0.2` - Core LLM framework
- `langgraph==1.0.1` - State machine orchestration
- `langchain-openai==1.0.1` - OpenAI integration
- `chromadb==1.2.1` - Vector database for RAG
- `python-dotenv==1.1.1` - Environment variable management

3. **Configure Environment Variables**

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-api-key-here
KLARO_RECURSION_LIMIT=50  # Optional: Maximum agent steps
```

4. **Verify Installation**
```bash
python main.py
```

If successful, you should see:
```
--- Launching Klaro LangGraph Agent (Stage 4 - gpt-4o-mini) ---
📢 Initializing RAG Knowledge Base...
```

---

## Usage & Expected Behavior

### Running Klaro

**Basic Usage**:
```bash
python main.py
```

By default, Klaro analyzes the current directory (`.`) and generates a README.md document.

**Analyze Specific Project**:
Modify `main.py` line 172:
```python
run_klaro_langgraph(project_path="./path/to/your/project")
```

### Agent Workflow

Klaro follows a mandatory multi-step process:

1. **Exploration Phase** (`list_files`)
   - Navigates project structure
   - Identifies key files (main entry points, configuration files)

2. **Analysis Phase** (`read_file` + `analyze_code`)
   - Reads critical files identified in exploration
   - Performs AST analysis to extract structural data
   - Optionally uses `web_search` for external library information

3. **Style Guide Retrieval** (`retrieve_knowledge`) ⚠️ **MANDATORY**
   - Queries ChromaDB for README formatting guidelines
   - Retrieves relevant style guide chunks
   - **Agent cannot skip this step** - enforced by system prompt

4. **Generation Phase** (Final Answer)
   - Synthesizes all gathered information
   - Produces final README.md adhering to retrieved style guide

### Expected Output

```markdown
✅ TASK SUCCESS: LangGraph Agent Finished.
====================================

# Project Name

## Setup
Installation instructions...

## Usage
How to run the project...

## Components
- **module.py**: Description of main module
  - `function_name(param1, param2)`: Function description
```

### Configuration Options

Edit `main.py` for customization:

```python
# Model Selection (Line 21)
LLM_MODEL = "gpt-4o-mini"  # Options: "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"

# Recursion Limit (Line 22)
RECURSION_LIMIT = 50  # Maximum agent steps before timeout
```

---

## Future Roadmap & Contributions

### Planned Features

#### 1. Smart Model Steering (High Priority)
**Vision**: Optimize API costs through intelligent model routing

**Current State**: Single model (GPT-4o mini) for all tasks

**Goal**: Dynamic model selection based on task complexity:
- **Simple Tasks** (file listing, basic decisions): GPT-4o mini (~$0.15/1M input tokens)
- **Complex Tasks** (code analysis, final generation): GPT-4o or Claude Sonnet (~$3-5/1M tokens)

**Estimated Cost Savings**: 60-70% reduction per documentation run

**Implementation**: LangGraph's conditional routing to switch models mid-workflow

#### 2. Multi-Language Support
Extend AST analysis beyond Python to support:
- JavaScript/TypeScript (using `esprima` or `@babel/parser`)
- Java (using `javalang`)
- Go (using `go/ast`)

#### 3. API Endpoint Documentation
Auto-generate API reference documentation for:
- REST APIs (FastAPI, Flask, Django)
- GraphQL schemas
- RPC definitions

#### 4. GitHub Integration
- **GitHub Action**: Auto-update documentation on PR merge
- **CLI Tool**: `klaro --repo https://github.com/user/repo`
- **VS Code Extension**: Generate docs directly in IDE

### Contributing

We welcome contributions under the **MIT License**! Areas for contribution:

- **Tool Development**: Add new analysis tools (e.g., database schema extraction)
- **Language Support**: Implement AST parsers for other languages
- **Prompt Engineering**: Improve agent reasoning and output quality
- **Testing**: Expand test coverage for edge cases
- **Documentation**: Improve setup guides, add tutorials

**Getting Started**:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and commit (`git commit -m 'Add amazing feature'`)
4. Push to your branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines.

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

---

## Acknowledgments

Klaro's architecture is inspired by research in:
- **LangGraph**: Stateful agent orchestration framework
- **ReAct**: Reasoning and Acting paradigm for LLM agents
- **RAG**: Retrieval-Augmented Generation for quality control

Built with passion to solve the documentation problem. ❤️

---

<div align="center">
  <strong>Star ⭐ this repository if Klaro helps your project!</strong>
</div>
