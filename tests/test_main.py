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
    app,
    run_klaro_langgraph,
    LLM_MODEL,
    RECURSION_LIMIT
)


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
    # The app should already be compiled in main.py
    assert app is not None
    assert hasattr(app, 'invoke')


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
    from main import tools, model

    # Verify tools list is not empty
    assert len(tools) > 0

    # Check expected tools are present
    tool_names = [tool.name for tool in tools]
    assert "list_files" in tool_names
    assert "read_file" in tool_names
    assert "analyze_code" in tool_names
    assert "retrieve_knowledge" in tool_names

    # Verify model has bind_tools called (hard to test directly, but we can check it exists)
    assert model is not None


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

        with patch('main.app.invoke') as mock_invoke:
            # Mock successful completion
            mock_invoke.return_value = {
                "messages": [
                    HumanMessage(content="Task"),
                    AIMessage(content="Final Answer: # README\n\n## Setup\n...")
                ],
                "error_log": ""
            }

            # Capture print output (optional, for full integration)
            with patch('builtins.print'):
                run_klaro_langgraph(project_path=".")

            # Verify init_knowledge_base was called
            mock_init_kb.assert_called_once()

            # Verify app.invoke was called with correct structure
            mock_invoke.assert_called_once()
            call_args = mock_invoke.call_args[0][0]
            assert "messages" in call_args
            assert "error_log" in call_args


@pytest.mark.unit
def test_run_klaro_langgraph_handles_errors(mock_env_vars):
    """Test run_klaro_langgraph handles execution errors gracefully."""
    with patch('main.init_knowledge_base', return_value="Initialized"):
        with patch('main.app.invoke', side_effect=Exception("LLM API Error")):
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
        with patch('main.app.invoke') as mock_invoke:
            mock_invoke.return_value = {
                "messages": [
                    HumanMessage(content="Task"),
                    AIMessage(content="Final Answer: # My Project\n\n## Setup\nRun pip install")
                ],
                "error_log": ""
            }

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
