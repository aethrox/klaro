"""
Klaro Test Suite

This package contains all tests for the Klaro autonomous documentation agent.

Test Organization:
    - test_tools.py: Unit tests for custom tools (list_files, read_file, analyze_code, RAG)
    - test_main.py: Unit tests for agent state, graph structure, and workflow
    - test_integration.py: End-to-end integration tests simulating full agent execution
    - conftest.py: Shared pytest fixtures and configuration
    - fixtures/: Sample projects and code for testing

Running Tests:
    # Run all tests
    pytest tests/

    # Run specific test file
    pytest tests/test_tools.py

    # Run specific test
    pytest tests/test_tools.py::test_list_files_current_directory

    # Run with coverage
    pytest --cov=. tests/

    # Run with verbose output
    pytest -v tests/
"""
