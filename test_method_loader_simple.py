"""Simple test script for MethodLoader functionality"""

import sys
from pathlib import Path
import json

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agent-scheduler"))

from shared.models import DatabaseConfig, MethodMetadata, MethodParameter
from src.method_loader import MethodLoader

def test_convert_to_qwen_tools():
    """Test converting methods to qwen-agent format"""
    print("Testing convert_to_qwen_tools...")
    
    # Create a sample method
    params = [
        MethodParameter(
            name="city",
            type="string",
            description="City name",
            required=True
        ),
        MethodParameter(
            name="unit",
            type="string",
            description="Temperature unit",
            required=False,
            default="celsius"
        )
    ]
    
    params_json = json.dumps([p.to_dict() for p in params])
    
    method = MethodMetadata(
        name="get_weather",
        description="Get weather information for a city",
        parameters_json=params_json,
        return_type="dict",
        module_path="tools.weather",
        function_name="get_weather"
    )
    
    # Create loader (without actual DB connection for this test)
    db_config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="test",
        user="test",
        password="test"
    )
    
    try:
        loader = MethodLoader(db_config)
    except Exception as e:
        print(f"Note: Could not connect to database (expected): {e}")
        print("Testing convert_to_qwen_tools without DB connection...")
        # We can still test the conversion method
        loader = object.__new__(MethodLoader)
    
    # Test conversion
    qwen_tools = loader.convert_to_qwen_tools([method])
    
    assert len(qwen_tools) == 1, f"Expected 1 tool, got {len(qwen_tools)}"
    
    tool = qwen_tools[0]
    assert tool["name"] == "get_weather", f"Expected name 'get_weather', got {tool['name']}"
    assert tool["description"] == "Get weather information for a city"
    assert "parameters" in tool
    
    params = tool["parameters"]
    assert params["type"] == "object"
    assert "city" in params["properties"]
    assert params["properties"]["city"]["type"] == "string"
    assert "city" in params["required"]
    assert "unit" not in params["required"]
    
    print("✓ convert_to_qwen_tools test passed!")
    print(f"  Generated tool: {json.dumps(tool, indent=2)}")
    
    return True

def test_type_mapping():
    """Test parameter type mapping"""
    print("\nTesting type mapping...")
    
    test_cases = [
        ("string", "string"),
        ("int", "integer"),
        ("float", "number"),
        ("bool", "boolean"),
        ("dict", "object"),
        ("list", "array"),
    ]
    
    loader = object.__new__(MethodLoader)
    
    for input_type, expected_type in test_cases:
        method = MethodMetadata(
            name=f"test_{input_type}",
            description="Test method",
            parameters_json=json.dumps([{
                "name": "param",
                "type": input_type,
                "description": "Test parameter",
                "required": True
            }]),
            return_type="string",
            module_path="test",
            function_name="test"
        )
        
        qwen_tools = loader.convert_to_qwen_tools([method])
        param_type = qwen_tools[0]["parameters"]["properties"]["param"]["type"]
        
        assert param_type == expected_type, f"Type {input_type} should map to {expected_type}, got {param_type}"
        print(f"  ✓ {input_type} -> {expected_type}")
    
    print("✓ Type mapping test passed!")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("MethodLoader Simple Tests")
    print("=" * 60)
    
    try:
        test_convert_to_qwen_tools()
        test_type_mapping()
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
