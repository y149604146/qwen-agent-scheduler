"""Demo script showing MetadataValidator usage

This script demonstrates how to use the MetadataValidator to validate
method configurations before registration.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Add workspace root
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add method-registration root

from shared.models import MethodConfig, MethodParameter
from src.validator import MetadataValidator


def main():
    """Run validator demo"""
    validator = MetadataValidator()
    
    print("=" * 70)
    print("MetadataValidator Demo")
    print("=" * 70)
    print()
    
    # Example 1: Valid method
    print("Example 1: Valid method configuration")
    print("-" * 70)
    valid_method = MethodConfig(
        name="get_weather",
        description="Get weather information for a city",
        parameters=[
            MethodParameter(
                name="city",
                type="string",
                description="Name of the city",
                required=True
            ),
            MethodParameter(
                name="unit",
                type="string",
                description="Temperature unit (celsius or fahrenheit)",
                required=False,
                default="celsius"
            )
        ],
        return_type="dict",
        module_path="tools.weather",
        function_name="get_weather"
    )
    
    result = validator.validate_method(valid_method)
    print(f"Method name: {valid_method.name}")
    print(f"Valid: {result.valid}")
    if result.errors:
        print(f"Errors: {result.errors}")
    else:
        print("No errors - method is valid!")
    print()
    
    # Example 2: Invalid method name
    print("Example 2: Invalid method name (contains hyphen)")
    print("-" * 70)
    invalid_name_method = MethodConfig(
        name="get-weather",  # Invalid: contains hyphen
        description="Get weather information",
        parameters=[],
        return_type="dict",
        module_path="tools.weather",
        function_name="get_weather"
    )
    
    result = validator.validate_method(invalid_name_method)
    print(f"Method name: {invalid_name_method.name}")
    print(f"Valid: {result.valid}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    print()
    
    # Example 3: Missing parameter fields
    print("Example 3: Parameter missing required fields")
    print("-" * 70)
    invalid_param_method = MethodConfig(
        name="calculate",
        description="Perform calculation",
        parameters=[
            MethodParameter(
                name="value",
                type="",  # Invalid: empty type
                description=""  # Invalid: empty description
            )
        ],
        return_type="float",
        module_path="tools.math",
        function_name="calculate"
    )
    
    result = validator.validate_method(invalid_param_method)
    print(f"Method name: {invalid_param_method.name}")
    print(f"Valid: {result.valid}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
    print()
    
    # Example 4: Batch validation with duplicate names
    print("Example 4: Batch validation detecting duplicate names")
    print("-" * 70)
    methods = [
        MethodConfig(
            name="process_data",
            description="Process data method 1",
            parameters=[],
            return_type="None",
            module_path="tools.processor",
            function_name="process1"
        ),
        MethodConfig(
            name="process_data",  # Duplicate name
            description="Process data method 2",
            parameters=[],
            return_type="None",
            module_path="tools.processor",
            function_name="process2"
        )
    ]
    
    results = validator.validate_methods(methods)
    for idx, result in enumerate(results):
        print(f"Method {idx + 1}: {result.method_name}")
        print(f"  Valid: {result.valid}")
        if result.errors:
            print("  Errors:")
            for error in result.errors:
                print(f"    - {error}")
    print()
    
    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
