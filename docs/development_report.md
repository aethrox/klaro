# **Klaro Project: Development Stages Report (Current Status)**

This report summarizes all progress of the Klaro project from its inception (MVP) to the latest LangGraph stabilization, including technical achievements and architectural imperatives.

## **Stage 1: MVP (Minimum Viable Product) and Basic Setup**

**Goal:** Prove the project's viability and establish the basic LLM chain.

| Achievement | Description | Technical Detail |
| :---- | :---- | :---- |
| **Agent Architecture** | A simple LangChain Chain was used to establish the first interaction with the LLM. | Passive, consisting of predefined steps. No state management. |
| **Basic Tools** | Simple I/O tools like read_file were designed. | Inefficient reading methods were used that stressed the LLM's context window. |
| **Language Standard** | The decision was made to **transition to English language standard** in preparation for an international project. | All prompts, comments, and main variable names were translated to English. |

## **Stage 2: ReAct Agent Architecture and AST Integration**

**Goal:** Move the agent to a ReAct (Thought → Action → Observation) structure capable of making autonomous decisions.

| Achievement | Description | Technical Detail |
| :---- | :---- | :---- |
| **Architecture Transition (ReAct)** | Due to persistent ImportError issues in LangChain, a **Pure Python ReAct Loop** was implemented. | The agent's logic loop was managed with the parse_action function and while loop within main.py instead of external LangChain components. Stability was achieved. |
| **Custom Tools** | list_files, read_file, web_search, and most importantly **analyze_code** (AST-based) were added. | @tool decorators were removed from tools in tools.py (necessity for Pure ReAct) and presented to the LLM as directly callable functions. |
| **Code Analysis Depth** | analyze_code used Python's **AST (Abstract Syntax Tree)** library to convert code into structured (JSON) data. | The LLM began understanding not just the text of the code, but also the **class/function/parameter structure**. |

## **Stage 3: RAG (Retrieval-Augmented Generation) and Quality Improvement**

**Goal:** Use external style guides to improve documentation output quality and consistency.

| Achievement | Description | Technical Detail |
| :---- | :---- | :---- |
| **RAG Infrastructure Setup** | **ChromaDB** (Vector Database) and **OpenAI Embeddings** integration was completed. | DEFAULT_GUIDE_CONTENT was indexed with init_knowledge_base. The retrieve_knowledge tool was added. |
| **Output Control** | The agent was **mandated** via the system prompt to use the retrieve_knowledge tool before writing the README. | Generated READMEs were guaranteed to follow the same professional format (Headings, Sections) each time. |
| **Final Output** | Klaro produced high-quality READMEs using both code analysis information and the mandatory Style Guide. |  |

## **Stage 4: LangGraph Architecture (Final Stabilization)**

**Goal:** Migrate the Pure Python ReAct loop to **LangGraph** structure designed for error handling and flow control to make the project production-ready.

| Goal | Description | Technical Detail |
| :---- | :---- | :---- |
| **Architecture Transition (LangGraph)** | Despite all import crises (LangChain/LangGraph package incompatibilities), the architecture was migrated to StateGraph structure. | The agent's memory (messages, errors) was managed with LangGraph's AgentState structure. |
| **Stable Tool Calling** | An automatic tool calling system was established using LangGraph's ToolNode and ToolExecutor structure. | The manual parse_action mechanism was removed. The agent gained the ability to replan after faulty steps (decide_next_step router). |
| **Error Tolerance** | Thanks to LangGraph's conditional edges, instead of stopping the flow after a failed tool call, the agent gained the ability to analyze the state and **replan**. |  |

### **Conclusion and Project Vision**

The Klaro project has achieved its vision of an **autonomous, analytical, and stylistically consistent** documentation agent. The project is running on its most stable architecture and is production-ready.
