# **Klaro: Technical Design - Agent Architecture and Integration**

## **1. Introduction**

This document explains the architecture, integration, and core operating principles of the autonomous agent that will use the custom tools (CodebaseReaderTool, CodeAnalyzerTool) designed in the tech_design_custom_tools document. This stage creates the project's "brain," enabling the agent to autonomously plan and execute tasks.

## **2. Agent Architecture Choice: ReAct (Reasoning and Acting)**

For the project's initial and MVP (Minimum Viable Product) stages, LangChain's **ReAct** agent architecture will be used.

### **2.1. Why ReAct?**

* **Simplicity and Comprehensibility:** ReAct operates with a Thought -> Action -> Observation loop. This structure makes it extremely easy to follow the agent's decision-making process and debugging.
* **Effective Tool Usage:** This architecture requires the LLM to explicitly state which tool it's choosing and why, and what it plans to do in the next step. This is ideal for tool-focused tasks.
* **Industry Standard:** One of the most common and well-documented agent types in LangChain, enabling a quick start.

## **3. Agent and Tool Integration**

For the agent to use the designed custom tools, these tools must be defined in LangChain format and "presented" to the agent.

### **3.1. Tool Definition**

Each custom tool should be packaged as a Tool object. This object contains at least two important parameters:

* **name:** A unique name that the LLM will use to call the tool (e.g., codebase_reader or code_analyzer).
* **description:** **The most critical part.** This is where the LLM understands what the tool does, when it should be used, and what parameters it takes. The clearer the description, the smarter the agent becomes.

**Example Tool Definition (Python Code Concept):**

from langchain.agents import Tool
from your_tools import CodebaseReaderTool, CodeAnalyzerTool

# Create tool objects
reader_tool = CodebaseReaderTool()
analyzer_tool = CodeAnalyzerTool()

tools = [
    Tool(
        name="Codebase Explorer",
        func=reader_tool.list_files,
        description="Used to list the file structure of a Git repository or local folder. You should use this tool first when starting a project."
    ),
    Tool(
        name="File Reader",
        func=reader_tool.read_file,
        description="Used to read the content of a specific file. Must take file path (file_path) as argument."
    ),
    Tool(
        name="Code Analyzer",
        func=analyzer_tool.analyze,
        description="Used to analyze, summarize, and structurally extract functions/classes from a code file's content."
    )
]

### **3.2. Creating the Agent Executor**

The defined tools are combined with an LLM and a main prompt within an AgentExecutor. This executor manages the entire Thought -> Action -> Observation loop.

## **4. System/Main Prompt Design**

One of the most important elements shaping the agent's behavior is the initial instructions given to it (system prompt). This prompt defines the agent's identity, task, rules, and how to use its tools.

**Example System Prompt:**

You are Klaro, an expert AI assistant. Your task is to autonomously analyze a given codebase and create high-quality, clear, and professional technical documentation (README.md file).

You have access to the following tools to accomplish the tasks given to you:

1. **Codebase Explorer:** Lists a project's file structure. Always start analysis with this tool.
2. **File Reader:** Reads the content of a specific file.
3. **Code Analyzer:** Analyzes a code segment's purpose and structure.

**Your Rules:**
- You must think step by step. Explain what you will do and why at each step.
- Always start by listing the project structure.
- Determine the project's purpose, dependencies, how to install it, and how to use it.
- Analyze important functions or classes to create the "Usage" or "API" section of the documentation.
- After gathering all information, present a complete and formatted Markdown output as "Final Answer".

## **5. Example Working Loop: Step-by-Step README Creation**

Below is a simplified simulation of how the agent completes a task with the above prompt and tools:

**User Input:** "Create a README for https://github.com/user/project-name"

**Loop 1:**

* **Thought:** User requested a README file. To start my task, I need to understand the project's file structure first. I'll use the Codebase Explorer tool for this.
* **Action:** Codebase Explorer(path="https://github.com/user/project-name")
* **Observation:**
  /
  ├── requirements.txt
  ├── src/
  │   ├── main.py

**Loop 2:**

* **Thought:** I see the project structure. The requirements.txt file should contain dependencies. src/main.py looks like the main code. I'll first read requirements.txt with File Reader to learn the dependencies.
* **Action:** File Reader(file_path="requirements.txt")
* **Observation:** fastapi\nuvicorn

**Loop 3:**

* **Thought:** Okay, this is a FastAPI project. Now I need to read src/main.py to understand the main logic.
* **Action:** File Reader(file_path="src/main.py")
* **Observation:** (content of main.py)

**Loop 4:**

* **Thought:** I got the content of main.py. Now I need to use the Code Analyzer tool to understand what this code does and which API endpoints it has.
* **Action:** Code Analyzer(code_content="...")
* **Observation:** (JSON output from CodeAnalyzerTool)

**... (This loop continues until the agent gathers enough information) ...**

**Final Step:**

* **Thought:** I learned the project's purpose (FastAPI), dependencies, installation steps (pip install), and API endpoints. I now have enough information to create the final README file.
* **Final Answer:**
  # Project Name

  This project is a web service created using FastAPI.

  ## Installation

  ...

  ## API Endpoints

  ...

## **6. Next Step: Transition to LangGraph**

While the ReAct architecture is sufficient for MVP, it may fall short in more complex projects or when the agent encounters errors. In Stage 4 of the project, a transition to **LangGraph** is planned, which allows for more flexible, stateful, and cyclical logic flows. This will make the agent more robust and fault-tolerant.
