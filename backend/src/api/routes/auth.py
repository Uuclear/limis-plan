"""认证路由 (JWT + Session + CSRF)"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.core.db import get_db
from src.core.exceptions import AuthError, BusinessError

router = APIRouter()

class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

@router.post("/login")
async def login(req: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    from src.modules.auth.service import AuthService
    svc = AuthService(db)
    return svc.login(req, body.username, body.password)

@router.post("/logout")
async def logout(req: Request, db=Depends(get_db)):
    req.session.pop("user_id", None)
    req.session.pop("role", None)
    return {"message": "已登出"}

@router.get("/me")
async def get_current_user(req: Request, db=Depends(get_db)):
    from src.modules.auth.service import AuthService
    uid = req.session.get("user_id")
    if not uid:
        raise AuthError("未登录", 401)
    return await AuthService(db).get_user(uid)
