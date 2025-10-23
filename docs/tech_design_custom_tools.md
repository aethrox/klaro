# **Klaro: Technical Design - Custom Agent Tools**

## **1. Introduction**

This document explains the technical design of the custom tools that form the foundation of Klaro project's autonomous documentation agent. These tools are the core capabilities that enable the agent to "see," "navigate," and "understand" a codebase. Their designs use a modular and agentic approach to enable the agent to make proactive and intelligent decisions.

## **2. Core Design Principle: Agent-Centric Capabilities**

Rather than a monolithic structure that processes the entire codebase at once, the tools are designed as a set of capabilities that allow the agent to pull information as needed. This approach overcomes LLM context window limitations and enables the agent to work efficiently even on large projects. The agent is the pilot at the wheel, and the tools are its dashboard and control mechanisms.

## **3. Tool 1: CodebaseReaderTool**

This tool enables the agent to interact with a file system or Git repository. Its primary purpose is to provide the agent with exploration and reading capabilities.

### **3.1. Purpose**

To enable the agent to understand project structure and access specific file contents by analyzing a Git repository or local project folder.

### **3.2. Challenge to Solve**

It's impossible to fit an entire large codebase into an LLM's context window. Therefore, the agent must be able to navigate intelligently within the project without "seeing" everything at once.

### **3.3. Design and Sub-functions**

CodebaseReaderTool consists of a capability set with multiple sub-functions:

#### **a) list_files(path: str) -> str**

* **Input:** A Git repository URL or local file path.
* **Process:**
  1. If input is a URL, clones the repository to a temporary directory.
  2. Navigates the project root directory to scan file and folder structure.
  3. Reads .gitignore file and filters these files along with commonly ignored files like .git, node_modules, __pycache__.
* **Output:** Clean, readable text (string) showing the project's file tree structure.

#### **b) read_file(file_path: str) -> str**

* **Input:** Full path of the file to be read (e.g., src/main.py).
* **Process:** Reads the content of the specified file.
* **Output:** Text containing the raw content of the file.

### **3.4. Example Workflow**

1. **Agent Thought:** "I need to understand the overall structure of the project."
2. **Action:** CodebaseReaderTool.list_files(path="https://github.com/...")
3. **Observation (Tool Output):**
   /
   ├── .gitignore
   ├── README.md
   ├── requirements.txt
   ├── src/
   │   ├── main.py
   │   └── utils.py

4. **Agent Thought:** "I understand the structure. I need to read requirements.txt to learn dependencies and src/main.py to see the main logic."
5. **Action:** CodebaseReaderTool.read_file(file_path="requirements.txt")
6. **Observation:** (requirements.txt content)
7. **Action:** CodebaseReaderTool.read_file(file_path="src/main.py")
8. **Observation:** (main.py content)

## **4. Tool 2: CodeAnalyzerTool**

This tool semantically and structurally analyzes what a code segment "does."

### **4.1. Purpose**

To analyze the content of a code file read by the agent and present its purpose, contained functions, classes, and their relationships in a structured format.

### **4.2. Challenge to Solve**

Sending raw code directly to the LLM can cause the model to miss important details or misinterpret (hallucinate). Programmatic analysis reduces this risk and provides more reliable results.

### **4.3. Design and Architecture (Hybrid Approach: AST + LLM)**

This tool uses a two-stage architecture for best results:

#### **Stage 1: Programmatic Analysis (AST - Abstract Syntax Tree)**

* Using built-in tools like Python's ast library, code content is programmatically parsed.
* At this stage, structural information is extracted without understanding code logic:
  * All class and function definitions (ClassDef, FunctionDef).
  * Parameters functions take, their default values, and type hints.
  * Existing docstrings.

#### **Stage 2: Semantic Summarization (LLM)**

* Structural data extracted in the AST stage is sent to the LLM with a special prompt template.
* This prompt asks the LLM to use this structural information and docstrings to explain each component's (function/class) purpose "in human language" and extract an overall summary of the file.

### **4.4. Input and Output Format**

* **Input:** Text (string) containing the code content to be analyzed.
* **Output:** A standard JSON object that the agent can easily process.

**Example JSON Output:**

{
  "file_path": "src/utils.py",
  "summary": "This module contains helper functions for processing and validating user data.",
  "components": [
    {
      "type": "function",
      "name": "format_user_data",
      "parameters": ["user_id (int)", "data (dict)"],
      "returns": "dict",
      "description": "Takes user data and converts it to a standard format for the API."
    },
    {
      "type": "function",
      "name": "validate_email",
      "parameters": ["email (str)"],
      "returns": "bool",
      "description": "Checks whether the given email is in a valid format."
    }
  ]
}

## **5. Next Steps**

These two core tools form the foundation of the project. The next technical stage is to integrate these tools with a LangChain Agent (e.g., ReAct Agent) to enable the agent to autonomously plan and execute tasks using these capabilities.
