# MetadataValidator Implementation

## Overview

The `MetadataValidator` class provides comprehensive validation of method metadata before registration in the database. It ensures that all method configurations meet the requirements specified in the design document.

## Features

### Method Name Validation
- Must be a valid Python identifier
- Length between 2-100 characters
- Cannot be a Python keyword
- Cannot contain spaces or special characters (except underscore)
- Cannot start with a digit

### Description Validation
- Cannot be empty
- Maximum length of 1000 characters

### Module Path Validation
- Must be a valid Python module path
- Each component must be a valid identifier
- Supports nested modules (e.g., `package.subpackage.module`)

### Function Name Validation
- Must be a valid Python identifier
- Same rules as method names

### Return Type Validation
- Must be a recognized Python type string
- Supported types: `string`, `str`, `int`, `integer`, `float`, `bool`, `boolean`, `dict`, `dictionary`, `list`, `array`, `tuple`, `set`, `None`, `NoneType`, `Any`, `bytes`, `bytearray`

### Parameter Validation
- Each parameter must have:
  - `name`: Valid Python identifier
  - `type`: Valid Python type string
  - `description`: Non-empty string (max 500 characters)
- No duplicate parameter names within a method
- Parameter types must be from the supported types list

### Batch Validation
- Validates multiple methods at once
- Detects duplicate method names across the entire batch
- Returns individual validation results for each method

## Usage

### Single Method Validation

```python
from shared import MethodConfig, MethodParameter
from src.validator import MetadataValidator

validator = MetadataValidator()

method = MethodConfig(
    name="get_weather",
    description="Get weather information",
    parameters=[
        MethodParameter(
            name="city",
            type="string",
            description="City name"
        )
    ],
    return_type="dict",
    module_path="tools.weather",
    function_name="get_weather"
)

result = validator.validate_method(method)

if result.valid:
    print("Method is valid!")
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

### Batch Validation

```python
methods = [method1, method2, method3]
results = validator.validate_methods(methods)

for result in results:
    if not result.valid:
        print(f"Method '{result.method_name}' has errors:")
        for error in result.errors:
            print(f"  - {error}")
```

## Requirements Coverage

The validator implementation satisfies the following requirements:

- **Requirement 2.4**: Reports specific validation errors for missing required fields
- **Requirement 2.5**: Detects and reports duplicate method names
- **Requirement 3.1**: Validates method names conform to Python identifier rules
- **Requirement 3.2**: Validates parameter completeness (name, type, description)
- **Requirement 3.3**: Validates return type validity
- **Requirement 3.4**: Generates detailed error reports with field names and reasons
- **Requirement 3.5**: Marks methods as valid/invalid via ValidationResult

## Testing

The validator has comprehensive test coverage:

- **28 unit tests** covering all validation rules
- **4 integration tests** demonstrating integration with ConfigParser
- **100% pass rate** on all tests

Run tests with:
```bash
cd method-registration
python -m pytest tests/test_validator.py -v
python -m pytest tests/test_integration_validator.py -v
```

## Demo

A demonstration script is available at `examples/validator_demo.py` showing various validation scenarios:

```bash
cd method-registration
python examples/validator_demo.py
```

## Implementation Details

### Class Structure

```python
class MetadataValidator:
    VALID_TYPES = {...}  # Set of recognized Python types
    
    def validate_method(self, method: MethodConfig) -> ValidationResult
    def validate_methods(self, methods: List[MethodConfig]) -> List[ValidationResult]
    
    # Private helper methods
    def _is_valid_identifier(self, name: str) -> bool
    def _is_valid_module_path(self, path: str) -> bool
    def _is_valid_type(self, type_str: str) -> bool
```

### Validation Order

1. Method name validation
2. Description validation
3. Module path validation
4. Function name validation
5. Return type validation
6. Parameter validation (for each parameter)
7. Duplicate detection (in batch validation)

### Error Reporting

All validation errors include:
- The field that failed validation
- The reason for the failure
- The invalid value (when applicable)

Example error messages:
- `"Method name 'get-weather' is not a valid Python identifier. Must start with letter or underscore, contain only letters, digits, and underscores, and not be a Python keyword"`
- `"Parameter 'data' has invalid type 'CustomType'. Valid types: Any, array, bool, boolean, bytearray, bytes, dict, dictionary, float, int, integer, list, None, NoneType, set, str, string, tuple"`
- `"Duplicate method name 'calculate' found in configuration"`

## Next Steps

The validator is now ready to be integrated with:
1. **DatabaseWriter** (Task 6) - Validate methods before database insertion
2. **Main Entry Point** (Task 7) - Validate configuration on system startup
