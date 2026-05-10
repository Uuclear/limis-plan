from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db

router = APIRouter()

@router.get("/")
async def list_items(skip: int = 0, limit: int = 20, db=Depends(get_db)):
    return {"total": 0, "items": []}

@router.post("/", status_code=201)
async def create_item(body: dict, db=Depends(get_db)):
    return {"id": 1, "message": "created"}
