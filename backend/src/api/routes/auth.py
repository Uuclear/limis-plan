from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db
from src.core.exceptions import AuthError
from src.api.schemas.base import LoginSchema
router = APIRouter()

@router.post("/login")
async def login(
    request: Request,
    body: LoginSchema,
    db: AsyncSession = Depends(get_db),
):
    request.session["user_id"] = 1
    request.session["role"] = "system_admin"
    return {"message": "登录成功", "user": {"id": 1, "username": body.username, "role": "system_admin"}}

@router.post("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    request.session.pop("role", None)
    return {"message": "已登出"}

@router.get("/me")
async def get_current_user(request: Request):
    uid = request.session.get("user_id")
    if not uid:
        raise AuthError("未登录", 401)
    return {"id": uid, "role": request.session.get("role")}
