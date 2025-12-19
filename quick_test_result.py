"""Quick test for result field"""
import requests
import json

response = requests.post(
    "http://localhost:8000/api/tasks",
    json={"task_description": "你好"},
    timeout=30
)

print("Status Code:", response.status_code)
print("\nResponse JSON:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
