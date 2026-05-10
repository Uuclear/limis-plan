"""Pydantic V2 Schemas"""
from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional

class LoginSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("委托单位名称不能为空")
        return v.strip()

class OrderCreate(BaseModel):
    client_id: int = Field(gt=0)
    project_name: str = Field(min_length=1, max_length=200)
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    detection_category: Optional[str] = None
    detection_nature: Optional[str] = "委托检测"
    deadline: Optional[datetime] = None
    remark: Optional[str] = None

class SampleCreate(BaseModel):
    order_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    specification: Optional[str] = ""
    quantity: int = Field(gt=0, le=10000)
    manufacturer: Optional[str] = None

class OrderSubmit(BaseModel):
    sample_list: list[SampleCreate] = Field(min_length=1)
