# Method Registration System - Usage Guide

## Overview

The Method Registration System is a command-line tool that reads method configurations from YAML files, validates them, and registers them to a PostgreSQL database.

## Prerequisites

1. **Python 3.9+** installed
2. **PostgreSQL** database running (for actual registration, not needed for dry-run)
3. **Dependencies** installed:
   ```bash
   pip install -r requirements.txt
   pip install -r ../shared/requirements.txt
   ```

## Basic Usage

### 1. Validate Configuration (Dry Run)

Test your configuration without writing to the database:

```bash
cd method-registration
python src/main.py --dry-run
```

This will:
- Load model configuration from `config/model_config.yaml`
- Load methods configuration from `config/methods.yaml`
- Validate all method metadata
- Report any validation errors
- **NOT** write to database

### 2. Register Methods to Database

Register methods to PostgreSQL database:

```bash
cd method-registration
python src/main.py
```

This will:
- Load configurations
- Validate methods
- Create database schema if needed
- Insert/update methods in database

### 3. Custom Configuration Files

Use custom configuration files:

```bash
python src/main.py \
  --model-config path/to/custom_model.yaml \
  --methods-config path/to/custom_methods.yaml
```

### 4. Debug Mode

Run with detailed logging:

```bash
python src/main.py --log-level DEBUG
```

### 5. Save Logs to File

Save logs to a file:

```bash
python src/main.py --log-file logs/registration.log
```

## Command-Line Options

```
usage: main.py [-h] [--model-config MODEL_CONFIG]
               [--methods-config METHODS_CONFIG]
               [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
               [--log-file LOG_FILE] [--dry-run]

options:
  -h, --help            Show help message
  --model-config        Path to model config file (default: config/model_config.yaml)
  --methods-config      Path to methods config file (default: config/methods.yaml)
  --log-level           Logging level (default: INFO)
  --log-file            Optional log file path
  --dry-run             Validate without writing to database
```

## Configuration Files

### Model Configuration (model_config.yaml)

```yaml
model:
  name: "qwen3:4b"
  api_base: "http://localhost:11434"
  timeout: 30
  temperature: 0.7
  max_tokens: 2000

database:
  host: "localhost"
  port: 5432
  database: "test_db"
  user: "yuanyuan"
  password: "666666"
  pool_size: 5

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"
```

### Methods Configuration (methods.yaml)

```yaml
methods:
  - name: "get_weather"
    description: "Get weather information for a city"
    module_path: "tools.weather"
    function_name: "get_weather"
    parameters:
      - name: "city"
        type: "string"
        description: "City name"
        required: true
      - name: "unit"
        type: "string"
        description: "Temperature unit (celsius/fahrenheit)"
        required: false
        default: "celsius"
    return_type: "dict"
  
  - name: "calculate"
    description: "Perform mathematical calculation"
    module_path: "tools.calculator"
    function_name: "calculate"
    parameters:
      - name: "expression"
        type: "string"
        description: "Mathematical expression to evaluate"
        required: true
    return_type: "float"
```

## Exit Codes

- **0**: Success
- **1**: Error (configuration, validation, or database error)
- **130**: Cancelled by user (Ctrl+C)

## Examples

### Example 1: First Time Setup

```bash
# 1. Validate configuration
python src/main.py --dry-run

# 2. If validation passes, register to database
python src/main.py
```

### Example 2: Update Methods

```bash
# Edit config/methods.yaml to add/modify methods
# Then run:
python src/main.py
```

The system will automatically update existing methods or insert new ones.

### Example 3: Debug Validation Issues

```bash
python src/main.py --dry-run --log-level DEBUG
```

### Example 4: Production Deployment

```bash
python src/main.py \
  --model-config /etc/qwen-agent/model_config.yaml \
  --methods-config /etc/qwen-agent/methods.yaml \
  --log-file /var/log/qwen-agent/registration.log \
  --log-level INFO
```

## Common Issues

### Issue: "Configuration file not found"

**Solution**: Check that the configuration file path is correct. Use absolute paths or paths relative to the current directory.

```bash
# Check current directory
pwd

# Use absolute path
python src/main.py --model-config /full/path/to/config.yaml
```

### Issue: "Database connection failed"

**Solution**: 
1. Ensure PostgreSQL is running
2. Check database credentials in `model_config.yaml`
3. Verify database exists or has permissions to create it

```bash
# Check PostgreSQL status
pg_isready

# Test connection
psql -h localhost -U postgres -d test_db
```

### Issue: "Validation failed"

**Solution**: Check the error messages for specific validation issues:
- Method names must be valid Python identifiers
- All required fields must be present
- No duplicate method names
- Parameter types must be valid

Use `--log-level DEBUG` for detailed validation information.

### Issue: "Module not found"

**Solution**: Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
pip install -r ../shared/requirements.txt
```

## Integration with Agent Scheduler

After registering methods, they become available to the Agent Scheduler Brain:

1. **Register methods** using this tool
2. **Start Agent Scheduler** which will load methods from database
3. **Submit tasks** to Agent Scheduler via API
4. **Agent uses registered methods** to complete tasks

See `../agent-scheduler/README.md` for Agent Scheduler usage.

## Automation

### Cron Job

Register methods automatically on schedule:

```bash
# Add to crontab
0 2 * * * cd /path/to/method-registration && python src/main.py --log-file logs/cron.log
```

### CI/CD Pipeline

```yaml
# Example GitHub Actions workflow
- name: Register Methods
  run: |
    cd method-registration
    python src/main.py \
      --model-config config/production.yaml \
      --methods-config config/methods.yaml
```

## Development

### Testing Configuration

Use dry-run mode during development:

```bash
# Test configuration changes
python src/main.py --dry-run --log-level DEBUG
```

### Adding New Methods

1. Edit `config/methods.yaml`
2. Add new method definition
3. Validate: `python src/main.py --dry-run`
4. Register: `python src/main.py`

### Updating Existing Methods

Simply edit the method in `config/methods.yaml` and run:

```bash
python src/main.py
```

The system will automatically update the existing method in the database (upsert behavior).

## Support

For issues or questions:
1. Check logs with `--log-level DEBUG`
2. Verify configuration files are valid YAML
3. Ensure database is accessible
4. Review validation error messages

## See Also

- [Configuration Guide](config/CONFIG_GUIDE.md)
- [Agent Scheduler Documentation](../agent-scheduler/README.md)
- [Design Document](../.kiro/specs/qwen-agent-scheduler/design.md)
