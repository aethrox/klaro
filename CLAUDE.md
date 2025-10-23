# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Klaro is an autonomous AI agent that generates technical documentation by analyzing codebases. It uses a **LangGraph state machine** with a **ReAct loop** (Reasoning and Acting) to autonomously navigate code, perform deep logic analysis using Python's AST, and generate professional documentation. The system integrates **RAG (Retrieval-Augmented Generation)** using ChromaDB to ensure generated docs match project style guides.

## Key Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables (copy from .env.example)
# Required: OPENAI_API_KEY
# Optional: LANGSMITH_TRACING, LANGSMITH_API_KEY, KLARO_RECURSION_LIMIT
```

### Running Klaro
```bash
# Run the main agent to generate documentation
python main.py
```

## Architecture

### Core Components

**main.py** - LangGraph agent orchestration
- Implements a `StateGraph` with nodes for model invocation and tool execution
- Uses conditional routing based on agent state (tool calls, errors, completion)
- Manages agent state: message history and error logs
- Default model: `gpt-4o-mini` (configurable via `LLM_MODEL`)
- Recursion limit: 50 (override with `KLARO_RECURSION_LIMIT` env var)

**tools.py** - Custom analysis tools
- `list_files(directory)`: Tree-structured directory listing with .gitignore filtering
- `read_file(file_path)`: File content reader with UTF-8 encoding
- `analyze_code(code_content)`: AST-based Python code analyzer extracting classes, functions, parameters, docstrings, and return types (JSON output)
- `web_search(query)`: External information gathering (currently simulated)
- `init_knowledge_base(documents)`: Initializes ChromaDB vector store at `./klaro_db` using OpenAI embeddings (`text-embedding-3-small`)
- `retrieve_knowledge(query)`: RAG retrieval from vector database (k=3 results)

**prompts.py** - System prompt definition
- Defines Klaro's identity as a documentation agent
- Establishes ReAct loop protocol: Thought → Action → Observation
- Lists available tools and their usage guidelines
- Requires final output format: `Final Answer: [MARKDOWN_CONTENT]`

### Agent Flow

1. **Initialization**: RAG knowledge base is set up with default style guide
2. **Entry Point**: `run_model` node invokes LLM with message history
3. **Decision Logic** (`decide_next_step`):
   - If error exists → loop back to `run_model`
   - If "Final Answer" detected → END
   - If tool calls present → route to `call_tool`
   - Otherwise → continue to `run_model`
4. **Tool Execution**: `ToolNode` executes requested tools and appends results to messages
5. **Loop**: After tool execution, always returns to `run_model` to process observations

### ReAct Loop Pattern

The agent follows a strict cycle:
- **Thought**: LLM reasons about next steps
- **Action**: Selects and executes a tool (format: `tool_name[parameter]`)
- **Observation**: Processes tool output and decides next action
- **Final Answer**: Delivers markdown documentation when sufficient information is gathered

### RAG Integration

- Vector database persisted at `./klaro_db/`
- Uses `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=200)
- OpenAI embeddings model: `text-embedding-3-small`
- Global retriever instance (`KLARO_RETRIEVER`) shared across tool invocations
- Style guide content embedded at initialization for consistent documentation format

### State Management

`AgentState` (TypedDict):
- `messages`: Conversation history using LangChain's message reducor (append-only)
- `error_log`: Tracks execution errors for retry logic

## Code Analysis Behavior

The AST analyzer (`analyze_code`) extracts:
- Functions: name, parameters, return type annotation, docstring, line number
- Classes: name, docstring, methods (with same details as functions), line number
- Returns structured JSON with analysis summary and component details

## Important Notes

- All Python files must be analyzed via `analyze_code` after reading with `read_file`
- The agent MUST use `retrieve_knowledge` before generating final documentation
- .gitignore patterns are hardcoded in tools.py and automatically filter directory listings
- The system prompt emphasizes step-by-step exploration: list_files → read_file → analyze_code → retrieve_knowledge → Final Answer
- Tool descriptions in docstrings are critical - they guide the LLM's tool selection
