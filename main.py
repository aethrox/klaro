"""
Klaro LangGraph Agent - Main Orchestration Module

This module implements the core LangGraph-based autonomous documentation agent for the Klaro project.
It orchestrates the agent's workflow using a state machine architecture that enables:
- Autonomous decision-making through ReAct (Reasoning and Acting) loop
- Dynamic tool execution for codebase exploration and analysis
- RAG-enhanced documentation generation with style guide compliance
- Robust error handling and state management

Architecture Overview:
    The agent operates as a LangGraph StateGraph with three main components:

    1. **State Management (AgentState)**:
       - Maintains conversation history (messages)
       - Tracks execution errors (error_log)
       - Uses LangChain's message reducer for append-only history

    2. **Nodes**:
       - run_model: Invokes the LLM with current state
       - call_tool: Executes tools requested by the LLM (via ToolNode)

    3. **Conditional Routing (decide_next_step)**:
       - Checks for errors -> loops back to run_model
       - Detects "Final Answer" -> terminates execution (END)
       - Detects tool calls -> routes to call_tool
       - Otherwise -> continues to run_model for next thought

    The workflow ensures the agent follows a complete cycle:
    run_model -> decide_next_step -> call_tool -> run_model (repeat until Final Answer)

Available Tools:
    - list_files: Explores project directory structure with .gitignore filtering
    - read_file: Reads file contents with UTF-8 encoding
    - analyze_code: AST-based Python code analysis (extracts classes, functions, docstrings)
    - web_search: External information gathering (currently simulated)
    - retrieve_knowledge: RAG retrieval from ChromaDB vector store

Environment Variables:
    - OPENAI_API_KEY (required): OpenAI API key for LLM and embeddings
    - KLARO_RECURSION_LIMIT (optional): Maximum agent iterations, default 50
    - LANGSMITH_* (optional): LangSmith tracing configuration for debugging

Usage Example:
    >>> python main.py
    # Runs agent on current directory (project_path=".")
    # Analyzes codebase and generates README.md documentation

Technical Notes:
    - Default model: gpt-4o (change via LLM_MODEL constant)
    - RAG knowledge base initialized with default style guide at startup
    - System prompt emphasizes tool usage order: list_files -> read_file -> analyze_code -> retrieve_knowledge
    - Final output format must be: "Final Answer: [MARKDOWN_CONTENT]"
"""

import os
import threading
import time
from datetime import datetime
from typing import TypedDict, Annotated, Sequence

# LangGraph and LangChain Imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_core.documents import Document

from dotenv import load_dotenv
load_dotenv()

# LangSmith tracing support
try:
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False

from prompts import SYSTEM_PROMPT
from tools import (
    list_files, read_file, analyze_code, web_search,
    init_knowledge_base, retrieve_knowledge,
    analyze_project_size, select_model_by_project_size
)

# --- 1. Configuration ---
# Model Selection Thresholds: Configure project size-based model selection
# These thresholds determine which LLM model to use based on project complexity
MODEL_SELECTION_THRESHOLDS = {
    'small': {
        'max_lines': 10000,
        'model': os.getenv('KLARO_SMALL_MODEL', 'gpt-4o-mini'),
        'description': 'Fast and cost-effective for small projects'
    },
    'medium': {
        'max_lines': 100000,
        'model': os.getenv('KLARO_MEDIUM_MODEL', 'gpt-4o'),
        'description': 'Balanced performance for medium projects'
    },
    'large': {
        'max_lines': float('inf'),
        'model': os.getenv('KLARO_LARGE_MODEL', 'gpt-4-turbo'),
        'description': 'Maximum capability for large projects'
    }
}

# Default Model: Used as fallback if auto-selection is disabled
# Can be overridden via KLARO_DEFAULT_MODEL environment variable
LLM_MODEL = os.getenv('KLARO_DEFAULT_MODEL', "gpt-4o")

# Recursion Limit: Maximum number of agent iterations before forced termination
# Prevents infinite loops while allowing thorough analysis (default: 50)
RECURSION_LIMIT = int(os.getenv("KLARO_RECURSION_LIMIT", "50"))

# Timeout Configuration: Prevents indefinite hanging during execution
# LLM_TIMEOUT: Maximum seconds to wait for LLM response (default: 120s)
# EXECUTION_TIMEOUT: Maximum seconds for entire agent execution (default: 600s = 10 min)
# TOOL_TIMEOUT: Maximum seconds for individual tool execution (default: 60s)
LLM_TIMEOUT = int(os.getenv("KLARO_LLM_TIMEOUT", "120"))
EXECUTION_TIMEOUT = int(os.getenv("KLARO_EXECUTION_TIMEOUT", "600"))
TOOL_TIMEOUT = int(os.getenv("KLARO_TOOL_TIMEOUT", "60"))

# Debug Mode: Enable verbose logging to diagnose stalling issues
# Set KLARO_DEBUG=true to see detailed progress messages
DEBUG_MODE = os.getenv("KLARO_DEBUG", "false").lower() == "true"

# Auto Model Selection: Enable/disable automatic model selection based on project size
# Set KLARO_AUTO_MODEL_SELECTION=false to use fixed LLM_MODEL
AUTO_MODEL_SELECTION = os.getenv('KLARO_AUTO_MODEL_SELECTION', 'true').lower() == 'true'

# --- 2. Tool Setup (LLM Binding) ---

# Manually wrap the plain Python functions from tools.py into LangChain Tool objects.
# The docstrings from each function automatically provide the description for the LLM's Tool Calling mechanism.
# This enables the LLM to understand when and how to use each tool.
tools = [
    Tool(name="list_files", func=list_files, description=list_files.__doc__),
    Tool(name="read_file", func=read_file, description=read_file.__doc__),
    Tool(name="analyze_code", func=analyze_code, description=analyze_code.__doc__),
    Tool(name="web_search", func=web_search, description=web_search.__doc__),
    Tool(name="retrieve_knowledge", func=retrieve_knowledge, description=retrieve_knowledge.__doc__),
]

# --- 3. LangGraph State Definition ---

class AgentState(TypedDict):
    """Defines the state carried and updated across LangGraph execution steps.

    This TypedDict serves as the agent's memory, maintaining conversation history
    and error tracking throughout the workflow. State is passed to each node and
    updated incrementally using reducer functions.

    Attributes:
        messages (Annotated[Sequence[BaseMessage], lambda x, y: x + y]):
            Conversation history including HumanMessage, AIMessage, and ToolMessage.
            The lambda reducer (x + y) implements append-only behavior: new messages
            are concatenated to existing history rather than replacing it.
            This preserves the complete thought -> action -> observation chain.

        error_log (str): Tracks execution errors from tool calls or LLM invocations.
            Used by decide_next_step to detect failures and route back to run_model
            for replanning. Cleared after each successful run_model invocation.

    Example State Evolution:
        Initial:
        {
            "messages": [HumanMessage(content="Create README for project X")],
            "error_log": ""
        }

        After LLM responds with tool call:
        {
            "messages": [
                HumanMessage(...),
                AIMessage(content="", tool_calls=[{name: "list_files", args: {...}}])
            ],
            "error_log": ""
        }

        After tool execution:
        {
            "messages": [
                HumanMessage(...),
                AIMessage(...),
                ToolMessage(content="/ project/\n├── main.py", tool_call_id="...")
            ],
            "error_log": ""
        }
    """
    # Conversation history: Appends new messages to the end (Reducer logic).
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    # Tracks errors from tool execution for retry/replan logic.
    error_log: str 

# --- 4. LangGraph Nodes ---

def debug_log(message: str):
    """Logs debug messages with timestamp when DEBUG_MODE is enabled.

    Args:
        message (str): Debug message to log
    """
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[DEBUG {timestamp}] {message}")


def create_model(selected_model: str, temperature: float = 0.2):
    """Creates and configures an LLM instance with tool bindings and timeout.

    Args:
        selected_model (str): OpenAI model name (e.g., 'gpt-4o', 'gpt-4o-mini')
        temperature (float): Sampling temperature for model outputs

    Returns:
        ChatOpenAI: Configured LLM instance bound with tools

    Technical Notes:
        - Sets request_timeout to LLM_TIMEOUT (default: 120s)
        - Sets max_retries to 2 (prevents infinite retry loops)
        - Binds all tools for LLM function calling
    """
    llm = ChatOpenAI(
        model=selected_model,
        temperature=temperature,
        request_timeout=LLM_TIMEOUT,  # Prevent indefinite hanging on API calls
        max_retries=2  # Limit retry attempts to avoid infinite loops
    )
    debug_log(f"Created LLM model: {selected_model} with timeout={LLM_TIMEOUT}s")
    return llm.bind_tools(tools)


# Global model variable (will be set in run_klaro_langgraph)
model = None


def run_model(state: AgentState):
    """LangGraph node that invokes the LLM for reasoning and decision-making.

    This is the agent's "thinking" step in the ReAct loop. It sends the complete
    conversation history (including previous thoughts, tool calls, and tool results)
    to the LLM and receives the next action decision.

    The LLM can respond with:
    1. Tool calls: Requests to execute specific tools (e.g., list_files, analyze_code)
    2. Reasoning text: Intermediate thoughts about what to do next
    3. Final answer: Documentation output when task is complete

    Args:
        state (AgentState): Current agent state containing message history and error log.
            Only the "messages" field is read; error_log is cleared in the return.

    Returns:
        dict: Partial state update with two keys:
            - "messages": List containing single AIMessage with LLM response
                (includes tool_calls if LLM wants to use tools)
            - "error_log": Empty string (clears any previous errors after replanning)

    Example Flow:
        Input state["messages"]: [
            HumanMessage("Analyze project"),
            ToolMessage("/ project/\n├── main.py")
        ]

        LLM processes history and decides: "I should read main.py"

        Returns: {
            "messages": [AIMessage(
                content="",
                tool_calls=[{name: "read_file", args: {"file_path": "main.py"}}]
            )],
            "error_log": ""
        }

    Technical Notes:
        - Uses model.invoke() (not stream) for synchronous execution
        - model is the LLM bound with tools (via bind_tools)
        - Return dict is merged with existing state (messages appended via reducer)
    """
    # Progress logging
    message_count = len(state["messages"])
    debug_log(f"▶ Entering run_model (iteration {message_count})")

    # Send the entire message history to the LLM.
    try:
        debug_log(f"  → Invoking LLM with {message_count} messages in history")
        response = model.invoke(state["messages"])

        # Log response details
        if response.tool_calls:
            tool_names = [tc.get("name", "unknown") for tc in response.tool_calls]
            debug_log(f"  ← LLM responded with tool calls: {tool_names}")
        elif response.content:
            content_preview = response.content[:100].replace("\n", " ")
            debug_log(f"  ← LLM responded with content: {content_preview}...")
            if "Final Answer" in response.content:
                debug_log(f"  ✓ Final Answer detected - task complete")

        # Append the LLM's response and clear any previous error.
        return {"messages": [response], "error_log": ""}
    except Exception as e:
        debug_log(f"  ✗ LLM invocation failed: {str(e)}")
        raise 

# --- 5. LangGraph Router (Edges) ---

def decide_next_step(state: AgentState):
    """Conditional routing function that determines the next node in the LangGraph workflow.

    This is the decision-making "router" that analyzes the current state and decides
    where the graph should go next. It implements the conditional logic that enables:
    - Error recovery (loop back to LLM for replanning)
    - Task completion detection (terminate when "Final Answer" appears)
    - Tool execution routing (call tools when LLM requests them)
    - Continuous reasoning (keep thinking if no action decided yet)

    Args:
        state (AgentState): Current agent state with complete message history and error log.

    Returns:
        str: Name of the next node to execute:
            - "run_model": Route to LLM for (re)planning
                * Used when: errors exist, or LLM hasn't decided on action yet
            - "call_tool": Route to tool execution
                * Used when: LLM's last message contains tool_calls
            - END: Terminate graph execution
                * Used when: "Final Answer" detected in LLM's last message content

    Decision Logic (evaluated in order):
        1. **Error Check**: If error_log is non-empty, return "run_model"
           Allows LLM to see the error and replan with different approach.

        2. **Completion Check**: If last message contains "Final Answer", return END
           Agent has gathered enough information and produced documentation.

        3. **Tool Call Check**: If last message has tool_calls, return "call_tool"
           LLM has decided which tool to execute and with what parameters.

        4. **Default**: If none above, return "run_model"
           LLM is still reasoning; let it continue thinking.

    Example Scenarios:
        Scenario 1 - Tool Execution:
        >>> state = {"messages": [AIMessage(tool_calls=[...])], "error_log": ""}
        >>> decide_next_step(state)
        "call_tool"

        Scenario 2 - Task Complete:
        >>> state = {"messages": [AIMessage(content="Final Answer: # README\\n...")], "error_log": ""}
        >>> decide_next_step(state)
        <END marker>

        Scenario 3 - Error Recovery:
        >>> state = {"messages": [...], "error_log": "Tool failed: file not found"}
        >>> decide_next_step(state)
        "run_model"

    Technical Notes:
        - This function is used in workflow.add_conditional_edges()
        - The return string must match node names defined in the graph
        - END is a special LangGraph constant that terminates execution
    """
    # Get the most recent message from the conversation history
    # This is either an AIMessage (LLM response) or ToolMessage (tool result)
    last_message = state["messages"][-1]
    message_count = len(state["messages"])

    debug_log(f"◆ Routing decision (message count: {message_count})")

    # --- SAFETY CHECK: Prevent infinite loops ---
    # If message count approaches recursion limit, force termination
    if message_count >= RECURSION_LIMIT * 0.95:
        debug_log(f"  ⚠ Approaching recursion limit ({message_count}/{RECURSION_LIMIT})")
        if message_count >= RECURSION_LIMIT:
            debug_log(f"  ✗ Recursion limit exceeded - forcing termination")
            return END

    # --- ROUTING DECISION TREE (evaluated in priority order) ---

    # 1. ERROR RECOVERY: Check for errors from previous tool execution
    # The error_log is populated by failed tool calls or LLM invocation errors
    if state.get("error_log"):
         debug_log(f"  → Routing to run_model (error recovery)")
         # Route back to the model so it can see the error and try a different approach
         # The LLM will receive the error in the next run_model invocation
         return "run_model"

    # 2. COMPLETION CHECK: Detect if the agent has finished the task
    # Primary: Check for explicit "Final Answer" marker
    # Secondary: Detect if LLM produced substantial markdown documentation without the marker
    if last_message.content:
        content = last_message.content
        content_lower = content.lower()

        # Primary check: Explicit "Final Answer" marker (case-insensitive)
        if "final answer" in content_lower:
            debug_log(f"  → Routing to END (Final Answer detected)")
            return END

        # Secondary check: Detect if LLM forgot "Final Answer:" but produced README
        # Look for common README patterns: markdown headers + substantial content
        has_markdown_header = content.startswith("#") or "\n#" in content
        has_setup_section = "## setup" in content_lower or "## installation" in content_lower
        is_substantial = len(content) > 200  # More than 200 chars suggests complete output

        if has_markdown_header and (has_setup_section or is_substantial):
            debug_log(f"  ⚠ Markdown content detected without 'Final Answer:' prefix")
            debug_log(f"  → Routing to END (assuming completion)")
            print("\n⚠️  WARNING: LLM produced README without 'Final Answer:' prefix")
            print("   Treating as completed task to prevent infinite loop")
            return END

    # 3. TOOL EXECUTION: Check if LLM wants to call a tool
    # When LLM decides to use a tool, it populates last_message.tool_calls
    # tool_calls is a list of dictionaries with: {name: "tool_name", args: {...}}
    if last_message.tool_calls:
        tool_count = len(last_message.tool_calls)
        debug_log(f"  → Routing to call_tool ({tool_count} tool(s) to execute)")
        # Route to call_tool node, which will execute the requested tools
        # After execution, ToolMessages will be appended to conversation history
        return "call_tool"

    # 4. CONTINUE REASONING: If no action decided yet, keep the ReAct loop going
    # This happens when the LLM outputs a "Thought:" step without taking action
    # Loop back to run_model to let the LLM continue its reasoning process
    debug_log(f"  → Routing to run_model (continue reasoning)")
    return "run_model" 

# --- 6. LangGraph Setup ---

# Initialize the StateGraph with our AgentState schema
# This creates a stateful workflow where each node receives and updates the shared state
# AgentState defines the shape of data that flows through the graph (messages, error_log)
workflow = StateGraph(AgentState)

# --- Add Nodes (the "verbs" - what the graph can do) ---
# Nodes are the processing units of the graph - they take state, transform it, and return updates

# Node 1: run_model - LLM invocation for reasoning and decision-making
# This is the "thinking" node where the AI decides what to do next
workflow.add_node("run_model", run_model)

# Node 2: call_tool - Tool execution handler
# ToolNode is a LangGraph built-in that automatically handles tool execution:
# 1. Parses tool_calls from the last AIMessage (extracts tool names and arguments)
# 2. Executes the requested tools with provided arguments (calls the actual Python functions)
# 3. Returns ToolMessage results to append to conversation history (the "Observation" in ReAct)
workflow.add_node("call_tool", ToolNode(tools))

# --- Set Entry Point (where execution begins) ---
# Entry point defines the first node to execute when app.invoke() is called
# All workflows start at run_model with the initial HumanMessage containing the task
workflow.set_entry_point("run_model")

# --- Add Conditional Edges (dynamic routing based on state) ---
# Conditional edges use a router function to determine the next node at runtime
# This enables the ReAct loop: Thought → Action decision → Tool execution → Observation → repeat

# After run_model executes, decide_next_step() analyzes the state and determines next action
workflow.add_conditional_edges(
    "run_model",  # Source node: evaluate routing after this node completes
    decide_next_step,  # Router function: called with current state, returns next node name
    {
        # Edge mapping: router return value → target node
        # This dictionary defines all possible transitions from run_model

        "call_tool": "call_tool",  # If router returns "call_tool", transition to call_tool node
                                    # (LLM decided to use a tool)

        END: END,  # If router returns END, terminate the graph and return final state
                   # (LLM produced "Final Answer")

        "run_model": "run_model"  # If router returns "run_model", loop back (self-edge)
                                  # (LLM is still thinking, or there was an error to replan)
    }
)

# --- Add Fixed Edge (unconditional transition) ---
# Fixed edges always go to the same target node, regardless of state
# After tool execution completes, ALWAYS return to run_model to process the tool results
# This ensures the LLM sees the "Observation" (ToolMessage) before deciding the next action
# This is critical for the ReAct loop: Action → Observation → Thought
workflow.add_edge("call_tool", "run_model")

# --- Graph compilation is now done in run_klaro_langgraph after model selection ---
# This allows dynamic model selection based on project size

# --- 7. Execution Function ---

# RAG Style Guide Content (Copied from tools.py)
DEFAULT_GUIDE_CONTENT = """
# Klaro Project Documentation Style Guide: 
All README.md documents produced using this guide must adhere to the following standards:
1.  **Heading Structure:** Headings must start with # and ##.
2.  **Sections:** Every README must include the following sections: `# Project Name`, `## Setup`, `## Usage`, `## Components`.
3.  **Tone and Language:** The tone must be technical, professional, and clear. Code examples must always be formatted with triple backticks (```python).
"""

class TimeoutException(Exception):
    """Exception raised when execution timeout is exceeded."""
    pass


def finalize_langsmith_trace():
    """Ensures LangSmith trace is properly finalized and flushed.

    LangSmith uses background threads to send trace data to the server.
    When execution completes (especially in daemon threads), these background
    operations might not complete before the thread exits, leaving traces in
    "pending" state.

    This function:
    1. Checks if LangSmith tracing is enabled
    2. Waits briefly for background operations to complete
    3. Ensures trace data is flushed to the server

    Technical Notes:
        - Only executes if LANGSMITH_TRACING=true
        - Uses a small delay (1 second) to allow async operations to complete
        - Safe to call even if no trace is active
    """
    if not os.getenv("LANGSMITH_TRACING", "").lower() == "true":
        return

    if not LANGSMITH_AVAILABLE:
        debug_log("⚠ LangSmith tracing enabled but langsmith package not available")
        return

    try:
        debug_log("🔄 Finalizing LangSmith trace...")
        # Give LangSmith's background threads time to flush data
        # LangSmith uses async operations to send trace data to the server
        # A short delay ensures these operations complete before thread exit
        time.sleep(1.0)
        debug_log("✓ LangSmith trace finalized")
    except Exception as e:
        debug_log(f"⚠ Warning: Failed to finalize LangSmith trace: {e}")


def run_with_timeout(func, args, kwargs, timeout_seconds):
    """Executes a function with a timeout (Windows-compatible using threading).

    Args:
        func: Function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        timeout_seconds: Maximum execution time in seconds

    Returns:
        Function result if successful

    Raises:
        TimeoutException: If execution exceeds timeout_seconds

    Technical Notes:
        - After successful execution, calls finalize_langsmith_trace() to ensure
          LangSmith tracing data is properly flushed to the server
        - This prevents traces from showing as "pending" in LangSmith UI
    """
    result = [None]
    exception = [None]

    def target():
        try:
            result[0] = func(*args, **kwargs)
            # Finalize LangSmith trace after successful execution
            # This ensures trace data is flushed before thread exits
            finalize_langsmith_trace()
        except Exception as e:
            exception[0] = e
            # Also finalize on error to close the trace properly
            finalize_langsmith_trace()

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)

    if thread.is_alive():
        # Thread is still running - timeout occurred
        debug_log(f"✗ Execution timeout ({timeout_seconds}s) exceeded")
        raise TimeoutException(f"Execution exceeded timeout of {timeout_seconds} seconds")

    if exception[0]:
        raise exception[0]

    return result[0]


def run_klaro_langgraph(project_path: str = "."):
    """Executes the Klaro autonomous documentation agent on the specified project.

    This is the main entry point that:
    1. Analyzes project size and selects optimal LLM model
    2. Initializes the RAG knowledge base with style guide
    3. Configures the agent task (README generation)
    4. Runs the LangGraph workflow until completion or recursion limit
    5. Extracts and displays the final documentation output

    The agent autonomously navigates the codebase using ReAct loop:
    - Explores file structure with list_files
    - Reads critical files with read_file
    - Analyzes code structure with analyze_code (AST)
    - Retrieves style guidelines with retrieve_knowledge (RAG)
    - Produces final markdown documentation

    Args:
        project_path (str, optional): Path to the project directory to analyze.
            Can be relative or absolute. Defaults to "." (current directory).

    Returns:
        None: Prints execution progress and final documentation to stdout.
            Does not return a value; designed for CLI usage.

    Raises:
        Prints error message (doesn't raise exceptions) if:
        - LangGraph execution fails (network issues, API errors)
        - Recursion limit exceeded
        - Tool execution errors
        - Execution timeout exceeded

    Execution Flow:
        1. **Project Analysis**: Analyzes project size and complexity
           Selects optimal model based on total lines of code

        2. **RAG Initialization**: Creates ChromaDB with DEFAULT_GUIDE_CONTENT
           Prints: "📢 Initializing RAG Knowledge Base..."

        3. **Task Setup**: Combines SYSTEM_PROMPT with user task instruction
           Task includes explicit tool usage order and retrieve_knowledge requirement

        4. **Graph Execution**: Runs app.invoke() with initial state
           Max iterations controlled by RECURSION_LIMIT env var
           Max time controlled by EXECUTION_TIMEOUT env var

        5. **Output Extraction**: Extracts last message content, strips "Final Answer:" prefix
           Prints: "✅ TASK SUCCESS: LangGraph Agent Finished."

        6. **Error Handling**: Catches and displays exceptions
           Prints: "❌ ERROR: LangGraph execution failed."

    Example Usage:
        >>> run_klaro_langgraph("./my_project")
        --- Launching Klaro LangGraph Agent ---
        📊 Analyzing project size...
           -> Project metrics: 4,523 lines across 15 files
           -> Complexity: small
           -> Selected model: gpt-4o-mini
        📢 Initializing RAG Knowledge Base...
           -> Setup Result: Knowledge base (ChromaDB) successfully initialized at ./klaro_db. 3 chunks indexed.
        ==================================================
        ✅ TASK SUCCESS: LangGraph Agent Finished.
        ====================================
        # My Project

        This project is a Python application that...

        ## Setup
        ...

    Technical Notes:
        - Model selection can be disabled via KLARO_AUTO_MODEL_SELECTION=false
        - DEFAULT_GUIDE_CONTENT is embedded in this file (not imported from tools.py)
        - System prompt and task are combined into single HumanMessage
        - Final output stripped of "Final Answer:" prefix for clean markdown
        - Recursion limit prevents infinite loops (default 50 iterations)
        - Execution timeout prevents indefinite hanging (default 600s)
    """
    global model  # Use global model variable for run_model function

    start_time = datetime.now()
    print("--- Launching Klaro LangGraph Agent ---")
    print(f"🕐 Start time: {start_time.strftime('%H:%M:%S')}")
    print(f"⚙️  Configuration:")
    print(f"   - Recursion limit: {RECURSION_LIMIT}")
    print(f"   - Execution timeout: {EXECUTION_TIMEOUT}s")
    print(f"   - LLM timeout: {LLM_TIMEOUT}s")
    print(f"   - Debug mode: {'enabled' if DEBUG_MODE else 'disabled'}")
    print()

    # --- STEP 1: Project Size Analysis and Model Selection ---
    if AUTO_MODEL_SELECTION:
        print("📊 Analyzing project size...")
        metrics = analyze_project_size(project_path)

        if 'error' in metrics:
            print(f"   ⚠️  Warning: {metrics['error']}")
            print(f"   -> Using default model: {LLM_MODEL}")
            selected_model = LLM_MODEL
        else:
            selected_model = select_model_by_project_size(metrics)
            print(f"   -> Project metrics: {metrics['total_lines']:,} lines across {metrics['total_files']} files")
            print(f"   -> Complexity: {metrics['complexity']}")
            print(f"   -> Selected model: {selected_model}")
    else:
        selected_model = LLM_MODEL
        print(f"📌 Auto model selection disabled. Using: {selected_model}")

    # --- STEP 2: Create model with selected configuration ---
    model = create_model(selected_model, temperature=0.2)

    # --- STEP 3: Compile the workflow graph ---
    # Must be done after model is set, as run_model depends on it
    app = workflow.compile()

    print(f"🚀 Starting agent with model: {selected_model}")

    # --- STEP 4: Knowledge Base Setup (RAG) ---
    print("📢 Initializing RAG Knowledge Base...")
    documents_to_index = [
        Document(page_content=DEFAULT_GUIDE_CONTENT, metadata={"source": "Klaro_Style_Guide"}),
    ]
    
    setup_result = init_knowledge_base(documents_to_index)
    print(f"   -> Setup Result: {setup_result}")

    task_input = (
        f"Please analyze the codebase in '{project_path}' and create a README.md document. "
        "Steps: 1. Explore with 'list_files'. 2. Read critical files with 'read_file' and analyze code with 'analyze_code'. "
        "3. Gather external info with 'web_search'. 4. **You MUST use the 'retrieve_knowledge' tool to fetch the 'README style guidelines' before writing the final answer.**"
    )

    # Prepare the initial state for the graph.
    # The System Prompt and the user's task are combined into the first HumanMessage.
    initial_message_content = f"{SYSTEM_PROMPT}\n\nUSER'S TASK: {task_input}"
    
    inputs = {"messages": [HumanMessage(content=initial_message_content)], "error_log": ""}

    try:
        # Run the LangGraph flow with timeout protection
        debug_log(f"🚀 Starting LangGraph execution (timeout: {EXECUTION_TIMEOUT}s)")

        # Wrap app.invoke with timeout (Windows-compatible)
        final_state = run_with_timeout(
            app.invoke,
            args=(inputs,),
            kwargs={"recursion_limit": RECURSION_LIMIT},
            timeout_seconds=EXECUTION_TIMEOUT
        )

        # Calculate execution time
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()

        # Extract the final message
        final_message = final_state["messages"][-1].content

        print("\n" + "="*50)
        print("✅ TASK SUCCESS: LangGraph Agent Finished.")
        print(f"⏱️  Execution time: {elapsed:.1f}s")
        print(f"📊 Total iterations: {len(final_state['messages']) - 1}")
        print("====================================")

        # Clean the Final Answer format
        if final_message.startswith("Final Answer:"):
             final_message = final_message.replace("Final Answer:", "").strip()

        print(final_message)

    except TimeoutException as e:
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print("\n" + "="*50)
        print("⏱️  TIMEOUT: LangGraph execution exceeded time limit")
        print(f"⏱️  Execution time: {elapsed:.1f}s (limit: {EXECUTION_TIMEOUT}s)")
        print(f"💡 Suggestion: Increase KLARO_EXECUTION_TIMEOUT or check LangSmith trace at:")
        print(f"   https://eu.smith.langchain.com/")
        print("="*50)

    except Exception as e:
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        print("\n" + "="*50)
        print("❌ ERROR: LangGraph execution failed.")
        print(f"⏱️  Execution time: {elapsed:.1f}s")
        print(f"Error Details: {e}")
        print(f"💡 Check LangSmith trace at: https://eu.smith.langchain.com/")
        print("="*50)


if __name__ == "__main__":
    run_klaro_langgraph(project_path=".")