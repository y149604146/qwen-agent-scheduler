# Configuration Guide - Agent Scheduler Brain

This directory contains the configuration file for the Agent Scheduler Brain service.

## Configuration File

### model_config.yaml

This file configures:
- Ollama model settings for natural language understanding
- PostgreSQL database connection for loading registered methods
- Logging configuration

## Configuration Structure

```yaml
model:
  name: "qwen3:4b"                          # Ollama model name
  api_base: "http://localhost:11434"        # Ollama API endpoint
  timeout: 30                                # Request timeout (seconds)
  temperature: 0.7                           # Generation temperature (0.0-1.0)
  max_tokens: 2000                           # Maximum tokens to generate

database:
  host: "localhost"                          # PostgreSQL host
  port: 5432                                 # PostgreSQL port
  database: "test_db"                  # Database name
  user: "yuanyuan"                           # Database user
  password: "666666"                       # Database password
  pool_size: 5                               # Connection pool size

logging:
  level: "INFO"                              # Log level
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/agent_scheduler.log"           # Log file path
```

## Field Descriptions

### Model Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model.name` | string | Yes | Ollama model name (e.g., "qwen3:4b", "qwen2:7b") |
| `model.api_base` | string | Yes | Ollama API endpoint URL |
| `model.timeout` | integer | Yes | Request timeout in seconds (default: 30) |
| `model.temperature` | float | Yes | Generation temperature 0.0-1.0 (higher = more creative) |
| `model.max_tokens` | integer | Yes | Maximum tokens to generate per response |

### Database Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `database.host` | string | Yes | PostgreSQL host address |
| `database.port` | integer | Yes | PostgreSQL port number (default: 5432) |
| `database.database` | string | Yes | Database name (must match method-registration) |
| `database.user` | string | Yes | Database username |
| `database.password` | string | Yes | Database password |
| `database.pool_size` | integer | Yes | Connection pool size (default: 5) |

### Logging Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `logging.level` | string | Yes | Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `logging.format` | string | Yes | Python logging format string |
| `logging.file` | string | Yes | Log file path (relative or absolute) |

## Configuration Details

### Model Settings

**name**: The Ollama model to use for natural language understanding
- Recommended: `qwen3:4b` (good balance of speed and quality)
- Alternatives: `qwen2:7b`, `qwen2:13b` (better quality, slower)
- Must be pulled first: `ollama pull qwen3:4b`

**api_base**: The Ollama service endpoint
- Default: `http://localhost:11434`
- For remote Ollama: `http://your-server:11434`

**timeout**: Maximum time to wait for model response
- Default: 30 seconds
- Increase for complex tasks or slower models
- Decrease for faster response times

**temperature**: Controls randomness in generation
- 0.0: Deterministic, always same output
- 0.7: Balanced (recommended)
- 1.0: More creative, varied outputs

**max_tokens**: Maximum length of generated response
- Default: 2000 tokens
- Increase for longer responses
- Decrease to save resources

### Database Settings

**Important**: The database configuration must match the configuration used by the Method Registration System. Both systems must connect to the same database to work together.

**host**: PostgreSQL server address
- `localhost` for local development
- IP address or hostname for remote database

**port**: PostgreSQL port
- Default: 5432
- Change if using non-standard port

**database**: Database name
- Must exist before starting the service
- Must contain registered methods from Method Registration System

**user**: Database username
- Must have SELECT permissions on `registered_methods` table

**password**: Database password
- **Security**: Never commit passwords to version control
- Consider using environment variables

**pool_size**: Number of database connections to maintain
- Default: 5
- Increase for high-traffic scenarios
- Decrease to save resources

### Logging Settings

**level**: Controls verbosity of logs
- `DEBUG`: Very detailed, for development
- `INFO`: General information (recommended)
- `WARNING`: Only warnings and errors
- `ERROR`: Only errors
- `CRITICAL`: Only critical errors

**format**: Python logging format string
- Default includes timestamp, logger name, level, and message
- Customize as needed for your logging infrastructure

**file**: Where to write logs
- Relative path: `logs/agent_scheduler.log`
- Absolute path: `/var/log/agent_scheduler.log`
- Use `null` or empty string for console-only logging

## Usage Examples

### Basic Usage

```bash
# Use default configuration
python src/main.py

# Specify custom configuration file
python src/main.py --config config/model_config.yaml
```

### Command Line Overrides

```bash
# Override host and port
python src/main.py --host 0.0.0.0 --port 8080

# Override log level
python src/main.py --log-level DEBUG

# Override log file
python src/main.py --log-file /var/log/agent_scheduler.log

# Combine multiple overrides
python src/main.py --config config/model_config.yaml --host 0.0.0.0 --port 8080 --log-level DEBUG
```

## Environment-Specific Configurations

### Development Configuration

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
  database: "test_db_dev"
  user: "dev_user"
  password: "dev_password"
  pool_size: 3

logging:
  level: "DEBUG"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/dev.log"
```

### Production Configuration

```yaml
model:
  name: "qwen3:4b"
  api_base: "http://ollama-service:11434"
  timeout: 60
  temperature: 0.5
  max_tokens: 2000

database:
  host: "prod-db.example.com"
  port: 5432
  database: "test_db"
  user: "prod_user"
  password: "${DB_PASSWORD}"  # Use environment variable
  pool_size: 10

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/var/log/agent_scheduler/app.log"
```

### Testing Configuration

```yaml
model:
  name: "qwen3:4b"
  api_base: "http://localhost:11434"
  timeout: 10
  temperature: 0.0  # Deterministic for testing
  max_tokens: 1000

database:
  host: "localhost"
  port: 5432
  database: "test_db_test"
  user: "test_user"
  password: "test_password"
  pool_size: 2

logging:
  level: "DEBUG"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/test.log"
```

## Best Practices

### Security

1. **Never commit passwords**: Use environment variables or secret management
2. **Use strong passwords**: For database connections
3. **Restrict database permissions**: Grant only necessary permissions
4. **Use HTTPS**: For remote Ollama connections (if supported)
5. **Secure log files**: Ensure logs don't contain sensitive data

### Performance

1. **Tune pool_size**: Based on expected concurrent requests
2. **Adjust timeout**: Based on model speed and task complexity
3. **Monitor logs**: Watch for performance issues
4. **Use appropriate model**: Balance speed vs. quality
5. **Cache results**: Consider caching for repeated queries

### Reliability

1. **Test configuration**: Validate before deploying
2. **Monitor database**: Ensure database is healthy
3. **Check Ollama**: Verify Ollama service is running
4. **Log rotation**: Implement log rotation for long-running services
5. **Health checks**: Use `/health` endpoint for monitoring

### Development

1. **Use DEBUG logging**: During development
2. **Separate databases**: Use different databases for dev/test/prod
3. **Version control**: Track configuration changes
4. **Document changes**: Note why configuration was changed
5. **Test incrementally**: Test configuration changes one at a time

## Troubleshooting

### Cannot Connect to Database

**Symptoms**: Database connection errors on startup

**Solutions**:
1. Verify PostgreSQL is running: `pg_isready -h localhost -p 5432`
2. Check database exists: `psql -l | grep test_db`
3. Verify credentials: `psql -h localhost -U postgres -d test_db`
4. Check network connectivity
5. Review database logs

### Cannot Connect to Ollama

**Symptoms**: Model initialization errors

**Solutions**:
1. Verify Ollama is running: `ollama list`
2. Check model is available: `ollama pull qwen3:4b`
3. Test API endpoint: `curl http://localhost:11434/api/tags`
4. Check firewall settings
5. Review Ollama logs

### No Methods Available

**Symptoms**: Service starts but reports no methods

**Solutions**:
1. Verify methods are registered: Check database
2. Run Method Registration System first
3. Check database connection
4. Verify table exists: `registered_methods`
5. Check user permissions

### Slow Response Times

**Symptoms**: API requests take too long

**Solutions**:
1. Increase timeout value
2. Use faster model (e.g., qwen3:4b instead of qwen2:13b)
3. Reduce max_tokens
4. Check database query performance
5. Monitor system resources

### High Memory Usage

**Symptoms**: Service consumes too much memory

**Solutions**:
1. Reduce pool_size
2. Reduce max_tokens
3. Use smaller model
4. Implement request rate limiting
5. Monitor for memory leaks

## Integration with Method Registration System

The Agent Scheduler Brain depends on methods registered by the Method Registration System:

1. **Same Database**: Both systems must use the same database
2. **Same Schema**: Both systems expect the `registered_methods` table
3. **Reload Methods**: Restart Agent Scheduler Brain after registering new methods
4. **Consistent Configuration**: Keep database settings synchronized

### Workflow

```
1. Configure Method Registration System
   ↓
2. Register methods to database
   ↓
3. Configure Agent Scheduler Brain (same database)
   ↓
4. Start Agent Scheduler Brain
   ↓
5. Methods are loaded and available via API
```

## Additional Resources

- [Agent Scheduler Brain README](../README.md)
- [Main Project README](../../README.md)
- [Method Registration System](../../method-registration/README.md)
- [Design Document](../../.kiro/specs/qwen-agent-scheduler/design.md)
- [API Documentation](http://localhost:8000/docs) (when service is running)
