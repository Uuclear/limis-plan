import qrcode
import io
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db
router = APIRouter()

@router.get("/")
async def list_samples(request: Request, skip: int = 0, limit: int = 20, db=Depends(get_db)):
    return {"total": 0, "items": [], "skip": skip, "limit": limit}

@router.get("/{sample_id}")
async def get_sample(sample_id: int, request: Request, db=Depends(get_db)):
    return {"id": sample_id, "sample_no": "YP-20250501-0001-A", "status": "received"}

@router.get("/{sample_id}/barcode")
async def get_barcode(sample_id: int):
    qr = qrcode.make(f"SAMPLE-{sample_id}")
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buf, media_type="image/png")
