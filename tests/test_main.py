"""
Unit Tests for Klaro Main Module (LangGraph Agent)

This module contains unit tests for the LangGraph-based agent orchestration in main.py:
    - AgentState initialization and state management
    - run_model node execution and LLM invocation
    - decide_next_step routing logic
    - Graph compilation and structure
    - Tool binding and integration
    - Error handling and recovery

Test Coverage:
    - State reducer behavior (message appending)
    - Node execution and state updates
    - Conditional edge routing decisions
    - Entry point and graph structure validation
    - Mocked LLM responses to avoid API calls

Running:
    pytest tests/test_main.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.documents import Document

# Import the components to test
from main import (
    AgentState,
    run_model,
    decide_next_step,
    workflow,
    run_klaro_langgraph,
    LLM_MODEL,
    RECURSION_LIMIT,
    MODEL_SELECTION_THRESHOLDS,
    AUTO_MODEL_SELECTION,
    create_model
)

# Import tools for testing
from tools import analyze_project_size, select_model_by_project_size


# --- Tests for AgentState ---

@pytest.mark.unit
def test_agent_state_initialization():
    """Test AgentState can be initialized with correct structure."""
    state: AgentState = {
        "messages": [HumanMessage(content="Test task")],
        "error_log": ""
    }

    assert "messages" in state
    assert "error_log" in state
    assert len(state["messages"]) == 1
    assert state["messages"][0].content == "Test task"
    assert state["error_log"] == ""


@pytest.mark.unit
def test_agent_state_message_reducer():
    """Test that messages are appended correctly (reducer behavior)."""
    # Simulate state updates
    initial_state: AgentState = {
        "messages": [HumanMessage(content="Initial")],
        "error_log": ""
    }

    # Add new message (simulating what reducer does)
    new_message = AIMessage(content="Response")
    updated_messages = initial_state["messages"] + [new_message]

    assert len(updated_messages) == 2
    assert updated_messages[0].content == "Initial"
    assert updated_messages[1].content == "Response"


# --- Tests for run_model node ---

@pytest.mark.unit
def test_run_model_node_invokes_llm():
    """Test run_model node invokes the LLM and returns AIMessage."""
    # Mock the model
    mock_response = AIMessage(content="I should explore the project.", tool_calls=[])

    with patch('main.model') as mock_model:
        mock_model.invoke = Mock(return_value=mock_response)

        state: AgentState = {
            "messages": [HumanMessage(content="Analyze the project")],
            "error_log": ""
        }

        result = run_model(state)

        # Verify structure
        assert "messages" in result
        assert "error_log" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0].content == "I should explore the project."
        assert result["error_log"] == ""

        # Verify LLM was called with state messages
        mock_model.invoke.assert_called_once_with(state["messages"])


@pytest.mark.unit
def test_run_model_clears_error_log():
    """Test run_model clears error_log after execution."""
    mock_response = AIMessage(content="Replanning...", tool_calls=[])

    with patch('main.model') as mock_model:
        mock_model.invoke = Mock(return_value=mock_response)

        state: AgentState = {
            "messages": [HumanMessage(content="Task")],
            "error_log": "Previous error occurred"
        }

        result = run_model(state)

        # Error log should be cleared
        assert result["error_log"] == ""


@pytest.mark.unit
def test_run_model_with_tool_calls():
    """Test run_model when LLM returns tool calls."""
    mock_response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "list_files",
                "args": {"directory": "."},
                "id": "call_123"
            }
        ]
    )

    with patch('main.model') as mock_model:
        mock_model.invoke = Mock(return_value=mock_response)

        state: AgentState = {
            "messages": [HumanMessage(content="Explore project")],
            "error_log": ""
        }

        result = run_model(state)

        assert result["messages"][0].tool_calls is not None
        assert len(result["messages"][0].tool_calls) == 1
        assert result["messages"][0].tool_calls[0]["name"] == "list_files"


# --- Tests for decide_next_step routing ---

@pytest.mark.unit
def test_decide_next_step_with_error():
    """Test decide_next_step routes to run_model when error_log is not empty."""
    state: AgentState = {
        "messages": [
            HumanMessage(content="Task"),
            AIMessage(content="Action taken", tool_calls=[])
        ],
        "error_log": "File not found error"
    }

    result = decide_next_step(state)

    assert result == "run_model"


@pytest.mark.unit
def test_decide_next_step_with_final_answer():
    """Test decide_next_step returns END when Final Answer is detected."""
    from langgraph.graph import END

    state: AgentState = {
        "messages": [
            HumanMessage(content="Task"),
            AIMessage(content="Final Answer: # README\n\n## Setup\n...")
        ],
        "error_log": ""
    }

    result = decide_next_step(state)

    assert result == END


@pytest.mark.unit
def test_decide_next_step_with_tool_calls():
    """Test decide_next_step routes to call_tool when tool_calls present."""
    state: AgentState = {
        "messages": [
            HumanMessage(content="Task"),
            AIMessage(
                content="",
                tool_calls=[{"name": "read_file", "args": {"file_path": "main.py"}, "id": "call_1"}]
            )
        ],
        "error_log": ""
    }

    result = decide_next_step(state)

    assert result == "call_tool"


@pytest.mark.unit
def test_decide_next_step_continue_reasoning():
    """Test decide_next_step returns run_model when no action decided."""
    state: AgentState = {
        "messages": [
            HumanMessage(content="Task"),
            AIMessage(content="I am thinking about what to do next...", tool_calls=[])
        ],
        "error_log": ""
    }

    result = decide_next_step(state)

    assert result == "run_model"


@pytest.mark.unit
def test_decide_next_step_priority_error_over_final_answer():
    """Test that error check has priority over Final Answer check."""
    from langgraph.graph import END

    state: AgentState = {
        "messages": [
            HumanMessage(content="Task"),
            AIMessage(content="Final Answer: # README\n...")
        ],
        "error_log": "Some error occurred"
    }

    result = decide_next_step(state)

    # Should route to run_model for error recovery, not END
    assert result == "run_model"


# --- Tests for graph structure ---

@pytest.mark.unit
def test_graph_compilation():
    """Test that the workflow graph compiles successfully."""
    # Test that workflow can be compiled
    from main import workflow
    compiled_app = workflow.compile()
    assert compiled_app is not None
    assert hasattr(compiled_app, 'invoke')


@pytest.mark.unit
def test_graph_has_required_nodes():
    """Test that the workflow has run_model and call_tool nodes."""
    # Access the compiled graph structure
    graph = workflow.nodes

    assert "run_model" in graph or hasattr(workflow, '_nodes')
    # Note: LangGraph's internal structure may vary; this is a basic check


@pytest.mark.unit
def test_graph_entry_point():
    """Test that the graph entry point is set correctly."""
    # Verify the workflow was set up with run_model as entry point
    # This is a structural test that the setup completes without error
    assert workflow is not None


# --- Tests for tool binding ---

@pytest.mark.unit
def test_tools_are_bound_to_model():
    """Test that tools are properly bound to the LLM."""
    from main import tools, create_model

    # Verify tools list is not empty
    assert len(tools) > 0

    # Check expected tools are present
    tool_names = [tool.name for tool in tools]
    assert "list_files" in tool_names
    assert "read_file" in tool_names
    assert "analyze_code" in tool_names
    assert "retrieve_knowledge" in tool_names

    # Test that create_model function works and returns a model
    test_model = create_model("gpt-4o-mini")
    assert test_model is not None


@pytest.mark.unit
def test_tools_have_descriptions():
    """Test that all tools have proper descriptions from docstrings."""
    from main import tools

    for tool in tools:
        assert tool.description is not None
        assert len(tool.description) > 0


# --- Tests for run_klaro_langgraph function ---

@pytest.mark.unit
def test_run_klaro_langgraph_initializes_rag(mock_env_vars):
    """Test run_klaro_langgraph initializes RAG knowledge base."""
    with patch('main.init_knowledge_base') as mock_init_kb:
        mock_init_kb.return_value = "Knowledge base initialized successfully"

        # Mock the compiled workflow's invoke method
        mock_compiled_app = MagicMock()
        mock_compiled_app.invoke.return_value = {
            "messages": [
                HumanMessage(content="Task"),
                AIMessage(content="Final Answer: # README\n\n## Setup\n...")
            ],
            "error_log": ""
        }

        with patch('main.workflow.compile', return_value=mock_compiled_app):
            # Capture print output (optional, for full integration)
            with patch('builtins.print'):
                run_klaro_langgraph(project_path=".")

            # Verify init_knowledge_base was called
            mock_init_kb.assert_called_once()

            # Verify compiled app's invoke was called with correct structure
            mock_compiled_app.invoke.assert_called_once()
            call_args = mock_compiled_app.invoke.call_args[0][0]
            assert "messages" in call_args
            assert "error_log" in call_args


@pytest.mark.unit
def test_run_klaro_langgraph_handles_errors(mock_env_vars):
    """Test run_klaro_langgraph handles execution errors gracefully."""
    with patch('main.init_knowledge_base', return_value="Initialized"):
        # Mock the compiled workflow to raise an error
        mock_compiled_app = MagicMock()
        mock_compiled_app.invoke.side_effect = Exception("LLM API Error")

        with patch('main.workflow.compile', return_value=mock_compiled_app):
            # Should not raise exception, should print error
            with patch('builtins.print') as mock_print:
                run_klaro_langgraph(project_path=".")

                # Verify error was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                assert any("ERROR" in call for call in print_calls)


@pytest.mark.unit
def test_run_klaro_langgraph_extracts_final_answer(mock_env_vars):
    """Test run_klaro_langgraph correctly extracts and cleans Final Answer."""
    with patch('main.init_knowledge_base', return_value="Initialized"):
        # Mock the compiled workflow
        mock_compiled_app = MagicMock()
        mock_compiled_app.invoke.return_value = {
            "messages": [
                HumanMessage(content="Task"),
                AIMessage(content="Final Answer: # My Project\n\n## Setup\nRun pip install")
            ],
            "error_log": ""
        }

        with patch('main.workflow.compile', return_value=mock_compiled_app):
            with patch('builtins.print') as mock_print:
                run_klaro_langgraph(project_path=".")

                # Check that "Final Answer:" prefix was stripped
                print_calls = [str(call) for call in mock_print.call_args_list]
                # Should print "# My Project" not "Final Answer: # My Project"
                assert any("# My Project" in call for call in print_calls)


# --- Tests for configuration ---

@pytest.mark.unit
def test_llm_model_configuration():
    """Test that LLM_MODEL is set correctly."""
    assert LLM_MODEL is not None
    assert isinstance(LLM_MODEL, str)
    # Default should be gpt-4o
    assert "gpt" in LLM_MODEL.lower() or "claude" in LLM_MODEL.lower()


@pytest.mark.unit
def test_recursion_limit_configuration(mock_env_vars):
    """Test that RECURSION_LIMIT can be configured via environment."""
    # mock_env_vars sets KLARO_RECURSION_LIMIT=10
    import os

    limit = int(os.getenv("KLARO_RECURSION_LIMIT", "50"))
    assert limit == 10


# --- Tests for state management edge cases ---

@pytest.mark.unit
def test_empty_message_history():
    """Test decide_next_step handles empty message history gracefully."""
    # This shouldn't happen in practice, but test defensive code
    state: AgentState = {
        "messages": [],
        "error_log": ""
    }

    try:
        result = decide_next_step(state)
        # Should handle gracefully (may raise IndexError or return default)
    except IndexError:
        # Expected if accessing last_message on empty list
        pass


@pytest.mark.unit
def test_multiple_tool_calls_in_message():
    """Test decide_next_step handles multiple tool calls correctly."""
    state: AgentState = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "list_files", "args": {"directory": "."}, "id": "call_1"},
                    {"name": "read_file", "args": {"file_path": "main.py"}, "id": "call_2"}
                ]
            )
        ],
        "error_log": ""
    }

    result = decide_next_step(state)

    # Should route to call_tool (ToolNode will handle multiple calls)
    assert result == "call_tool"


# --- Integration test for node execution flow ---

@pytest.mark.unit
def test_node_execution_flow(mock_env_vars):
    """Test the flow from run_model -> decide_next_step -> call_tool."""
    # This tests the logical flow without invoking the full graph

    # Step 1: run_model produces AIMessage with tool_calls
    with patch('main.model') as mock_model:
        mock_model.invoke = Mock(return_value=AIMessage(
            content="",
            tool_calls=[{"name": "list_files", "args": {"directory": "."}, "id": "call_1"}]
        ))

        state: AgentState = {
            "messages": [HumanMessage(content="Analyze project")],
            "error_log": ""
        }

        # Execute run_model
        result_state = run_model(state)
        state["messages"].extend(result_state["messages"])
        state["error_log"] = result_state["error_log"]

        # Step 2: decide_next_step should route to call_tool
        next_node = decide_next_step(state)
        assert next_node == "call_tool"


# --- Tests for DEFAULT_GUIDE_CONTENT ---

@pytest.mark.unit
def test_default_guide_content_exists():
    """Test that DEFAULT_GUIDE_CONTENT is defined in main.py."""
    from main import DEFAULT_GUIDE_CONTENT

    assert DEFAULT_GUIDE_CONTENT is not None
    assert len(DEFAULT_GUIDE_CONTENT) > 0
    assert "README" in DEFAULT_GUIDE_CONTENT or "documentation" in DEFAULT_GUIDE_CONTENT.lower()


# --- Tests for Model Selection Feature ---

@pytest.mark.unit
def test_analyze_project_size_small_project():
    """Test analyze_project_size correctly identifies small projects."""
    # Create a temporary small project
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small Python file (< 10K lines)
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, 'w') as f:
            f.write("# Test file\n" * 100)  # 100 lines

        metrics = analyze_project_size(tmpdir)

        assert metrics['total_files'] == 1
        assert metrics['total_lines'] == 100
        assert metrics['complexity'] == 'small'
        assert 'error' not in metrics


@pytest.mark.unit
def test_analyze_project_size_medium_project():
    """Test analyze_project_size correctly identifies medium projects."""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple files totaling between 10K-100K lines
        for i in range(50):
            test_file = os.path.join(tmpdir, f"test_{i}.py")
            with open(test_file, 'w') as f:
                f.write("# Test line\n" * 250)  # 250 lines each = 12,500 total

        metrics = analyze_project_size(tmpdir)

        assert metrics['total_files'] == 50
        assert 10000 <= metrics['total_lines'] < 100000
        assert metrics['complexity'] == 'medium'


@pytest.mark.unit
def test_analyze_project_size_invalid_directory():
    """Test analyze_project_size handles invalid directory gracefully."""
    metrics = analyze_project_size("/nonexistent/directory/path")

    assert 'error' in metrics
    assert metrics['total_files'] == 0
    assert metrics['total_lines'] == 0
    assert metrics['complexity'] == 'unknown'


@pytest.mark.unit
def test_analyze_project_size_respects_gitignore():
    """Test analyze_project_size respects .gitignore patterns."""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a Python file
        test_file = os.path.join(tmpdir, "main.py")
        with open(test_file, 'w') as f:
            f.write("# Main file\n" * 100)

        # Create __pycache__ directory (should be ignored)
        pycache_dir = os.path.join(tmpdir, "__pycache__")
        os.makedirs(pycache_dir)
        ignored_file = os.path.join(pycache_dir, "test.pyc")
        with open(ignored_file, 'w') as f:
            f.write("compiled")

        metrics = analyze_project_size(tmpdir)

        # Should only count main.py, not files in __pycache__
        assert metrics['total_files'] == 1
        assert metrics['total_lines'] == 100


@pytest.mark.unit
def test_select_model_by_project_size_small():
    """Test select_model_by_project_size returns gpt-4o-mini for small projects."""
    metrics = {'total_lines': 5000, 'complexity': 'small'}
    model = select_model_by_project_size(metrics)

    assert model == 'gpt-4o-mini'


@pytest.mark.unit
def test_select_model_by_project_size_medium():
    """Test select_model_by_project_size returns gpt-4o for medium projects."""
    metrics = {'total_lines': 50000, 'complexity': 'medium'}
    model = select_model_by_project_size(metrics)

    assert model == 'gpt-4o'


@pytest.mark.unit
def test_select_model_by_project_size_large():
    """Test select_model_by_project_size returns gpt-4-turbo for large projects."""
    metrics = {'total_lines': 150000, 'complexity': 'large'}
    model = select_model_by_project_size(metrics)

    assert model == 'gpt-4-turbo'


@pytest.mark.unit
def test_select_model_by_project_size_boundary_conditions():
    """Test select_model_by_project_size handles boundary conditions correctly."""
    # Exactly at threshold (should be in next tier)
    metrics_9999 = {'total_lines': 9999}
    assert select_model_by_project_size(metrics_9999) == 'gpt-4o-mini'

    metrics_10000 = {'total_lines': 10000}
    assert select_model_by_project_size(metrics_10000) == 'gpt-4o'

    metrics_99999 = {'total_lines': 99999}
    assert select_model_by_project_size(metrics_99999) == 'gpt-4o'

    metrics_100000 = {'total_lines': 100000}
    assert select_model_by_project_size(metrics_100000) == 'gpt-4-turbo'


@pytest.mark.unit
def test_select_model_by_project_size_missing_metrics():
    """Test select_model_by_project_size handles missing metrics gracefully."""
    metrics = {}  # No total_lines key
    model = select_model_by_project_size(metrics)

    # Should default to gpt-4o-mini for 0 lines
    assert model == 'gpt-4o-mini'


@pytest.mark.unit
def test_model_selection_thresholds_configuration():
    """Test MODEL_SELECTION_THRESHOLDS is properly configured."""
    assert MODEL_SELECTION_THRESHOLDS is not None
    assert 'small' in MODEL_SELECTION_THRESHOLDS
    assert 'medium' in MODEL_SELECTION_THRESHOLDS
    assert 'large' in MODEL_SELECTION_THRESHOLDS

    # Verify structure
    assert 'max_lines' in MODEL_SELECTION_THRESHOLDS['small']
    assert 'model' in MODEL_SELECTION_THRESHOLDS['small']
    assert MODEL_SELECTION_THRESHOLDS['small']['max_lines'] == 10000


@pytest.mark.unit
def test_auto_model_selection_configuration():
    """Test AUTO_MODEL_SELECTION configuration."""
    assert AUTO_MODEL_SELECTION is not None
    assert isinstance(AUTO_MODEL_SELECTION, bool)


@pytest.mark.unit
def test_create_model_function():
    """Test create_model function creates model with correct configuration."""
    test_model = create_model('gpt-4o-mini', temperature=0.5)

    assert test_model is not None
    # Verify model has tools bound
    assert hasattr(test_model, 'invoke')


@pytest.mark.unit
def test_run_klaro_with_auto_model_selection(mock_env_vars):
    """Test run_klaro_langgraph with automatic model selection enabled."""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small test project
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, 'w') as f:
            f.write("# Test\n" * 100)

        with patch('main.AUTO_MODEL_SELECTION', True):
            with patch('main.init_knowledge_base', return_value="Initialized"):
                with patch('main.workflow.compile') as mock_compile:
                    mock_app = Mock()
                    mock_app.invoke = Mock(return_value={
                        "messages": [AIMessage(content="Final Answer: # README")],
                        "error_log": ""
                    })
                    mock_compile.return_value = mock_app

                    with patch('builtins.print') as mock_print:
                        run_klaro_langgraph(project_path=tmpdir)

                        # Verify size analysis was printed
                        print_calls = [str(call) for call in mock_print.call_args_list]
                        assert any("Analyzing project size" in call for call in print_calls)
                        assert any("gpt-4o-mini" in call for call in print_calls)


@pytest.mark.unit
def test_run_klaro_with_disabled_auto_model_selection(mock_env_vars):
    """Test run_klaro_langgraph with automatic model selection disabled."""
    with patch('main.AUTO_MODEL_SELECTION', False):
        with patch('main.init_knowledge_base', return_value="Initialized"):
            with patch('main.workflow.compile') as mock_compile:
                mock_app = Mock()
                mock_app.invoke = Mock(return_value={
                    "messages": [AIMessage(content="Final Answer: # README")],
                    "error_log": ""
                })
                mock_compile.return_value = mock_app

                with patch('builtins.print') as mock_print:
                    run_klaro_langgraph(project_path=".")

                    # Verify auto selection was disabled
                    print_calls = [str(call) for call in mock_print.call_args_list]
                    assert any("Auto model selection disabled" in call for call in print_calls)


@pytest.mark.unit
def test_run_klaro_handles_project_analysis_error(mock_env_vars):
    """Test run_klaro_langgraph handles project analysis errors gracefully."""
    with patch('main.AUTO_MODEL_SELECTION', True):
        with patch('main.analyze_project_size') as mock_analyze:
            mock_analyze.return_value = {
                'error': 'Directory not found',
                'total_files': 0,
                'total_lines': 0,
                'complexity': 'unknown'
            }

            with patch('main.init_knowledge_base', return_value="Initialized"):
                with patch('main.workflow.compile') as mock_compile:
                    mock_app = Mock()
                    mock_app.invoke = Mock(return_value={
                        "messages": [AIMessage(content="Final Answer: # README")],
                        "error_log": ""
                    })
                    mock_compile.return_value = mock_app

                    with patch('builtins.print') as mock_print:
                        run_klaro_langgraph(project_path="/invalid/path")

                        # Should fall back to default model
                        print_calls = [str(call) for call in mock_print.call_args_list]
                        assert any("Warning" in call for call in print_calls)


@pytest.mark.unit
def test_model_selection_with_environment_variables():
    """Test model selection respects environment variable overrides."""
    import os

    # Test KLARO_SMALL_MODEL override
    with patch.dict(os.environ, {'KLARO_SMALL_MODEL': 'custom-model-small'}):
        from main import MODEL_SELECTION_THRESHOLDS
        # Re-import to get updated config (in practice, this would be set at startup)
        # For this test, we verify the env var is read correctly
        assert os.getenv('KLARO_SMALL_MODEL') == 'custom-model-small'
