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
    - Default model: gpt-4o-mini (change via LLM_MODEL constant)
    - RAG knowledge base initialized with default style guide at startup
    - System prompt emphasizes tool usage order: list_files -> read_file -> analyze_code -> retrieve_knowledge
    - Final output format must be: "Final Answer: [MARKDOWN_CONTENT]"
"""

import os
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

from prompts import SYSTEM_PROMPT
from tools import list_files, read_file, analyze_code, web_search, init_knowledge_base, retrieve_knowledge 

# --- 1. Configuration ---
# Model Selection: gpt-4o-mini chosen for cost-effectiveness and good performance on documentation tasks
# Can be changed to gpt-4o or claude-3-5-sonnet for more complex analysis
LLM_MODEL = "gpt-4o-mini"

# Recursion Limit: Maximum number of agent iterations before forced termination
# Prevents infinite loops while allowing thorough analysis (default: 50)
RECURSION_LIMIT = int(os.getenv("KLARO_RECURSION_LIMIT", "50"))

# Temperature: 0.2 for more deterministic, consistent outputs
# Lower temperature reduces creativity but improves reliability for documentation
llm = ChatOpenAI(model=LLM_MODEL, temperature=0.2)

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

# Bind the tools to the LLM model to enable Tool Calling functionality.
model = llm.bind_tools(tools)

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
    # Send the entire message history to the LLM.
    response = model.invoke(state["messages"])
    # Append the LLM's response and clear any previous error.
    return {"messages": [response], "error_log": ""} 

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
    last_message = state["messages"][-1]

    # 1. Check for immediate error from a previous tool execution.
    if state.get("error_log"):
         # If an error occurred, route back to the model for replanning.
         return "run_model"

    # 2. Check for Final Answer (Agent has completed the task).
    if last_message.content and "Final Answer" in last_message.content:
        return END  # Terminate the graph.

    # 3. Check for Tool Call (The LLM requesting to use a tool).
    if last_message.tool_calls:
        return "call_tool"

    # 4. If none of the above, loop back to the model for the next thought step.
    return "run_model" 

# --- 6. LangGraph Setup ---

# Initialize the StateGraph with our AgentState schema
# This creates a stateful workflow where each node receives and updates the shared state
workflow = StateGraph(AgentState)

# Add Nodes (the "verbs" - what the graph can do)
# Node 1: run_model - LLM invocation for reasoning and decision-making
workflow.add_node("run_model", run_model)

# Node 2: call_tool - Tool execution handler
# ToolNode is a LangGraph built-in that automatically:
# 1. Parses tool_calls from the last AIMessage
# 2. Executes the requested tools with provided arguments
# 3. Returns ToolMessage results to append to conversation history
workflow.add_node("call_tool", ToolNode(tools))

# Set Entry Point (where execution begins)
# All workflows start at run_model with the initial HumanMessage
workflow.set_entry_point("run_model")

# Add Conditional Edges (the "grammar" - how nodes connect)
# After run_model executes, decide_next_step determines the next node
workflow.add_conditional_edges(
    "run_model",  # Source node: start from here
    decide_next_step,  # Router function: calls this to decide next node
    {
        # Mapping of router return values to target nodes:
        "call_tool": "call_tool",  # If router returns "call_tool", go to call_tool node
        END: END,  # If router returns END, terminate the graph
        "run_model": "run_model"  # If router returns "run_model", loop back (continue thinking)
    }
)

# Add Fixed Edge (unconditional transition)
# After tool execution, ALWAYS return to the model to process the Observation (ToolMessage).
# This ensures the LLM sees tool results before deciding the next action.
workflow.add_edge("call_tool", "run_model")

# Compile the graph into an executable application
# This validates the graph structure and creates the runnable app
app = workflow.compile()

# --- 7. Execution Function ---

# RAG Style Guide Content (Copied from tools.py)
DEFAULT_GUIDE_CONTENT = """
# Klaro Project Documentation Style Guide: 
All README.md documents produced using this guide must adhere to the following standards:
1.  **Heading Structure:** Headings must start with # and ##.
2.  **Sections:** Every README must include the following sections: `# Project Name`, `## Setup`, `## Usage`, `## Components`.
3.  **Tone and Language:** The tone must be technical, professional, and clear. Code examples must always be formatted with triple backticks (```python).
"""

def run_klaro_langgraph(project_path: str = "."):
    """Executes the Klaro autonomous documentation agent on the specified project.

    This is the main entry point that:
    1. Initializes the RAG knowledge base with style guide
    2. Configures the agent task (README generation)
    3. Runs the LangGraph workflow until completion or recursion limit
    4. Extracts and displays the final documentation output

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

    Execution Flow:
        1. **RAG Initialization**: Creates ChromaDB with DEFAULT_GUIDE_CONTENT
           Prints: "📢 Initializing RAG Knowledge Base..."

        2. **Task Setup**: Combines SYSTEM_PROMPT with user task instruction
           Task includes explicit tool usage order and retrieve_knowledge requirement

        3. **Graph Execution**: Runs app.invoke() with initial state
           Max iterations controlled by RECURSION_LIMIT env var

        4. **Output Extraction**: Extracts last message content, strips "Final Answer:" prefix
           Prints: "✅ TASK SUCCESS: LangGraph Agent Finished."

        5. **Error Handling**: Catches and displays exceptions
           Prints: "❌ ERROR: LangGraph execution failed."

    Example Usage:
        >>> run_klaro_langgraph("./my_project")
        --- Launching Klaro LangGraph Agent (Stage 4 - gpt-4o-mini) ---
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
        - DEFAULT_GUIDE_CONTENT is embedded in this file (not imported from tools.py)
        - System prompt and task are combined into single HumanMessage
        - Final output stripped of "Final Answer:" prefix for clean markdown
        - Recursion limit prevents infinite loops (default 50 iterations)
    """
    print(f"--- Launching Klaro LangGraph Agent (Stage 4 - {LLM_MODEL}) ---")
    
    # --- STAGE 3 INTEGRATION: Knowledge Base Setup (RAG) ---
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
        # Run the LangGraph flow
        final_state = app.invoke(inputs, {"recursion_limit": RECURSION_LIMIT}) 
        
        # Extract the final message
        final_message = final_state["messages"][-1].content
        
        print("\n" + "="*50)
        print("✅ TASK SUCCESS: LangGraph Agent Finished.")
        print("====================================")
        
        # Clean the Final Answer format
        if final_message.startswith("Final Answer:"):
             final_message = final_message.replace("Final Answer:", "").strip()
             
        print(final_message)

    except Exception as e:
        print("\n" + "="*50)
        print("❌ ERROR: LangGraph execution failed.")
        print(f"Error Details: {e}")
        print("="*50)


if __name__ == "__main__":
    run_klaro_langgraph(project_path=".")