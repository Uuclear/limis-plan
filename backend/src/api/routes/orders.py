from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db
from src.api.schemas.base import OrderCreate, OrderSubmit, ClientCreate
router = APIRouter()

@router.get("/")
async def list_orders(request: Request, skip: int = 0, limit: int = 20, db=Depends(get_db)):
    return {"total": 0, "items": [], "skip": skip, "limit": limit}

@router.post("/", status_code=201)
async def create_order(body: OrderCreate, request: Request, db=Depends(get_db)):
    return {"message": "委托创建成功", "order": {"id": 1, "order_no": "WT-202505-0001"}}

@router.post("/{order_id}/submit", status_code=200)
async def submit_order(order_id: int, body: OrderSubmit, request: Request, db=Depends(get_db)):
    return {"message": f"委托 {order_id} 已提交, 共 {len(body.sample_list)} 个样品", "order_no": "WT-202505-0001"}
