"""
Calculator tool implementation

This module provides calculation functionality for the Agent Scheduler Brain.
"""


def calculate(expression: str) -> dict:
    """
    计算数学表达式
    
    Args:
        expression: 要计算的数学表达式，例如 "2+2" 或 "5*16"
        
    Returns:
        dict: 包含计算结果的字典
        {
            "expression": "5*16",
            "result": 80,
            "success": True
        }
    """
    try:
        # 安全地计算表达式
        # 注意：在生产环境中，应该使用更安全的方法，避免 eval
        # 这里为了演示简单使用 eval
        result = eval(expression, {"__builtins__": {}}, {})
        
        return {
            "expression": expression,
            "result": result,
            "success": True
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e),
            "success": False
        }
