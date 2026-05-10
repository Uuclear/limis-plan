from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db import get_db
from src.core.exceptions import WorkflowError
from src.api.schemas.reports import ReportCreate
router = APIRouter()

REPORT_STATES = ["draft", "pending_review", "review_rejected", "pending_approval", "approval_rejected", "signed"]

@router.get("/")
async def list_reports(skip: int = 0, limit: int = 20, db=Depends(get_db)):
    return {"total": 0, "items": []}

@router.post("/", status_code=201)
async def create_report(body: ReportCreate, request: Request, db=Depends(get_db)):
    return {"id": 1, "report_no": "REP-2025-0001", "status": "draft"}

@router.post("/{report_id}/actions/review")
async def review_report(report_id: int, body: dict, request: Request, db=Depends(get_db)):
    approved = body.get("approved", False)
    reason = body.get("reason", "")
    status = "通过" if approved else f"驳回: {reason}"
    return {"report_id": report_id, "action": "reviewed", "status": status}

@router.post("/{report_id}/actions/approve")
async def approve_report(report_id: int, body: dict, request: Request, db=Depends(get_db)):
    approved = body.get("approved", False)
    reason = body.get("reason", "")
    return {"report_id": report_id, "action": "approved", "status": "通过" if approved else f"驳回: {reason}"}

@router.post("/{report_id}/actions/sign")
async def sign_report(report_id: int, body: dict, request: Request, db=Depends(get_db)):
    password = body.get("password")
    ip = request.client.host if request.client else "unknown"
    return {"report_id": report_id, "action": "signed", "ip": ip, "timestamp": "2025-05-10T23:00:00"}

@router.get("/{report_id}/pdf")
async def download_pdf(report_id: int):
    return {"report_id": report_id, "pdf_url": "/files/reports/REP-2025-0001.pdf"}
