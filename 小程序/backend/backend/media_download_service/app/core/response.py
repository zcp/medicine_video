from datetime import datetime
from typing import Any, Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class ResponseModel(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None
    timestamp: str = datetime.utcnow().isoformat()

def create_response(
    data: Any = None,
    message: str = "success",
    code: int = 200
) -> JSONResponse:
    """创建成功响应"""
    return JSONResponse(
        content=ResponseModel(
            code=code,
            message=message,
            data=data
        ).model_dump()
    )

def create_error_response(
    message: str,
    code: int = 400,
    data: Any = None
) -> JSONResponse:
    """创建错误响应"""
    return JSONResponse(
        content=ResponseModel(
            code=code,
            message=message,
            data=data
        ).model_dump()
    ) 