"""
Unit Tests for Klaro Custom Tools

This module contains comprehensive unit tests for all custom tools defined in tools.py:
    - list_files: Directory listing with .gitignore filtering
    - read_file: File reading with error handling
    - analyze_code: AST-based Python code analysis
    - web_search: Simulated external information gathering
    - init_knowledge_base: RAG knowledge base initialization
    - retrieve_knowledge: Semantic search in vector database
    - Helper functions: is_ignored, get_gitignore_patterns

Test Coverage:
    - Normal operation (happy path)
    - Edge cases (empty inputs, nonexistent files)
    - Error handling (syntax errors, missing files)
    - .gitignore pattern matching
    - RAG system integration

Running:
    pytest tests/test_tools.py -v
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock

from tools import (
    list_files,
    read_file,
    analyze_code,
    web_search,
    init_knowledge_base,
    retrieve_knowledge,
    is_ignored,
    get_gitignore_patterns,
    _extract_docstring
)


# --- Tests for list_files ---

@pytest.mark.unit
def test_list_files_current_directory(temp_dir):
    """Test list_files on a temporary directory with sample structure."""
    # Create sample structure
    os.makedirs(os.path.join(temp_dir, "src"))
    os.makedirs(os.path.join(temp_dir, "tests"))
    Path(os.path.join(temp_dir, "main.py")).touch()
    Path(os.path.join(temp_dir, "README.md")).touch()
    Path(os.path.join(temp_dir, "src", "module.py")).touch()

    result = list_files(temp_dir)

    # Verify output contains expected files
    assert "main.py" in result
    assert "README.md" in result
    assert "src/" in result
    assert "tests/" in result
    assert "module.py" in result


@pytest.mark.unit
def test_list_files_nonexistent_directory():
    """Test list_files with a directory that doesn't exist."""
    result = list_files("/nonexistent/path/12345")

    assert "Error" in result
    assert "not found" in result.lower() or "not a directory" in result.lower()


@pytest.mark.unit
def test_list_files_with_gitignore_filtering(temp_dir):
    """Test that list_files properly filters .gitignore patterns."""
    # Create files that should be ignored
    os.makedirs(os.path.join(temp_dir, "__pycache__"))
    os.makedirs(os.path.join(temp_dir, ".git"))
    Path(os.path.join(temp_dir, "test.py")).touch()
    Path(os.path.join(temp_dir, "__pycache__", "cached.pyc")).touch()
    Path(os.path.join(temp_dir, ".git", "config")).touch()

    result = list_files(temp_dir)

    # Should include test.py but not __pycache__ or .git
    assert "test.py" in result
    assert "__pycache__" not in result
    assert ".git" not in result
    assert "cached.pyc" not in result


# --- Tests for read_file ---

@pytest.mark.unit
def test_read_file_existing_file(temp_dir):
    """Test read_file with a valid existing file."""
    file_path = os.path.join(temp_dir, "test.txt")
    content = "This is a test file.\nLine 2."

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    result = read_file(file_path)

    assert result == content
    assert "Line 2" in result


@pytest.mark.unit
def test_read_file_nonexistent_file():
    """Test read_file with a file that doesn't exist."""
    result = read_file("/nonexistent/file.txt")

    assert "Error" in result
    assert "not found" in result.lower() or "not a file" in result.lower()


@pytest.mark.unit
def test_read_file_directory_instead_of_file(temp_dir):
    """Test read_file when given a directory path instead of file."""
    result = read_file(temp_dir)

    assert "Error" in result
    assert "directory" in result.lower()


@pytest.mark.unit
def test_read_file_utf8_encoding(temp_dir):
    """Test read_file handles UTF-8 encoded content correctly."""
    file_path = os.path.join(temp_dir, "unicode.txt")
    content = "Hello 世界! 🚀 Café"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    result = read_file(file_path)

    assert result == content
    assert "世界" in result
    assert "🚀" in result


# --- Tests for analyze_code ---

@pytest.mark.unit
def test_analyze_code_valid_python(sample_python_code):
    """Test analyze_code with valid Python code."""
    result = analyze_code(sample_python_code)
    data = json.loads(result)

    # Check structure
    assert "analysis_summary" in data
    assert "components" in data

    # Check components extracted
    component_names = [c["name"] for c in data["components"]]
    assert "greet" in component_names
    assert "Calculator" in component_names

    # Check function details
    greet_func = next(c for c in data["components"] if c["name"] == "greet")
    assert greet_func["type"] == "function"
    assert "name" in greet_func["parameters"]
    assert greet_func["returns"] == "str"
    assert "greeting" in greet_func["docstring"].lower()

    # Check class details
    calc_class = next(c for c in data["components"] if c["name"] == "Calculator")
    assert calc_class["type"] == "class"
    assert "methods" in calc_class
    method_names = [m["name"] for m in calc_class["methods"]]
    assert "add" in method_names
    assert "multiply" in method_names


@pytest.mark.unit
def test_analyze_code_invalid_python(invalid_python_code):
    """Test analyze_code with syntactically invalid Python code."""
    result = analyze_code(invalid_python_code)
    data = json.loads(result)

    assert "error" in data
    assert "SyntaxError" in data["error"] or "parsing error" in data["error"].lower()


@pytest.mark.unit
def test_analyze_code_empty_input():
    """Test analyze_code with empty code content."""
    result = analyze_code("")
    data = json.loads(result)

    assert "error" in data
    assert "empty" in data["error"].lower()


@pytest.mark.unit
def test_analyze_code_function_without_docstring():
    """Test analyze_code extracts functions without docstrings."""
    code = """
def no_doc_function(x, y):
    return x + y
"""
    result = analyze_code(code)
    data = json.loads(result)

    func = data["components"][0]
    assert func["name"] == "no_doc_function"
    assert func["docstring"] == "None"


@pytest.mark.unit
def test_analyze_code_async_function():
    """Test analyze_code handles async functions."""
    code = """
async def async_task(duration: float) -> str:
    '''An async function.'''
    return "done"
"""
    result = analyze_code(code)
    data = json.loads(result)

    func = data["components"][0]
    assert func["name"] == "async_task"
    assert func["type"] == "function"
    assert "duration" in func["parameters"]


# --- Tests for _extract_docstring helper ---

@pytest.mark.unit
def test_extract_docstring():
    """Test _extract_docstring helper function."""
    import ast

    code_with_doc = '''
def example():
    """This is a docstring."""
    pass
'''
    tree = ast.parse(code_with_doc)
    func_node = tree.body[0]

    docstring = _extract_docstring(func_node)
    assert docstring == "This is a docstring."


@pytest.mark.unit
def test_extract_docstring_none():
    """Test _extract_docstring returns None when no docstring."""
    import ast

    code_without_doc = '''
def example():
    pass
'''
    tree = ast.parse(code_without_doc)
    func_node = tree.body[0]

    docstring = _extract_docstring(func_node)
    assert docstring is None


# --- Tests for web_search ---

@pytest.mark.unit
def test_web_search_fastapi():
    """Test web_search returns expected result for FastAPI query."""
    result = web_search("FastAPI")

    assert "FastAPI" in result
    assert "web framework" in result.lower()


@pytest.mark.unit
def test_web_search_uvicorn():
    """Test web_search returns expected result for uvicorn query."""
    result = web_search("uvicorn")

    assert "uvicorn" in result.lower()
    assert "ASGI" in result


@pytest.mark.unit
def test_web_search_unknown_query():
    """Test web_search returns generic response for unknown queries."""
    result = web_search("unknown_library_xyz")

    assert "unknown_library_xyz" in result
    assert "Search result" in result or "found" in result


# --- Tests for is_ignored ---

@pytest.mark.unit
def test_is_ignored_pycache():
    """Test is_ignored correctly identifies __pycache__ directories."""
    assert is_ignored("__pycache__/module.pyc") is True
    assert is_ignored("src/__pycache__/test.pyc") is True


@pytest.mark.unit
def test_is_ignored_git_directory():
    """Test is_ignored correctly identifies .git directories."""
    assert is_ignored(".git/config") is True
    assert is_ignored(".git") is True


@pytest.mark.unit
def test_is_ignored_env_file():
    """Test is_ignored correctly identifies .env files."""
    assert is_ignored(".env") is True


@pytest.mark.unit
def test_is_ignored_normal_files():
    """Test is_ignored returns False for normal project files."""
    assert is_ignored("main.py") is False
    assert is_ignored("src/module.py") is False
    assert is_ignored("README.md") is False


@pytest.mark.unit
def test_is_ignored_pyc_files():
    """Test is_ignored correctly identifies .pyc files."""
    assert is_ignored("module.pyc") is True


# --- Tests for get_gitignore_patterns ---

@pytest.mark.unit
def test_get_gitignore_patterns_basic():
    """Test get_gitignore_patterns converts .gitignore syntax to regex."""
    gitignore = """
# Comment
*.pyc
__pycache__/
.env
"""
    patterns = get_gitignore_patterns(gitignore)

    assert len(patterns) > 0
    assert any("pyc" in p for p in patterns)
    assert any("__pycache__" in p for p in patterns)


@pytest.mark.unit
def test_get_gitignore_patterns_ignores_comments():
    """Test get_gitignore_patterns ignores comment lines."""
    gitignore = """
# This is a comment
*.log
# Another comment
"""
    patterns = get_gitignore_patterns(gitignore)

    # Should only have 1 pattern (*.log)
    assert len(patterns) == 1
    assert "log" in patterns[0]


# --- Tests for init_knowledge_base ---

@pytest.mark.rag
@pytest.mark.unit
def test_init_knowledge_base(sample_documents, mock_embeddings, tmp_path):
    """Test init_knowledge_base successfully initializes ChromaDB."""
    with patch('tools.OpenAIEmbeddings', return_value=mock_embeddings):
        with patch('tools.VECTOR_DB_PATH', str(tmp_path / "test_db")):
            with patch('langchain_community.vectorstores.Chroma.from_documents') as mock_chroma:
                mock_vectorstore = MagicMock()
                mock_retriever = MagicMock()
                mock_vectorstore.as_retriever = MagicMock(return_value=mock_retriever)
                mock_chroma.return_value = mock_vectorstore

                result = init_knowledge_base(sample_documents)

                assert "successfully initialized" in result.lower()
                assert "chunks indexed" in result.lower()
                mock_chroma.assert_called_once()


@pytest.mark.unit
def test_init_knowledge_base_empty_documents():
    """Test init_knowledge_base handles empty document list."""
    result = init_knowledge_base([])

    assert "Warning" in result or "No documents" in result


@pytest.mark.rag
@pytest.mark.unit
def test_init_knowledge_base_error_handling():
    """Test init_knowledge_base handles initialization errors gracefully."""
    from langchain_core.documents import Document

    docs = [Document(page_content="test", metadata={})]

    with patch('tools.OpenAIEmbeddings', side_effect=Exception("API Error")):
        result = init_knowledge_base(docs)

        assert "Error" in result
        assert "initializing" in result.lower()


# --- Tests for retrieve_knowledge ---

@pytest.mark.rag
@pytest.mark.unit
def test_retrieve_knowledge(sample_documents, mock_chroma):
    """Test retrieve_knowledge successfully retrieves from vector database."""
    import tools

    # Set up global retriever
    mock_retriever = MagicMock()
    mock_retriever.invoke = MagicMock(return_value=[
        MagicMock(page_content="Style guide rule 1"),
        MagicMock(page_content="Style guide rule 2"),
        MagicMock(page_content="Style guide rule 3")
    ])
    tools.KLARO_RETRIEVER = mock_retriever

    result = retrieve_knowledge("README style guidelines")

    assert "Retrieved Information" in result
    assert "Source 1" in result
    assert "Source 2" in result
    assert "Source 3" in result
    assert "Style guide rule 1" in result

    # Clean up
    tools.KLARO_RETRIEVER = None


@pytest.mark.unit
def test_retrieve_knowledge_not_initialized():
    """Test retrieve_knowledge handles uninitialized knowledge base."""
    import tools

    # Ensure retriever is not initialized
    original_retriever = tools.KLARO_RETRIEVER
    tools.KLARO_RETRIEVER = None

    result = retrieve_knowledge("test query")

    assert "Error" in result
    assert "not initialized" in result.lower()

    # Restore original state
    tools.KLARO_RETRIEVER = original_retriever


@pytest.mark.rag
@pytest.mark.unit
def test_retrieve_knowledge_error_handling():
    """Test retrieve_knowledge handles retrieval errors."""
    import tools

    mock_retriever = MagicMock()
    mock_retriever.invoke = MagicMock(side_effect=Exception("Retrieval failed"))
    tools.KLARO_RETRIEVER = mock_retriever

    result = retrieve_knowledge("test query")

    assert "Error" in result
    assert "retrieving" in result.lower()

    # Clean up
    tools.KLARO_RETRIEVER = None


# --- Integration tests for tools ---

@pytest.mark.unit
def test_full_workflow_list_read_analyze(temp_dir):
    """Test complete workflow: list_files -> read_file -> analyze_code."""
    # Create a Python file
    file_path = os.path.join(temp_dir, "example.py")
    code_content = '''
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b
'''
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code_content)

    # Step 1: List files
    file_list = list_files(temp_dir)
    assert "example.py" in file_list

    # Step 2: Read file
    file_content = read_file(file_path)
    assert "def add" in file_content

    # Step 3: Analyze code
    analysis = analyze_code(file_content)
    data = json.loads(analysis)
    assert data["components"][0]["name"] == "add"
    assert data["components"][0]["returns"] == "int"


@pytest.mark.unit
def test_analyze_code_with_sample_fixtures(sample_project_path):
    """Test analyze_code with actual fixture files."""
    # Read the sample_code.py fixture
    fixture_path = Path(__file__).parent / "fixtures" / "sample_code.py"

    if fixture_path.exists():
        content = read_file(str(fixture_path))
        result = analyze_code(content)
        data = json.loads(result)

        # Verify key components are extracted
        component_names = [c["name"] for c in data["components"]]
        assert "SimpleClass" in component_names
        assert "ComplexClass" in component_names
        assert "simple_function" in component_names
