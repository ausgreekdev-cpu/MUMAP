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

TASK_RUN_COST = 0.01
TOOL_CALL_COST = 0.001


def calculate_cost(model: Optional[str], input_tokens: int = 0, output_tokens: int = 0) -> float:
    if model and model in MODEL_PRICING:
        pricing = MODEL_PRICING[model]
        return input_tokens * pricing["input"] + output_tokens * pricing["output"]
    return 0.0


class UsageTracker:
    def __init__(self, db: Session):
        self.db = db

    def record_usage(
        self,
        user_id: int,
        usage_type: UsageType,
        quantity: float,
        unit_cost: float,
        org_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        model: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> UsageRecord:
        total_cost = round(quantity * unit_cost, 6)

        record = UsageRecord(
            user_id=user_id,
            org_id=org_id,
            usage_type=usage_type.value,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            resource_type=resource_type,
            resource_id=resource_id,
            model=model,
            usage_metadata=metadata or {},
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def _month_bounds(self, dt: Optional[datetime] = None) -> tuple[datetime, datetime]:
        now = dt or datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            period_end = period_start.replace(year=now.year + 1, month=1)
        else:
            period_end = period_start.replace(month=now.month + 1)
        return period_start, period_end

    def get_usage_summary(
        self,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        org_id: Optional[int] = None,
    ) -> dict:
        # Usage is always counted per user; org_id only selects the billing plan.
        query = self.db.query(UsageRecord).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.created_at >= period_start,
            UsageRecord.created_at < period_end,
        )

        records = query.all()

        total_cost = 0.0
        total_tokens = 0.0
        total_tasks = 0.0
        by_type: dict[str, float] = {}
        for r in records:
            total_cost += r.total_cost
            by_type[r.usage_type] = by_type.get(r.usage_type, 0.0) + r.total_cost
            if r.usage_type in (UsageType.TOKEN_INPUT.value, UsageType.TOKEN_OUTPUT.value):
                total_tokens += r.quantity
            elif r.usage_type == UsageType.TASK_RUN.value:
                total_tasks += r.quantity

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_cost": round(total_cost, 6),
            "total_tokens": int(total_tokens),
            "total_tasks": int(total_tasks),
            "by_type": {k: round(v, 6) for k, v in by_type.items()},
        }

    def get_usage_by_model(
        self,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        org_id: Optional[int] = None,
    ) -> dict:
        query = self.db.query(UsageRecord).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.created_at >= period_start,
            UsageRecord.created_at < period_end,
            UsageRecord.usage_type.in_([UsageType.TOKEN_INPUT.value, UsageType.TOKEN_OUTPUT.value]),
        )

        records = query.all()

        by_model: dict[str, dict] = {}
        for r in records:
            model_name = r.model or "unknown"
            if model_name not in by_model:
                by_model[model_name] = {"total_cost": 0.0, "input_tokens": 0, "output_tokens": 0}
            entry = by_model[model_name]
            entry["total_cost"] += r.total_cost
            if r.usage_type == UsageType.TOKEN_INPUT.value:
                entry["input_tokens"] += r.quantity
            elif r.usage_type == UsageType.TOKEN_OUTPUT.value:
                entry["output_tokens"] += r.quantity

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "by_model": {
                k: {**v, "total_cost": round(v["total_cost"], 6)}
                for k, v in by_model.items()
            },
        }

    def check_limits(self, user_id: int, org_id: Optional[int] = None) -> dict:
        period_start, period_end = self._month_bounds()

        token_query = self.db.query(sql_func.coalesce(sql_func.sum(UsageRecord.quantity), 0.0)).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.usage_type.in_([UsageType.TOKEN_INPUT.value, UsageType.TOKEN_OUTPUT.value]),
            UsageRecord.created_at >= period_start,
            UsageRecord.created_at < period_end,
        )
        total_tokens = float(token_query.scalar() or 0.0)

        task_query = self.db.query(sql_func.coalesce(sql_func.sum(UsageRecord.quantity), 0.0)).filter(
            UsageRecord.user_id == user_id,
            UsageRecord.usage_type == UsageType.TASK_RUN.value,
            UsageRecord.created_at >= period_start,
            UsageRecord.created_at < period_end,
        )
        total_tasks = float(task_query.scalar() or 0.0)

        plan = self._get_plan_for_user(org_id)
        token_limit = plan.token_limit if plan else settings.FREE_PLAN_TOKEN_LIMIT
        task_limit = plan.task_limit if plan else settings.FREE_PLAN_TASK_LIMIT

        remaining_tokens = -1 if token_limit == -1 else max(0, token_limit - int(total_tokens))
        remaining_tasks = -1 if task_limit == -1 else max(0, task_limit - int(total_tasks))

        allowed = True
        message = "Within usage limits"
        if token_limit != -1 and total_tokens >= token_limit:
            allowed = False
            message = "Monthly token limit reached"
        elif task_limit != -1 and total_tasks >= task_limit:
            allowed = False
            message = "Monthly task limit reached"

        return {
            "allowed": allowed,
            "remaining_tokens": remaining_tokens,
            "remaining_tasks": remaining_tasks,
            "message": message,
        }

    def get_monthly_cost(self, user_id: int, org_id: Optional[int] = None) -> float:
        period_start, period_end = self._month_bounds()
        summary = self.get_usage_summary(user_id, period_start, period_end, org_id)
        return summary["total_cost"]

    def _get_plan_for_user(self, org_id: Optional[int]) -> Optional[BillingPlan]:
        if org_id is None:
            return None
        from ..models.organization import Organization
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if org and org.plan:
            return self.db.query(BillingPlan).filter(BillingPlan.name == org.plan).first()
        return None

    def generate_invoice(
        self,
        user_id: int,
        period_start: datetime,
        period_end: datetime,
        org_id: Optional[int] = None,
    ) -> Invoice:
        summary = self.get_usage_summary(user_id, period_start, period_end, org_id)

        line_items = []
        for usage_type, cost in summary.get("by_type", {}).items():
            if cost > 0:
                line_items.append({
                    "description": usage_type.replace("_", " ").title(),
                    "quantity": 1,
                    "unit_cost": round(cost, 6),
                    "total": round(cost, 6),
                })

        if not line_items:
            line_items.append({
                "description": "No usage this period",
                "quantity": 0,
                "unit_cost": 0.0,
                "total": 0.0,
            })

        invoice = Invoice(
            user_id=user_id,
            org_id=org_id,
            period_start=period_start,
            period_end=period_end,
            total_cost=summary["total_cost"],
            status="draft",
            line_items=line_items,
        )
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice


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
            features=["basic_agents", "basic_tasks", "community_support"],
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
            features=[
                "basic_agents", "basic_tasks", "community_support",
                "advanced_agents", "priority_execution", "custom_models",
                "analytics", "api_access",
            ],
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
            features=[
                "basic_agents", "basic_tasks", "community_support",
                "advanced_agents", "priority_execution", "custom_models",
                "analytics", "api_access", "unlimited_agents",
                "sso", "audit_logs", "dedicated_support", "sla",
            ],
            is_active=True,
        ),
    ]

    db.add_all(plans)
    db.commit()
