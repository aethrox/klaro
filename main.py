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
LLM_MODEL = "gpt-4o-mini"
RECURSION_LIMIT = int(os.getenv("KLARO_RECURSION_LIMIT", "50"))
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
    """Defines the state carried across the LangGraph steps."""
    # Conversation history: Appends new messages to the end (Reductor logic).
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y] 
    # Placeholder for tracking errors or complex state manipulation.
    error_log: str 

# --- 4. LangGraph Nodes ---

def run_model(state: AgentState):
    """The node that invokes the LLM (Agent's Thinking step)."""
    # Send the entire message history to the LLM.
    response = model.invoke(state["messages"])
    # Append the LLM's response and clear any previous error.
    return {"messages": [response], "error_log": ""} 

# --- 5. LangGraph Router (Edges) ---

def decide_next_step(state: AgentState):
    """Decides where the flow goes based on the LLM's last output."""
    last_message = state["messages"][-1]
    
    # 1. Check for immediate error from a previous tool execution.
    if state.get("error_log"):
         # If an error occurred, route back to the model for replanning.
         return "run_model" 

    # 2. Check for Final Answer (Agent has completed the task).
    if last_message.content and "Final Answer" in last_message.content:
        return END # Terminate the graph.

    # 3. Check for Tool Call (The LLM requesting to use a tool).
    if last_message.tool_calls:
        return "call_tool"
    
    # 4. If none of the above, loop back to the model for the next thought step.
    return "run_model" 

# --- 6. LangGraph Setup ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("run_model", run_model)
# ToolNode handles the execution of the tools when the LLM requests them
workflow.add_node("call_tool", ToolNode(tools)) 

# Set Entry Point
workflow.set_entry_point("run_model")

# Add Conditional Edges
workflow.add_conditional_edges(
    "run_model",
    decide_next_step,
    {
        "call_tool": "call_tool", 
        END: END,               
        "run_model": "run_model" 
    }
)

# After tool execution, always return to the model to process the Observation (ToolMessage).
workflow.add_edge("call_tool", "run_model")

# Compile the graph
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
    Runs the Klaro LangGraph Agent.
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