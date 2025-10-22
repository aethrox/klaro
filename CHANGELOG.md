# **Changelog**

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## **\[0.4.0\] \- Unreleased**

### **Added**

* **LangGraph Architecture (Stage 4):** Implemented the final, most stable agent architecture using LangGraph (StateGraph, ToolNode, ToolExecutor). This provides robust state management, conditional routing, and self-healing capabilities \[cite: tech\_design\_advanced\_agent\_langgraph\].  
* **RAG Integration:** Added init\_knowledge\_base and retrieve\_knowledge tools to tools.py to enable Retrieval-Augmented Generation \[cite: klaro\_project\_plan\].  
* **Documentation Standard:** Added the CHANGELOG.md file itself and updated the README.md to reflect the Stage 3 & 4 features.

### **Changed**

* **Agent Core:** Replaced the fragile Pure Python ReAct loop with the native LangGraph/Tool Calling mechanism for reliable execution.  
* **Dependencies:** Updated requirements.txt to include langgraph, chromadb, and langchain-text-splitters for RAG functionality.  
* **Codebase Language:** All system prompts, comments, and project documentation were converted to English for standardization.

### **Fixed**

* **ModuleNotFoundError:** Resolved persistent import conflicts (e.g., langchain.agents.executor, langchain\_core.agents) by enforcing the use of the final, correct import path for ToolExecutor (a critical fix for LangGraph stability).

## **\[0.3.0\] \- Stage 3 Completion (RAG & Quality)**

### **Added**

* **Quality Control (RAG):** Implemented RAG via ChromaDB and OpenAI Embeddings to inject project style guides into the agent's context, ensuring high-quality, consistent output.  
* **New Tools:** Added init\_knowledge\_base and retrieve\_knowledge to the toolset.  
* **Mandatory Tool Use:** Updated prompts.py to force the agent to call retrieve\_knowledge before writing the Final Answer.

### **Changed**

* **Architecture:** The agent is now fully capable of both external (web) and internal (vector DB) information retrieval.

## **\[0.2.0\] \- Stage 2 Completion (ReAct & AST Analysis)**

### **Added**

* **Autonomous Core:** Implemented the **Saf Python ReAct Loop** to allow the agent to make autonomous decisions (Thought \-\> Action \-\> Observation).  
* **Deep Analysis Tool:** Added analyze\_code tool using Python's **AST (Abstract Syntax Tree)** library, enabling the agent to understand code structure (classes, functions, parameters) instead of just raw text.  
* **New I/O Tools:** Added list\_files and enhanced read\_file.

### **Fixed**

* **Import/Call Errors:** Resolved errors like 'StructuredTool' object is not callable by removing the @tool decorator and using manual function calls (plain Python functions).

## **\[0.1.0\] \- MVP (Minimum Viable Product)**

### **Added**

* **Initial Setup:** Project structure, .gitignore, and basic requirements.txt created.  
* **Initial Agent:** Simple sequential LangChain Chain (not ReAct) established to perform basic file reading.  
* **Dependencies:** Initial installation of langchain-core and langchain-openai.