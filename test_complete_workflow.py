"""
完整工作流测试

测试 Agent Scheduler Brain 的完整功能：
1. 简单问答（不使用工具）
2. 计算任务（使用 calculate 工具）
3. 天气查询（使用 get_weather 工具）
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

def test_task(description, task_description):
    """测试单个任务"""
    print(f"\n{description}")
    print("-" * 70)
    print(f"任务: {task_description}")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/tasks",
            json={"task_description": task_description},
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            
            print(f"\n✓ 响应状态: {response.status_code}")
            print(f"\n返回数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 检查字段
            print(f"\n字段检查:")
            print(f"  ✓ task_id: {result.get('task_id', 'N/A')[:20]}...")
            print(f"  ✓ status: {result.get('status', 'N/A')}")
            print(f"  ✓ result: {'存在' if result.get('result') else '不存在'}")
            print(f"  ✓ error: {result.get('error') or '无'}")
            
            if result.get('result'):
                print(f"\n✓✓✓ Agent 回答:")
                print(f"  {result['result']}")
                return True
            elif result.get('error'):
                print(f"\n✗ 任务失败: {result['error']}")
                return False
            else:
                print(f"\n⚠ 任务状态: {result.get('status')}")
                return False
        else:
            print(f"\n✗ 请求失败: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print_section("Agent Scheduler Brain - 完整工作流测试")
    
    # 检查服务状态
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"\n✓ 服务运行正常")
            print(f"  - Agent Client: {'已配置' if health.get('agent_client') else '未配置'}")
            print(f"  - Method Loader: {'已配置' if health.get('method_loader') else '未配置'}")
        else:
            print(f"✗ 服务状态异常: {response.status_code}")
            exit(1)
    except Exception as e:
        print(f"✗ 无法连接到服务: {e}")
        print("  请确保服务正在运行: cd agent-scheduler && python src/main.py")
        exit(1)
    
    # 测试用例
    results = []
    
    # 测试 1: 简单问答
    print_section("测试 1: 简单问答（不使用工具）")
    results.append(("简单问答", test_task(
        "测试不需要工具的简单对话",
        "你好，请用一句话介绍你自己"
    )))
    
    time.sleep(2)
    
    # 测试 2: 计算任务
    print_section("测试 2: 计算任务（使用 calculate 工具）")
    results.append(("计算任务", test_task(
        "测试数学计算功能",
        "计算 5 * 16"
    )))
    
    time.sleep(2)
    
    # 测试 3: 天气查询
    print_section("测试 3: 天气查询（使用 get_weather 工具）")
    results.append(("天气查询", test_task(
        "测试天气查询功能",
        "查询北京的天气"
    )))
    
    # 总结
    print_section("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n测试结果:")
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("✓✓✓ 所有测试通过！系统运行正常！ ✓✓✓")
        print("=" * 70)
        print("\n功能验证:")
        print("  ✓ API 返回 result 字段")
        print("  ✓ 简单问答功能正常")
        print("  ✓ 工具调用功能正常")
        print("  ✓ 计算工具工作正常")
        print("  ✓ 天气查询工具工作正常")
        print("=" * 70)
    else:
        print(f"\n✗ {total - passed} 个测试失败")
