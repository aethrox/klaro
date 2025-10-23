# **Klaro: Technical Design - Advanced Agent Architecture (LangGraph)**

## **1. Introduction**

This document details Klaro project's Stage 4 development: the transition from the existing **ReAct** agent architecture to **LangGraph**, a more advanced, stateful, and flexible structure. This upgrade will significantly enhance the agent's ability to manage more complex tasks, learn from errors, and establish a more robust decision-making mechanism.

## **2. Why LangGraph? Limitations of ReAct Architecture**

While ReAct is an excellent starting point for the MVP stage, it is inherently stateless and based on a simple Thought -> Action -> Observation loop. This can lead to challenges such as:

* **Error Management:** When a tool fails or produces an unexpected output, the ReAct agent typically terminates the loop or struggles to manage the error.
* **Complex Planning:** It's difficult for the agent to follow complex multi-step plans or pivot to an alternative path when a step fails using ReAct.
* **Cyclical Logic:** Creating cyclical logic like "read files until sufficient information is gathered" is not natural.

LangGraph provides a graph data structure to solve these problems. This structure provides full control by defining the agent's logic flow with nodes and edges.

## **3. LangGraph Architecture Overview**

The LangGraph architecture consists of three main components:

1. **State:** A central data object that is carried and updated at each step of the graph. Can be thought of as the agent's "memory."
2. **Nodes:** Functions or chains that perform specific work (e.g., running a tool, asking the LLM a question). Each node takes the current state and returns an updated state.
3. **Edges:** Logical connections that determine which node runs after which node. These edges can be conditional, enabling the agent to make dynamic decisions.

### **3.1. State (AgentState) Design for Klaro Agent**

The Klaro agent's memory will be designed to contain the following information:

from typing import TypedDict, List, Dict

class AgentState(TypedDict):
    task: str                 # User's initial task (e.g., "create README")
    file_tree: str            # Project's file structure
    files_read: List[str]     # List of files that have been read
    analysis_results: Dict    # Analysis results from CodeAnalyzerTool
    document_draft: str       # Document draft being developed
    last_action_result: str   # Result of the last tool executed
    error_log: List[str]      # Log of errors encountered

### **3.2. Main Nodes**

1. **plan_step (Planning Node):** The agent's brain. Takes the current state (AgentState) and decides which tool to run with which parameters in the next step.
2. **execute_tool (Tool Execution Node):** Implements the decision from the planning node. Runs one of the tools like Codebase Explorer, File Reader, or Code Analyzer and adds the result to state as last_action_result.
3. **update_draft (Draft Update Node):** Takes new information from execute_tool (file content, code analysis, etc.) and enriches document_draft with this information.
4. **check_completeness (Completeness Check Node):** Checks whether the agent has enough information to complete the task. This node triggers the conditional edge that decides whether the next step is planning or generating the final output.

## **4. Example Workflow Graph**

Below is a simplified diagram of the LangGraph flow for a README creation task:

        [ Start ]
            |
            v
    [ plan_step ] --------> [ execute_tool ]
        ^   |                      |
        |   |                      v
        |   '---------------- [ update_draft ]
        |
        v (Complete task?)
[ check_completeness ] --(No)--> [ plan_step ] (Loop)
        |
        '--(Yes)--> [ Final Answer ]

### **Conditional Logic:**

The edge after the check_completeness node is the agent's most powerful feature.

* **If** the LLM says "I need more information," the edge redirects the flow back to the plan_step node.
* **If** the LLM says "I have all the information," the edge directs the flow to the Final Answer node, terminating the loop.
* **If** execute_tool returns an error, the error_log in state is updated and the flow returns to plan_step. This way the agent can say "This tool didn't work, I should try something else."

## **5. Conclusion and Advantages**

The transition to LangGraph will transform the Klaro agent from simple tool automation into a robust and intelligent system with the following capabilities:

* **Robustness:** Can manage tool errors and try alternative paths.
* **Advanced Logic:** Can plan and execute complex, multi-step tasks.
* **Observability:** Thanks to the graph structure, the agent's decision-making process becomes much more transparent and easy to follow.
* **Flexibility:** Adding new tools or logic flows will be as easy as adding new nodes and edges to the graph.
