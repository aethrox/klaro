# Klaro Architecture: Technical Deep Dive

## Table of Contents
1. [Architectural Evolution](#architectural-evolution)
2. [LangGraph State Machine](#langgraph-state-machine)
3. [AST-Based Code Analysis](#ast-based-code-analysis)
4. [RAG System Architecture](#rag-system-architecture)
5. [Tool System Design](#tool-system-design)
6. [Error Handling & Recovery](#error-handling--recovery)
7. [Future Architectural Enhancements](#future-architectural-enhancements)

---

## Architectural Evolution

Klaro's architecture evolved through 4 distinct development stages, each solving critical limitations discovered in the previous iteration:

### Stage 1: MVP (Minimum Viable Product)
**Architecture**: Simple LangChain Sequential Chain

**Characteristics**:
- Predefined, linear execution flow
- No autonomous decision-making
- Basic file reading capabilities
- LLM used purely for text generation

**Limitations**:
- Could not adapt to different project structures
- No error recovery
- Inefficient context window usage

### Stage 2: Pure Python ReAct Loop
**Architecture**: Custom Reasoning-and-Acting (ReAct) implementation

**Motivation**: LangChain's unstable import system caused persistent `ImportError` issues

**Key Implementation** (`main.py` - legacy approach):
```python
def parse_action(llm_response: str):
    """Manual parser for extracting tool calls from LLM output."""
    # Extracts "Action: tool_name" and "Action Input: parameters"
    pass

while iteration < max_iterations:
    llm_response = model.invoke(messages)

    if "Final Answer:" in llm_response:
        break

    action, action_input = parse_action(llm_response)
    observation = execute_tool(action, action_input)

    messages.append(f"Observation: {observation}")
```

**Achievements**:
- Full autonomy: Agent decides which tools to use
- AST-based code analysis integrated (`tools.py:analyze_code`)
- Stable execution (no dependency issues)

**Limitations**:
- **Stateless**: No memory between iterations beyond message history
- **Fragile error handling**: Tool failures caused loop termination
- **Manual parsing**: Regex-based action extraction prone to errors

### Stage 3: RAG Integration
**Architecture**: ReAct loop + Vector database (ChromaDB)

**Key Addition**: Quality control through Retrieval-Augmented Generation

**Implementation**:
```python
# tools.py
KLARO_RETRIEVER: VectorStoreRetriever = None

def init_knowledge_base(documents: list[Document]) -> str:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH
    )
    global KLARO_RETRIEVER
    KLARO_RETRIEVER = vectorstore.as_retriever(search_kwargs={"k": 3})
```

**Impact**:
- Consistent documentation formatting
- Adherence to project-specific style guides
- Reduced hallucinations in output

**Limitations**:
- Still relied on fragile ReAct loop
- No structured error recovery

### Stage 4: LangGraph State Machine (Current)
**Architecture**: Stateful graph-based agent orchestration

**Motivation**:
- Eliminate manual action parsing
- Add structured error handling
- Support complex workflows with cycles

**Result**: Production-ready, robust autonomous agent

---

## LangGraph State Machine

### Core Concepts

LangGraph models agent behavior as a **directed graph** where:
- **Nodes** = Computational steps (LLM calls, tool executions)
- **Edges** = Control flow between nodes
- **State** = Persistent memory carried across all nodes

### State Definition

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """Central state object passed through the entire workflow."""

    # Message history: Automatically appends new messages
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]

    # Error tracking for recovery logic
    error_log: str
```

**Key Feature**: The `Annotated` type with reducer function `lambda x, y: x + y` automatically accumulates messages without manual list manipulation.

### Node Architecture

#### 1. `run_model` Node (Agent Reasoning)
```python
def run_model(state: AgentState):
    """Invokes the LLM to process current state and decide next action."""
    response = model.invoke(state["messages"])
    return {"messages": [response], "error_log": ""}
```

**Behavior**:
- Takes full message history from state
- LLM analyzes context and decides: "Should I call a tool? Which one?"
- Returns updated state with LLM's response appended

**Output Types**:
1. **Tool call request**: `response.tool_calls` populated → Routes to `call_tool`
2. **Final answer**: Contains "Final Answer:" → Routes to `END`
3. **Continued reasoning**: Neither of above → Routes back to `run_model`

#### 2. `call_tool` Node (Action Execution)
```python
from langgraph.prebuilt import ToolNode

workflow.add_node("call_tool", ToolNode(tools))
```

**LangGraph Magic**: `ToolNode` is a prebuilt component that:
- Automatically parses `tool_calls` from LLM response
- Invokes the corresponding tool function
- Wraps result in a `ToolMessage`
- Appends `ToolMessage` to state's message history

**Eliminates**: Manual action parsing, input validation, error formatting

### Edge System: Conditional Routing

#### The `decide_next_step` Router
```python
def decide_next_step(state: AgentState):
    """Determines next node based on current state."""
    last_message = state["messages"][-1]

    # Priority 1: Handle errors from tool execution
    if state.get("error_log"):
        return "run_model"  # Give agent another chance to replan

    # Priority 2: Check for task completion
    if last_message.content and "Final Answer" in last_message.content:
        return END  # Terminate workflow

    # Priority 3: Execute tool if LLM requested one
    if last_message.tool_calls:
        return "call_tool"

    # Default: Continue reasoning
    return "run_model"
```

#### Graph Construction
```python
workflow = StateGraph(AgentState)

# Define nodes
workflow.add_node("run_model", run_model)
workflow.add_node("call_tool", ToolNode(tools))

# Set entry point
workflow.set_entry_point("run_model")

# Conditional routing from run_model
workflow.add_conditional_edges(
    "run_model",
    decide_next_step,
    {
        "call_tool": "call_tool",
        END: END,
        "run_model": "run_model"  # Allows loops!
    }
)

# Always return to run_model after tool execution
workflow.add_edge("call_tool", "run_model")

app = workflow.compile()
```

### Execution Flow Example

**Scenario**: Generate README for a Python project

```
┌─────────────────────────────────────────────────┐
│ INITIAL STATE                                   │
│ messages: [HumanMessage("Analyze project...")]  │
│ error_log: ""                                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
         ┌─────────────────┐
         │   run_model     │ ← LLM thinks: "I need to see files"
         └────────┬────────┘
                  │ (tool_calls: [list_files])
                  ↓
         ┌─────────────────┐
         │   call_tool     │ ← Executes list_files()
         └────────┬────────┘
                  │ (ToolMessage: "File tree: ...")
                  ↓
         ┌─────────────────┐
         │   run_model     │ ← LLM: "I see main.py, let me read it"
         └────────┬────────┘
                  │ (tool_calls: [read_file("main.py")])
                  ↓
         ┌─────────────────┐
         │   call_tool     │ ← Executes read_file()
         └────────┬────────┘
                  │ (ToolMessage: "File content: ...")
                  ↓
         ┌─────────────────┐
         │   run_model     │ ← LLM: "I need to analyze this code"
         └────────┬────────┘
                  │ (tool_calls: [analyze_code(...)])
                  ↓
         ┌─────────────────┐
         │   call_tool     │ ← Executes analyze_code()
         └────────┬────────┘
                  │ (ToolMessage: JSON with functions/classes)
                  ↓
         ┌─────────────────┐
         │   run_model     │ ← LLM: "Before writing, need style guide"
         └────────┬────────┘
                  │ (tool_calls: [retrieve_knowledge(...)])
                  ↓
         ┌─────────────────┐
         │   call_tool     │ ← Queries ChromaDB
         └────────┬────────┘
                  │ (ToolMessage: "Style guide: ...")
                  ↓
         ┌─────────────────┐
         │   run_model     │ ← LLM: "I have everything, generating..."
         └────────┬────────┘
                  │ (content: "Final Answer: # README...")
                  ↓
              ┌───────┐
              │  END  │
              └───────┘
```

**Key Observations**:
1. State automatically accumulates all messages
2. Agent can loop as many times as needed
3. No manual parsing of actions
4. Error-tolerant: If tool fails, agent gets another chance

---

## AST-Based Code Analysis

### The Problem with Text-Based Analysis

Traditional documentation tools feed raw code as text to LLMs:

```python
# Sent to LLM as plain text:
def calculate_metrics(user_id, start_date, end_date=None):
    # Complex implementation...
    pass
```

**Issues**:
- LLM may hallucinate parameter types
- May miss default values
- Cannot reliably extract docstrings
- Struggles with nested structures

### Klaro's AST Approach

**Abstract Syntax Tree (AST)**: Python's built-in parser that converts code into a structured tree representation.

#### Implementation (`tools.py:analyze_code`)

```python
import ast
import json

def analyze_code(code_content: str) -> str:
    """
    Parses Python code into AST and extracts structural metadata.
    Returns JSON with functions, classes, parameters, and docstrings.
    """
    tree = ast.parse(code_content)
    components = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Extract function metadata
            components.append({
                "type": "function",
                "name": node.name,
                "parameters": [arg.arg for arg in node.args.args],
                "returns": ast.unparse(node.returns) if node.returns else "None",
                "docstring": _extract_docstring(node),
                "lineno": node.lineno
            })

        elif isinstance(node, ast.ClassDef):
            # Extract class and method metadata
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        "name": item.name,
                        "parameters": [arg.arg for arg in item.args.args],
                        "returns": ast.unparse(item.returns) if item.returns else "None",
                        "docstring": _extract_docstring(item)
                    })

            components.append({
                "type": "class",
                "name": node.name,
                "docstring": _extract_docstring(node),
                "methods": methods,
                "lineno": node.lineno
            })

    return json.dumps({"components": components}, indent=2)
```

#### Example Transformation

**Input Code**:
```python
class UserManager:
    """Handles user authentication and session management."""

    def authenticate(self, username: str, password: str) -> bool:
        """Verifies user credentials."""
        # Implementation...
        return True

    def create_session(self, user_id: int) -> str:
        """Creates a new user session and returns token."""
        # Implementation...
        return "token"
```

**AST Output** (JSON sent to LLM):
```json
{
  "components": [
    {
      "type": "class",
      "name": "UserManager",
      "docstring": "Handles user authentication and session management.",
      "methods": [
        {
          "name": "authenticate",
          "parameters": ["self", "username", "password"],
          "returns": "bool",
          "docstring": "Verifies user credentials."
        },
        {
          "name": "create_session",
          "parameters": ["self", "user_id"],
          "returns": "str",
          "docstring": "Creates a new user session and returns token."
        }
      ],
      "lineno": 1
    }
  ]
}
```

**Benefits**:
- LLM receives structured, unambiguous data
- No guessing about parameter types or return values
- Preserves original docstrings for semantic understanding
- Line numbers enable precise documentation references

---

## RAG System Architecture

### Purpose

Ensure generated documentation adheres to project-specific style guidelines without retraining the LLM.

### Components

#### 1. Vector Database (ChromaDB)
- **Storage**: Local directory (`./klaro_db`)
- **Purpose**: Stores embedded chunks of style guides
- **Persistence**: Database survives across runs

#### 2. Embeddings (OpenAI text-embedding-3-small)
- **Model**: `text-embedding-3-small` (1536 dimensions)
- **Cost**: ~$0.02 per 1M tokens (very cheap)
- **Purpose**: Convert text into semantic vectors for similarity search

#### 3. Text Splitter
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Maximum characters per chunk
    chunk_overlap=200     # Overlap to preserve context at boundaries
)
```

### Initialization Flow

```python
# main.py - Executed at agent startup
DEFAULT_GUIDE_CONTENT = """
# Klaro Project Documentation Style Guide:
1. **Heading Structure:** Use # and ##.
2. **Sections:** Include `# Project Name`, `## Setup`, `## Usage`, `## Components`.
3. **Tone:** Technical, professional, clear. Code examples use triple backticks.
"""

documents = [
    Document(
        page_content=DEFAULT_GUIDE_CONTENT,
        metadata={"source": "Klaro_Style_Guide"}
    )
]

# Initialize vector store
init_knowledge_base(documents)
```

**Behind the Scenes**:
1. Text splitter breaks guide into 1000-character chunks
2. Each chunk embedded using OpenAI API
3. Vectors stored in ChromaDB with metadata
4. Global `KLARO_RETRIEVER` object created for queries

### Retrieval Flow

```python
def retrieve_knowledge(query: str) -> str:
    """Agent calls this tool to fetch relevant style guide sections."""
    docs = KLARO_RETRIEVER.invoke(query)  # Returns top 3 most similar chunks

    result_texts = [
        f"Source {i+1}: {doc.page_content}"
        for i, doc in enumerate(docs)
    ]

    return "Retrieved Information:\n" + "\n---\n".join(result_texts)
```

**Agent Workflow**:
1. Agent analyzes code and gathers information
2. Before generating final README, calls: `retrieve_knowledge("README formatting guidelines")`
3. ChromaDB performs similarity search on embedded query
4. Returns top 3 most relevant style guide chunks
5. LLM uses retrieved guidelines to format output

### Why It's Mandatory

System prompt explicitly enforces RAG usage (`prompts.py`):

```
STEP 4 (CRITICAL - NEVER SKIP):
Before writing the Final Answer, you MUST use the 'retrieve_knowledge' tool with a query like
"README formatting standards" or "documentation style guide".
```

**Enforcement Mechanism**: Agent workflow is designed such that prematurely outputting "Final Answer" without `retrieve_knowledge` results in incomplete documentation.

---

## Tool System Design

### Philosophy: Agent-Centric Design

Tools are not monolithic "analyze entire project" functions. Instead, they're fine-grained capabilities the agent composes:

| Tool | Granularity | Agent's Thought Process |
|------|-------------|------------------------|
| `list_files` | Single directory | "What files exist?" |
| `read_file` | Single file | "I need to see this specific file" |
| `analyze_code` | Code string → JSON | "Parse this code's structure" |
| `web_search` | Single query | "What is this library?" |
| `retrieve_knowledge` | Single query | "What's the style guide?" |

### Tool Implementation Pattern

All tools follow LangChain's tool interface:

```python
from langchain_core.tools import Tool

tools = [
    Tool(
        name="list_files",
        func=list_files,              # Plain Python function
        description=list_files.__doc__  # Docstring becomes tool description
    ),
    # ... other tools
]

# Bind tools to LLM
model = llm.bind_tools(tools)
```

**LLM Tool Calling**: Model receives tool descriptions and decides when to invoke them by outputting structured `tool_calls` in its response.

### Key Tool: `list_files` with `.gitignore` Support

```python
def list_files(directory: str = '.') -> str:
    """Lists files in tree structure, respecting .gitignore patterns."""

    for root, dirs, files in os.walk(directory):
        # In-place filtering of directories to skip
        i = 0
        while i < len(dirs):
            relative_dir = os.path.relpath(os.path.join(root, dirs[i]), abs_dir)
            if is_ignored(relative_dir):  # Checks against IGNORE_PATTERNS
                del dirs[i]
            else:
                i += 1

        # Output files not matching ignore patterns
        for file in sorted(files):
            if not is_ignored(file):
                output_lines.append(f"{indent}├── {file}")
```

**Critical Feature**: Avoids exposing `.env`, `node_modules`, `__pycache__` to agent, reducing noise and context window usage.

---

## Error Handling & Recovery

### Traditional Agent Problem

ReAct agents terminate on tool errors:
```python
# Old approach (Stage 2)
try:
    observation = execute_tool(action, action_input)
except Exception as e:
    print(f"Error: {e}")
    break  # Agent stops, task fails
```

### LangGraph Solution

Errors become just another message in the conversation:

```python
def decide_next_step(state: AgentState):
    if state.get("error_log"):
        # Error occurred, but don't terminate - give agent another chance
        return "run_model"
```

**Workflow**:
1. Tool fails (e.g., file not found)
2. `ToolMessage` with error content appended to state
3. `decide_next_step` routes back to `run_model`
4. LLM sees error message and adjusts strategy:
   - "File not found? Let me list files first."
   - "Parse error? Let me try reading a different file."

### Recursion Limit Safety

```python
RECURSION_LIMIT = int(os.getenv("KLARO_RECURSION_LIMIT", "50"))

final_state = app.invoke(inputs, {"recursion_limit": RECURSION_LIMIT})
```

Prevents infinite loops while allowing up to 50 agent steps (sufficient for most projects).

---

## Future Architectural Enhancements

### 1. Smart Model Steering

**Current Limitation**: Single model for all tasks

**Proposed Architecture**:
```python
class DualModelState(TypedDict):
    messages: Sequence[BaseMessage]
    current_model: str  # "cheap" or "expensive"
    task_complexity: str  # "simple" or "complex"

def run_model_smart(state: DualModelState):
    """Dynamically selects model based on task complexity."""

    if state["task_complexity"] == "simple":
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    else:
        model = ChatOpenAI(model="gpt-4o", temperature=0.2)

    response = model.invoke(state["messages"])
    return {"messages": [response]}

def classify_task_complexity(state: DualModelState):
    """Router that determines task complexity."""
    last_message = state["messages"][-1]

    # Simple tasks: file operations, basic queries
    if any(keyword in last_message.content for keyword in ["list", "read", "find"]):
        return {"task_complexity": "simple"}

    # Complex tasks: analysis, generation
    elif any(keyword in last_message.content for keyword in ["analyze", "generate", "explain"]):
        return {"task_complexity": "complex"}
```

**Benefits**:
- 60-70% cost reduction
- Maintains quality for complex tasks
- Faster execution for simple operations

### 2. Multi-Language AST Support

**Architecture**:
```python
class LanguageAnalyzer(ABC):
    @abstractmethod
    def analyze(self, code: str) -> dict:
        pass

class PythonAnalyzer(LanguageAnalyzer):
    def analyze(self, code: str) -> dict:
        tree = ast.parse(code)
        # Current implementation
        return extract_components(tree)

class JavaScriptAnalyzer(LanguageAnalyzer):
    def analyze(self, code: str) -> dict:
        import esprima
        tree = esprima.parseScript(code)
        # Convert to Klaro's unified JSON format
        return extract_components(tree)

def analyze_code(code_content: str, language: str = "python") -> str:
    analyzers = {
        "python": PythonAnalyzer(),
        "javascript": JavaScriptAnalyzer(),
        # ... more languages
    }

    analyzer = analyzers.get(language)
    return json.dumps(analyzer.analyze(code_content))
```

### 3. Streaming Output

**Current**: Agent prints final output after completion

**Proposed**: Stream partial results as they're generated

```python
async def run_klaro_streaming(project_path: str):
    async for event in app.astream(inputs):
        if "messages" in event:
            last_message = event["messages"][-1]
            if last_message.content:
                print(last_message.content, flush=True)  # Live updates
```

**Benefits**:
- Better user experience (see progress in real-time)
- Faster perceived performance
- Ability to cancel long-running tasks

---

## Summary

Klaro's architecture represents a mature, production-ready approach to autonomous documentation generation:

1. **LangGraph State Machine**: Robust, stateful orchestration with error recovery
2. **AST Analysis**: Structured, accurate code understanding
3. **RAG System**: Consistent, high-quality output enforcing style guides
4. **Tool Composition**: Fine-grained capabilities for agent autonomy
5. **Error Tolerance**: Graceful handling of failures with automatic retry logic

The architecture is designed for **extensibility** (easy to add new tools/languages), **reliability** (stateful error recovery), and **quality** (RAG-enforced standards).
