# Usage Examples

This guide provides real-world usage scenarios, input/output examples, common workflows, and integration examples for Klaro.

## Table of Contents
- [Real-World Usage Scenarios](#real-world-usage-scenarios)
- [Input/Output Examples](#inputoutput-examples)
- [Common Workflows](#common-workflows)
- [Integration Examples](#integration-examples)
- [LangSmith Tracing Interpretation Guide](#langsmith-tracing-interpretation-guide)

---

## Real-World Usage Scenarios

### Scenario 1: New Project Onboarding
**Context:** You've joined a new team and need to understand an undocumented codebase quickly.

**Solution:**
```bash
cd /path/to/new-project
python /path/to/klaro/main.py .
```

**Expected Outcome:**
- Comprehensive README with project architecture
- List of key files and their purposes
- Technology stack identification
- Entry point and configuration documentation

**Time Saved:** 3-4 hours of manual exploration → 2-3 minutes automated analysis

---

### Scenario 2: Open Source Project Documentation
**Context:** You're maintaining an open-source library with outdated README.

**Solution:**
```bash
# Clone your project
git clone https://github.com/youruser/yourproject.git
cd yourproject

# Run Klaro
python /path/to/klaro/main.py . > NEW_README.md

# Review and merge
git diff README.md NEW_README.md
```

**Expected Outcome:**
- Up-to-date feature descriptions
- Accurate installation instructions
- Current API documentation
- Technology stack updates

---

### Scenario 3: Legacy Code Maintenance
**Context:** You need to document a legacy Python project with no existing documentation.

**Solution:**
```bash
python main.py /path/to/legacy-project > legacy-docs.md
```

**Expected Outcome:**
- Complete function and class inventory
- Dependency mapping
- Architecture overview
- Entry points identification

---

### Scenario 4: Multi-Module Project Analysis
**Context:** Analyzing a large project with multiple modules.

**Workflow:**
```bash
# Analyze entire project
python main.py /path/to/large-project > full-docs.md

# Analyze specific module
cd /path/to/large-project/modules/auth
python /path/to/klaro/main.py . > auth-module-docs.md
```

**Expected Outcome:**
- High-level project documentation
- Module-specific detailed documentation
- Dependency relationships
- Inter-module communication patterns

---

### Scenario 5: Pre-Release Documentation Update
**Context:** You're preparing for a release and need updated docs.

**Workflow:**
```bash
# Checkout release branch
git checkout release/v2.0

# Generate documentation
python /path/to/klaro/main.py . > RELEASE_DOCS.md

# Compare with existing docs
diff README.md RELEASE_DOCS.md

# Update README
cp RELEASE_DOCS.md README.md
git add README.md
git commit -m "docs: Update README for v2.0 release"
```

---

## Input/Output Examples

### Example 1: Simple Python Project

**Input Project Structure:**
```
my_project/
├── main.py
├── utils.py
├── config.py
└── requirements.txt
```

**Command:**
```bash
python main.py /path/to/my_project
```

**Output (Abbreviated):**
```markdown
# My Project

## Overview
This project is a Python application that implements...

## Technology Stack
- **Language:** Python 3.11+
- **Dependencies:**
  - requests==2.28.0
  - pydantic==2.0.0

## File Structure
- `main.py` - Main application entry point
  - `main()` - Initializes configuration and runs application
- `utils.py` - Utility functions
  - `load_data(file_path)` - Loads data from JSON files
  - `validate_input(data)` - Validates user input
- `config.py` - Configuration management
  - `Config` class - Stores application settings

## Installation
...

## Usage
...
```

---

### Example 2: Flask API Project

**Input Project Structure:**
```
api_project/
├── app.py
├── models/
│   ├── user.py
│   └── post.py
├── routes/
│   ├── auth.py
│   └── posts.py
├── requirements.txt
└── config.py
```

**Output Highlights:**
```markdown
# API Project

## Overview
This is a Flask-based REST API that provides endpoints for...

## Technology Stack
- **Framework:** Flask 2.3.0
- **Database:** SQLAlchemy
- **Authentication:** JWT

## API Endpoints

### Authentication
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration

### Posts
- `GET /api/posts` - List all posts
- `POST /api/posts` - Create new post
- `GET /api/posts/<id>` - Get specific post

## Models
- `User` - User authentication and profile
  - Fields: id, username, email, password_hash
- `Post` - Blog post data
  - Fields: id, title, content, author_id, created_at

...
```

---

## Common Workflows

### Workflow 1: Documentation-First Development

**Use Case:** You want to maintain up-to-date docs throughout development.

**Steps:**
1. Write initial code structure
2. Run Klaro to generate docs
3. Review and customize docs
4. Continue development
5. Re-run Klaro before each commit

**Automation Script:**
```bash
#!/bin/bash
# pre-commit-docs.sh

python /path/to/klaro/main.py . > README_NEW.md

if ! diff -q README.md README_NEW.md > /dev/null; then
  echo "Documentation is outdated. Updating..."
  mv README_NEW.md README.md
  git add README.md
else
  rm README_NEW.md
  echo "Documentation is up-to-date."
fi
```

---

### Workflow 2: Multi-Project Documentation

**Use Case:** You maintain multiple projects and need consistent documentation.

**Script:**
```bash
#!/bin/bash
# document-all-projects.sh

PROJECTS=(
  "/path/to/project1"
  "/path/to/project2"
  "/path/to/project3"
)

for PROJECT in "${PROJECTS[@]}"; do
  echo "Documenting $PROJECT..."
  python main.py "$PROJECT" > "${PROJECT}/README_GENERATED.md"
done

echo "All projects documented!"
```

---

### Workflow 3: CI/CD Integration

**Use Case:** Automatically check if documentation is outdated in CI pipeline.

**GitHub Actions Example:**
```yaml
# .github/workflows/check-docs.yml
name: Check Documentation

on: [push, pull_request]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Klaro
        run: |
          git clone https://github.com/aethrox/klaro.git
          cd klaro
          pip install -r requirements.txt

      - name: Generate Documentation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd klaro
          python main.py ../ > ../README_GENERATED.md

      - name: Check if docs are outdated
        run: |
          if ! diff -q README.md README_GENERATED.md > /dev/null; then
            echo "❌ Documentation is outdated!"
            exit 1
          else
            echo "✅ Documentation is up-to-date!"
          fi
```

---

## Integration Examples

### Integration 1: Jupyter Notebook

**Use Case:** Analyze and document Klaro programmatically in a notebook.

```python
# notebook.ipynb
import sys
sys.path.append('/path/to/klaro')

from main import run_klaro_langgraph

# Analyze current project
result = run_klaro_langgraph(project_path=".")

# Display results
print(result)

# Or analyze multiple projects
projects = ['./project1', './project2', './project3']
results = {}

for project in projects:
    print(f"Analyzing {project}...")
    results[project] = run_klaro_langgraph(project_path=project)

# Compare documentation
for project, doc in results.items():
    print(f"\n{'='*50}")
    print(f"Project: {project}")
    print(f"{'='*50}")
    print(doc[:500])  # Print first 500 chars
```

---

### Integration 2: Custom Python Script

**Use Case:** Build a custom documentation pipeline.

```python
# custom_doc_generator.py
import os
from pathlib import Path
from main import run_klaro_langgraph

def generate_docs_for_directory(root_dir: str, output_dir: str):
    """Generate documentation for all Python projects in a directory."""
    root_path = Path(root_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Find all directories with Python files
    python_projects = []
    for item in root_path.iterdir():
        if item.is_dir() and any(item.glob('*.py')):
            python_projects.append(item)

    print(f"Found {len(python_projects)} Python projects")

    # Generate docs for each
    for project in python_projects:
        print(f"\nAnalyzing: {project.name}")
        try:
            docs = run_klaro_langgraph(project_path=str(project))

            # Save to output directory
            output_file = output_path / f"{project.name}_README.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(docs)

            print(f"✅ Saved: {output_file}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_docs_for_directory(
        root_dir="/path/to/projects",
        output_dir="/path/to/docs"
    )
```

---

### Integration 3: FastAPI Endpoint

**Use Case:** Expose Klaro as a web service.

```python
# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import run_klaro_langgraph
import tempfile
import os

app = FastAPI()

class DocumentationRequest(BaseModel):
    project_path: str

class DocumentationResponse(BaseModel):
    documentation: str
    status: str

@app.post("/generate-docs", response_model=DocumentationResponse)
async def generate_documentation(request: DocumentationRequest):
    """Generate documentation for a given project path."""
    try:
        if not os.path.exists(request.project_path):
            raise HTTPException(status_code=404, detail="Project path not found")

        # Generate documentation
        docs = run_klaro_langgraph(project_path=request.project_path)

        return DocumentationResponse(
            documentation=docs,
            status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn api:app --reload
```

---

## LangSmith Tracing Interpretation Guide

### Enabling LangSmith Tracing

**Configuration:**
```bash
# .env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-key-here
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=klaro
```

---

### Understanding Trace Output

#### 1. Run View
Shows the overall execution flow:

```
Run: run_klaro_langgraph
├─ Node: run_model (Duration: 2.3s)
│  └─ LLM Call: ChatOpenAI (gpt-4o-mini)
│     ├─ Input: System prompt + messages
│     └─ Output: Tool calls requested
├─ Node: call_tool (Duration: 0.8s)
│  ├─ Tool: list_files
│  └─ Tool: read_file
├─ Node: run_model (Duration: 1.9s)
│  └─ LLM Call: ChatOpenAI
│     └─ Output: More tool calls
...
└─ Final Output: README content
```

**Key Metrics:**
- **Total Duration:** Overall execution time
- **LLM Calls:** Number of model invocations
- **Tool Executions:** Which tools were used and when

---

#### 2. Token Usage Analysis

**What to Look For:**
```
Token Usage per LLM Call:
- Input Tokens: 1,234
- Output Tokens: 567
- Total: 1,801

Cost Estimate:
- Input: $0.0012
- Output: $0.0011
- Total: $0.0023
```

**Optimization Tips:**
- If input tokens > 10,000 consistently: RAG context may be too large
- If output tokens > 2,000: Model is being too verbose
- High total cost: Consider using gpt-4o-mini instead of gpt-4o

---

#### 3. Error Trace Analysis

**Example Error Trace:**
```
Run: run_klaro_langgraph (FAILED)
├─ Node: run_model ✓
├─ Node: call_tool ✗
│  └─ Tool: analyze_code
│     └─ Error: SyntaxError: invalid syntax in file.py
└─ Node: run_model ✓
   └─ Output: Logged error, retrying...
```

**Interpretation:**
- ✓ = Successful execution
- ✗ = Failed execution
- Error messages show exact failure point
- Following nodes show recovery attempts

---

#### 4. ReAct Loop Visualization

**Typical Trace Pattern:**
```
Iteration 1:
├─ Thought: "I need to explore the file structure"
├─ Action: list_files["."]
└─ Observation: File tree returned

Iteration 2:
├─ Thought: "I should read the main entry point"
├─ Action: read_file["main.py"]
└─ Observation: File content returned

Iteration 3:
├─ Thought: "I need to analyze the code structure"
├─ Action: analyze_code[content]
└─ Observation: AST analysis returned

...

Iteration N:
├─ Thought: "I have enough information"
└─ Final Answer: [Generated README]
```

---

#### 5. Performance Bottlenecks

**Identifying Slow Operations:**
```
Duration Analysis:
- list_files: 0.3s ✓
- read_file: 0.5s ✓
- analyze_code: 0.8s ✓
- retrieve_knowledge: 2.1s ⚠️ (SLOW)
- LLM call: 3.5s ⚠️ (SLOW)
```

**Solutions:**
- **Slow retrieve_knowledge:** Reduce embedding dimensions or k value
- **Slow LLM calls:** Reduce prompt length or use faster model
- **Multiple slow read_file:** Files may be too large

---

#### 6. Recursion Limit Warnings

**Trace Showing Approaching Limit:**
```
Iteration 45/50 ⚠️
Iteration 46/50 ⚠️
Iteration 47/50 ⚠️
...
Iteration 50/50 ❌ RECURSION LIMIT EXCEEDED
```

**Solution:**
```bash
# Increase limit in .env
KLARO_RECURSION_LIMIT=100
```

**Note:** If consistently hitting limits, the agent may be stuck in a loop. Check for:
- Invalid tool outputs
- Confusing prompts
- Missing information in knowledge base

---

### Best Practices for Tracing

1. **Always Enable During Development**
   ```bash
   LANGSMITH_TRACING=true
   ```

2. **Review Traces for Failed Runs**
   - Identify exact failure point
   - Check tool inputs/outputs
   - Verify error messages

3. **Monitor Token Usage**
   - Track cost per run
   - Optimize prompts if usage is high
   - Consider model switching

4. **Analyze Successful Patterns**
   - Note which tool sequences work best
   - Identify optimal iteration counts
   - Reuse successful patterns

5. **Export Traces for Documentation**
   - Use LangSmith UI to export traces
   - Share with team for debugging
   - Create benchmark traces

---

## Summary

This guide covered:
- ✅ Real-world scenarios (5 examples)
- ✅ Input/output examples (2 detailed examples)
- ✅ Common workflows (3 workflows with scripts)
- ✅ Integration examples (3 integration patterns)
- ✅ LangSmith tracing interpretation (6 detailed sections)

For more information, see:
- [Troubleshooting Guide](./troubleshooting.md)
- [Configuration Guide](./configuration.md)
- [Main README](../README.md)
