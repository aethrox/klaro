import os
import re
import ast
import json

# --- RAG/Vector Database Imports (Aşama 3) ---
from langchain_openai import OpenAIEmbeddings 
from langchain_community.vectorstores import Chroma 
# Doğru paket yoluna yönlendirildi
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
    """Translates simple .gitignore patterns into Regex patterns."""
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
    """Checks if the given path matches any ignore patterns."""
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
    """Lists files and folders in the given directory in a tree-like structure. Filters ignored paths."""
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
    """Reads and returns the content of the specified file path."""
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
    """Extracts the docstring from an AST node."""
    if not node.body or not isinstance(node.body[0], ast.Expr):
        return None
    if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
        return node.body[0].value.value
    return None


def analyze_code(code_content: str) -> str:
    """
    Analyzes Python code content using AST (Abstract Syntax Tree).
    Extracts classes, functions, parameters, and docstrings, returning the output in JSON format.
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
    """Performs a web search for the given query (e.g., Google). Used to gather external info or concepts."""
    # This is a simulation for the LLM agent
    if "FastAPI" in query:
        return "Search Result: FastAPI is a modern, high-performance Python web framework."
    elif "uvicorn" in query:
        return "Search Result: Uvicorn is an ASGI server."
    else:
        return f"Search result found for '{query}': (Example Answer: The requested information is here.)"

# --- RAG Tool Functions ---

def init_knowledge_base(documents: list[Document]) -> str:
    """Initializes and persists Klaro's knowledge base (Vector Database). Must be called once."""
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
    """Retrieves the most relevant information from the Vector Database (ChromaDB) for a given query (RAG)."""
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