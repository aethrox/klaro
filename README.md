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

## Overview
`Klaro` is an **autonomous AI agent** designed to solve the problem of neglected technical documentation. It works by autonomously navigating your codebase, performing deep logic analysis, and generating clear, professional, and up-to-date documentation (such as README files and API references) with minimal human intervention.

### 💡 The Problem
Writing and maintaining documentation is a time-consuming, tedious, and often neglected task. This common issue leads to accumulated technical debt, slow project onboarding for new team members, and overall project inefficiency.

### 🚀 The Solution
Klaro automates the entire documentation process. It employs an advanced **Pure Python ReAct loop** coupled with custom analysis tools and a **Retrieval-Augmented Generation (RAG) system** to ensure the generated documentation is not only accurate but also adheres to specified project style guides.

## ✨ Core Features (Completed & Planned)
* **Autonomous Code Analysis:** Implemented using **Python's AST (Abstract Syntax Tree)** to read the entire file tree, identify key logic (classes, functions), and extract structured data for analysis.
* **Style Guide Integration (RAG):** **(Completed in Stage 3)** Learns from your existing project style guides or reference documents, retrieving relevant context from a vector database to match the tone, structure, and style of the final documentation.
* **Multi-Tool Orchestration:** Uses a **Pure Python ReAct** (Reasoning and Acting) loop to dynamically plan steps, execute custom tools (`list_files`, `analyze_code`, `web_search`), and self-correct errors during the documentation process.
* **Multi-Format Output (Planned):** Generates professional Markdown (`README.md`), API references, and more.
* **Smart Model Steering (Planned):** Will utilize LangGraph for dynamic model routing (e.g., using GPT-4o mini for file listing and GPT-4o for complex analysis) to optimize API costs.

## 🛠 Technology Stack
* **Core:** Python 3.11+ (Current stable version)
* **AI Framework:** LangChain (Tools & Prompts) & **LangGraph (Agent Orchestration)**
* **Agent Core:** LangGraph State Machine (Stage 4 Completed)
* **Vector DB/RAG:** ChromaDB, OpenAI Embeddings
* **Code Analysis:** `ast` (Abstract Syntax Tree)

## 🚧 Status: Under Active Development
This project is currently in active development, having completed **Stages 2 (Agent Core)**, **3 (RAG/Quality)**, and **4 (LangGraph Integration)** of the roadmap.

## Prerequisites

Before installing Klaro, ensure you have:

- **Python 3.11 or higher** (Current stable version)
- **OpenAI API key** - Get yours at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Git** - For version control
- **pip** package manager (included with Python)

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/aethrox/klaro.git
cd klaro
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv klaro-env

# Activate virtual environment
# On Windows:
klaro-env\Scripts\activate

# On macOS/Linux:
source klaro-env/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

3. (Optional) Add LangSmith credentials for debugging:
   ```
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=your-langsmith-key
   LANGSMITH_PROJECT=klaro
   ```

### Step 5: Initialize Knowledge Base

The knowledge base (ChromaDB) is automatically initialized on first run. No manual setup required.

### Step 6: Verify Installation

```bash
python main.py
```

If successful, you'll see the agent start analyzing the current directory and generating documentation.

## Configuration

### Environment Variables

Configure Klaro's behavior via environment variables in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key for LLM and embeddings |
| `KLARO_RECURSION_LIMIT` | No | `50` | Maximum agent iterations (increase for large projects) |
| `LANGSMITH_TRACING` | No | `false` | Enable LangSmith tracing for debugging |
| `LANGSMITH_API_KEY` | No | - | LangSmith API key (required if tracing enabled) |
| `LANGSMITH_PROJECT` | No | `klaro` | LangSmith project name |

### Model Selection

Default model: **gpt-4o-mini** (excellent cost/performance balance)

To change the LLM model, edit `main.py` line 77:

```python
LLM_MODEL = "gpt-4o-mini"  # Options: gpt-4o-mini, gpt-4o, claude-3-5-sonnet
```

**Model Comparison:**
- `gpt-4o-mini`: Best for cost-conscious users (~$0.10-0.40 per run)
- `gpt-4o`: Higher quality analysis (~$0.50-1.00 per run)
- `claude-3-5-sonnet`: Alternative high-quality option (requires Anthropic API key)

### Recursion Limit Tuning

The recursion limit controls maximum agent iterations:

- **Default (50)**: Suitable for most projects
- **Small projects (< 10 files)**: Can reduce to 30
- **Large projects (> 50 files)**: Increase to 100+

Adjust via environment variable:
```bash
export KLARO_RECURSION_LIMIT=100
```

Or in `.env`:
```
KLARO_RECURSION_LIMIT=100
```

## Usage

### Basic Usage

Run the agent on the current directory:

```bash
python main.py
```

### Analyze Specific Project

```bash
python main.py /path/to/project
```

### Programmatic Usage

```python
from main import run_klaro_langgraph

# Analyze a project
result = run_klaro_langgraph(project_path="./my-project")
```

## Output

The agent generates and displays:

1. **Project Overview**: High-level description of project purpose
2. **Technology Stack Analysis**: Detected frameworks, libraries, dependencies
3. **Generated README.md**: Complete Markdown documentation
4. **File Structure Documentation**: Visual tree of important files

**Output Format:**
- Printed to terminal (stdout)
- To save to file: `python main.py > output.txt`
- Future versions will support direct file writing

## Quick Start Example

**Analyze Klaro itself:**

```bash
python main.py .
```

Expected output:
```
--- Launching Klaro LangGraph Agent (Stage 4 - gpt-4o-mini) ---
📢 Initializing RAG Knowledge Base...
   -> Setup Result: Knowledge base (ChromaDB) successfully initialized...

==================================================
✅ TASK SUCCESS: LangGraph Agent Finished.
====================================

# Klaro

Klaro is an autonomous AI agent that analyzes codebases...
[Full README content]
```

**Analyze another project:**

```bash
python main.py ../my-fastapi-app
```

## Troubleshooting

### Common Issues

**Issue: "OpenAI API key not found"**
- **Solution**: Ensure `OPENAI_API_KEY` is set in `.env` file
- **Test**: `echo $OPENAI_API_KEY` (should display your key)

**Issue: "ChromaDB initialization failed"**
- **Solution**: Delete `./klaro_db` directory and re-run
- **Cause**: Corrupted vector database

**Issue: "Recursion limit exceeded"**
- **Solution**: Increase `KLARO_RECURSION_LIMIT` to 100 or higher
- **Cause**: Project too large for default 50 iterations

For more detailed troubleshooting, see [docs/troubleshooting.md](docs/troubleshooting.md).

## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.