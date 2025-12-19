"""
Test script to verify Ollama's OpenAI-compatible API

This script tests if Ollama's OpenAI-compatible endpoint is working correctly.
"""

import requests
import json

def test_ollama_openai_api():
    """Test Ollama's OpenAI-compatible API endpoint"""
    
    print("Testing Ollama OpenAI-compatible API...")
    print("=" * 60)
    
    # Ollama's OpenAI-compatible endpoint
    url = "http://localhost:11434/v1/chat/completions"
    
    # Request payload in OpenAI format
    payload = {
        "model": "qwen3:4b",
        "messages": [
            {"role": "user", "content": "你好，请用一句话介绍你自己"}
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Sending request to: {url}")
        print(f"Model: {payload['model']}")
        print(f"Message: {payload['messages'][0]['content']}")
        print()
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Success!")
            print()
            print("Response:")
            print("-" * 60)
            
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0]['message']['content']
                print(message)
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            
            print("-" * 60)
            print()
            print("Ollama's OpenAI-compatible API is working correctly!")
            return True
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection Error")
        print()
        print("Ollama service is not running or not accessible.")
        print("Please start Ollama with: ollama serve")
        return False
    except requests.exceptions.Timeout:
        print("✗ Timeout Error")
        print()
        print("Request timed out. The model might be loading or the service is slow.")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_ollama_standard_api():
    """Test Ollama's standard API endpoint (for comparison)"""
    
    print("\nTesting Ollama standard API (for comparison)...")
    print("=" * 60)
    
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "qwen3:4b",
        "prompt": "你好，请用一句话介绍你自己",
        "stream": False
    }
    
    try:
        print(f"Sending request to: {url}")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Standard API also working!")
            print(f"Response: {result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"✗ Failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print()
    print("Ollama OpenAI-Compatible API Test")
    print("=" * 60)
    print()
    
    # Test OpenAI-compatible API
    openai_success = test_ollama_openai_api()
    
    # Test standard API
    standard_success = test_ollama_standard_api()
    
    print()
    print("=" * 60)
    print("Test Summary:")
    print(f"  OpenAI-compatible API: {'✓ Working' if openai_success else '✗ Failed'}")
    print(f"  Standard API: {'✓ Working' if standard_success else '✗ Failed'}")
    print("=" * 60)
    
    if openai_success:
        print()
        print("✓ Ollama is configured correctly for qwen-agent!")
        print("  You can now restart the Agent Scheduler service.")
    else:
        print()
        print("✗ Please ensure:")
        print("  1. Ollama service is running: ollama serve")
        print("  2. qwen3:4b model is downloaded: ollama pull qwen3:4b")
        print("  3. Ollama is accessible at http://localhost:11434")
