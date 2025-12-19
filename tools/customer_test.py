"""
Calculator tool implementation

This module provides customer function call test for the Agent Scheduler Brain.
"""


def customer_tool_call() -> dict:
    """
    计算数学表达式
    
    Args:
        None
        
    Returns:
        str: 打印已调用customer_tool_call，表示方法已经调用
        "customer_tool_call function is called."
    """
    try:
        # 安全地计算表达式
        # 注意：在生产环境中，应该使用更安全的方法，避免 eval
        # 这里为了演示简单使用 eval
        result = "customer_tool_call function is called"
        
        return {
            "result": result,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }
