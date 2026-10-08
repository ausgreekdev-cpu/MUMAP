from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models.usage import UsageRecord, UsageType
from ..models.organization import OrgMember
from ..schemas.usage import (
    UsageRecordResponse,
    UsageRecordListResponse,
    UsageSummary,
    BillingPlanResponse,
    InvoiceResponse,
    InvoiceListResponse,
    UsageCheckResponse,
)
from ..services.auth import get_current_user
from ..services.usage import UsageTracker

router = APIRouter(prefix="/usage", tags=["usage"])


def _get_user_org_id(db: Session, user) -> Optional[int]:
    """Resolve the first organization the user belongs to (User has no org_id column)."""
    member = db.query(OrgMember).filter(OrgMember.user_id == user.id).first()
    return member.org_id if member else None


def _month_bounds_utc() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        period_end = period_start.replace(year=now.year + 1, month=1)
    else:
        period_end = period_start.replace(month=now.month + 1)
    return period_start, period_end


@router.get("/summary", response_model=UsageSummary)
def get_usage_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    tracker = UsageTracker(db)
    period_start, period_end = _month_bounds_utc()

    by_type = tracker.get_usage_summary(current_user.id, period_start, period_end)
    by_model = tracker.get_usage_by_model(current_user.id, period_start, period_end)

    return UsageSummary(
        period_start=by_type["period_start"],
        period_end=by_type["period_end"],
        total_cost=by_type["total_cost"],
        total_tokens=by_type["total_tokens"],
        total_tasks=by_type["total_tasks"],
        by_type=by_type["by_type"],
        by_model=by_model.get("by_model", {}),
    )


@router.get("/records", response_model=UsageRecordListResponse)
def list_usage_records(
    usage_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    query = db.query(UsageRecord).filter(UsageRecord.user_id == current_user.id)

    if usage_type:
        query = query.filter(UsageRecord.usage_type == usage_type)
    if start_date:
        query = query.filter(UsageRecord.created_at >= start_date)
    if end_date:
        query = query.filter(UsageRecord.created_at <= end_date)

    query = query.order_by(UsageRecord.created_at.desc())
    total = query.count()
    records = query.offset(skip).limit(limit).all()

    return UsageRecordListResponse(records=records, total=total)


@router.get("/check", response_model=UsageCheckResponse)
def check_usage_limits(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    tracker = UsageTracker(db)
    org_id = _get_user_org_id(db, current_user)
    result = tracker.check_limits(current_user.id, org_id)
    return UsageCheckResponse(**result)


@router.get("/costs/by-model", response_model=UsageSummary)
def get_costs_by_model(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    tracker = UsageTracker(db)
    period_start, period_end = _month_bounds_utc()

    summary = tracker.get_usage_summary(current_user.id, period_start, period_end)
    by_model = tracker.get_usage_by_model(current_user.id, period_start, period_end)

    return UsageSummary(
        period_start=summary["period_start"],
        period_end=summary["period_end"],
        total_cost=summary["total_cost"],
        total_tokens=summary["total_tokens"],
        total_tasks=summary["total_tasks"],
        by_type=summary["by_type"],
        by_model=by_model.get("by_model", {}),
    )


@router.get("/billing/plans", response_model=list[BillingPlanResponse])
def list_billing_plans(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    from ..models.usage import BillingPlan
    plans = db.query(BillingPlan).filter(BillingPlan.is_active == True).all()
    return plans


@router.get("/billing/invoices", response_model=InvoiceListResponse)
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    from ..models.usage import Invoice
    query = db.query(Invoice).filter(Invoice.user_id == current_user.id)
    query = query.order_by(Invoice.created_at.desc())
    total = query.count()
    invoices = query.offset(skip).limit(limit).all()
    return InvoiceListResponse(invoices=invoices, total=total)


@router.post("/billing/invoices/generate", response_model=InvoiceResponse)
def generate_invoice(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    tracker = UsageTracker(db)
    period_start, period_end = _month_bounds_utc()
    org_id = _get_user_org_id(db, current_user)
    invoice = tracker.generate_invoice(current_user.id, period_start, period_end, org_id)
    return invoice
