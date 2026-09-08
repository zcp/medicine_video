"""
LiveCore Service - Batch Import Schemas

This module contains Pydantic schemas for the batch import feature.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

class BatchImportRow(BaseModel):
    """批量导入的单行结果"""
    row_no: int
    room_id: Optional[UUID]
    session_id: Optional[UUID]
    status: str  # 'success' or 'failed'
    error: Optional[str]

class BatchImportResponse(BaseModel):
    """批量导入的响应体"""
    total_rows: int
    success_count: int
    failed_count: int
    items: List[BatchImportRow]
