"""
Sample Project Tools Module

Contains utility functions for the sample project.
"""


class Calculator:
    """A simple calculator class."""

    def add(self, a: int, b: int) -> int:
        """Adds two numbers together."""
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """Subtracts b from a."""
        return a - b


class Greeter:
    """A simple greeter class."""

    def greet(self, name: str) -> str:
        """Returns a greeting message."""
        return f"Hello, {name}!"


# Global instances
calculator = Calculator()
greeter = Greeter()
