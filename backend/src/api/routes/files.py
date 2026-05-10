from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db
from src.core.file_storage import LocalFileStorage
from src.core.config import settings

router = APIRouter()

storage = LocalFileStorage(settings.file_storage_base_dir)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    meta = storage.store(content, "attachments", file.filename)
    return meta
