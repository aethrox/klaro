# Klaro Glossary

This glossary defines key terms and concepts used throughout the Klaro project documentation.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Technologies](#technologies)
- [Architecture Components](#architecture-components)
- [Agent Terminology](#agent-terminology)
- [Development Terms](#development-terms)

---

## Core Concepts

### Agent
An autonomous AI system that can make decisions, use tools, and complete tasks without continuous human guidance. Klaro is an agent that generates documentation by analyzing codebases.

### AST (Abstract Syntax Tree)
A tree representation of the syntactic structure of source code. Klaro uses Python's `ast` module to parse and analyze code structure programmatically, extracting classes, functions, parameters, and docstrings without relying on LLM interpretation.

### Knowledge Base
The collection of documents (such as style guides and reference documentation) stored in ChromaDB that Klaro retrieves from during documentation generation to ensure consistency and adherence to project standards.

### ReAct Loop
A reasoning pattern where an AI agent alternates between **Rea**soning (thinking about what to do next) and **Act**ing (executing tools or actions). The cycle is: Thought → Action → Observation → Thought → ... → Final Answer. This allows the agent to break down complex tasks into manageable steps.

### Retrieval-Augmented Generation (RAG)
A technique that enhances LLM outputs by retrieving relevant context from an external knowledge source (vector database) before generating responses. Klaro uses RAG to inject project-specific style guides into the documentation generation process.

---

## Technologies

### ChromaDB
An open-source vector database used by Klaro to store and retrieve document embeddings. ChromaDB enables semantic search over the Knowledge Base, allowing the agent to find relevant style guide sections based on query similarity.

### LangChain
A framework for building applications with large language models (LLMs). LangChain provides tools, prompts, chains, and agents that Klaro uses to orchestrate its documentation generation workflow.

### LangGraph
A library for building stateful, multi-actor applications with LLMs. LangGraph extends LangChain with graph-based workflow orchestration, enabling Klaro to implement complex agent logic with conditional routing, state management, and error recovery.

### LangSmith
An observability and debugging platform for LangChain applications. LangSmith provides detailed traces of agent execution, showing LLM calls, tool usage, token counts, and costs. Essential for debugging and optimizing Klaro's performance.

### OpenAI Embeddings
A service that converts text into high-dimensional vectors (embeddings) that capture semantic meaning. Klaro uses OpenAI's `text-embedding-3-small` model to create embeddings for documents in the Knowledge Base, enabling semantic search via ChromaDB.

---

## Architecture Components

### Agent State
A TypedDict in `main.py` that defines the structure of data passed between nodes in the LangGraph workflow. Contains:
- `messages`: Conversation history (list of BaseMessage objects)
- `error_log`: Tracking of execution errors for retry logic

### Node
A function in the LangGraph state machine that performs a specific operation (e.g., `run_model`, `call_tool`). Nodes receive the current agent state, perform processing, and return updated state.

### Recursion Limit
The maximum number of iterations (Thought → Action → Observation cycles) the agent can perform before timing out. Default is 50. Prevents infinite loops and controls API costs.

### StateGraph
The LangGraph construct that defines the agent's workflow as a directed graph with nodes (functions) and edges (transitions). Enables conditional routing based on agent state.

### Tool
A Python function that provides the agent with a capability (e.g., reading files, analyzing code, searching the web). Tools are registered with LangChain and exposed to the LLM via function calling.

### ToolNode
A LangGraph built-in node type that executes tools requested by the LLM. Parses tool calls from AI messages, executes the corresponding functions, and returns results as tool messages.

---

## Agent Terminology

### Action
In the ReAct loop, an action is the agent's decision to use a specific tool with specific parameters. Example: `read_file["main.py"]`

### Final Answer
The signal that the agent has completed its task and is ready to present the generated documentation. When the LLM includes "Final Answer:" in its response, the agent terminates execution.

### Observation
In the ReAct loop, the observation is the result returned by a tool after execution. The agent uses observations to inform its next reasoning step.

### System Prompt
The initial instruction given to the LLM that defines its role, capabilities, available tools, and output format requirements. Defined in `prompts.py`.

### Thought
In the ReAct loop, the thought is the agent's internal reasoning about what to do next, which tool to use, or whether it has enough information to produce the final answer.

---

## Development Terms

### .gitignore Filtering
The process of excluding certain files and directories (like `__pycache__`, `node_modules`, `.git`) from the agent's file listing and analysis. Klaro uses pattern matching to respect .gitignore rules.

### Conditional Routing
LangGraph's mechanism for determining which node to execute next based on the current state. Klaro's `decide_next_step` function implements conditional routing based on errors, tool calls, and completion signals.

### Docstring
A string literal that appears as the first statement in a Python module, function, class, or method definition. Klaro extracts docstrings during AST analysis to understand code purpose and behavior.

### Embedding
A numerical vector representation of text that captures semantic meaning. Similar texts have similar embeddings. Used in RAG to find relevant Knowledge Base documents.

### Reducer
A function in LangGraph that determines how to merge state updates from different nodes. Klaro uses `lambda x, y: x + y` to append new messages to the message history.

### Token
The unit of text processed by LLMs. One token is approximately 4 characters or 0.75 words in English. Token count affects API costs and context limits.

### Type Hint
Python syntax for specifying expected types of function parameters and return values (e.g., `def read_file(file_path: str) -> str:`). Required for all Klaro functions for clarity and type checking.

### Vector Store
A database optimized for storing and querying high-dimensional vectors (embeddings). ChromaDB is Klaro's vector store, used to implement the RAG system.

---

## Acronyms

- **AI**: Artificial Intelligence
- **API**: Application Programming Interface
- **AST**: Abstract Syntax Tree
- **LLM**: Large Language Model
- **RAG**: Retrieval-Augmented Generation
- **JSON**: JavaScript Object Notation

---

## Related Documentation

- [Architecture Guide](architecture.md) - System architecture overview
- [Configuration Guide](configuration.md) - Configuration options and settings
- [Main README](../README.md) - Project overview and quick start

---

**Last Updated**: 2025-10-23
**Klaro Version**: 1.0
**Maintained by**: Klaro Development Team
