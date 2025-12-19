"""
Test qwen-agent configuration with Ollama

This script tests different qwen-agent configurations to find one that works
with local Ollama without requiring DashScope API key.
"""

import os
import sys

# Set empty API key to disable validation
os.environ['DASHSCOPE_API_KEY'] = ''

print("Testing qwen-agent with Ollama...")
print("=" * 60)

try:
    from qwen_agent.agents import Assistant
    print("✓ qwen-agent imported successfully")
except ImportError as e:
    print(f"✗ Failed to import qwen-agent: {e}")
    sys.exit(1)

# Test configuration
configs_to_test = [
    {
        'name': 'Config 1: Basic Ollama',
        'config': {
            'model': 'qwen3:4b',
            'api_base': 'http://localhost:11434',
            'generate_cfg': {
                'temperature': 0.7,
                'max_tokens': 100,
            }
        }
    },
    {
        'name': 'Config 2: Ollama with model_server',
        'config': {
            'model': 'qwen3:4b',
            'model_server': 'ollama',
            'api_base': 'http://localhost:11434',
            'generate_cfg': {
                'temperature': 0.7,
                'max_tokens': 100,
            }
        }
    },
    {
        'name': 'Config 3: OpenAI-compatible',
        'config': {
            'model': 'qwen3:4b',
            'model_server': 'openai',
            'api_base': 'http://localhost:11434/v1',
            'api_key': 'dummy',
            'generate_cfg': {
                'temperature': 0.7,
                'max_tokens': 100,
            }
        }
    },
]

for test in configs_to_test:
    print(f"\n{test['name']}")
    print("-" * 60)
    
    try:
        # Try to create Assistant
        agent = Assistant(llm=test['config'])
        print("✓ Assistant created successfully")
        
        # Try a simple query
        messages = [{'role': 'user', 'content': '你好'}]
        
        print("  Sending test message...")
        response = agent.run(messages=messages)
        
        if response:
            print("✓ Got response from agent")
            print(f"  Response: {str(response)[:100]}...")
            print("\n✓✓✓ This configuration works! ✓✓✓")
            break
        else:
            print("✗ No response from agent")
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        if "api" in str(e).lower() and "key" in str(e).lower():
            print("  (API key error)")

print("\n" + "=" * 60)
print("Test complete")
