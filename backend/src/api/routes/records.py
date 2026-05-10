from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db
router = APIRouter()

@router.post("/tasks/{task_id}/records", status_code=201)
async def create_record(task_id: int, body: dict, request: Request, db=Depends(get_db)):
    return {"task_id": task_id, "record_id": 1, "parameters": body.get("parameters", [])}

@router.get("/tasks/{task_id}/records")
async def get_records(task_id: int, db=Depends(get_db)):
    return {"task_id": task_id, "records": []}

@router.put("/records/{record_id}")
async def update_record(record_id: int, body: dict, request: Request, db=Depends(get_db)):
    return {"record_id": record_id, "message": "更新成功"}

@router.websocket("/ws/instrument/{task_id}")
async def instrument_ws(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"status": "received", "data": data, "task_id": task_id})
    except WebSocketDisconnect:
        pass
