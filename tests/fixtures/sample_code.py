"""
Sample Python Code for Testing

This file provides sample Python code used in test cases for AST analysis,
code reading, and documentation generation testing.

Contains:
    - Functions with various parameter types and return annotations
    - Classes with methods and docstrings
    - Docstrings in Google style format
    - Type hints for testing annotation extraction
"""


def simple_function(name: str) -> str:
    """Returns a greeting message.

    Args:
        name: The name to greet

    Returns:
        A greeting string
    """
    return f"Hello, {name}!"


def function_with_multiple_params(x: int, y: int, z: int = 0) -> int:
    """Adds three numbers together.

    Args:
        x: First number
        y: Second number
        z: Third number (optional, defaults to 0)

    Returns:
        The sum of x, y, and z
    """
    return x + y + z


def function_without_docstring(a, b):
    return a + b


class SimpleClass:
    """A simple class for demonstration.

    This class demonstrates basic class structure for testing
    AST analysis capabilities.

    Attributes:
        name: The name attribute
    """

    def __init__(self, name: str):
        """Initializes the SimpleClass.

        Args:
            name: The name to store
        """
        self.name = name

    def get_name(self) -> str:
        """Returns the name.

        Returns:
            The stored name
        """
        return self.name

    def set_name(self, name: str) -> None:
        """Sets a new name.

        Args:
            name: The new name to set
        """
        self.name = name


class ComplexClass:
    """A more complex class with various method types."""

    def __init__(self, value: int = 0):
        self.value = value

    def increment(self) -> int:
        """Increments the value by 1."""
        self.value += 1
        return self.value

    def add(self, amount: int) -> int:
        """Adds the specified amount to value."""
        self.value += amount
        return self.value

    @staticmethod
    def static_method(x: int, y: int) -> int:
        """A static method that multiplies two numbers."""
        return x * y

    @classmethod
    def from_string(cls, value_str: str):
        """Creates an instance from a string."""
        return cls(int(value_str))


async def async_function(duration: float) -> str:
    """An async function for testing async function detection.

    Args:
        duration: How long to wait

    Returns:
        A completion message
    """
    import asyncio
    await asyncio.sleep(duration)
    return "Done"


class ClassWithoutDocstring:
    def method_without_docstring(self, x):
        return x * 2
