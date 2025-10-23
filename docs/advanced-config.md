# Advanced Configuration Guide

This guide covers advanced configuration options for Klaro, including custom LLM models, performance tuning, memory optimization, and integration patterns.

## Table of Contents

- [Custom LLM Models](#custom-llm-models)
- [Performance Tuning for Large Projects](#performance-tuning-for-large-projects)
- [Memory Optimization](#memory-optimization)
- [Batch Processing](#batch-processing)
- [Custom Prompts](#custom-prompts)
- [Tool Customization](#tool-customization)
- [Integration with Other Systems](#integration-with-other-systems)

---

## Custom LLM Models

Klaro supports multiple LLM models through the LangChain integration. By default, it uses `gpt-4o-mini` for cost-effectiveness, but you can configure alternative models.

### Switching Models

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
# Before:
LLM_MODEL = "gpt-4o-mini"

# After:
LLM_MODEL = "gpt-4o"  # or any other supported model
```

### Supported Models

| Model | Speed | Cost | Quality | Best For |
|-------|-------|------|---------|----------|
| `gpt-4o-mini` | ⚡⚡⚡ | $ | ⭐⭐⭐ | Standard docs, small-medium projects |
| `gpt-4o` | ⚡⚡ | $$ | ⭐⭐⭐⭐ | Complex codebases, detailed analysis |
| `gpt-4-turbo` | ⚡ | $$$ | ⭐⭐⭐⭐⭐ | Large projects requiring deep understanding |

### Using Non-OpenAI Models

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

## Performance Tuning for Large Projects

Klaro's default configuration is optimized for small to medium projects. For large codebases (>100 files), apply these optimizations.

### Recursion Limit Adjustment

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

### Temperature Optimization

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

### Parallel Tool Execution

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

## Memory Optimization

For resource-constrained environments or very large projects.

### Vector Database Optimization

**Reduce chunk size for less memory usage:**

```python
# tools.py line 725 (in init_knowledge_base)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,   # Reduced from 1000
    chunk_overlap=100 # Reduced from 200
)
```

**Trade-off:** Smaller chunks = lower memory usage but less context per retrieval.

### ChromaDB Configuration

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

### Message History Pruning

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

## Batch Processing

Process multiple projects in a single run for efficiency.

### Basic Batch Script

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

### Parallel Batch Processing

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

## Custom Prompts

Customize the agent's behavior by modifying the system prompt.

### Modifying System Prompt

Edit `prompts.py`:

```python
# prompts.py
SYSTEM_PROMPT = """
You are Klaro, an advanced AI documentation agent.

# YOUR CUSTOM INSTRUCTIONS HERE

TASK: Generate professional technical documentation...
"""
```

### Task-Specific Prompts

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

### Prompt Templates

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

## Tool Customization

Extend Klaro's capabilities by adding custom tools.

### Adding a New Tool

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

### Tool Best Practices

1. **Clear docstrings:** LLM uses these to understand when to call the tool
2. **Error handling:** Always return strings (never raise exceptions)
3. **JSON output:** For structured data, use JSON format
4. **Idempotent:** Tools should be safe to call multiple times
5. **Fast execution:** Avoid long-running operations (>5 seconds)

---

## Integration with Other Systems

Integrate Klaro into your existing workflows and pipelines.

### CI/CD Integration

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

### Pre-commit Hook

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

### REST API Wrapper

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
    model: str = "gpt-4o-mini"

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

### Docker Integration

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

### VSCode Extension Integration

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

## Additional Resources

- [Configuration Guide](configuration.md) - Basic configuration options
- [Architecture Documentation](architecture.md) - System design overview
- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines

## Troubleshooting

For common issues with advanced configurations, see:
- [Troubleshooting Guide](troubleshooting.md)
- [GitHub Issues](https://github.com/your-org/klaro/issues)

---

**Last Updated:** 2025-10-23
