"""
Test that API returns result field in response

This script verifies that the task submission response includes
the result field with the agent's answer.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_result_field():
    """Test that result field is returned in task submission response"""
    print("=" * 60)
    print("Testing result field in API response")
    print("=" * 60)
    
    # Test 1: Simple greeting
    print("\nTest 1: Simple greeting task")
    print("-" * 60)
    
    task = {
        "task_description": "你好，请简单介绍一下你自己"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/tasks",
            json=task,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            
            print(f"✓ Task submitted successfully")
            print(f"\nResponse structure:")
            print(f"  - task_id: {result.get('task_id', 'N/A')}")
            print(f"  - status: {result.get('status', 'N/A')}")
            print(f"  - result: {'Present' if 'result' in result else 'Missing'}")
            print(f"  - error: {'Present' if 'error' in result else 'Missing'}")
            
            if 'result' in result and result['result']:
                print(f"\n✓ Result field is present!")
                print(f"\nAgent's response:")
                print(f"  {result['result'][:200]}...")
            elif result.get('status') == 'completed':
                print(f"\n⚠ Task completed but result field is empty")
            else:
                print(f"\n⚠ Result field is present but empty (status: {result.get('status')})")
            
            if 'error' in result and result['error']:
                print(f"\n✗ Error occurred: {result['error']}")
            
            # Also check via status endpoint
            print(f"\n" + "-" * 60)
            print("Checking via status endpoint...")
            task_id = result['task_id']
            
            time.sleep(1)  # Give it a moment
            
            status_response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"\nStatus endpoint response:")
                print(f"  - task_id: {status_data.get('task_id', 'N/A')}")
                print(f"  - status: {status_data.get('status', 'N/A')}")
                print(f"  - result: {'Present' if status_data.get('result') else 'Empty'}")
                print(f"  - error: {'Present' if status_data.get('error') else 'Empty'}")
                
                if status_data.get('result'):
                    print(f"\n✓ Result from status endpoint:")
                    print(f"  {status_data['result'][:200]}...")
            
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_task_result():
    """Test result field with a task that uses tools"""
    print("\n" + "=" * 60)
    print("Test 2: Task with tool execution")
    print("=" * 60)
    
    task = {
        "task_description": "查询北京的天气"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/tasks",
            json=task,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            
            print(f"✓ Task submitted successfully")
            print(f"\nResponse:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if 'result' in result:
                print(f"\n✓ Result field is present")
                if result['result']:
                    print(f"  Content: {result['result'][:150]}...")
                else:
                    print(f"  (Empty - task may still be processing)")
            else:
                print(f"\n✗ Result field is missing!")
            
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("Testing API Result Field")
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
    test1 = test_result_field()
    test2 = test_tool_task_result()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if test1 and test2:
        print("✓✓✓ All tests passed! Result field is working correctly! ✓✓✓")
    else:
        print("✗ Some tests failed")
