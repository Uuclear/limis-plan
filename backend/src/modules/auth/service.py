"""认证服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import AuthError, BusinessError

class AuthService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    def login(self, request, username: str, password: str):
        return {"message": "todo: implement login with password hash + session", "user": username}

    async def get_user(self, user_id: int):
        return {"id": user_id, "username": "placeholder"}
