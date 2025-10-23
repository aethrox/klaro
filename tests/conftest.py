"""
Pytest Configuration and Shared Fixtures

This module provides shared test fixtures, mock objects, and pytest configuration
for the Klaro test suite. Fixtures defined here are automatically available to
all test files without explicit imports.

Fixtures:
    - temp_dir: Temporary directory for file operations
    - sample_python_code: Valid Python code for AST testing
    - mock_llm: Mocked OpenAI LLM for testing without API calls
    - mock_embeddings: Mocked embeddings for RAG testing
    - sample_project_path: Path to fixtures/sample_project
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import pytest
from unittest.mock import Mock, MagicMock, patch

# Fixture for temporary directory
@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Creates a temporary directory for file operations.

    Yields:
        str: Path to temporary directory

    Cleanup:
        Automatically removes directory after test
    """
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


# Fixture for sample Python code
@pytest.fixture
def sample_python_code() -> str:
    """Provides valid Python code for AST analysis testing.

    Returns:
        str: Sample Python code with classes and functions
    """
    return '''
def greet(name: str) -> str:
    """Returns a greeting message."""
    return f"Hello, {name}"

class Calculator:
    """A simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Adds two numbers."""
        return a + b

    def multiply(self, a: int, b: int) -> int:
        """Multiplies two numbers."""
        return a * b
'''


# Fixture for invalid Python code
@pytest.fixture
def invalid_python_code() -> str:
    """Provides syntactically invalid Python code.

    Returns:
        str: Invalid Python code that will raise SyntaxError
    """
    return '''
def broken_function(
    print("This is missing closing parenthesis"
'''


# Fixture for sample project path
@pytest.fixture
def sample_project_path() -> Path:
    """Returns path to the sample project fixture.

    Returns:
        Path: Path to tests/fixtures/sample_project
    """
    return Path(__file__).parent / "fixtures" / "sample_project"


# Fixture for mocked OpenAI LLM
@pytest.fixture
def mock_llm():
    """Creates a mocked ChatOpenAI instance for testing without API calls.

    Returns:
        Mock: Mocked LLM that returns predefined responses
    """
    mock = Mock()
    mock.bind_tools = Mock(return_value=mock)
    mock.invoke = Mock(return_value=MagicMock(
        content="Thought: I should explore the project.",
        tool_calls=[]
    ))
    return mock


# Fixture for mocked OpenAI embeddings
@pytest.fixture
def mock_embeddings():
    """Creates a mocked OpenAIEmbeddings instance for RAG testing.

    Returns:
        Mock: Mocked embeddings that return dummy vectors
    """
    mock = Mock()
    mock.embed_documents = Mock(return_value=[[0.1, 0.2, 0.3] * 512])
    mock.embed_query = Mock(return_value=[0.1, 0.2, 0.3] * 512)
    return mock


# Fixture for mocked ChromaDB
@pytest.fixture
def mock_chroma(mock_embeddings):
    """Creates a mocked Chroma vector store for RAG testing.

    Args:
        mock_embeddings: Injected mocked embeddings fixture

    Returns:
        Mock: Mocked Chroma vector store
    """
    mock_vectorstore = Mock()
    mock_retriever = Mock()
    mock_retriever.invoke = Mock(return_value=[
        MagicMock(page_content="Style guide content 1"),
        MagicMock(page_content="Style guide content 2"),
        MagicMock(page_content="Style guide content 3")
    ])
    mock_vectorstore.as_retriever = Mock(return_value=mock_retriever)

    with patch('langchain_community.vectorstores.Chroma.from_documents',
               return_value=mock_vectorstore):
        yield mock_vectorstore


# Fixture for environment variables
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Sets up environment variables for testing.

    Args:
        monkeypatch: Pytest's monkeypatch fixture
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key-12345")
    monkeypatch.setenv("KLARO_RECURSION_LIMIT", "10")


# Fixture for sample document list
@pytest.fixture
def sample_documents():
    """Creates sample LangChain Document objects for RAG testing.

    Returns:
        list: List of Document objects
    """
    from langchain_core.documents import Document

    return [
        Document(
            page_content="# Style Guide\n\nAll READMEs must have Setup and Usage sections.",
            metadata={"source": "style_guide"}
        ),
        Document(
            page_content="Use professional technical tone with code examples.",
            metadata={"source": "style_guide"}
        )
    ]


# Pytest configuration
def pytest_configure(config):
    """Pytest hook for initial configuration.

    Registers custom markers for test categorization.
    """
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (slower)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (fast)"
    )
    config.addinivalue_line(
        "markers", "rag: mark test as requiring RAG/embeddings"
    )
