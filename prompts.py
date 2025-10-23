"""
Klaro System Prompts Module

This module defines the core system prompts that shape the behavior, decision-making, and
operational guidelines of the Klaro autonomous documentation agent.

The prompts implement a ReAct (Reasoning and Acting) framework that guides the agent through:
- Structured thought process (Thought -> Action -> Observation)
- Tool selection and usage protocols
- Documentation generation standards and workflows

ReAct Format Explanation:
    The agent operates in a continuous loop where each iteration consists of:

    1. **Thought**: Agent reasons about the current situation and decides next action
       Example: "I need to understand the project structure first."

    2. **Action**: Agent selects and executes a tool with specific parameters
       Format: Action: tool_name[parameter]
       Example: Action: list_files["."]

    3. **Observation**: Agent receives and processes tool output
       Example: "I can see the project has main.py, tools.py, and requirements.txt"

    This cycle repeats until the agent determines it has sufficient information to
    produce the final documentation output.

Prompt Structure:
    - **Identity**: Defines agent as "Klaro" - a technical documentation specialist
    - **Operating Principle**: Emphasizes strict adherence to ReAct format
    - **Available Tools**: Lists all tools with descriptions and usage guidelines
    - **Goals**: Ordered workflow steps from exploration to final output
    - **Output Format**: Mandates "Final Answer: [MARKDOWN_CONTENT]" format

Tool Usage Order (Enforced by Prompt):
    1. list_files: Get project overview and file structure
    2. read_file: Read critical files (main.py, requirements.txt, etc.)
    3. analyze_code: Extract structured code information via AST
    4. retrieve_knowledge: Fetch README style guidelines from RAG system
    5. Final Answer: Generate formatted markdown documentation

Design Decisions:
    - Tools must be called with explicit format: tool_name[parameter]
    - retrieve_knowledge is MANDATORY before final output (ensures style consistency)
    - Agent must explore incrementally (not attempt to read entire codebase at once)
    - Documentation must follow retrieved style guidelines for professional consistency

Usage:
    This prompt is injected into the agent's initial message in main.py:
    >>> from prompts import SYSTEM_PROMPT
    >>> initial_message = HumanMessage(content=f"{SYSTEM_PROMPT}\\n\\nUSER'S TASK: {task_input}")

Customization Notes:
    - Modify tool descriptions here to change agent's tool selection behavior
    - Adjust goal ordering to change agent's workflow priorities
    - Update output format requirements to change final documentation structure
"""

SYSTEM_PROMPT = """
You are Klaro, an autonomous AI agent specializing in technical documentation. Your mission is to analyze a given codebase and autonomously generate a comprehensive, high-quality technical README.md file.

Core Operating Principle:
Base all your decisions on a clear Thought, Action, and Observation loop (ReAct).
You MUST strictly adhere to the following Action format: Action: tool_name[parameter]

Available Tools (Tools) and Their Functions:
- list_files(directory: str): Lists files and folders in the given directory in a tree structure. Use this as the very first step for an overview of the project.
- read_file(file_path: str): Reads and returns the content of the specified file path.
- analyze_code(code_content: str): Analyzes the content of Python code using AST and returns JSON output about classes and functions. (Must only be used with Python code content obtained from read_file.)
- web_search(query: str): Gathers external information (e.g., library documentation) or information about concepts you don't know.
- retrieve_knowledge(query: str): Retrieves relevant information (like 'README style guidelines') from the vector database (RAG). You MUST use this to determine the documentation standard.

Goals:
1. Start by exploring the file structure using list_files.
2. Read critical files (main.py, prompts.py, tools.py, requirements.txt) with read_file.
3. Analyze Python code using analyze_code.
4. Retrieve the 'README style guidelines' using retrieve_knowledge.
5. Once sufficient information is gathered, present your final answer in the format: **'Final Answer: [MARKDOWN_CONTENT]'**.
"""