from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float, Index
from sqlalchemy.sql import func
import enum

from .base import Base


class UsageType(str, enum.Enum):
    TOKEN_INPUT = "token_input"
    TOKEN_OUTPUT = "token_output"
    TASK_RUN = "task_run"
    TOOL_CALL = "tool_call"
    API_REQUEST = "api_request"
    STORAGE = "storage"
    COMPUTE_SECONDS = "compute_seconds"


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    usage_type = Column(String(30), nullable=False)
    quantity = Column(Float, nullable=False, default=0.0)
    unit_cost = Column(Float, nullable=False, default=0.0)
    total_cost = Column(Float, nullable=False, default=0.0)

    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    model = Column(String(100), nullable=True)

    usage_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_usage_user_created", "user_id", "created_at"),
        Index("ix_usage_org_created", "org_id", "created_at"),
    )


class BillingPlan(Base):
    __tablename__ = "billing_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)

    price_monthly = Column(Float, nullable=False, default=0.0)
    price_yearly = Column(Float, nullable=False, default=0.0)

    token_limit = Column(Integer, nullable=False, default=-1)
    task_limit = Column(Integer, nullable=False, default=-1)
    agent_limit = Column(Integer, nullable=False, default=-1)
    member_limit = Column(Integer, nullable=False, default=-1)

    features = Column(JSON, default=list)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    total_cost = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="USD")

    status = Column(String(20), nullable=False, default="draft")

    line_items = Column(JSON, default=list)

    payment_method_id = Column(String(255), nullable=True)
    stripe_invoice_id = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
