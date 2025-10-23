"""
Sample Project Main Module

This is a sample project used for integration testing of the Klaro agent.
"""

from tools import calculator, greeter


def main():
    """Main entry point for the sample application."""
    print("Sample Project Running")

    result = calculator.add(5, 3)
    print(f"5 + 3 = {result}")

    greeting = greeter.greet("World")
    print(greeting)


if __name__ == "__main__":
    main()
