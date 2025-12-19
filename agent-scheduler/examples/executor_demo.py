"""Demo script for MethodExecutor

This script demonstrates how to use the MethodExecutor to execute
registered methods dynamically.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from shared.models import MethodMetadata, MethodParameter

# Import from agent-scheduler
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.executor import MethodExecutor


def create_sample_methods():
    """Create sample method metadata for demonstration"""
    methods = {}
    
    # Method 1: add_numbers
    add_params = [
        MethodParameter(name="a", type="int", description="First number", required=True),
        MethodParameter(name="b", type="int", description="Second number", required=True)
    ]
    methods["add_numbers"] = MethodMetadata(
        name="add_numbers",
        description="Add two numbers",
        parameters_json=json.dumps([p.to_dict() for p in add_params]),
        return_type="int",
        module_path="workspace.tools.test_tools",
        function_name="add_numbers"
    )
    
    # Method 2: greet
    greet_params = [
        MethodParameter(name="name", type="string", description="Name to greet", required=True),
        MethodParameter(name="greeting", type="string", description="Greeting word", 
                       required=False, default="Hello")
    ]
    methods["greet"] = MethodMetadata(
        name="greet",
        description="Generate greeting",
        parameters_json=json.dumps([p.to_dict() for p in greet_params]),
        return_type="string",
        module_path="workspace.tools.test_tools",
        function_name="greet"
    )
    
    # Method 3: divide
    divide_params = [
        MethodParameter(name="numerator", type="float", description="Numerator", required=True),
        MethodParameter(name="denominator", type="float", description="Denominator", required=True)
    ]
    methods["divide"] = MethodMetadata(
        name="divide",
        description="Divide two numbers",
        parameters_json=json.dumps([p.to_dict() for p in divide_params]),
        return_type="float",
        module_path="workspace.tools.test_tools",
        function_name="divide"
    )
    
    return methods


def main():
    """Main demo function"""
    print("=" * 60)
    print("MethodExecutor Demo")
    print("=" * 60)
    
    # Create sample methods
    methods = create_sample_methods()
    
    # Initialize executor
    executor = MethodExecutor(methods, default_timeout=30)
    print(f"\nInitialized executor with {len(methods)} methods")
    
    # Demo 1: Execute simple method
    print("\n" + "-" * 60)
    print("Demo 1: Execute add_numbers(5, 3)")
    print("-" * 60)
    result = executor.execute("add_numbers", {"a": 5, "b": 3})
    if result.success:
        print(f"✓ Success: {result.result}")
        print(f"  Execution time: {result.execution_time:.3f}s")
    else:
        print(f"✗ Error: {result.error}")
    
    # Demo 2: Execute with type conversion
    print("\n" + "-" * 60)
    print("Demo 2: Execute add_numbers('10', '20') - with type conversion")
    print("-" * 60)
    result = executor.execute("add_numbers", {"a": "10", "b": "20"})
    if result.success:
        print(f"✓ Success: {result.result}")
        print(f"  Execution time: {result.execution_time:.3f}s")
    else:
        print(f"✗ Error: {result.error}")
    
    # Demo 3: Execute with optional parameter
    print("\n" + "-" * 60)
    print("Demo 3: Execute greet('Alice') - using default greeting")
    print("-" * 60)
    result = executor.execute("greet", {"name": "Alice"})
    if result.success:
        print(f"✓ Success: {result.result}")
        print(f"  Execution time: {result.execution_time:.3f}s")
    else:
        print(f"✗ Error: {result.error}")
    
    # Demo 4: Execute with optional parameter provided
    print("\n" + "-" * 60)
    print("Demo 4: Execute greet('Bob', 'Hi') - custom greeting")
    print("-" * 60)
    result = executor.execute("greet", {"name": "Bob", "greeting": "Hi"})
    if result.success:
        print(f"✓ Success: {result.result}")
        print(f"  Execution time: {result.execution_time:.3f}s")
    else:
        print(f"✗ Error: {result.error}")
    
    # Demo 5: Handle exception
    print("\n" + "-" * 60)
    print("Demo 5: Execute divide(10, 0) - division by zero")
    print("-" * 60)
    result = executor.execute("divide", {"numerator": 10.0, "denominator": 0.0})
    if result.success:
        print(f"✓ Success: {result.result}")
    else:
        print(f"✗ Error: {result.error}")
        print(f"  Execution time: {result.execution_time:.3f}s")
    
    # Demo 6: Missing required parameter
    print("\n" + "-" * 60)
    print("Demo 6: Execute add_numbers(5) - missing parameter 'b'")
    print("-" * 60)
    result = executor.execute("add_numbers", {"a": 5})
    if result.success:
        print(f"✓ Success: {result.result}")
    else:
        print(f"✗ Error: {result.error}")
        print(f"  Execution time: {result.execution_time:.3f}s")
    
    # Demo 7: Invalid type conversion
    print("\n" + "-" * 60)
    print("Demo 7: Execute add_numbers('abc', 5) - invalid type conversion")
    print("-" * 60)
    result = executor.execute("add_numbers", {"a": "abc", "b": 5})
    if result.success:
        print(f"✓ Success: {result.result}")
    else:
        print(f"✗ Error: {result.error}")
        print(f"  Execution time: {result.execution_time:.3f}s")
    
    # Demo 8: Method not found
    print("\n" + "-" * 60)
    print("Demo 8: Execute nonexistent_method() - method not found")
    print("-" * 60)
    result = executor.execute("nonexistent_method", {})
    if result.success:
        print(f"✓ Success: {result.result}")
    else:
        print(f"✗ Error: {result.error}")
        print(f"  Execution time: {result.execution_time:.3f}s")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
