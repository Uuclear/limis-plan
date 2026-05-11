from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db
router = APIRouter()

@router.get("/workflows/{entity_type}/{entity_id}")
async def get_workflow(entity_type: str, entity_id: int, db=Depends(get_db)):
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "current_state": "received",
        "available_actions": ["start_testing", "cancel"],
        "history": [
            {"action": "submit", "from_state": "draft", "to_state": "received", "time": "2025-05-10T09:00:00"}
        ]
    }

@router.post("/workflows/{entity_type}/{entity_id}/transitions")
async def apply_transition(entity_type: str, entity_id: int, body: dict, request: Request, db=Depends(get_db)):
    action = body.get("action")
    reason = body.get("reason", "")
    user = body.get("user", "system")
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "previous_state": "received",
        "new_state": "testing",
        "user": user,
        "reason": reason,
    }
