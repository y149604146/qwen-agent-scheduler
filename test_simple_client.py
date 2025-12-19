"""
Test the simplified Agent client

This script tests the SimpleAgentClient by submitting tasks to the API.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_simple_task():
    """Test a simple task that doesn't require tools"""
    print("=" * 60)
    print("Test 1: Simple greeting (no tools needed)")
    print("=" * 60)
    
    task = {
        "task_description": "你好，介绍一下你自己"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/tasks",
            json=task,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Task created: {result['task_id']}")
            print(f"  Status: {result['status']}")
            
            # Wait a bit for processing
            time.sleep(2)
            
            # Check task status
            task_id = result['task_id']
            status_response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"\n✓ Task status: {status['status']}")
                if status.get('result'):
                    print(f"  Response: {status['result'][:200]}...")
                if status.get('error'):
                    print(f"  Error: {status['error']}")
            
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_tool_task():
    """Test a task that requires tool execution"""
    print("\n" + "=" * 60)
    print("Test 2: Weather query (requires get_weather tool)")
    print("=" * 60)
    
    task = {
        "task_description": "查询北京今天的天气"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/tasks",
            json=task,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Task created: {result['task_id']}")
            print(f"  Status: {result['status']}")
            
            # Wait for processing
            time.sleep(3)
            
            # Check task status
            task_id = result['task_id']
            status_response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"\n✓ Task status: {status['status']}")
                if status.get('result'):
                    print(f"  Response: {status['result'][:200]}...")
                if status.get('error'):
                    print(f"  Error: {status['error']}")
            
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_list_methods():
    """Test listing available methods"""
    print("\n" + "=" * 60)
    print("Test 3: List available methods")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/api/methods")
        
        if response.status_code == 200:
            methods = response.json()
            print(f"✓ Found {len(methods)} methods:")
            for method in methods:
                print(f"  - {method['name']}: {method['description']}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("Testing SimpleAgentClient Implementation")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running\n")
        else:
            print("✗ Server returned unexpected status")
            exit(1)
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print("  Make sure the server is running: cd agent-scheduler && python src/main.py")
        exit(1)
    
    # Run tests
    results = []
    
    results.append(("List methods", test_list_methods()))
    results.append(("Simple task", test_simple_task()))
    results.append(("Tool task", test_tool_task()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓✓✓ All tests passed! SimpleAgentClient is working! ✓✓✓")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
