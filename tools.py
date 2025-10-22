"""
Klaro Tools Module - Agent Capabilities
========================================

This module provides the core tools that enable Klaro's autonomous analysis of codebases.
These tools serve as the agent's "hands" and "eyes", allowing it to explore projects,
read files, analyze code structure, search for information, and retrieve style guidelines.

Tool Collection Overview:
-------------------------
1. **Codebase Exploration Tools:**
   - list_files: Navigate project directory structure
   - read_file: Access file contents

2. **Code Analysis Tools:**
   - analyze_code: AST-based Python code structure extraction
   - _extract_docstring: Helper for docstring extraction

3. **Information Retrieval Tools:**
   - web_search: External information lookup (simulated)
   - retrieve_knowledge: RAG-based style guide retrieval

4. **RAG System Tools:**
   - init_knowledge_base: Initialize ChromaDB vector database
   - retrieve_knowledge: Semantic search for documentation guidelines

Dependencies:
-------------
- ast: Python's Abstract Syntax Tree for code parsing
- ChromaDB: Local vector database for RAG
- OpenAI Embeddings: Text vectorization for semantic search
- LangChain: Document processing and text splitting

Usage Patterns:
---------------
These functions are designed to be called by the LLM through LangGraph's ToolNode.
Each function:
- Takes simple Python types as input (str, list, etc.)
- Returns str output that the LLM can interpret
- Includes comprehensive docstrings that serve as tool descriptions

Example:
    from tools import list_files, read_file, analyze_code

    # Explore project structure
    file_tree = list_files(".")

    # Read a specific file
    content = read_file("main.py")

    # Analyze Python code
    analysis = analyze_code(content)

Design Philosophy:
------------------
- **Pull-based Architecture**: Agent pulls information as needed rather than
  receiving entire codebase upfront. This respects LLM context window limits.

- **Defensive Error Handling**: All functions return str (never raise exceptions)
  to prevent agent crashes. Errors are returned as descriptive strings.

- **Gitignore Awareness**: Automatically filters out .git, __pycache__, node_modules,
  and other common non-code directories.

- **Structured Output**: Complex results (like code analysis) return JSON strings
  for easy LLM parsing.

Global Configuration:
---------------------
- VECTOR_DB_PATH: ChromaDB persistence directory (./klaro_db)
- KLARO_RETRIEVER: Global retriever instance (initialized by init_knowledge_base)
- GITIGNORE_CONTENT: Embedded .gitignore patterns for filtering
- IGNORE_PATTERNS: Compiled regex patterns from GITIGNORE_CONTENT

See also:
---------
- docs/tech_design_custom_tools.md: Detailed tool design documentation
- main.py: How tools are bound to the LLM
- prompts.py: Tool descriptions presented to the agent
"""

import os
import re
import ast
import json

# --- RAG/Vector Database Imports (Stage 3) ---
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
# Correct package path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.documents import Document 

# Global RAG Configuration
VECTOR_DB_PATH = "./klaro_db"
KLARO_RETRIEVER: VectorStoreRetriever | None = None

# --- Helper Functions: .gitignore Content ---
GITIGNORE_CONTENT = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class
# C extensions
*.so
# ... (Diğer standart ignore desenleri) ...
# Environments
.env
.venv
env/
venv/
ENV/
"""

def get_gitignore_patterns(gitignore_content: str) -> list[str]:
    """
    Converts .gitignore-style patterns into compiled regex patterns.

    Translates common git ignore patterns (e.g., '*.pyc', '__pycache__/', '**/*.log')
    into Python regex patterns that can be used with re.search() for file filtering.

    Args:
        gitignore_content (str): Raw .gitignore file content with one pattern per line.
            Comments (lines starting with #) and empty lines are automatically ignored.

    Returns:
        list[str]: List of regex pattern strings ready for re.search().
            Each pattern is designed to match relative file paths.

    Pattern Translation Rules:
        - '**' (recursive wildcard) -> '.*' (match any characters)
        - '*' (single-level wildcard) -> '[^/]*' (match any non-slash characters)
        - Patterns ending with '/' match directories
        - Patterns without '/' match files/dirs at any level

    Example:
        >>> patterns = get_gitignore_patterns("*.pyc\\n__pycache__/\\n# Comment\\n")
        >>> patterns
        ['(.*/)? *.pyc$', '(.*/)? __pycache__(/.*)?$']

    Note:
        This is a simplified implementation. Full .gitignore syntax (negation with '!',
        bracket expressions, etc.) is not supported. Sufficient for common Python projects.
    """
    patterns = []
    for line in gitignore_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        pattern = re.escape(line).replace(r'\*\*', '.*').replace(r'\*', '[^/]*')
        if not pattern.endswith(r'/'):
            pattern = r'(.*/)?' + pattern + r'$'
        else:
            pattern = r'(.*/)?' + pattern[:-len(r'/')] + r'(/.*)?$'
            
        patterns.append(pattern)
    return patterns

IGNORE_PATTERNS = get_gitignore_patterns(GITIGNORE_CONTENT)

def is_ignored(path: str) -> bool:
    """
    Determines if a file path should be excluded from codebase analysis.

    Checks the given path against compiled .gitignore patterns and hardcoded exclusions
    (like .git directory) to decide if the file/directory should be filtered out.

    Args:
        path (str): Relative or absolute file/directory path to check.
            Can use either forward slashes (/) or backslashes (\\).

    Returns:
        bool: True if path should be ignored (excluded from analysis), False otherwise.

    Exclusion Rules:
        1. Matches any pattern in IGNORE_PATTERNS (derived from GITIGNORE_CONTENT)
        2. Explicitly ignores: .git, .git/, .env

    Example:
        >>> is_ignored("__pycache__/module.pyc")
        True
        >>> is_ignored("src/main.py")
        False
        >>> is_ignored(".git/config")
        True

    Note:
        Path comparison is case-sensitive. Paths are normalized to use forward slashes
        for cross-platform compatibility.
    """
    path = path.replace('\\', '/')
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, path):
            return True
    
    # Explicitly ignore common project directories
    if path.startswith(('./.git', '.git/')) or path in ('.git', '.env'):
        return True
    
    return False

# --- CodebaseReaderTool Functions ---

def list_files(directory: str = '.') -> str:
    """
    Lists files and folders in the given directory in a tree-like structure. Filters ignored paths.

    Recursively explores a project directory and generates a visual tree representation
    of its file structure, automatically excluding files matching .gitignore patterns.
    This is typically the first tool the agent uses to understand project layout.

    Args:
        directory (str, optional): Path to the directory to explore. Can be relative
            or absolute. Defaults to '.' (current working directory).

    Returns:
        str: Multi-line string containing a visual tree representation of the directory.
            Format uses ASCII characters (├── for files, └── for root).

            Example output:
                └── klaro/
                ├── main.py
                ├── tools.py
                ├── prompts.py
                ├── requirements.txt
                ├── docs/
                ├── README.md

            If directory doesn't exist, returns error message string.

    Filtering Behavior:
        - Automatically excludes: .git/, __pycache__/, .env, *.pyc
        - Respects patterns in GITIGNORE_CONTENT global variable
        - Directories in ignore list are completely skipped (not recursed into)

    Error Handling:
        - Non-existent directory: Returns "Error: Directory not found or is not a directory: '{path}'"
        - Permission errors: Silently skips inaccessible directories
        - Never raises exceptions (returns error strings for LLM consumption)

    Example:
        >>> tree = list_files("./my-project")
        >>> print(tree)
        └── my-project/
        ├── src/
        ├── main.py
        ├── utils.py
        ├── README.md

    Note:
        Output format is optimized for LLM readability. The agent uses this to decide
        which files to read with read_file() tool.
    """
    if not os.path.isdir(directory):
        return f"Error: Directory not found or is not a directory: '{directory}'"

    abs_dir = os.path.abspath(directory)
    output_lines = [os.path.basename(abs_dir)]
    
    for root, dirs, files in os.walk(directory):
        i = 0
        while i < len(dirs):
            relative_dir = os.path.relpath(os.path.join(root, dirs[i]), abs_dir)
            if is_ignored(relative_dir):
                del dirs[i]
            else:
                i += 1
        
        rel_root = os.path.relpath(root, abs_dir)
        
        if rel_root != '.':
            indent_level = rel_root.count(os.sep)
        else:
            indent_level = 0
            
        indent = '|   ' * indent_level

        for file in sorted(files):
            relative_path = os.path.join(rel_root, file)
            if not is_ignored(relative_path):
                output_lines.append(f"{indent}├── {file}")
        
        for dir_name in sorted(dirs):
             output_lines.append(f"{indent}├── {dir_name}/")

    tree_output = '\n'.join(output_lines)
    tree_output = tree_output.replace(os.path.basename(abs_dir), f"└── {os.path.basename(abs_dir)}/")
    
    # Clean format for easier reading of the LLM
    return tree_output.replace('└──', '/').replace('├──', '├── ')


def read_file(file_path: str) -> str:
    """
    Reads and returns the content of the specified file path.

    Retrieves the raw text content of a file for the agent to analyze. Typically used
    after list_files() to read specific files of interest (main.py, README.md, etc.).

    Args:
        file_path (str): Absolute or relative path to the file to read.
            Can be any text-based file (source code, markdown, config files).

    Returns:
        str: Complete file contents as a UTF-8 decoded string.
            For binary files or encoding errors, returns error message string.

    Error Handling:
        Returns descriptive error strings for:
        - Non-existent paths: "Error: File path not found or is not a file: '{path}'"
        - Directories (not files): "Error: Path '{path}' is a directory, not a file. Please use 'list_files'."
        - Encoding errors: "Error reading file: {exception_message}"

    Example:
        >>> content = read_file("main.py")
        >>> print(content[:50])
        import os
        from typing import TypedDict

        def main():

    Usage in Agent Workflow:
        1. Agent calls list_files() to see project structure
        2. Agent identifies important files (main.py, requirements.txt)
        3. Agent calls read_file() for each file to analyze content
        4. Agent may call analyze_code() on Python files for deeper analysis

    Note:
        - Assumes UTF-8 encoding (standard for modern code files)
        - No file size limits (be cautious with very large files > 1MB)
        - Content is returned as-is (no preprocessing or filtering)
    """
    if not os.path.exists(file_path):
        return f"Error: File path not found or is not a file: '{file_path}'"
    
    if os.path.isdir(file_path):
        return f"Error: Path '{file_path}' is a directory, not a file. Please use 'list_files'."
        
    try:
        # Code files typically use UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {e}"

# --- CodeAnalyzerTool Function ---

def _extract_docstring(node):
    """
    Extracts the docstring from an AST node (function or class).

    Helper function for analyze_code() that safely extracts docstrings from
    AST FunctionDef or ClassDef nodes.

    Args:
        node (ast.FunctionDef | ast.ClassDef | ast.AsyncFunctionDef): AST node
            that may contain a docstring as its first statement.

    Returns:
        str | None: The docstring text if found, None otherwise.

    Extraction Logic:
        A docstring must be:
        1. The first statement in the body (node.body[0])
        2. An Expr node (expression statement)
        3. Containing a Constant node with a string value

    Example:
        >>> import ast
        >>> code = '''
        ... def foo():
        ...     \"\"\"This is a docstring.\"\"\"
        ...     pass
        ... '''
        >>> tree = ast.parse(code)
        >>> func_node = tree.body[0]
        >>> _extract_docstring(func_node)
        'This is a docstring.'

    Note:
        This is a private helper function (indicated by leading underscore).
        Not intended to be called by the agent directly.
    """
    if not node.body or not isinstance(node.body[0], ast.Expr):
        return None
    if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
        return node.body[0].value.value
    return None


def analyze_code(code_content: str) -> str:
    """
    Analyzes Python code content using AST (Abstract Syntax Tree).
    Extracts classes, functions, parameters, and docstrings, returning the output in JSON format.

    Performs deep structural analysis of Python code without executing it. Uses Python's
    built-in AST parser to extract function signatures, class structures, parameters,
    return types, and docstrings. The LLM uses this structured data to understand code
    purpose and generate accurate documentation.

    Args:
        code_content (str): Raw Python source code to analyze. Must be syntactically
            valid Python code (any version compatible with ast.parse).

    Returns:
        str: JSON-formatted string containing analysis results. Structure:
            {
                "analysis_summary": "This Python file contains X classes and Y functions.",
                "components": [
                    {
                        "type": "function"|"class",
                        "name": "function_name",
                        "parameters": ["param1", "param2: int"],
                        "returns": "return_type_hint",
                        "docstring": "Function description",
                        "lineno": 42
                    },
                    ...
                ]
            }

            For classes, includes additional "methods" key with method details.

    Error Handling:
        Returns JSON error objects for:
        - Empty code: {"error": "Code content to analyze is empty."}
        - Syntax errors: {"error": "Code parsing error (SyntaxError): ..."}
        - Other exceptions: {"error": "Unexpected error during code analysis: ..."}

    Example:
        >>> code = '''
        ... def calculate_total(items: list[int]) -> int:
        ...     \"\"\"Sums all items in the list.\"\"\"
        ...     return sum(items)
        ... '''
        >>> result = analyze_code(code)
        >>> import json
        >>> data = json.loads(result)
        >>> data["components"][0]["name"]
        'calculate_total'
        >>> data["components"][0]["parameters"]
        ['items']
        >>> data["components"][0]["docstring"]
        'Sums all items in the list.'

    Extraction Details:
        - **Functions**: Name, parameters (with defaults), return type, docstring, line number
        - **Classes**: Name, docstring, line number, plus list of all methods
        - **Type Hints**: Extracted when present (e.g., "-> int", "param: str")
        - **Async Functions**: Treated identically to regular functions

    Limitations:
        - Only analyzes Python code (other languages not supported)
        - Does not analyze: imports, global variables, decorators, inner functions
        - Focuses on top-level definitions and class methods only
        - Type hint extraction may fail for complex types (returns "Unknown")

    Usage in Agent Workflow:
        1. Agent calls list_files() to find Python files
        2. Agent calls read_file() to get source code
        3. Agent calls analyze_code() to extract structure
        4. Agent uses structured data to write API documentation, usage examples

    Note:
        This tool provides the "understanding" layer between raw code and documentation.
        By extracting structure programmatically, we reduce LLM hallucination risk.
    """
    if not code_content:
        return json.dumps({"error": "Code content to analyze is empty."})

    components = []
    
    try:
        tree = ast.parse(code_content)
    except SyntaxError as e:
        return json.dumps({"error": f"Code parsing error (SyntaxError): {e}"})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error during code analysis: {e}"})

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = _extract_docstring(node)
            parameters = [f"{arg.arg}" for arg in node.args.args]

            # Safely extract return type annotation
            try:
                return_type = ast.unparse(node.returns).strip() if node.returns else "None"
            except Exception:
                return_type = "Unknown"

            components.append({
                "type": "function",
                "name": node.name,
                "parameters": parameters,
                "returns": return_type,
                "docstring": docstring if docstring else "None",
                "lineno": node.lineno
            })
            
        elif isinstance(node, ast.ClassDef):
            docstring = _extract_docstring(node)
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_docstring = _extract_docstring(item)
                    method_parameters = [f"{arg.arg}" for arg in item.args.args]

                    # Safely extract return type annotation
                    try:
                        method_return_type = ast.unparse(item.returns).strip() if item.returns else "None"
                    except Exception:
                        method_return_type = "Unknown"

                    methods.append({
                        "name": item.name,
                        "parameters": method_parameters,
                        "returns": method_return_type,
                        "docstring": method_docstring if method_docstring else "None",
                    })

            components.append({
                "type": "class",
                "name": node.name,
                "docstring": docstring if docstring else "None",
                "methods": methods,
                "lineno": node.lineno
            })

    result = {
        "analysis_summary": f"This Python file contains {len([c for c in components if c['type'] == 'class'])} classes and {len([c for c in components if c['type'] == 'function'])} functions.",
        "components": components
    }
    
    return json.dumps(result, indent=2)

# --- WebSearchTool Function ---

def web_search(query: str) -> str:
    """
    Performs a web search for the given query (e.g., Google). Used to gather external info or concepts.

    **CURRENT IMPLEMENTATION: SIMULATION**
    This is a simplified mock implementation for demonstration. In production, this would
    integrate with a real search API (DuckDuckGo, SerpAPI, Google Custom Search, etc.).

    Args:
        query (str): Search query string. Can be library names (e.g., "FastAPI"),
            technical concepts (e.g., "what is ASGI"), or framework questions.

    Returns:
        str: Simulated search result as a plain text string. Format:
            "Search Result: [information about the query]"

    Current Behavior:
        - "FastAPI" queries -> Returns info about FastAPI framework
        - "uvicorn" queries -> Returns info about Uvicorn ASGI server
        - Other queries -> Returns generic placeholder message

    Production Implementation TODO:
        Replace with one of:
        - DuckDuckGo API (free, no API key required)
        - SerpAPI (paid, reliable)
        - Google Custom Search API (limited free tier)

    Example:
        >>> result = web_search("What is FastAPI")
        >>> print(result)
        Search Result: FastAPI is a modern, high-performance Python web framework.

    Usage in Agent Workflow:
        1. Agent encounters unknown library in requirements.txt (e.g., "boto3")
        2. Agent calls web_search("boto3 Python library")
        3. Agent uses result to add context to README (e.g., "AWS integration")

    Note:
        Currently this tool provides limited value due to simulation. Priority for
        production upgrade.
    """
    # This is a simulation for the LLM agent
    if "FastAPI" in query:
        return "Search Result: FastAPI is a modern, high-performance Python web framework."
    elif "uvicorn" in query:
        return "Search Result: Uvicorn is an ASGI server."
    else:
        return f"Search result found for '{query}': (Example Answer: The requested information is here.)"

# --- RAG Tool Functions ---

def init_knowledge_base(documents: list[Document]) -> str:
    """
    Initializes and persists Klaro's knowledge base (Vector Database). Must be called once.

    Sets up the RAG (Retrieval-Augmented Generation) system by:
    1. Chunking provided documents into smaller segments
    2. Generating embeddings using OpenAI's text-embedding-3-small model
    3. Storing embeddings in ChromaDB (persistent local vector database)
    4. Creating a global retriever instance for retrieve_knowledge() to use

    Args:
        documents (list[Document]): LangChain Document objects to index.
            Each Document should have:
            - page_content (str): The text content to embed
            - metadata (dict): Source information (e.g., {"source": "style_guide"})

    Returns:
        str: Status message indicating success or failure. Format:
            Success: "Knowledge base (ChromaDB) successfully initialized at {path}. X chunks indexed."
            Warning: "Warning: No documents provided for initialization."
            Error: "Error initializing knowledge base: {exception_message}"

    Side Effects:
        - Creates/updates ./klaro_db directory with ChromaDB files
        - Sets global KLARO_RETRIEVER variable for use by retrieve_knowledge()
        - Requires OPENAI_API_KEY environment variable

    Chunking Strategy:
        - chunk_size: 1000 characters (balances context vs. specificity)
        - chunk_overlap: 200 characters (prevents information loss at boundaries)

    Example:
        >>> from langchain_core.documents import Document
        >>> docs = [Document(
        ...     page_content="README sections: # Title, ## Setup, ## Usage",
        ...     metadata={"source": "Klaro_Style_Guide"}
        ... )]
        >>> result = init_knowledge_base(docs)
        >>> print(result)
        Knowledge base (ChromaDB) successfully initialized at ./klaro_db. 1 chunks indexed.

    Usage in Agent Workflow:
        1. Called once at agent startup in run_klaro_langgraph()
        2. Indexes DEFAULT_GUIDE_CONTENT (documentation style guidelines)
        3. Agent later calls retrieve_knowledge() to ensure README follows style

    Error Handling:
        - Missing API key: Returns error message (doesn't crash agent)
        - Empty documents list: Returns warning message
        - ChromaDB errors: Returns error message with exception details

    Note:
        - Vector database persists across runs (stored in ./klaro_db)
        - Re-running with different documents will recreate the database
        - Embeddings are generated via OpenAI API (costs ~$0.00001 per document)
    """
    global KLARO_RETRIEVER

    if not documents:
        return "Warning: No documents provided for initialization."

    try:
        # 1. Chunking
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)

        # 2. Embeddings and Vector Store Creation
        # This requires the OPENAI_API_KEY environment variable to be set.
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # Chroma is used as the local vector store
        vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=embeddings,
            persist_directory=VECTOR_DB_PATH
        )

        # 3. Set Retriever Globally
        KLARO_RETRIEVER = vectorstore.as_retriever(search_kwargs={"k": 3})

        return f"Knowledge base (ChromaDB) successfully initialized at {VECTOR_DB_PATH}. {len(texts)} chunks indexed."
    except Exception as e:
        return f"Error initializing knowledge base: {e}"


def retrieve_knowledge(query: str) -> str:
    """
    Retrieves the most relevant information from the Vector Database (ChromaDB) for a given query (RAG).

    Performs semantic search over the indexed knowledge base to find documentation guidelines
    relevant to the agent's current task. This implements the "Retrieval" part of
    Retrieval-Augmented Generation (RAG), ensuring the agent's output follows project style.

    Args:
        query (str): Natural language query describing what information is needed.
            Examples:
            - "README style guidelines"
            - "How to format code examples"
            - "Required sections for documentation"

    Returns:
        str: Formatted string containing top k retrieved documents. Format:
            Retrieved Information:
            Source 1: [relevant text chunk 1]
            ---
            Source 2: [relevant text chunk 2]
            ---
            Source 3: [relevant text chunk 3]

            If retriever not initialized:
            "Error: Knowledge base not initialized. Please ensure init_knowledge_base was called."

            On retrieval error:
            "Error retrieving knowledge: {exception_message}"

    Retrieval Configuration:
        - Top-k: 3 documents (configured via search_kwargs={"k": 3})
        - Similarity: Cosine similarity between query embedding and document embeddings
        - Model: Same embedding model as used in init_knowledge_base

    Example:
        >>> # After init_knowledge_base has been called
        >>> guidelines = retrieve_knowledge("README format requirements")
        >>> print(guidelines)
        Retrieved Information:
        Source 1: # Klaro Project Documentation Style Guide:
        All README.md documents must include: # Project Name, ## Setup, ## Usage...
        ---
        Source 2: Code examples must always be formatted with triple backticks...

    Usage in Agent Workflow:
        1. Agent explores codebase, analyzes files
        2. Agent prepares to write final README
        3. Agent calls retrieve_knowledge("README style guidelines")
        4. Agent incorporates retrieved guidelines into final output
        5. This ensures consistency with project documentation standards

    Error Handling:
        - Retriever not initialized: Returns error message (agent must call init first)
        - Network/API errors: Returns error message with details
        - Never raises exceptions

    Note:
        - This tool is MANDATORY before final answer (enforced in SYSTEM_PROMPT)
        - Semantic search means exact keyword matches aren't required
        - Quality depends on documents provided to init_knowledge_base
        - Results are ranked by relevance (most similar first)
    """
    global KLARO_RETRIEVER

    if KLARO_RETRIEVER is None:
        return "Error: Knowledge base not initialized. Please ensure init_knowledge_base was called."
        
    try:
        # Use the global retriever instance
        docs = KLARO_RETRIEVER.invoke(query)
        
        # Format the results for the LLM
        result_texts = [f"Source {i+1}: {doc.page_content}" for i, doc in enumerate(docs)]
        
        return "Retrieved Information:\n" + "\n---\n".join(result_texts)
        
    except Exception as e:
        return f"Error retrieving knowledge: {e}"