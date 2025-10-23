# Klaro Architecture Documentation

This document provides a comprehensive overview of Klaro's system architecture, including the LangGraph state machine, ReAct loop implementation, tool integration, and RAG system.

## Table of Contents

1. [System Overview](#system-overview)
2. [LangGraph State Machine](#langgraph-state-machine)
3. [ReAct Loop Flow](#react-loop-flow)
4. [Tool Integration](#tool-integration)
5. [RAG System Architecture](#rag-system-architecture)
6. [Data Flow Diagrams](#data-flow-diagrams)

---

## System Overview

Klaro is an autonomous AI agent built on LangGraph that generates technical documentation by analyzing codebases. The system combines:

- **LangGraph StateGraph**: Orchestrates agent workflow with conditional routing
- **ReAct Framework**: Enables autonomous reasoning through Thought-Action-Observation cycles
- **Custom Tools**: Provide codebase exploration, AST analysis, and knowledge retrieval
- **RAG System**: Ensures documentation consistency with ChromaDB vector store
- **OpenAI LLM**: Powers decision-making and content generation (gpt-4o-mini)

**Key Design Principles:**
- Incremental exploration (avoids loading entire codebase into context)
- Deterministic code analysis (AST prevents hallucinations)
- Style-guided generation (RAG enforces documentation standards)
- Error recovery (state tracking enables replanning)

---

## LangGraph State Machine

### State Definition

```
AgentState (TypedDict):
  ├─ messages: Sequence[BaseMessage]
  │    └─ Reducer: lambda x, y: x + y  (append-only history)
  └─ error_log: str
       └─ Tracks tool execution failures for retry logic
```

**State Fields:**

1. **messages** (Annotated with reducer function)
   - Type: `Sequence[BaseMessage]`
   - Purpose: Maintains complete conversation history
   - Reducer: `lambda x, y: x + y` (appends new messages)
   - Contains: HumanMessage, AIMessage, ToolMessage objects

2. **error_log** (Simple string)
   - Type: `str`
   - Purpose: Stores error messages from tool failures
   - Behavior: Cleared after each LLM invocation
   - Usage: Triggers error recovery routing

### Node Definitions

```
StateGraph Nodes:
  ┌─────────────────────────────────────────────┐
  │  run_model                                  │
  │  ─────────────────────────────────────────  │
  │  • Invokes LLM with message history         │
  │  • Returns AIMessage with:                  │
  │    - Reasoning text                         │
  │    - Tool calls (if action needed)          │
  │    - Final Answer (if task complete)        │
  │  • Clears error_log after invocation        │
  └─────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────┐
  │  call_tool (ToolNode)                       │
  │  ─────────────────────────────────────────  │
  │  • Parses tool_calls from last AIMessage    │
  │  • Executes requested tools                 │
  │  • Returns ToolMessage with results         │
  │  • Appends results to message history       │
  └─────────────────────────────────────────────┘
```

**run_model Node (main.py:157-203)**
- **Input**: Current AgentState with complete message history
- **Function**: Invokes LLM via `model.invoke(state["messages"])`
- **Output**: `{"messages": [response], "error_log": ""}`
- **LLM Model**: gpt-4o-mini (temperature=0.2)
- **Bound Tools**: 5 tools (list_files, read_file, analyze_code, web_search, retrieve_knowledge)

**call_tool Node (main.py:296)**
- **Type**: LangGraph built-in ToolNode
- **Input**: State with AIMessage containing tool_calls
- **Execution**: Automatically parses and executes tools
- **Output**: ToolMessage appended to message history

### Edge Transitions (Routing Logic)

```
Conditional Routing (decide_next_step function):

  ┌──────────────────────────────────────────┐
  │  Check 1: Error Log                      │
  │  ────────────────────────────────────    │
  │  if state["error_log"] is not empty:     │
  │      return "run_model"  (replan)        │
  └──────────────────────────────────────────┘
                    ↓ (if no error)
  ┌──────────────────────────────────────────┐
  │  Check 2: Task Completion                │
  │  ────────────────────────────────────    │
  │  if "Final Answer" in last_message:      │
  │      return END  (terminate)             │
  └──────────────────────────────────────────┘
                    ↓ (if not complete)
  ┌──────────────────────────────────────────┐
  │  Check 3: Tool Calls                     │
  │  ────────────────────────────────────    │
  │  if last_message.tool_calls:             │
  │      return "call_tool"  (execute)       │
  └──────────────────────────────────────────┘
                    ↓ (if no tool calls)
  ┌──────────────────────────────────────────┐
  │  Default: Continue Reasoning             │
  │  ────────────────────────────────────    │
  │  return "run_model"  (think more)        │
  └──────────────────────────────────────────┘
```

**Routing Decision Logic (main.py:207-279):**

1. **Error Recovery** (`state["error_log"]` not empty)
   - Action: Return "run_model"
   - Purpose: Let LLM see error and replan with different approach

2. **Task Completion** ("Final Answer" detected)
   - Action: Return END
   - Purpose: Terminate graph when documentation is ready

3. **Tool Execution** (tool_calls present)
   - Action: Return "call_tool"
   - Purpose: Execute tools requested by LLM

4. **Continue Reasoning** (default case)
   - Action: Return "run_model"
   - Purpose: Let LLM continue thinking

### Graph Structure

```
Graph Compilation:

  ENTRY POINT
      ↓
  run_model ←─────┐ (conditional edges)
      │           │
      ├──[Error?]─┘
      │
      ├──[Final Answer?]──→ END
      │
      ├──[Tool calls?]──→ call_tool
      │                       │
      └──[Default]────────────┘ (unconditional edge)
```

**Graph Setup (main.py:281-322):**

```python
workflow = StateGraph(AgentState)
workflow.add_node("run_model", run_model)
workflow.add_node("call_tool", ToolNode(tools))
workflow.set_entry_point("run_model")

workflow.add_conditional_edges(
    "run_model",
    decide_next_step,
    {
        "call_tool": "call_tool",
        END: END,
        "run_model": "run_model"
    }
)

workflow.add_edge("call_tool", "run_model")  # Always return to LLM
app = workflow.compile()
```

---

## ReAct Loop Flow

The ReAct (Reasoning and Acting) pattern enables autonomous decision-making through a structured cycle.

### Thought Step (LLM Reasoning)

```
Agent State: {...messages, error_log: ""}
      ↓
  run_model node invokes LLM
      ↓
LLM processes history and thinks:
  "I need to understand the project structure.
   I should use list_files to explore the directory."
      ↓
AIMessage with reasoning text
```

**Characteristics:**
- LLM receives complete conversation history
- Can reference previous observations
- Decides which tool to use based on current knowledge gap
- Guided by SYSTEM_PROMPT (prompts.py:59-79)

### Action Step (Tool Calling)

```
AIMessage with tool_calls:
  tool_calls = [
    {
      "name": "list_files",
      "args": {"directory": "."},
      "id": "call_abc123"
    }
  ]
      ↓
decide_next_step returns "call_tool"
      ↓
ToolNode executes list_files(".")
      ↓
Result returned as ToolMessage
```

**Tool Call Format:**
- LLM uses OpenAI function calling format
- ToolNode automatically parses and executes
- Parameters validated against tool signatures
- Errors caught and logged to error_log

### Observation Step (Tool Results)

```
ToolMessage appended to state:
  content = """
  / klaro/
  ├── main.py
  ├── tools.py
  ├── prompts.py
  ├── requirements.txt
  """
  tool_call_id = "call_abc123"
      ↓
State updated with new message
      ↓
Route back to run_model
      ↓
LLM sees tool result and continues reasoning
```

**Observation Processing:**
- ToolMessage linked to original AIMessage via tool_call_id
- LLM interprets results in next invocation
- Decides next action based on gathered information
- Can request more tools or provide Final Answer

### Cycle Repetition

```
Typical Agent Workflow:

Iteration 1:
  Thought: "Need to explore project structure"
  Action: list_files["."]
  Observation: "Found main.py, tools.py, prompts.py..."

Iteration 2:
  Thought: "Should read main.py to understand entry point"
  Action: read_file["main.py"]
  Observation: "File contains LangGraph setup..."

Iteration 3:
  Thought: "Need to analyze code structure"
  Action: analyze_code[<main.py content>]
  Observation: "Found AgentState class, run_model function..."

Iteration 4:
  Thought: "Should get README style guidelines"
  Action: retrieve_knowledge["README style guidelines"]
  Observation: "Retrieved style guide with required sections..."

Iteration 5:
  Thought: "Have sufficient information to write README"
  Action: Final Answer: # Klaro\n\n## Setup\n...
  Result: END (graph terminates)
```

**Termination Conditions:**
- LLM outputs "Final Answer: [MARKDOWN_CONTENT]"
- Recursion limit reached (default: 50 iterations)
- Unrecoverable error occurs

---

## Tool Integration

### Tool Binding to LLM

```
Tool Creation Flow:

1. Define Python functions in tools.py:
   def list_files(directory: str) -> str:
       """Lists files and folders..."""
       ...

2. Wrap in LangChain Tool objects (main.py:93-99):
   tools = [
       Tool(
           name="list_files",
           func=list_files,
           description=list_files.__doc__
       ),
       ...
   ]

3. Bind tools to LLM (main.py:102):
   model = llm.bind_tools(tools)

4. LLM can now call tools via function calling API
```

**Tool Registration (main.py:89-102):**
- Tools wrapped as LangChain Tool objects
- Docstrings automatically used as descriptions
- LLM uses descriptions to decide when to call tools
- Tool names must match function names

### Tool Execution Flow

```
Tool Execution Pipeline:

AIMessage.tool_calls:
  [{"name": "read_file", "args": {"file_path": "main.py"}}]
      ↓
ToolNode receives tool call
      ↓
Looks up "read_file" in tools list
      ↓
Executes read_file(file_path="main.py")
      ↓
Catches exceptions:
  • FileNotFoundError → Error message
  • SyntaxError (for analyze_code) → Error JSON
  • Other exceptions → Generic error
      ↓
Returns ToolMessage:
  content = <tool result or error>
  tool_call_id = <original call id>
      ↓
Message appended to state.messages
```

### Error Handling in Tools

**Error Patterns:**

1. **File Not Found** (tools.py:460-461)
   ```python
   if not os.path.exists(file_path):
       return f"Error: File path not found: '{file_path}'"
   ```

2. **Code Parsing Error** (tools.py:569-570)
   ```python
   except SyntaxError as e:
       return json.dumps({"error": f"Code parsing error: {e}"})
   ```

3. **RAG Initialization Error** (tools.py:743-744)
   ```python
   except Exception as e:
       return f"Error initializing knowledge base: {e}"
   ```

**Error Recovery:**
- Tool errors returned as strings (not exceptions)
- LLM sees errors in next observation
- Can decide to retry with different parameters
- State machine routes back to run_model for replanning

### Tool Result Processing

```
Tool Output Formats:

list_files:
  / project_name/
  ├── main.py
  ├── tools.py
  └── requirements.txt

read_file:
  <raw file contents>

analyze_code:
  {
    "analysis_summary": "...",
    "components": [{"type": "function", "name": "..."}, ...]
  }

retrieve_knowledge:
  Retrieved Information:
  Source 1: <chunk 1>
  ---
  Source 2: <chunk 2>
  ---
  Source 3: <chunk 3>
```

---

## RAG System Architecture

### ChromaDB Initialization

```
RAG Setup Flow (main.py:405-411):

1. Style Guide Content Preparation:
   DEFAULT_GUIDE_CONTENT = """
   # Documentation Style Guide
   ...
   """

2. Document Creation:
   documents = [
       Document(
           page_content=DEFAULT_GUIDE_CONTENT,
           metadata={"source": "Klaro_Style_Guide"}
       )
   ]

3. Knowledge Base Initialization:
   init_knowledge_base(documents)
       ↓
   • Chunks documents (1000 chars, 200 overlap)
   • Generates embeddings (text-embedding-3-small)
   • Stores in ChromaDB at ./klaro_db
   • Sets global KLARO_RETRIEVER
```

**Initialization Implementation (tools.py:674-744):**

```python
def init_knowledge_base(documents: list[Document]) -> str:
    global KLARO_RETRIEVER

    # 1. Text Splitting
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)

    # 2. Embedding & Vector Store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH  # ./klaro_db
    )

    # 3. Global Retriever Setup
    KLARO_RETRIEVER = vectorstore.as_retriever(search_kwargs={"k": 3})

    return f"Initialized at {VECTOR_DB_PATH}. {len(texts)} chunks indexed."
```

### Document Indexing

```
Document Processing Pipeline:

Raw Document (page_content + metadata)
      ↓
RecursiveCharacterTextSplitter
  • chunk_size: 1000 characters
  • chunk_overlap: 200 characters
  • Splits on: \n\n, \n, " ", ""
      ↓
Text Chunks (smaller documents)
      ↓
OpenAI Embeddings API
  • Model: text-embedding-3-small
  • Dimensions: 1536
  • API Call: text-embedding-ada-002 replacement
      ↓
Vector Representations (float arrays)
      ↓
ChromaDB Persistence
  • Directory: ./klaro_db/
  • Format: SQLite + Parquet
  • Indexes: HNSW (approximate nearest neighbor)
      ↓
Retriever Ready (k=3 top results)
```

**Chunking Strategy:**
- **chunk_size=1000**: Balances context vs. specificity
- **chunk_overlap=200**: Preserves context across boundaries
- **Recursive splitting**: Tries to split on semantic boundaries (paragraphs, sentences)

### Semantic Retrieval

```
Retrieval Flow (tools.py:747-816):

1. Query Embedding:
   query = "README style guidelines"
       ↓
   OpenAI Embeddings API
       ↓
   query_vector = [0.123, -0.456, ...]

2. Similarity Search:
   ChromaDB computes cosine similarity:
       similarity = dot(query_vector, doc_vector) /
                    (||query_vector|| * ||doc_vector||)
       ↓
   Returns top k=3 most similar chunks

3. Result Formatting:
   Retrieved Information:
   Source 1: <most relevant chunk>
   ---
   Source 2: <second most relevant>
   ---
   Source 3: <third most relevant>

4. LLM Integration:
   Agent receives formatted results as ToolMessage
   Uses retrieved guidelines to generate documentation
```

**Retrieval Implementation (tools.py:747-816):**

```python
def retrieve_knowledge(query: str) -> str:
    global KLARO_RETRIEVER

    if KLARO_RETRIEVER is None:
        return "Error: Knowledge base not initialized."

    try:
        docs = KLARO_RETRIEVER.invoke(query)  # Top 3 results
        result_texts = [
            f"Source {i+1}: {doc.page_content}"
            for i, doc in enumerate(docs)
        ]
        return "Retrieved Information:\n" + "\n---\n".join(result_texts)
    except Exception as e:
        return f"Error retrieving knowledge: {e}"
```

### Integration with Prompts

```
Style Guide Enforcement:

1. System Prompt Requirement (prompts.py:71):
   "You MUST use retrieve_knowledge to fetch style guidelines
    before writing the final answer."

2. Task Instruction (main.py:413-417):
   "4. **You MUST use the 'retrieve_knowledge' tool to fetch
       the 'README style guidelines' before writing the
       final answer.**"

3. Agent Behavior:
   • Explores codebase first
   • Analyzes code structure
   • Retrieves style guidelines
   • Generates documentation matching guidelines

4. Consistency:
   • RAG ensures all READMEs follow same format
   • Style guide can be updated without changing agent code
   • Multiple style guides can be indexed for different doc types
```

---

## Data Flow Diagrams

### Overall System Data Flow

```
User Input
   ↓
┌──────────────────────────────────────────────────────────┐
│ main.py: run_klaro_langgraph()                           │
│ ──────────────────────────────────────────────────────── │
│ 1. Initialize RAG with style guide                       │
│ 2. Create initial state with task                        │
│ 3. Invoke LangGraph app                                  │
└──────────────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────────────┐
│ LangGraph StateGraph Execution                           │
│ ──────────────────────────────────────────────────────── │
│  ┌─────────────────┐                                     │
│  │  run_model      │←──────────────┐                     │
│  │  (LLM)          │                │                     │
│  └────────┬────────┘                │                     │
│           │ AIMessage               │                     │
│           ↓                         │                     │
│  ┌─────────────────┐                │                     │
│  │ decide_next_    │                │                     │
│  │ step (router)   │                │                     │
│  └────────┬────────┘                │                     │
│           │                         │                     │
│           ├─[tool calls?]───→┌─────┴──────┐              │
│           │                  │ call_tool  │              │
│           │                  │ (ToolNode) │              │
│           │                  └─────┬──────┘              │
│           │                        │ ToolMessage         │
│           │                        ↓                     │
│           │                   ┌─────────────────┐        │
│           │                   │ Tool Execution: │        │
│           │                   │ • list_files    │        │
│           │                   │ • read_file     │        │
│           │                   │ • analyze_code  │        │
│           │                   │ • retrieve_...  │        │
│           │                   └─────┬───────────┘        │
│           │                         │                    │
│           │                         └────────────────────┤
│           │                                              │
│           └─[Final Answer?]──→ END                       │
└──────────────────────────────────────────────────────────┘
   ↓
Final Documentation Output
```

### Tool Execution Pipeline

```
LLM Decision to Call Tool
   ↓
AIMessage with tool_calls field:
  {
    "name": "analyze_code",
    "args": {"code_content": "<python code>"},
    "id": "call_xyz789"
  }
   ↓
ToolNode receives AIMessage
   ↓
┌──────────────────────────────────────────────────────┐
│ ToolNode Processing                                  │
│ ──────────────────────────────────────────────────── │
│ 1. Parse tool_calls from AIMessage                   │
│ 2. Look up tool by name in tools list                │
│ 3. Extract arguments                                 │
│ 4. Execute function: analyze_code(code_content="...") │
│ 5. Catch exceptions and format errors                │
└──────────────────────────────────────────────────────┘
   ↓
Tool Execution (tools.py):
┌──────────────────────────────────────────────────────┐
│ analyze_code Implementation                          │
│ ──────────────────────────────────────────────────── │
│ 1. Parse code with ast.parse()                       │
│ 2. Walk AST nodes                                    │
│ 3. Extract:                                          │
│    • Functions (name, params, returns, docstring)    │
│    • Classes (name, methods, docstring)              │
│ 4. Format as JSON                                    │
└──────────────────────────────────────────────────────┘
   ↓
Tool Result (JSON string):
  {
    "analysis_summary": "2 classes, 5 functions",
    "components": [...]
  }
   ↓
ToolMessage created:
  content = <JSON result>
  tool_call_id = "call_xyz789"
   ↓
ToolMessage appended to state.messages
   ↓
Graph routes back to run_model
   ↓
LLM sees result in next invocation
```

### State Transition Flow

```
Initial State:
┌────────────────────────────────────────┐
│ messages: [HumanMessage("Analyze...")]  │
│ error_log: ""                          │
└────────────────────────────────────────┘
   ↓ (run_model)
┌────────────────────────────────────────┐
│ messages: [HumanMessage, AIMessage]    │
│   AIMessage.tool_calls = [list_files]  │
│ error_log: ""                          │
└────────────────────────────────────────┘
   ↓ (call_tool)
┌────────────────────────────────────────┐
│ messages: [                            │
│   HumanMessage,                        │
│   AIMessage(tool_calls),               │
│   ToolMessage(content="/ proj/...")    │
│ ]                                      │
│ error_log: ""                          │
└────────────────────────────────────────┘
   ↓ (run_model)
┌────────────────────────────────────────┐
│ messages: [...previous..., AIMessage]  │
│   AIMessage.tool_calls = [read_file]   │
│ error_log: ""                          │
└────────────────────────────────────────┘
   ↓ (call_tool)
┌────────────────────────────────────────┐
│ messages: [..., ToolMessage]           │
│   ToolMessage.content = <file content> │
│ error_log: ""                          │
└────────────────────────────────────────┘
   ↓ (continue until...)
┌────────────────────────────────────────┐
│ messages: [..., AIMessage]             │
│   AIMessage.content = "Final Answer:   │
│     # Project README\n..."             │
│ error_log: ""                          │
└────────────────────────────────────────┘
   ↓ (END)

Final State Extracted and Displayed
```

---

## Configuration and Extensibility

### Environment Variables

- **OPENAI_API_KEY** (required): OpenAI API authentication
- **KLARO_RECURSION_LIMIT** (optional, default: 50): Maximum agent iterations
- **LANGSMITH_TRACING** (optional): Enable LangSmith debugging
- **LANGSMITH_API_KEY** (optional): LangSmith authentication
- **LLM_MODEL** (code constant, default: "gpt-4o-mini"): Model selection

### Adding New Tools

To add a custom tool:

1. **Define function in tools.py:**
   ```python
   def my_new_tool(parameter: str) -> str:
       """Clear description of what this tool does.

       Args:
           parameter: Description of parameter

       Returns:
           Description of return value
       """
       # Implementation
       return result
   ```

2. **Register in main.py:**
   ```python
   from tools import my_new_tool

   tools = [
       Tool(name="my_new_tool", func=my_new_tool, description=my_new_tool.__doc__),
       # ... other tools
   ]
   ```

3. **Update system prompt (prompts.py):**
   ```python
   SYSTEM_PROMPT = """
   ...
   Available Tools:
   - my_new_tool(parameter: str): <description from docstring>
   ...
   """
   ```

4. **Tool automatically available to agent**

### Modifying Agent Behavior

**Change Model:**
```python
# main.py:78
LLM_MODEL = "gpt-4o"  # or "claude-3-5-sonnet"
```

**Adjust Recursion Limit:**
```bash
export KLARO_RECURSION_LIMIT=100
```

**Modify Style Guide:**
```python
# main.py:327-333
DEFAULT_GUIDE_CONTENT = """
Your custom style guide here...
"""
```

**Customize Prompts:**
Edit `prompts.py:59-79` to change agent instructions, tool usage order, or output format requirements.

---

## Performance Considerations

**Context Window Management:**
- Agent uses incremental exploration (not bulk loading)
- Prevents context overflow on large codebases
- Tools return focused results (file trees, individual files)

**API Call Optimization:**
- Temperature=0.2 reduces non-determinism
- gpt-4o-mini balances cost vs. quality
- RAG embeddings cached on disk (avoids re-embedding)

**Execution Time:**
- Typical run: 10-20 LLM calls (2-5 minutes)
- Recursion limit prevents runaway loops
- Tool execution is fast (local operations except embeddings)

**Cost Estimation:**
- gpt-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Embeddings: ~$0.02 per 1M tokens
- Typical documentation task: $0.05-0.10

---

## Error Handling and Recovery

### Error Detection

**Tool Errors:**
- File not found → Returned as error string
- Syntax errors in code → Returned as error JSON
- RAG initialization failures → Returned as error message

**State Tracking:**
- Errors stored in `state["error_log"]`
- Router checks error_log before routing
- If error exists → route back to run_model

### Recovery Mechanisms

**Automatic Retry:**
```
Tool fails (e.g., file not found)
   ↓
Error logged to state["error_log"]
   ↓
decide_next_step detects error
   ↓
Routes to run_model (not call_tool)
   ↓
LLM sees error in context
   ↓
LLM replans with corrected approach
   ↓
Requests different tool or parameters
```

**Recursion Limit:**
- Prevents infinite loops
- Default: 50 iterations
- Raises exception if exceeded
- User sees error message and partial progress

---

## References

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **ReAct Paper**: https://arxiv.org/abs/2210.03629
- **ChromaDB**: https://docs.trychroma.com/
- **OpenAI Function Calling**: https://platform.openai.com/docs/guides/function-calling

---

**Last Updated**: 2025-10-23
**Klaro Version**: 1.0
**Maintained by**: Klaro Development Team
