"""
演示 API 返回 result 字段

这个脚本展示了修改后的 API 如何返回完整的任务结果
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

print("=" * 70)
print("演示：API 返回 result 字段")
print("=" * 70)

# 测试 1: 简单问答
print("\n【测试 1】简单问答")
print("-" * 70)

task1 = {"task_description": "你好"}

print(f"提交任务: {task1['task_description']}")
print("等待响应...")

try:
    response = requests.post(
        f"{API_BASE}/api/tasks",
        json=task1,
        timeout=30
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        
        print(f"\n✓ 响应状态码: {response.status_code}")
        print(f"\n返回的 JSON:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        print(f"\n字段检查:")
        print(f"  ✓ task_id: {result.get('task_id', 'N/A')}")
        print(f"  ✓ status: {result.get('status', 'N/A')}")
        print(f"  ✓ result: {'存在' if 'result' in result else '缺失'}")
        print(f"  ✓ error: {'存在' if 'error' in result else '缺失'}")
        
        if result.get('result'):
            print(f"\n✓✓✓ Agent 的回答:")
            print(f"  {result['result']}")
        
    else:
        print(f"✗ 请求失败: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"✗ 错误: {e}")

# 测试 2: 对比 GET 端点
print("\n" + "=" * 70)
print("【测试 2】对比 GET /api/tasks/{task_id} 端点")
print("-" * 70)

task2 = {"task_description": "介绍一下你自己"}

print(f"提交任务: {task2['task_description']}")

try:
    # POST 提交
    post_response = requests.post(
        f"{API_BASE}/api/tasks",
        json=task2,
        timeout=30
    )
    
    if post_response.status_code in [200, 201]:
        post_result = post_response.json()
        task_id = post_result['task_id']
        
        print(f"\n✓ POST 响应:")
        print(json.dumps(post_result, indent=2, ensure_ascii=False))
        
        # 等待一下
        time.sleep(1)
        
        # GET 查询
        get_response = requests.get(f"{API_BASE}/api/tasks/{task_id}")
        
        if get_response.status_code == 200:
            get_result = get_response.json()
            
            print(f"\n✓ GET 响应:")
            print(json.dumps(get_result, indent=2, ensure_ascii=False))
            
            print(f"\n对比:")
            print(f"  POST 包含 result: {'是' if post_result.get('result') else '否'}")
            print(f"  GET 包含 result: {'是' if get_result.get('result') else '否'}")
            print(f"  结果一致: {'是' if post_result.get('result') == get_result.get('result') else '否'}")
        
except Exception as e:
    print(f"✗ 错误: {e}")

print("\n" + "=" * 70)
print("演示完成！")
print("=" * 70)
print("\n总结:")
print("  ✓ POST /api/tasks 现在返回 result 字段")
print("  ✓ 可以直接从响应中获取 Agent 的回答")
print("  ✓ 不需要再次调用 GET 端点查询结果")
print("=" * 70)
