"""数据模型定义"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Numeric, JSON, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

class TimestampMixin:
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class User(TimestampMixin):
    __tablename__ = "auth_users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    role_id = Column(Integer, ForeignKey("auth_roles.id"))
    status = Column(String(10), default="active")
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(TIMESTAMP(timezone=True))
    last_login = Column(TIMESTAMP(timezone=True))

class Role(TimestampMixin):
    __tablename__ = "auth_roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(30), unique=True, nullable=False)
    description = Column(Text)
    is_system = Column(Boolean, default=False)

class Permission(TimestampMixin):
    __tablename__ = "auth_permissions"
    id = Column(Integer, primary_key=True)
    resource = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    scope = Column(String(20), nullable=False)
    description = Column(String(200))

class RolePermission(TimestampMixin):
    __tablename__ = "auth_role_permissions"
    role_id = Column(Integer, ForeignKey("auth_roles.id"), primary_key=True)
    resource = Column(String(50), primary_key=True)
    action = Column(String(20), primary_key=True)
    scope = Column(String(20), default="self")

class Client(TimestampMixin):
    __tablename__ = "commission_clients"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(30), unique=True)
    contact_person = Column(String(50))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    credit_level = Column(String(10), default="A")
    discount_rate = Column(Numeric(5, 2), default=0)
    status = Column(String(10), default="active")

class Order(TimestampMixin):
    __tablename__ = "commission_orders"
    id = Column(Integer, primary_key=True)
    order_no = Column(String(30), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("commission_clients.id"))
    project_name = Column(String(200))
    contact_person = Column(String(50))
    phone = Column(String(20))
    detection_category = Column(String(20))
    detection_nature = Column(String(10))
    deadline = Column(DateTime)
    status = Column(String(20), default="draft")
    remark = Column(Text)
    created_by = Column(Integer, ForeignKey("auth_users.id"))
    total_price = Column(Numeric(10, 2), default=0)

class Sample(TimestampMixin):
    __tablename__ = "commission_samples"
    id = Column(Integer, primary_key=True)
    sample_no = Column(String(30), unique=True, nullable=False, index=True)
    barcode = Column(String(64), unique=True)
    order_id = Column(Integer, ForeignKey("commission_orders.id"))
    name = Column(String(200), nullable=False)
    specification = Column(String(500))
    quantity = Column(Integer, nullable=False)
    manufacturer = Column(String(200))
    status = Column(String(20), default="received")
    location = Column(String(100))
    received_by = Column(Integer, ForeignKey("auth_users.id"))
    received_at = Column(TIMESTAMP(timezone=True))
    expiry_date = Column(DateTime)

class TestMethod(TimestampMixin):
    __tablename__ = "testing_methods"
    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    standard_id = Column(Integer, ForeignKey("standards_library.id"))
    category = Column(String(30))
    description = Column(Text)
    pricing_code = Column(String(30))

class TestTask(TimestampMixin):
    __tablename__ = "testing_tasks"
    id = Column(Integer, primary_key=True)
    task_no = Column(String(30), unique=True, nullable=False)
    sample_id = Column(Integer, ForeignKey("commission_samples.id"))
    test_method_id = Column(Integer, ForeignKey("testing_methods.id"))
    assigned_to = Column(Integer, ForeignKey("auth_users.id"))
    status = Column(String(30), default="pending")
    priority = Column(String(10), default="normal")
    deadline = Column(DateTime)
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))

class AuditLog:
    __tablename__ = "auth_audit_log"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("auth_users.id"))
    action = Column(String(30), nullable=False)
    resource = Column(String(50), nullable=False)
    resource_id = Column(Integer)
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
