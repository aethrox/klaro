"""
Integration Tests for Klaro Agent

This module contains end-to-end integration tests that simulate full agent execution:
    - Complete agent workflow on sample projects
    - README generation with style guide compliance
    - Error handling and recovery scenarios
    - Multi-step tool execution chains
    - RAG system integration in full workflow

These tests are slower than unit tests as they may involve:
    - Mocked LLM calls with realistic responses
    - Full LangGraph execution
    - Multiple tool invocations
    - File system operations

Test Coverage:
    - Full agent execution from start to finish
    - Tool execution chains (list -> read -> analyze -> retrieve)
    - Final output format validation
    - Error recovery and replanning
    - RAG knowledge base integration

Running:
    # Run all integration tests
    pytest tests/test_integration.py -v -m integration

    # Run specific test
    pytest tests/test_integration.py::test_full_agent_execution_on_sample_project -v
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.documents import Document

from main import run_klaro_langgraph, app
from tools import list_files, read_file, analyze_code, retrieve_knowledge


# --- Full Agent Execution Tests ---

@pytest.mark.integration
def test_full_agent_execution_on_sample_project(sample_project_path, mock_env_vars, mock_embeddings):
    """Test complete agent execution on the sample project fixture."""
    # Mock LLM to simulate realistic agent behavior
    call_count = [0]  # Use list to allow mutation in nested function

    def mock_invoke(messages):
        """Simulate agent's thought process."""
        call_count[0] += 1

        # Iteration 1: Explore project
        if call_count[0] == 1:
            return AIMessage(
                content="Thought: I should list files to understand structure.",
                tool_calls=[
                    {
                        "name": "list_files",
                        "args": {"directory": str(sample_project_path)},
                        "id": "call_1"
                    }
                ]
            )

        # Iteration 2: Read main.py
        elif call_count[0] == 2:
            return AIMessage(
                content="Thought: I should read main.py.",
                tool_calls=[
                    {
                        "name": "read_file",
                        "args": {"file_path": str(sample_project_path / "main.py")},
                        "id": "call_2"
                    }
                ]
            )

        # Iteration 3: Analyze code
        elif call_count[0] == 3:
            # Get actual file content for analysis
            return AIMessage(
                content="Thought: I should analyze this code.",
                tool_calls=[
                    {
                        "name": "analyze_code",
                        "args": {"code_content": 'def main():\n    """Main function."""\n    pass'},
                        "id": "call_3"
                    }
                ]
            )

        # Iteration 4: Retrieve style guidelines
        elif call_count[0] == 4:
            return AIMessage(
                content="Thought: I should get README style guidelines.",
                tool_calls=[
                    {
                        "name": "retrieve_knowledge",
                        "args": {"query": "README style guidelines"},
                        "id": "call_4"
                    }
                ]
            )

        # Iteration 5: Final Answer
        else:
            return AIMessage(
                content="""Final Answer: # Sample Project

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python main.py
```

## Components

- main.py: Main application entry point
- tools.py: Utility functions
"""
            )

    with patch('main.model') as mock_model:
        mock_model.invoke = mock_invoke

        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('builtins.print'):
                # Run agent
                run_klaro_langgraph(project_path=str(sample_project_path))

    # Verify agent went through expected iterations
    assert call_count[0] >= 5


@pytest.mark.integration
def test_readme_generation_output_format(mock_env_vars):
    """Test that generated README follows expected markdown format."""

    def mock_invoke_with_final_answer(messages):
        """Return a properly formatted README."""
        return AIMessage(
            content="""Final Answer: # Test Project

## Setup

Run the following command:
```bash
pip install -r requirements.txt
```

## Usage

Execute:
```bash
python main.py
```

## Components

- main.py: Entry point
- utils.py: Utilities
"""
        )

    with patch('main.model') as mock_model:
        mock_model.invoke = mock_invoke_with_final_answer

        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('builtins.print') as mock_print:
                run_klaro_langgraph(project_path=".")

                # Capture printed output
                print_calls = [str(call) for call in mock_print.call_args_list]
                output = "\n".join(print_calls)

                # Verify markdown structure
                assert "# Test Project" in output
                assert "## Setup" in output
                assert "## Usage" in output
                assert "## Components" in output
                assert "```" in output  # Code blocks present


@pytest.mark.integration
def test_error_handling_and_recovery(mock_env_vars):
    """Test agent's ability to handle errors and recover."""
    call_count = [0]

    def mock_invoke_with_error_recovery(messages):
        """Simulate error and recovery."""
        call_count[0] += 1

        # First attempt: Try to read nonexistent file
        if call_count[0] == 1:
            return AIMessage(
                content="Thought: I should read config.py.",
                tool_calls=[
                    {
                        "name": "read_file",
                        "args": {"file_path": "nonexistent_config.py"},
                        "id": "call_error"
                    }
                ]
            )

        # After error: Replan and try different approach
        elif call_count[0] == 2:
            # Agent should see error in message history and replan
            return AIMessage(
                content="Thought: That file doesn't exist. Let me list files instead.",
                tool_calls=[
                    {
                        "name": "list_files",
                        "args": {"directory": "."},
                        "id": "call_recover"
                    }
                ]
            )

        # Final answer after recovery
        else:
            return AIMessage(
                content="Final Answer: # Project\n\n## Setup\nInstall dependencies."
            )

    with patch('main.model') as mock_model:
        mock_model.invoke = mock_invoke_with_error_recovery

        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('builtins.print'):
                run_klaro_langgraph(project_path=".")

    # Agent should have recovered from error
    assert call_count[0] >= 3


# --- Tool Chain Integration Tests ---

@pytest.mark.integration
def test_list_read_analyze_tool_chain(sample_project_path):
    """Test complete tool chain: list_files -> read_file -> analyze_code."""
    # Step 1: List files
    file_tree = list_files(str(sample_project_path))
    assert "main.py" in file_tree

    # Step 2: Read main.py
    main_path = sample_project_path / "main.py"
    file_content = read_file(str(main_path))
    assert "def main" in file_content or "main" in file_content

    # Step 3: Analyze code
    analysis_result = analyze_code(file_content)
    data = json.loads(analysis_result)

    assert "analysis_summary" in data
    assert "components" in data


@pytest.mark.integration
@pytest.mark.rag
def test_rag_integration_in_workflow(sample_documents, mock_embeddings, tmp_path):
    """Test RAG system integration with full workflow."""
    from tools import init_knowledge_base, retrieve_knowledge
    import tools

    # Initialize knowledge base
    with patch('tools.OpenAIEmbeddings', return_value=mock_embeddings):
        with patch('tools.VECTOR_DB_PATH', str(tmp_path / "test_rag_db")):
            with patch('langchain_community.vectorstores.Chroma.from_documents') as mock_chroma:
                mock_vectorstore = MagicMock()
                mock_retriever = MagicMock()
                mock_retriever.invoke = MagicMock(return_value=[
                    MagicMock(page_content="Style guide rule 1: Use ## for sections"),
                    MagicMock(page_content="Style guide rule 2: Include Setup section"),
                    MagicMock(page_content="Style guide rule 3: Use code blocks")
                ])
                mock_vectorstore.as_retriever = MagicMock(return_value=mock_retriever)
                mock_chroma.return_value = mock_vectorstore

                # Initialize
                init_result = init_knowledge_base(sample_documents)
                assert "successfully" in init_result.lower() or "initialized" in init_result.lower()

                # Set retriever for testing
                tools.KLARO_RETRIEVER = mock_retriever

                # Retrieve knowledge
                retrieval_result = retrieve_knowledge("README style guidelines")
                assert "Style guide rule" in retrieval_result
                assert "sections" in retrieval_result.lower()

                # Clean up
                tools.KLARO_RETRIEVER = None


# --- Workflow Validation Tests ---

@pytest.mark.integration
def test_agent_uses_all_required_tools(mock_env_vars):
    """Test that agent uses list_files, read_file, analyze_code, and retrieve_knowledge."""
    tools_called = set()

    def track_tool_calls(messages):
        """Track which tools the agent calls."""
        # Simulate agent calling all required tools
        if "list_files" not in tools_called:
            tools_called.add("list_files")
            return AIMessage(
                content="Listing files...",
                tool_calls=[{"name": "list_files", "args": {"directory": "."}, "id": "c1"}]
            )
        elif "read_file" not in tools_called:
            tools_called.add("read_file")
            return AIMessage(
                content="Reading file...",
                tool_calls=[{"name": "read_file", "args": {"file_path": "main.py"}, "id": "c2"}]
            )
        elif "analyze_code" not in tools_called:
            tools_called.add("analyze_code")
            return AIMessage(
                content="Analyzing...",
                tool_calls=[{"name": "analyze_code", "args": {"code_content": "def foo(): pass"}, "id": "c3"}]
            )
        elif "retrieve_knowledge" not in tools_called:
            tools_called.add("retrieve_knowledge")
            return AIMessage(
                content="Retrieving guidelines...",
                tool_calls=[{"name": "retrieve_knowledge", "args": {"query": "style"}, "id": "c4"}]
            )
        else:
            return AIMessage(content="Final Answer: # README\n\n## Setup\nDone.")

    with patch('main.model') as mock_model:
        mock_model.invoke = track_tool_calls

        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('builtins.print'):
                run_klaro_langgraph(project_path=".")

    # Verify all required tools were called
    assert "list_files" in tools_called
    assert "read_file" in tools_called
    assert "analyze_code" in tools_called
    assert "retrieve_knowledge" in tools_called


@pytest.mark.integration
def test_agent_respects_recursion_limit(mock_env_vars):
    """Test that agent terminates when recursion limit is reached."""
    call_count = [0]

    def infinite_loop_mock(messages):
        """Simulate agent that never finishes."""
        call_count[0] += 1
        # Never return Final Answer, keep calling tools
        return AIMessage(
            content="Thinking...",
            tool_calls=[{"name": "list_files", "args": {"directory": "."}, "id": f"call_{call_count[0]}"}]
        )

    with patch('main.model') as mock_model:
        mock_model.invoke = infinite_loop_mock

        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('builtins.print'):
                # Should raise exception or terminate due to recursion limit
                try:
                    run_klaro_langgraph(project_path=".")
                except Exception as e:
                    # Expected: recursion limit exceeded
                    assert "recursion" in str(e).lower() or call_count[0] >= 10


# --- Output Validation Tests ---

@pytest.mark.integration
def test_final_answer_format_validation(mock_env_vars):
    """Test that Final Answer is properly formatted and extracted."""

    def mock_final_answer(messages):
        return AIMessage(
            content="""Final Answer: # My Project

This is a comprehensive README.

## Setup

Install with pip:
```bash
pip install -r requirements.txt
```

## Usage

Run the app:
```bash
python main.py
```

## Components

Key files:
- main.py: Entry point
- config.py: Configuration
"""
        )

    with patch('main.model') as mock_model:
        mock_model.invoke = mock_final_answer

        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('builtins.print') as mock_print:
                run_klaro_langgraph(project_path=".")

                # Extract printed output
                output = "\n".join([str(call) for call in mock_print.call_args_list])

                # Verify "Final Answer:" prefix is stripped
                assert "# My Project" in output
                # Should NOT contain the "Final Answer:" prefix in output
                lines = output.split("\n")
                markdown_lines = [line for line in lines if line.strip().startswith("#")]
                for line in markdown_lines:
                    assert "Final Answer:" not in line


@pytest.mark.integration
def test_multiple_files_analysis(sample_project_path, mock_env_vars):
    """Test agent analyzing multiple files in a project."""

    # Read and analyze multiple files
    main_content = read_file(str(sample_project_path / "main.py"))
    tools_content = read_file(str(sample_project_path / "tools.py"))

    # Analyze both
    main_analysis = analyze_code(main_content)
    tools_analysis = analyze_code(tools_content)

    main_data = json.loads(main_analysis)
    tools_data = json.loads(tools_analysis)

    # Verify both analyses succeed
    assert "components" in main_data
    assert "components" in tools_data

    # tools.py should have Calculator and Greeter classes
    tools_components = [c["name"] for c in tools_data["components"]]
    assert "Calculator" in tools_components or "Greeter" in tools_components


# --- Edge Case Tests ---

@pytest.mark.integration
def test_empty_project_handling(temp_dir, mock_env_vars):
    """Test agent handling of empty project directory."""

    def mock_empty_project(messages):
        """Simulate handling empty project."""
        if any("list_files" in str(m) for m in messages):
            # After seeing empty file list, provide final answer
            return AIMessage(
                content="""Final Answer: # Empty Project

## Setup

No files found. This appears to be an empty project.

## Usage

Add files to get started.
"""
            )
        else:
            # First call: try to list files
            return AIMessage(
                content="Let me explore the project.",
                tool_calls=[{"name": "list_files", "args": {"directory": temp_dir}, "id": "c1"}]
            )

    with patch('main.model') as mock_model:
        mock_model.invoke = mock_empty_project

        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('builtins.print') as mock_print:
                run_klaro_langgraph(project_path=temp_dir)

                output = "\n".join([str(call) for call in mock_print.call_args_list])
                assert "Empty Project" in output or "No files" in output


@pytest.mark.integration
def test_syntax_error_in_code_analysis(mock_env_vars):
    """Test agent handling syntax errors during code analysis."""
    invalid_code = "def broken(\n    print('missing paren')"

    result = analyze_code(invalid_code)
    data = json.loads(result)

    # Should return error without crashing
    assert "error" in data
    assert "SyntaxError" in data["error"] or "parsing" in data["error"].lower()


# --- Performance Tests ---

@pytest.mark.integration
def test_agent_completes_within_reasonable_iterations(mock_env_vars):
    """Test that agent completes task within reasonable iteration count."""
    call_count = [0]
    max_calls = 15  # Reasonable limit for simple project

    def count_calls(messages):
        call_count[0] += 1
        if call_count[0] >= max_calls:
            # Force completion
            return AIMessage(content="Final Answer: # README\n\n## Setup\nCompleted.")
        else:
            # Normal progression
            if call_count[0] == 1:
                return AIMessage(
                    content="Exploring...",
                    tool_calls=[{"name": "list_files", "args": {"directory": "."}, "id": "c1"}]
                )
            elif call_count[0] < 5:
                return AIMessage(
                    content="Reading files...",
                    tool_calls=[{"name": "read_file", "args": {"file_path": "main.py"}, "id": f"c{call_count[0]}"}]
                )
            else:
                return AIMessage(content="Final Answer: # README\n\n## Setup\nDone.")

    with patch('main.model') as mock_model:
        mock_model.invoke = count_calls

        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('builtins.print'):
                run_klaro_langgraph(project_path=".")

    # Should complete in reasonable number of iterations
    assert call_count[0] < max_calls
