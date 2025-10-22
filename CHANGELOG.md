# **Klaro Project Changelog**

All notable changes to the Klaro autonomous documentation agent project are documented here.

The project follows the "Keep a Changelog" standard and adheres to semantic versioning principles.

## **\[v0.2.0\] \- 2025-10-22 (Stable Agent Core & RAG Integration)**

This is a major architectural release, completing **Stage 2 (Agentic Core)** and **Stage 3 (Quality/RAG)** of the project plan. The agent architecture was completely refactored for stability and advanced documentation features.

### **Added**

* **RAG (Retrieval-Augmented Generation) System:** Implemented core RAG functionality.  
  * New dependencies: chromadb, tiktoken, langchain-text-splitters were added.  
  * **New Tools:** init\_knowledge\_base (ChromaDB setup) and retrieve\_knowledge (information retrieval) were integrated to enforce documentation style.  
* **Code Analyzer Tool:** The analyze\_code tool, utilizing Python's **Abstract Syntax Tree (AST)**, was fully integrated. This allows the agent to extract structural data (classes, functions, docstrings) from Python files.  
* **Web Search Tool:** web\_search tool was added to gather external context and documentation for dependencies.  
* **Environment Management:** Added python-dotenv to correctly load OPENAI\_API\_KEY from the .env file.

### **Changed**

* **Core Agent Architecture (Critical Refactor):**  
  * The unstable LangChain AgentExecutor and create\_react\_agent logic was replaced with a **Pure Python ReAct Loop**. This ensures agent functionality without reliance on specific, error-prone LangChain module imports.  
* **Tool Standardization:**  
  * The @tool decorator was removed from all functions in tools.py. Tools are now plain Python functions, resolving runtime errors like 'StructuredTool' object is not callable.  
* **Project Language Standard:**  
  * All system prompts (prompts.py), comments, and internal variables were fully **translated from Turkish to English** for international project standard and optimal LLM performance.

### **Fixed**

* **Recurring Import Errors:** Resolved a chain of fatal ImportError and ModuleNotFoundError issues by migrating to the stable Pure Python ReAct model and correcting module paths for RAG components (e.g., langchain\_text\_splitters).  
* **Parsing Robustness:** Improved the parse\_action function to reliably handle various action formats produced by the LLM (Action: tool\[param\] vs. Action: tool("param")).

## **\[v0.1.0\] \- 2025-09-20 (Initial Project Setup / MVP)**

The initial version, establishing the basic project structure and initial agent logic.

### **Added**

* **Project Structure:** Initial creation of main.py, tools.py, prompts.py, requirements.txt, and .gitignore.  
* **Initial Tools:** Basic file exploration (list\_files) and content reading (read\_file) tools were created (CodebaseReaderTool MVP).  
* **Basic Agent Logic:** Initial implementation used a simple LangChain Chain structure (not a full agent) to test basic LLM calls.