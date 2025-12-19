"""
Weather tool implementation

This module provides weather query functionality for the Agent Scheduler Brain.
"""

import random


def get_weather(city: str, unit: str = "celsius") -> dict:
    """
    查询城市天气信息
    
    Args:
        city: 城市名称，例如 "北京"、"上海"
        unit: 温度单位，"celsius" 或 "fahrenheit"
        
    Returns:
        dict: 包含天气信息的字典
        {
            "city": "北京",
            "temperature": 15,
            "unit": "celsius",
            "condition": "晴天",
            "humidity": 45,
            "success": True
        }
    """
    try:
        # 模拟天气数据
        # 在实际应用中，这里应该调用真实的天气 API
        
        conditions = ["晴天", "多云", "阴天", "小雨", "大雨", "雪"]
        
        # 生成模拟数据
        if unit == "celsius":
            temperature = random.randint(-10, 35)
        else:  # fahrenheit
            temperature = random.randint(14, 95)
        
        weather_data = {
            "city": city,
            "temperature": temperature,
            "unit": unit,
            "condition": random.choice(conditions),
            "humidity": random.randint(20, 90),
            "wind_speed": random.randint(0, 30),
            "success": True
        }
        
        return weather_data
        
    except Exception as e:
        return {
            "city": city,
            "error": str(e),
            "success": False
        }
