from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db
router = APIRouter()

@router.get("/")
def list_samples(db=Depends(get_db)):
    return []

@router.post("/")
def create_sample(db=Depends(get_db)):
    return {"message": "sample created"}
