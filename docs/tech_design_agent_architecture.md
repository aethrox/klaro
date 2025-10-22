# **Klaro: Technical Design - Agent Architecture and Integration**

## **1. Introduction**

This document explains the architecture, integration, and core operating principles of the autonomous agent that will use the custom tools (CodebaseReaderTool, CodeAnalyzerTool) designed in the tech_design_custom_tools document. This stage creates the project's "brain", enabling the agent to plan and execute tasks autonomously.

## **2. Agent Architecture Selection: ReAct (Reasoning and Acting)**

LangChain's **ReAct** agent architecture will be used for the project's initial and MVP (Minimum Viable Product) stages.

### **2.1. Why ReAct?**

* **Simplicity and Understandability:** ReAct works with a Thought -> Action -> Observation loop. This structure makes it extremely easy to track the agent's decision-making process and debug.
* **Effective Tool Usage:** This architecture requires the LLM to explicitly state which tool it chose and why, and what it plans to do in the next step. This is ideal for tool-centric tasks.
* **Industry Standard:** It is one of the most common and well-documented agent types in LangChain, enabling a quick start.

## **3. Integration of Agent and Tools**

For the agent to use the designed custom tools, these tools must be defined in LangChain format and "presented" to the agent.

### **3.1. Tool Definition**

Each custom tool must be packaged as a Tool object. This object contains at least two important parameters:

* **name:** A unique name the LLM will use to call the tool (e.g., codebase_reader or code_analyzer).
* **description:** **The most critical part.** This is where the LLM understands what the tool does, when it should be used, and what parameters it takes. The clearer the description, the smarter the agent becomes.

**Example Tool Definition (Python Code Concept):**

```python
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
        description="Used to read the content of a specific file. Takes the file path (file_path) as an argument."
    ),
    Tool(
        name="Code Analyzer",
        func=analyzer_tool.analyze,
        description="Used to analyze the content of a code file, summarize it, and structurally extract functions/classes within it."
    )
]
```

### **3.2. Creating the Agent Executor**

The defined tools are combined in an AgentExecutor with the LLM and a main prompt. This executor manages the entire Thought -> Action -> Observation loop.

## **4. System/Main Prompt Design**

One of the most important factors shaping the agent's behavior is the initial instructions given to it (system prompt). This prompt defines the agent's identity, task, rules, and how to use its tools.

**Example System Prompt:**

```
You are Klaro, an expert AI assistant. Your task is to analyze a given codebase autonomously and create high-quality, clear, and professional technical documentation (README.md file).

You have access to the following tools to accomplish your tasks:

1. **Codebase Explorer:** Lists the file structure of a project. Always start analysis with this tool.
2. **File Reader:** Reads the content of a specific file.
3. **Code Analyzer:** Analyzes the purpose and structure of a piece of code.

**Your Rules:**
- You must think step by step. Explain what you will do at each step and why.
- Always start by listing the project structure.
- Determine the project's purpose, dependencies, how to install it, and how to use it.
- Analyze important functions or classes to create the "Usage" or "API" section of documentation.
- After gathering all information, present a complete and formatted Markdown output as "Final Answer".
```

## **5. Example Workflow: Step-by-Step README Generation**

Below is a simplified simulation of how the agent completes a task with the above prompt and tools:

**User Input:** "Create a README for https://github.com/user/project-name"

**Loop 1:**

* **Thought:** The user requested a README file. To start my task, I first need to understand the project's file structure. I'll use the Codebase Explorer tool for this.
* **Action:** Codebase Explorer(path="https://github.com/user/project-name")
* **Observation:**
  ```
  /
  ├── requirements.txt
  ├── src/
  │   ├── main.py
  ```

**Loop 2:**

* **Thought:** I saw the project structure. The requirements.txt file should contain dependencies. src/main.py looks like the main code. I'll first read requirements.txt with File Reader to learn the dependencies.
* **Action:** File Reader(file_path="requirements.txt")
* **Observation:** fastapi\nuvicorn

**Loop 3:**

* **Thought:** Okay, this is a FastAPI project. Now I need to read the src/main.py file to understand the main logic.
* **Action:** File Reader(file_path="src/main.py")
* **Observation:** (content of main.py)

**Loop 4:**

* **Thought:** I got the main.py content. Now I should use the Code Analyzer tool to understand what this code does and what API endpoints it has.
* **Action:** Code Analyzer(code_content="...")
* **Observation:** (JSON output from CodeAnalyzerTool)

**... (This loop continues until the agent gathers enough information) ...**

**Final Step:**

* **Thought:** I learned the project's purpose (FastAPI), dependencies, installation steps (pip install), and API endpoints. I now have enough information to create the final README file.
* **Final Answer:**
  ```markdown
  # Project Name

  This project is a web service built using FastAPI.

  ## Installation

  ...

  ## API Endpoints

  ...
  ```

## **6. Next Step: Transition to LangGraph**

Although the ReAct architecture is sufficient for MVP, it may fall short in more complex projects or situations where the agent encounters errors. In Stage 4 of the project, a transition to **LangGraph** is planned, which allows for more flexible, stateful, and cyclical (cyclical) logic flows. This will make the agent more robust and error-tolerant.
