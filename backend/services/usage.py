from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from datetime import datetime, timezone
from typing import Optional

from ..models.usage import UsageRecord, BillingPlan, Invoice, UsageType
from ..config import settings


MODEL_PRICING = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.0 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "claude-sonnet": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
    "claude-haiku": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
}


class UsageTracker:
    def __init__(self, db: Session):
        self.db = db

    def record_usage(self, user_id: int, usage_type: UsageType, quantity: float, unit_cost: float, **kwargs):
        total_cost = round(quantity * unit_cost, 6)
        record = UsageRecord(
            user_id=user_id,
            usage_type=usage_type.value,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            **kwargs,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def check_limits(self, user_id: int, org_id: Optional[int] = None) -> dict:
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        token_query = self.db.query(sql_func.coalesce(sql_func.sum(UsageRecord.quantity), 0.0)).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.usage_type.in_([UsageType.TOKEN_INPUT.value, UsageType.TOKEN_OUTPUT.value]),
            UsageRecord.created_at >= period_start,
        )
        total_tokens = float(token_query.scalar() or 0.0)

        token_limit = settings.FREE_PLAN_TOKEN_LIMIT
        task_limit = settings.FREE_PLAN_TASK_LIMIT

        return {
            "allowed": total_tokens < token_limit,
            "remaining_tokens": max(0, token_limit - int(total_tokens)),
            "remaining_tasks": task_limit,
        }


def seed_billing_plans(db: Session) -> None:
    existing = db.query(BillingPlan).count()
    if existing > 0:
        return

    plans = [
        BillingPlan(
            name="free",
            display_name="Free",
            price_monthly=0.0,
            price_yearly=0.0,
            token_limit=settings.FREE_PLAN_TOKEN_LIMIT,
            task_limit=settings.FREE_PLAN_TASK_LIMIT,
            agent_limit=3,
            member_limit=1,
            features=["basic_agents", "basic_tasks"],
            is_active=True,
        ),
        BillingPlan(
            name="pro",
            display_name="Pro",
            price_monthly=49.0,
            price_yearly=470.0,
            token_limit=settings.PRO_PLAN_TOKEN_LIMIT,
            task_limit=settings.PRO_PLAN_TASK_LIMIT,
            agent_limit=20,
            member_limit=5,
            features=["basic_agents", "basic_tasks", "advanced_agents", "priority_execution"],
            is_active=True,
        ),
        BillingPlan(
            name="enterprise",
            display_name="Enterprise",
            price_monthly=299.0,
            price_yearly=2990.0,
            token_limit=-1,
            task_limit=-1,
            agent_limit=-1,
            member_limit=-1,
            features=["basic_agents", "basic_tasks", "unlimited_agents", "dedicated_support"],
            is_active=True,
        ),
    ]

    db.add_all(plans)
    db.commit()
