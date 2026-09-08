"""
LiveCore Service - Response Utilities

This module contains utility functions for constructing standardized API responses.
"""

from datetime import datetime
from typing import Any


def success_response(data: Any, message: str = "success") -> dict:
    """
    构建标准的成功响应体
    
    Args:
        data: 响应数据
        message: 响应消息
        
    Returns:
        标准格式的响应字典
    """
    return {
        "code": 200,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat() + "Z"
    }


def error_response(code: int, message: str, data: Any = None) -> dict:
    """
    构建标准的错误响应体
    
    Args:
        code: 业务错误码
        message: 错误消息
        data: 错误详细数据
        
    Returns:
        标准格式的错误响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat() + "Z"
    } 