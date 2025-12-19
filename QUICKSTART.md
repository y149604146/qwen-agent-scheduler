# Quick Start Guide - Qwen Agent Scheduler

This guide will help you get the Qwen Agent Scheduler system up and running in minutes.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.9 or higher installed
- [ ] PostgreSQL 13 or higher installed and running
- [ ] Ollama installed and running
- [ ] qwen3:4b model downloaded in Ollama

## Step-by-Step Setup

### 1. Install Ollama and Model (5 minutes)

```bash
# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.ai/install.sh | sh

# For Windows, download from https://ollama.ai

# Pull the qwen3:4b model
ollama pull qwen3:4b

# Verify installation
ollama list
```

### 2. Setup PostgreSQL Database (2 minutes)

```bash
# Create database
createdb test_db

# Or using psql
psql -U postgres
CREATE DATABASE test_db;
\q
```

### 3. Install Python Dependencies (3 minutes)

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install separately
pip install -r shared/requirements.txt
pip install -r method-registration/requirements.txt
pip install -r agent-scheduler/requirements.txt
```

### 4. Configure Database Connection (2 minutes)

Edit the database password in both configuration files:

**method-registration/config/model_config.yaml**:
```yaml
database:
  password: "666666"  # Change this!
```

**agent-scheduler/config/model_config.yaml**:
```yaml
database:
  password: "666666"  # Change this!
```

### 5. Register Methods (1 minute)

```bash
cd method-registration
python src/main.py
```

Expected output:
```
INFO - Successfully registered method: get_weather
INFO - Successfully registered method: calculate
INFO - Registration complete: 2 methods registered
```

### 6. Start Agent Scheduler Brain (1 minute)

```bash
cd agent-scheduler
python src/main.py
```

Expected output:
```
INFO - Loaded 2 methods from database
INFO - Starting server on http://0.0.0.0:8000
INFO - Application startup complete
```

### 7. Test the System (2 minutes)

Open a new terminal and test the API:

```bash
# Check health
curl http://localhost:8000/health

# List registered methods
curl http://localhost:8000/api/methods

# Submit a task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Calculate 2 + 2"}'
```

### 8. View API Documentation

Open your browser and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Verification Checklist

After setup, verify everything works:

- [ ] Ollama service is running: `ollama list` shows qwen3:4b
- [ ] PostgreSQL is running: `pg_isready` returns success
- [ ] Database exists: `psql -l | grep test_db` shows the database
- [ ] Methods are registered: Check database or API response
- [ ] Agent Scheduler Brain is running: http://localhost:8000/health returns OK
- [ ] API is accessible: Can submit tasks and get responses

## Common Issues and Solutions

### Issue: "Cannot connect to database"

**Solution**:
```bash
# Check PostgreSQL is running
pg_isready

# Verify database exists
psql -l | grep test_db

# Test connection
psql -h localhost -U postgres -d test_db
```

### Issue: "Cannot connect to Ollama"

**Solution**:
```bash
# Check Ollama is running
ollama list

# Test API endpoint
curl http://localhost:11434/api/tags

# Restart Ollama if needed
# (method depends on your OS)
```

### Issue: "No methods available"

**Solution**:
```bash
# Register methods first
cd method-registration
python src/main.py

# Then restart Agent Scheduler Brain
cd agent-scheduler
python src/main.py
```

### Issue: "Module not found" errors

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific module
pip install -r method-registration/requirements.txt
pip install -r agent-scheduler/requirements.txt
```

## Next Steps

Now that your system is running:

1. **Add Custom Methods**: 
   - Create your method implementation in `agent-scheduler/workspace/tools/`
   - Add method definition to `method-registration/config/methods.yaml`
   - Run Method Registration System
   - Restart Agent Scheduler Brain

2. **Explore Examples**:
   - Check `method-registration/examples/` for registration examples
   - Check `agent-scheduler/examples/` for usage examples

3. **Read Documentation**:
   - [Main README](README.md) - Complete system overview
   - [Method Registration README](method-registration/README.md) - Registration system details
   - [Agent Scheduler README](agent-scheduler/README.md) - Scheduler details
   - [Configuration Guides](method-registration/config/CONFIG_GUIDE.md) - Configuration options

4. **Run Tests**:
   ```bash
   # Run all tests
   pytest
   
   # Run specific module tests
   pytest method-registration/tests/
   pytest agent-scheduler/tests/
   ```

5. **Monitor Logs**:
   - Method Registration: `logs/app.log`
   - Agent Scheduler: `logs/agent_scheduler.log`

## Development Workflow

For ongoing development:

```bash
# 1. Implement new method
# Edit: agent-scheduler/workspace/tools/your_module.py

# 2. Define method in config
# Edit: method-registration/config/methods.yaml

# 3. Register method
cd method-registration
python src/main.py

# 4. Restart scheduler
cd agent-scheduler
python src/main.py

# 5. Test method
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task description"}'
```

## Production Deployment

For production deployment:

1. **Use Environment Variables** for sensitive data
2. **Configure Logging** to appropriate level (INFO or WARNING)
3. **Setup Log Rotation** for long-running services
4. **Use Process Manager** (systemd, supervisor, pm2)
5. **Setup Monitoring** for health checks
6. **Configure Firewall** to restrict access
7. **Use HTTPS** for API endpoints (with reverse proxy)
8. **Backup Database** regularly

See individual README files for detailed production deployment instructions.

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#common-issues-and-solutions) section above
2. Review the detailed README files
3. Check the logs for error messages
4. Verify all prerequisites are met
5. Try the examples to isolate the issue

## Summary

You should now have:
- ✅ Ollama running with qwen3:4b model
- ✅ PostgreSQL database created
- ✅ Python dependencies installed
- ✅ Methods registered in database
- ✅ Agent Scheduler Brain running
- ✅ API accessible and responding

**Total setup time**: ~15 minutes

Enjoy using Qwen Agent Scheduler! 🚀
