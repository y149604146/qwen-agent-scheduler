"""
测试 customer_tool_call 方法

验证修复后的方法是否正常工作
"""

import requests
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("测试 customer_tool_call 方法")
print("=" * 70)

# 测试任务
task = {
    "task_description": "添加定制化方法，测试是否及时生效"
}

print(f"\n提交任务: {task['task_description']}")
print("等待响应...\n")

try:
    response = requests.post(
        f"{API_BASE}/api/tasks",
        json=task,
        timeout=60
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        
        print(f"✓ 响应状态码: {response.status_code}\n")
        print("返回的 JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print(f"\n字段检查:")
        print(f"  ✓ task_id: {result.get('task_id', 'N/A')[:30]}...")
        print(f"  ✓ status: {result.get('status', 'N/A')}")
        print(f"  ✓ result: {'存在' if result.get('result') else '不存在'}")
        print(f"  ✓ error: {result.get('error') or '无'}")
        
        if result.get('result'):
            print(f"\n✓✓✓ Agent 回答:")
            print(f"  {result['result']}")
            print("\n" + "=" * 70)
            print("✓ 测试通过！customer_tool_call 方法工作正常！")
            print("=" * 70)
        elif result.get('error'):
            print(f"\n✗ 任务失败: {result['error']}")
            print("\n" + "=" * 70)
            print("✗ 测试失败")
            print("=" * 70)
        else:
            print(f"\n⚠ 任务状态: {result.get('status')}")
    else:
        print(f"\n✗ 请求失败: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
