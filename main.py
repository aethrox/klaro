"""
Klaro LangGraph Agent - Main Execution Module
==============================================

This module implements Klaro's autonomous documentation agent using LangGraph architecture.
Klaro is an AI agent that analyzes codebases and generates comprehensive technical documentation
(README files, API references) with minimal human intervention.

Architecture Overview:
---------------------
Klaro uses a LangGraph state machine to implement a ReAct-style (Reasoning and Acting) agent:

1. **State Management (AgentState):**
   - Tracks conversation history (messages)
   - Maintains error logs for debugging
   - Uses reducers to append messages sequentially

2. **Core Components:**
   - run_model: LLM invocation node that processes agent's thinking step
   - call_tool: Automatic tool execution node via ToolNode
   - decide_next_step: Router that determines next state (tool call, completion, or continue)

3. **Tool Integration:**
   - list_files: Explores codebase structure
   - read_file: Reads file contents
   - analyze_code: AST-based Python code analysis
   - web_search: External information retrieval (simulated)
   - retrieve_knowledge: RAG-based style guide retrieval from ChromaDB

4. **RAG System:**
   - ChromaDB vector database for documentation style guides
   - OpenAI embeddings for semantic search
   - Ensures consistent, professional output format

Environment Variables:
----------------------
- OPENAI_API_KEY (required): OpenAI API key for LLM and embeddings
- KLARO_RECURSION_LIMIT (optional): Maximum agent iterations (default: 50)
- LANGSMITH_TRACING (optional): Enable LangSmith tracing for debugging

Usage:
------
    python main.py

    # Or programmatically:
    from main import run_klaro_langgraph
    run_klaro_langgraph(project_path="./my_project")

For more information, see:
- docs/ARCHITECTURE.md: Detailed architecture documentation
- docs/klaro_tech_docs_guide.md: Technical documentation guide
- docs/tech_design_advanced_agent_langgraph.md: LangGraph design rationale
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
# Model Selection: gpt-4o-mini provides excellent cost/performance balance for most tasks.
# For more complex analysis, consider upgrading to gpt-4o or claude-3-5-sonnet.
LLM_MODEL = "gpt-4o-mini"

# Recursion Limit: Maximum number of agent loop iterations to prevent infinite loops.
# Typical README generation uses 15-30 iterations. Increase if working with large projects.
RECURSION_LIMIT = int(os.getenv("KLARO_RECURSION_LIMIT", "50"))

# Temperature: Low value (0.2) ensures consistent, deterministic output for technical documentation.
llm = ChatOpenAI(model=LLM_MODEL, temperature=0.2) 

# --- 2. Tool Setup (LLM Binding) ---

# Manually wrap the plain Python functions from tools.py into LangChain Tool objects.
# The docstrings provide the description for the LLM's Tool Calling mechanism.
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
    """
    Defines the state carried across LangGraph execution steps.

    This TypedDict serves as the agent's memory, maintaining conversation context
    and error information throughout the documentation generation process.

    Attributes:
        messages (Sequence[BaseMessage]): Conversation history including system prompts,
            user requests, LLM responses, and tool execution results. Uses a reducer
            function (lambda x, y: x + y) to append new messages to existing history.

        error_log (str): Tracks error messages from failed tool executions or LLM issues.
            Cleared after each successful operation. Used by decide_next_step to trigger
            error recovery logic.

    Example:
        >>> state = {
        ...     "messages": [HumanMessage(content="Analyze this project")],
        ...     "error_log": ""
        ... }
    """
    # Conversation history: Appends new messages to the end (Reducer logic).
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    # Placeholder for tracking errors or complex state manipulation.
    error_log: str 

# --- 4. LangGraph Nodes ---

def run_model(state: AgentState):
    """
    Executes the LLM thinking step in the ReAct loop.

    This node represents the "Reasoning" phase where the LLM:
    1. Analyzes current state (conversation history, tool results)
    2. Decides what action to take next (call a tool, provide final answer, or think more)
    3. Generates tool calls or textual responses

    Args:
        state (AgentState): Current agent state containing message history and error log.
            The entire conversation context is passed to the LLM to maintain coherent
            reasoning across multiple steps.

    Returns:
        dict: State update containing:
            - messages (list): New message from LLM (may contain tool_calls)
            - error_log (str): Cleared to empty string after successful execution

    Note:
        The LLM is bound to tools (see `model = llm.bind_tools(tools)` above),
        enabling it to generate structured tool call requests that LangGraph's
        ToolNode can automatically execute.

    Example Flow:
        Input State:  {"messages": [HumanMessage("Analyze project")], "error_log": ""}
        LLM Decision: Calls list_files tool to explore project structure
        Output State: {"messages": [AIMessage(tool_calls=[...])], "error_log": ""}
    """
    # Send the entire message history to the LLM for context-aware reasoning.
    response = model.invoke(state["messages"])
    # Append the LLM's response and clear any previous error.
    return {"messages": [response], "error_log": ""} 

# --- 5. LangGraph Router (Edges) ---

def decide_next_step(state: AgentState):
    """
    Conditional edge router that determines the next node based on agent state.

    This function implements the core decision logic of the ReAct loop, examining
    the LLM's latest output to determine whether to:
    - Execute a tool (Action phase)
    - Return the final answer (Completion)
    - Handle an error (Recovery)
    - Continue thinking (Observation/Reasoning)

    Args:
        state (AgentState): Current agent state with message history and error log.

    Returns:
        str: Name of the next node to execute, or END to terminate:
            - "call_tool": LLM requested tool execution via tool_calls
            - END: Agent completed task (detected "Final Answer" in response)
            - "run_model": Continue thinking (error recovery or next reasoning step)

    Decision Logic:
        1. **Error Recovery**: If error_log is populated, return to run_model
           to let the LLM replan around the failed operation.

        2. **Task Completion**: If LLM's response contains "Final Answer",
           terminate the graph and return results to user.

        3. **Tool Execution**: If LLM generated tool_calls (structured requests
           to use list_files, read_file, etc.), route to call_tool node.

        4. **Continue Reasoning**: If none of the above, loop back to run_model
           for the LLM to continue its thought process.

    Example Routing:
        >>> state = {"messages": [AIMessage(tool_calls=[...])], "error_log": ""}
        >>> decide_next_step(state)
        "call_tool"

        >>> state = {"messages": [AIMessage(content="Final Answer: ...")], "error_log": ""}
        >>> decide_next_step(state)
        END
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
# Build the state machine graph that orchestrates the agent's execution flow.

workflow = StateGraph(AgentState)

# Add Nodes
# --------------------------------------------------
# run_model: The "brain" node where LLM reasoning happens. Analyzes current state
#            and decides next action (tool call or final answer).
workflow.add_node("run_model", run_model)

# call_tool: Automatic tool execution node. ToolNode intercepts tool_calls from
#            the LLM's response and executes the corresponding Python functions,
#            then adds results as ToolMessages to the conversation history.
workflow.add_node("call_tool", ToolNode(tools))

# Set Entry Point
# --------------------------------------------------
# All executions start at run_model, where the LLM receives the initial task.
workflow.set_entry_point("run_model")

# Add Conditional Edges
# --------------------------------------------------
# After run_model executes, decide_next_step determines the next node based on
# the LLM's output. This creates the core ReAct loop:
#   run_model -> [decide] -> call_tool -> run_model -> [decide] -> ... -> END
workflow.add_conditional_edges(
    "run_model",              # Source node
    decide_next_step,         # Router function
    {                         # Mapping: router return value -> target node
        "call_tool": "call_tool",   # Execute tool if LLM requested it
        END: END,                   # Terminate if task complete
        "run_model": "run_model"    # Continue thinking if needed
    }
)

# After tool execution, always return to the model to process the Observation (ToolMessage).
# This closes the ReAct loop: Thought (run_model) -> Action (call_tool) -> Observation (run_model again).
workflow.add_edge("call_tool", "run_model")

# Compile the graph
# --------------------------------------------------
# Compilation validates the graph structure and creates an executable application.
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
    """
    Executes the Klaro autonomous documentation agent on a specified project.

    This is the main entry point for running Klaro. It initializes the RAG knowledge base
    with documentation style guidelines, constructs the agent's initial state, and executes
    the LangGraph workflow to generate comprehensive project documentation.

    Args:
        project_path (str, optional): Absolute or relative path to the project directory
            to analyze. Defaults to "." (current directory).

            Examples:
                - "." : Analyze current directory
                - "../my-project" : Analyze sibling directory
                - "/home/user/projects/app" : Analyze absolute path

    Returns:
        None: Results are printed to stdout. The agent generates and displays:
            - Project overview and technology stack analysis
            - File structure documentation
            - README.md content in Markdown format

    Raises:
        Exception: If LangGraph execution fails (network errors, API issues, recursion limit).
            Error details are printed to stdout.

    Workflow:
        1. Initialize RAG knowledge base with DEFAULT_GUIDE_CONTENT (style guidelines)
        2. Construct initial AgentState with system prompt and user task
        3. Invoke LangGraph app with recursion limit
        4. Extract and display final README content from agent's last message

    Environment Requirements:
        - OPENAI_API_KEY must be set
        - ChromaDB directory (./klaro_db) must be writable

    Example:
        >>> run_klaro_langgraph(project_path="./my-app")
        --- Launching Klaro LangGraph Agent (Stage 4 - gpt-4o-mini) ---
        📢 Initializing RAG Knowledge Base...
           -> Setup Result: Knowledge base (ChromaDB) successfully initialized...
        ==================================================
        ✅ TASK SUCCESS: LangGraph Agent Finished.
        ====================================
        # Project Name
        ...

    Note:
        The agent will use up to RECURSION_LIMIT iterations. If this limit is reached
        before completion, consider increasing it via KLARO_RECURSION_LIMIT environment
        variable or simplifying the target project.
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