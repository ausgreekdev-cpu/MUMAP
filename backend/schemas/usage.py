from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UsageRecordResponse(BaseModel):
    id: int
    user_id: int
    org_id: Optional[int] = None
    usage_type: str
    quantity: float
    unit_cost: float
    total_cost: float
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    model: Optional[str] = None
    usage_metadata: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    period_start: str
    period_end: str
    total_cost: float
    by_type: dict[str, float]
    by_model: dict[str, dict]


class BillingPlanResponse(BaseModel):
    id: int
    name: str
    display_name: str
    price_monthly: float
    price_yearly: float
    token_limit: int
    task_limit: int
    agent_limit: int
    member_limit: int
    features: list[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceLineItem(BaseModel):
    description: str
    quantity: int
    unit_cost: float
    total: float


class InvoiceResponse(BaseModel):
    id: int
    user_id: int
    org_id: Optional[int] = None
    period_start: datetime
    period_end: datetime
    total_cost: float
    currency: str
    status: str
    line_items: list[InvoiceLineItem]
    payment_method_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    invoices: list[InvoiceResponse]
    total: int


class UsageCheckResponse(BaseModel):
    allowed: bool
    remaining_tokens: int
    remaining_tasks: int
    message: str


class UsageRecordListResponse(BaseModel):
    records: list[UsageRecordResponse]
    total: int
