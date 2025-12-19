"""Test tools for MethodExecutor testing

This module provides simple test functions that can be used
to test the MethodExecutor functionality.
"""


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


def greet(name: str, greeting: str = "Hello") -> str:
    """Generate a greeting message
    
    Args:
        name: Name to greet
        greeting: Greeting word (default: "Hello")
        
    Returns:
        Greeting message
    """
    return f"{greeting}, {name}!"


def divide(numerator: float, denominator: float) -> float:
    """Divide two numbers
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        
    Returns:
        Result of division
        
    Raises:
        ZeroDivisionError: If denominator is zero
    """
    return numerator / denominator


def slow_function(duration: int) -> str:
    """A function that takes time to execute
    
    Args:
        duration: How long to sleep in seconds
        
    Returns:
        Success message
    """
    import time
    time.sleep(duration)
    return f"Slept for {duration} seconds"


def process_data(data: dict) -> dict:
    """Process a dictionary of data
    
    Args:
        data: Input data dictionary
        
    Returns:
        Processed data with added metadata
    """
    result = data.copy()
    result['processed'] = True
    result['item_count'] = len(data)
    return result


def list_items(items: list) -> int:
    """Count items in a list
    
    Args:
        items: List of items
        
    Returns:
        Number of items
    """
    return len(items)
