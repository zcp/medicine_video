from typing import Generator, Dict
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.auth import JWTAuth
from fastapi import Depends

def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 

def get_current_user(token: Dict = Depends(JWTAuth.get_current_user)) -> Dict:
    """获取当前认证用户"""
    return token