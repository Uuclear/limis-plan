from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReportCreate(BaseModel):
    order_id: int = Field(gt=0)
    template_id: Optional[int] = None
    conclusion: Optional[str] = None

class ReportReview(BaseModel):
    approved: bool
    reason: str = Field(min_length=1, max_length=1000)

class ReportSign(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)
