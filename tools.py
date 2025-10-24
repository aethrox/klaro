"""
Klaro Custom Tools Module

This module provides the core toolset that enables the Klaro agent to interact with codebases,
analyze code structures, and access knowledge bases. These tools form the agent's capabilities
for autonomous documentation generation.

Tool Categories:
    1. **Codebase Exploration**:
       - list_files: Directory traversal with .gitignore filtering
       - read_file: File content reading with UTF-8 encoding

    2. **Code Analysis**:
       - analyze_code: AST-based Python code structure extraction
       - _extract_docstring: Helper for extracting docstrings from AST nodes

    3. **External Knowledge**:
       - web_search: External information gathering (simulated)
       - init_knowledge_base: RAG system initialization with ChromaDB
       - retrieve_knowledge: Semantic search in vector database

    4. **Support Functions**:
       - get_gitignore_patterns: Converts .gitignore rules to regex
       - is_ignored: Checks if path matches ignore patterns

Architecture Patterns:
    **Agent-Centric Design**: Tools are designed to be called incrementally rather than
    loading entire codebases at once. This overcomes LLM context window limitations and
    enables intelligent navigation of large projects.

    **Hybrid Analysis (AST + LLM)**: The analyze_code tool uses a two-stage approach:
    1. Programmatic extraction via Python's ast module (structure, signatures, types)
    2. Semantic interpretation by the LLM (purpose, relationships, summaries)

Dependencies:
    - ast: Python's built-in Abstract Syntax Tree parser
    - OpenAI Embeddings: text-embedding-3-small model for vector generation
    - ChromaDB: Local vector database for RAG knowledge base
    - RecursiveCharacterTextSplitter: Document chunking (1000 chars, 200 overlap)

Global State:
    - VECTOR_DB_PATH: Location of persisted ChromaDB database (./klaro_db)
    - KLARO_RETRIEVER: Global VectorStoreRetriever instance (initialized once)
    - IGNORE_PATTERNS: Compiled regex patterns from hardcoded .gitignore rules
    - GITIGNORE_CONTENT: Standard Python .gitignore template

Usage Patterns:
    These tools are wrapped as LangChain Tool objects in main.py:
    >>> from langchain_core.tools import Tool
    >>> tools = [
    ...     Tool(name="list_files", func=list_files, description=list_files.__doc__),
    ...     Tool(name="analyze_code", func=analyze_code, description=analyze_code.__doc__),
    ...     # ... other tools
    ... ]

    The agent calls them via LangGraph's ToolNode based on LLM decisions.

RAG System Flow:
    1. Initialization (once per run):
       >>> docs = [Document(page_content=style_guide, metadata={"source": "guide"})]
       >>> init_knowledge_base(docs)  # Creates ChromaDB at ./klaro_db

    2. Retrieval (multiple times):
       >>> results = retrieve_knowledge("README style guidelines")
       # Returns top 3 most relevant chunks from vector store

Technical Notes:
    - All file operations assume UTF-8 encoding
    - .gitignore filtering includes common patterns (__pycache__, .git, etc.)
    - AST analysis only supports Python code (SyntaxError for other languages)
    - Vector embeddings require OPENAI_API_KEY environment variable
    - ChromaDB persists to disk (survives restarts)
"""

import os
import re
import ast
import json

# --- RAG/Vector Database Imports ---
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
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
*.pyc
*.pyo
*.pyd
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# UV
#   Similar to Pipfile.lock, it is generally recommended to include uv.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#uv.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
#poetry.lock

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#pdm.lock
#   pdm stores project-wide configurations in .pdm.toml, but it is recommended to not include it
#   in version control.
#   https://pdm.fming.dev/latest/usage/project/#working-with-version-control
.pdm.toml
.pdm-python
.pdm-build/

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
*env/
*db/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#  JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#  be found at https://github.com/github/gitignore/blob/main/Global/JetBrains.gitignore
#  and can be added to the global gitignore or merged into this file.  For a more nuclear
#  option (not recommended) you can uncomment the following to ignore the entire idea folder.
#.idea/

# Ruff stuff:
.ruff_cache/

# PyPI configuration file
.pypirc

# Cursor  
#  Cursor is an AI-powered code editor.`.cursorignore` specifies files/directories to 
#  exclude from AI features like autocomplete and code analysis. Recommended for sensitive data
#  refer to https://docs.cursor.com/context/ignore-files
.cursorignore
.cursorindexingignore
"""

def get_gitignore_patterns(gitignore_content: str) -> list[str]:
    r"""Translates .gitignore patterns into compiled regex patterns for file filtering.

    This function parses .gitignore syntax and converts common glob patterns
    (*, **, /, etc.) into Python regular expressions that can be used for
    path matching during directory traversal.

    Args:
        gitignore_content (str): Raw content of a .gitignore file, with one
            pattern per line. Lines starting with # are treated as comments
            and empty lines are ignored.

    Returns:
        list[str]: List of regex pattern strings that can be used with re.search()
            to match file paths. Patterns handle:
            - Single asterisk (*) -> matches any characters except /
            - Double asterisk (**) -> matches any characters including /
            - Trailing slash (/) -> matches directories
            - Regular paths -> matches files or directories

    Example:
        >>> patterns = get_gitignore_patterns("*.py\n__pycache__/\n")
        >>> patterns
        ['(.*/)?\[\^/\]*\\.py$', '(.*/)?__pycache__(/.*)?$']
        >>> # Use with: re.search(pattern, "path/to/file.py")
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
    """Checks if a file or directory path should be ignored based on .gitignore rules.

    This function tests the provided path against all compiled .gitignore patterns
    (from IGNORE_PATTERNS) and explicit project-specific ignores (.git, .env).
    Used during directory traversal to filter out unwanted files.

    Args:
        path (str): Relative or absolute file/directory path to check.
            Backslashes are automatically converted to forward slashes for
            cross-platform compatibility.

    Returns:
        bool: True if the path should be ignored (matches a pattern),
            False if it should be included in directory listings.

    Example:
        >>> is_ignored("__pycache__/main.cpython-311.pyc")
        True
        >>> is_ignored("src/main.py")
        False
        >>> is_ignored(".git/config")
        True
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
    """Lists files and folders in a directory as a tree structure with .gitignore filtering.

    Recursively traverses the specified directory and generates a hierarchical
    tree view of files and subdirectories. Automatically filters out paths
    matching .gitignore patterns (defined in IGNORE_PATTERNS).

    Args:
        directory (str, optional): Path to the directory to list. Can be relative
            or absolute. Defaults to '.' (current working directory).

    Returns:
        str: Multi-line string representation of the directory tree using
            box-drawing characters (├──, |). Format example:
            ```
            / project_name/
            ├──  .gitignore
            ├──  README.md
            ├──  src/
            |   ├──  main.py
            ```

    Raises:
        Returns error message string if directory doesn't exist or is not a directory.

    Example:
        >>> tree = list_files(".")
        >>> print(tree)
        / klaro/
        ├──  main.py
        ├──  tools.py
        ├──  prompts.py
        ├──  requirements.txt
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
    """Reads and returns the complete content of a file with UTF-8 encoding.

    Opens and reads the entire contents of the specified file into a string.
    Designed for reading source code files as part of codebase analysis.

    Args:
        file_path (str): Absolute or relative path to the file to read.
            Must point to a file (not a directory).

    Returns:
        str: Complete file content as a string, or error message if operation fails.
            Error messages have format: "Error: <specific issue>"

    Raises:
        Returns error message string (doesn't raise exceptions) in these cases:
        - File doesn't exist
        - Path points to a directory
        - UTF-8 decoding fails
        - Permission denied

    Example:
        >>> content = read_file("main.py")
        >>> print(content[:50])
        import os
        from typing import TypedDict, Annotated
        >>> read_file("nonexistent.txt")
        "Error: File path not found or is not a file: 'nonexistent.txt'"
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
    """Extracts the docstring from an AST node (function or class).

    Helper function that inspects the body of an AST node (FunctionDef, AsyncFunctionDef,
    or ClassDef) and extracts the docstring if present. Follows Python's docstring
    convention: the first statement must be a string literal expression.

    Args:
        node: AST node object (typically ast.FunctionDef, ast.AsyncFunctionDef, or
            ast.ClassDef) that may contain a docstring.

    Returns:
        str or None: The docstring text if found, None if no docstring exists.
            Only extracts string constants (ast.Constant nodes with str value).

    Example:
        >>> import ast
        >>> code = '''
        ... def example():
        ...     \"\"\"This is a docstring.\"\"\"
        ...     pass
        ... '''
        >>> tree = ast.parse(code)
        >>> func_node = tree.body[0]
        >>> _extract_docstring(func_node)
        'This is a docstring.'
    """
    if not node.body or not isinstance(node.body[0], ast.Expr):
        return None
    if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
        return node.body[0].value.value
    return None


def analyze_code(code_content: str) -> str:
    """Analyzes Python code structure using AST and returns structured JSON data.

    Performs programmatic code analysis by parsing Python source code into an
    Abstract Syntax Tree (AST) and extracting structured information about
    classes, functions, methods, parameters, return types, and docstrings.

    This is the core code analysis tool used by the Klaro agent. Unlike LLM-based
    analysis, AST extraction is deterministic and prevents hallucinations, providing
    reliable structural data for documentation generation.

    Args:
        code_content (str): Raw Python source code to analyze. Must be syntactically
            valid Python code (will be parsed with ast.parse()).

    Returns:
        str: JSON-formatted string containing analysis results with structure:
            {
                "analysis_summary": "High-level summary of file contents",
                "components": [
                    {
                        "type": "function" | "class",
                        "name": "component_name",
                        "parameters": ["param1", "param2"],  # for functions
                        "returns": "return_type",             # for functions
                        "docstring": "extracted docstring",
                        "lineno": 42,
                        "methods": [...]  # for classes only
                    }
                ]
            }

    Raises:
        Returns JSON error object (doesn't raise exceptions) for:
        - Empty code_content: {"error": "Code content to analyze is empty."}
        - SyntaxError: {"error": "Code parsing error (SyntaxError): <details>"}
        - Other exceptions: {"error": "Unexpected error during code analysis: <details>"}

    Example:
        >>> code = '''
        ... def greet(name: str) -> str:
        ...     \"\"\"Returns a greeting message.\"\"\"
        ...     return f"Hello, {name}"
        ... '''
        >>> result = analyze_code(code)
        >>> import json
        >>> data = json.loads(result)
        >>> data["components"][0]["name"]
        'greet'
        >>> data["components"][0]["docstring"]
        'Returns a greeting message.'
    """
    if not code_content:
        return json.dumps({"error": "Code content to analyze is empty."})

    components = []

    # --- STEP 1: Parse Python source code into an Abstract Syntax Tree (AST) ---
    # AST is a tree representation of the syntactic structure of the code
    # This allows programmatic analysis without executing the code
    try:
        tree = ast.parse(code_content)
    except SyntaxError as e:
        # Return JSON error if code has syntax errors (invalid Python)
        return json.dumps({"error": f"Code parsing error (SyntaxError): {e}"})
    except Exception as e:
        # Catch unexpected parsing failures
        return json.dumps({"error": f"Unexpected error during code analysis: {e}"})

    # --- STEP 2: Walk the AST and extract code components ---
    # ast.walk() performs a depth-first traversal of all nodes in the tree
    # We're looking for FunctionDef, AsyncFunctionDef, and ClassDef nodes
    for node in ast.walk(tree):
        # --- CASE 1: Function or Async Function Definition ---
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Extract the docstring (first string literal in function body)
            docstring = _extract_docstring(node)

            # Extract parameter names from the function signature
            # node.args.args is a list of ast.arg objects (each has .arg attribute with param name)
            parameters = [f"{arg.arg}" for arg in node.args.args]

            # Extract return type annotation (if present)
            # node.returns contains the AST node for the return type hint (e.g., "-> str")
            # ast.unparse() converts AST node back to source code string
            try:
                return_type = ast.unparse(node.returns).strip() if node.returns else "None"
            except Exception:
                # If unparsing fails (rare), mark as Unknown
                return_type = "Unknown"

            # Build the function component dictionary
            components.append({
                "type": "function",
                "name": node.name,              # Function name
                "parameters": parameters,        # List of parameter names
                "returns": return_type,          # Return type annotation
                "docstring": docstring if docstring else "None",
                "lineno": node.lineno            # Line number where function is defined
            })

        # --- CASE 2: Class Definition ---
        elif isinstance(node, ast.ClassDef):
            # Extract class-level docstring
            docstring = _extract_docstring(node)

            # Extract all methods from the class body
            methods = []
            # node.body contains all statements inside the class definition
            for item in node.body:
                # Only process method definitions (functions inside classes)
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_docstring = _extract_docstring(item)

                    # Extract method parameters (same logic as standalone functions)
                    method_parameters = [f"{arg.arg}" for arg in item.args.args]

                    # Extract method return type annotation
                    try:
                        method_return_type = ast.unparse(item.returns).strip() if item.returns else "None"
                    except Exception:
                        method_return_type = "Unknown"

                    # Build the method dictionary (similar to function, but without lineno)
                    methods.append({
                        "name": item.name,
                        "parameters": method_parameters,
                        "returns": method_return_type,
                        "docstring": method_docstring if method_docstring else "None",
                    })

            # Build the class component dictionary
            components.append({
                "type": "class",
                "name": node.name,               # Class name
                "docstring": docstring if docstring else "None",
                "methods": methods,              # List of method dictionaries
                "lineno": node.lineno            # Line number where class is defined
            })

    # --- STEP 3: Generate summary and format results as JSON ---
    # Count classes and functions for the analysis summary
    result = {
        "analysis_summary": f"This Python file contains {len([c for c in components if c['type'] == 'class'])} classes and {len([c for c in components if c['type'] == 'function'])} functions.",
        "components": components
    }
    
    return json.dumps(result, indent=2)

# --- WebSearchTool Function ---

def web_search(query: str) -> str:
    """Performs simulated web search to gather external information about libraries and concepts.

    This tool is currently a placeholder that returns hardcoded responses for common
    queries. Designed to provide the agent with external knowledge about frameworks,
    libraries, and programming concepts that may not be evident from code analysis alone.

    Args:
        query (str): Search query string. Typically names of libraries, frameworks,
            or technical concepts (e.g., "FastAPI", "uvicorn", "ChromaDB").

    Returns:
        str: Simulated search result as a plain text string. Format:
            "Search Result: <information about query>"

            Currently supports:
            - "FastAPI" -> Returns FastAPI description
            - "uvicorn" -> Returns uvicorn description
            - Other queries -> Generic placeholder response

    Example:
        >>> result = web_search("FastAPI")
        >>> print(result)
        Search Result: FastAPI is a modern, high-performance Python web framework.
        >>> result = web_search("unknown library")
        >>> print(result)
        Search result found for 'unknown library': (Example Answer: The requested information is here.)

    Note:
        Future versions should integrate with real search APIs (DuckDuckGo, SerpAPI, etc.)
        or web scraping for actual external information retrieval.
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
    """Initializes the RAG knowledge base (ChromaDB) with style guide documents.

    Creates and persists a vector database containing embedded documentation style guides
    and reference materials. This enables the agent to retrieve relevant style guidelines
    during documentation generation, ensuring consistency and adherence to standards.

    Must be called once at agent startup before any retrieve_knowledge calls. The database
    is persisted to disk at VECTOR_DB_PATH (./klaro_db) and survives across runs.

    Args:
        documents (list[Document]): List of LangChain Document objects to index.
            Each Document should have:
            - page_content (str): The actual text content to embed
            - metadata (dict): Source information and tags

    Returns:
        str: Success or warning message with format:
            - Success: "Knowledge base (ChromaDB) successfully initialized at <path>. <n> chunks indexed."
            - Warning: "Warning: No documents provided for initialization."
            - Error: "Error initializing knowledge base: <exception details>"

    Raises:
        Returns error message string (doesn't raise exceptions) if:
        - OpenAI API key is missing or invalid (embeddings fail)
        - ChromaDB initialization fails
        - Document processing encounters errors

    Example:
        >>> from langchain_core.documents import Document
        >>> style_guide = Document(
        ...     page_content="# Style Guide\\n## Format all READMEs with H1, H2 headings...",
        ...     metadata={"source": "Company_Style_Guide"}
        ... )
        >>> result = init_knowledge_base([style_guide])
        >>> print(result)
        Knowledge base (ChromaDB) successfully initialized at ./klaro_db. 3 chunks indexed.

    Technical Details:
        - Uses RecursiveCharacterTextSplitter (chunk_size=1000, overlap=200)
        - Embeddings: OpenAI text-embedding-3-small model
        - Vector store: ChromaDB (persisted locally)
        - Sets global KLARO_RETRIEVER for use by retrieve_knowledge()
    """
    # Access the global retriever variable (will be set after initialization)
    global KLARO_RETRIEVER

    # Validate input: ensure at least one document is provided
    if not documents:
        return "Warning: No documents provided for initialization."

    try:
        # --- STEP 1: Document Chunking (Text Splitting) ---
        # Large documents are split into smaller chunks for better retrieval accuracy
        # RecursiveCharacterTextSplitter uses semantic boundaries (paragraphs, sentences)
        # rather than arbitrary character positions
        #
        # chunk_size=1000: Maximum characters per chunk (balances context vs. precision)
        # chunk_overlap=200: Characters shared between consecutive chunks (prevents
        #                    information loss at boundaries)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        # texts is now a list of Document objects, each with page_content <= 1000 chars

        # --- STEP 2: Generate Embeddings and Create Vector Store ---
        # Embeddings convert text chunks into high-dimensional vectors (numbers)
        # that capture semantic meaning. Similar concepts have similar vectors.
        #
        # This requires the OPENAI_API_KEY environment variable to be set.
        # Model: text-embedding-3-small (1536 dimensions, cost-effective)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # ChromaDB is a local vector database (stored on disk)
        # from_documents() performs two operations:
        # 1. Calls embeddings.embed_documents() to convert all text chunks to vectors
        # 2. Stores vectors + original text in ChromaDB at VECTOR_DB_PATH
        #
        # persist_directory: Database is saved to disk (survives restarts)
        vectorstore = Chroma.from_documents(
            documents=texts,              # List of Document chunks to embed
            embedding=embeddings,         # OpenAI embedding function
            persist_directory=VECTOR_DB_PATH  # Path to ./klaro_db directory
        )

        # --- STEP 3: Create and Store Global Retriever ---
        # Convert the vector store into a retriever (search interface)
        # as_retriever() wraps the vector store with a retrieval API
        #
        # search_kwargs={"k": 3}: Return top 3 most similar chunks for each query
        # Uses cosine similarity to compare query vector with stored vectors
        KLARO_RETRIEVER = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Return success message with statistics
        return f"Knowledge base (ChromaDB) successfully initialized at {VECTOR_DB_PATH}. {len(texts)} chunks indexed."
    except Exception as e:
        # Catch and return errors (missing API key, ChromaDB failures, etc.)
        return f"Error initializing knowledge base: {e}"


def retrieve_knowledge(query: str) -> str:
    """Retrieves relevant style guide information from the vector database via semantic search.

    Performs RAG (Retrieval-Augmented Generation) by searching the ChromaDB knowledge base
    for content semantically similar to the query. Used by the agent to fetch documentation
    standards and style guidelines before generating final output.

    The agent MUST call this tool before producing final documentation to ensure
    consistency with project style guides (enforced by system prompt).

    Args:
        query (str): Natural language query describing the information needed.
            Examples:
            - "README style guidelines"
            - "How to format API documentation sections"
            - "Required sections for technical documentation"

    Returns:
        str: Formatted string containing top 3 most relevant chunks from the knowledge base.
            Format:
            ```
            Retrieved Information:
            Source 1: <chunk content>
            ---
            Source 2: <chunk content>
            ---
            Source 3: <chunk content>
            ```

            Or error message if knowledge base is not initialized:
            "Error: Knowledge base not initialized. Please ensure init_knowledge_base was called."

    Raises:
        Returns error message string (doesn't raise exceptions) if:
        - KLARO_RETRIEVER is None (init_knowledge_base not called)
        - Query execution fails
        - Vector database access error

    Example:
        >>> result = retrieve_knowledge("README style guidelines")
        >>> print(result)
        Retrieved Information:
        Source 1: # README Format
        All READMEs must include ## Setup and ## Usage sections...
        ---
        Source 2: Use professional technical tone with code examples...
        ---
        Source 3: Headings must use # and ## format...

    Technical Details:
        - Uses global KLARO_RETRIEVER instance (set by init_knowledge_base)
        - Retrieves k=3 most similar chunks (configured in init_knowledge_base)
        - Similarity computed via cosine distance on OpenAI embeddings
    """
    # Access the global retriever (must be initialized by init_knowledge_base first)
    global KLARO_RETRIEVER

    # --- VALIDATION: Check if knowledge base has been initialized ---
    # KLARO_RETRIEVER is None until init_knowledge_base() is called
    # This ensures the agent follows the correct initialization sequence
    if KLARO_RETRIEVER is None:
        return "Error: Knowledge base not initialized. Please ensure init_knowledge_base was called."

    try:
        # --- STEP 1: Perform Semantic Search ---
        # The retriever performs the following operations:
        # 1. Convert the query string into an embedding vector (using OpenAI embeddings)
        # 2. Compare query vector with all stored document vectors (cosine similarity)
        # 3. Return the k=3 most similar document chunks (highest similarity scores)
        #
        # invoke() is the standard LangChain retriever interface (replaces get_relevant_documents)
        docs = KLARO_RETRIEVER.invoke(query)
        # docs is a list of Document objects, each with .page_content and .metadata

        # --- STEP 2: Format Results for LLM Consumption ---
        # Convert the list of Document objects into a human-readable string
        # Each chunk is labeled with a source number for reference
        result_texts = [f"Source {i+1}: {doc.page_content}" for i, doc in enumerate(docs)]

        # Join all chunks with separator for clarity
        # The LLM will use this information to guide documentation generation
        return "Retrieved Information:\n" + "\n---\n".join(result_texts)

    except Exception as e:
        # Catch errors: query embedding failures, ChromaDB access issues, etc.
        return f"Error retrieving knowledge: {e}"