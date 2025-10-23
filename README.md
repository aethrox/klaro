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

## 📦 Installation

### Prerequisites
Before installing Klaro, ensure you have the following:

* **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
* **OpenAI API Key** - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
* **Git** - For cloning the repository
* **pip** - Python package manager (included with Python)

### Step 1: Clone the Repository
```bash
git clone https://github.com/aethrox/klaro.git
cd klaro
```

### Step 2: Create a Virtual Environment
Creating a virtual environment is recommended to isolate project dependencies.

**On Windows:**
```bash
python -m venv klaro-env
klaro-env\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv klaro-env
source klaro-env/bin/activate
```

### Step 3: Install Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-api-key-here

# Optional: LangSmith tracing for debugging (requires LangSmith account)
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your-langsmith-key-here
LANGSMITH_PROJECT=klaro

# Optional: Override default recursion limit (default: 50)
KLARO_RECURSION_LIMIT=50
```

**Important:** Never commit your `.env` file to version control. It's already included in `.gitignore`.

### Step 5: Initialize the Knowledge Base
The knowledge base (ChromaDB vector database) is automatically initialized on first run. No manual setup required.

### Step 6: Verify Installation
Run Klaro to verify everything is working:

```bash
python main.py
```

You should see output indicating the agent is analyzing the codebase and generating documentation.

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | - | Your OpenAI API key for LLM and embeddings |
| `KLARO_RECURSION_LIMIT` | No | `50` | Maximum agent iterations before timeout |
| `LANGSMITH_TRACING` | No | `false` | Enable LangSmith tracing for debugging |
| `LANGSMITH_API_KEY` | No | - | LangSmith API key (if tracing enabled) |
| `LANGSMITH_ENDPOINT` | No | - | LangSmith endpoint URL |
| `LANGSMITH_PROJECT` | No | - | LangSmith project name |

### Model Selection
By default, Klaro uses `gpt-4o-mini` for cost-effectiveness. To change the model, edit `main.py` line 78:

```python
LLM_MODEL = "gpt-4o-mini"  # Change to "gpt-4o" or other supported model
```

**Supported Models:**
* `gpt-4o-mini` - Fast, cost-effective (recommended for most use cases)
* `gpt-4o` - More powerful reasoning (higher cost)
* `gpt-4-turbo` - Balanced performance and cost

## 🚀 Usage

### Basic Usage
Run the agent on current directory:
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

result = run_klaro_langgraph(project_path="./my_project")
```

### Output
The agent generates and displays:
- Project overview
- Technology stack analysis
- Generated README.md content
- File structure documentation

Output is printed to terminal. To save to file:
```bash
python main.py > output.txt
```

### Quick Start Example
```bash
# Analyze Klaro itself
python main.py .

# Analyze another project
python main.py ../another-project
```

### How It Works
The agent will:
1. Explore the project structure using `list_files`
2. Read critical files (main.py, requirements.txt, etc.)
3. Analyze Python code using AST
4. Retrieve style guidelines from the knowledge base
5. Generate comprehensive README documentation

## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.