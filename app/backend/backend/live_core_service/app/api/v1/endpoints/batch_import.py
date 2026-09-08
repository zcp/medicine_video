"""
LiveCore Service - Batch Import API Endpoints

This module contains API endpoints for batch importing rooms and sessions.
"""

from fastapi import APIRouter, Depends, Query, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional
from uuid import UUID
import logging

from app.core.deps import get_db, get_current_user
from app.core.response import success_response, error_response
from app.services.batch_import import BatchImportService
from app.exceptions import InvalidParameterException, PermissionDeniedException

logger = logging.getLogger(__name__)

batch_import_router = APIRouter(tags=["Batch Import"])


@batch_import_router.post("/import/batch")
async def batch_import_rooms(
    file: UploadFile = File(...),
    mode: str = Query("dry_run", regex="^(dry_run|apply)$"),
    encoding_hint: Optional[str] = Query(None, regex="^(utf-8-sig|utf-8|gbk)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    批量导入直播间和会话（Admin Only）
    
    参数：
    - file: CSV 或 Excel 文件
    - mode: dry_run（仅校验）或 apply（实际写库）
    - encoding_hint: 文件编码提示（可选）
    """
    # ← 新增：提取用户信息（在try之前）
    public_id = UUID(current_user.get("user_id") or current_user.get("public_id"))  # 从JWT的user_id字段提取
    role = current_user.get("role", "REGULAR")  # 从JWT的role字段提取
    
    # 验证文件类型
    if not file.filename.endswith(('.csv', '.xlsx')):
        logger.warning(f"无效的文件类型: {file.filename}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=4001, message="仅支持 .csv 或 .xlsx 文件")
        )

    try:
        service = BatchImportService(db)
        # ← 修改：传递权限参数
        import_report = await service.import_from_file(
            public_id=public_id,
            file=file,
            mode=mode,
            encoding_hint=encoding_hint,
            role=role  # ← 新增：传递role参数
        )
        return success_response(data=import_report)
    
    except PermissionDeniedException as e:  # ← 新增：捕获权限拒绝异常
        logger.warning(f"权限不足: public_id={public_id}, role={role}")
        return JSONResponse(
            status_code=403,
            content=error_response(code=3002, message="权限不足")
        )
    except InvalidParameterException as e:
        logger.warning(f"参数错误: {e.message}")
        return JSONResponse(
            status_code=400,
            content=error_response(code=e.code, message=e.message)
        )
    
    except Exception as e:
        logger.error(f"批量导入失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(code=1000, message="服务器内部错误")
        )
