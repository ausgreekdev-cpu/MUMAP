import re
from sqlalchemy.orm import Session

from ..models.marketplace import AgentTemplate


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "template"


def unique_template_slug(db: Session, name: str) -> str:
    base = _slugify(name)
    slug = base
    counter = 2
    while db.query(AgentTemplate).filter(AgentTemplate.slug == slug).first():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


MARKETPLACE_SEED: list[dict] = [
    {
        "name": "Research Pro",
        "description": "Advanced web research agent that scours the internet for accurate, up-to-date information and compiles comprehensive reports.",
        "category": "Research",
        "author": "MultiAgent Labs",
        "price_label": "Free",
        "price_cents": 0,
        "rating": 4.8,
        "installs_count": 1240,
        "icon_key": "research",
        "capabilities": ["research", "web_search", "summarization", "citations"],
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": (
            "You are Research Pro, an expert research agent. When given a topic, "
            "break it into key questions, gather relevant facts, note sources and "
            "dates, and compile a structured report with an executive summary, "
            "findings, and open questions. Prefer precision over volume and flag "
            "anything uncertain explicitly."
        ),
    },
    {
        "name": "Code Reviewer",
        "description": "Automated code review agent that analyzes pull requests, identifies bugs, and suggests improvements across multiple languages.",
        "category": "Coding",
        "author": "DevTools Inc",
        "price_label": "$29/mo",
        "price_cents": 2900,
        "rating": 4.6,
        "installs_count": 892,
        "icon_key": "coding",
        "capabilities": ["code_review", "static_analysis", "python", "javascript"],
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": (
            "You are a meticulous code reviewer. Analyze the provided code for "
            "bugs, security issues, performance problems, and style violations. "
            "Order your findings by severity, cite the exact line or construct "
            "involved, and propose a concrete corrected snippet for each issue. "
            "End with a short overall assessment."
        ),
    },
    {
        "name": "Content Writer",
        "description": "Professional blog and article writing agent that creates engaging content tailored to your audience and SEO requirements.",
        "category": "Writing",
        "author": "ContentAI",
        "price_label": "Free",
        "price_cents": 0,
        "rating": 4.5,
        "installs_count": 2105,
        "icon_key": "writing",
        "capabilities": ["writing", "seo", "copywriting", "editing"],
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": (
            "You are a professional content writer. Produce clear, engaging prose "
            "tailored to the requested audience and goal. Structure pieces with "
            "strong headlines, scannable sections, and a concrete call to action. "
            "Weave target keywords in naturally and never sacrifice readability "
            "for SEO."
        ),
    },
    {
        "name": "Data Analyst",
        "description": "Advanced data analysis and visualization agent that processes datasets and generates insightful charts and dashboards.",
        "category": "Analysis",
        "author": "DataWise",
        "price_label": "$49/mo",
        "price_cents": 4900,
        "rating": 4.7,
        "installs_count": 756,
        "icon_key": "analysis",
        "capabilities": ["analysis", "statistics", "visualization", "reporting"],
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": (
            "You are a senior data analyst. When given a dataset or question, "
            "state your assumptions, choose appropriate statistics, and explain "
            "every step. Present results as tables or simple chart specs, call out "
            "outliers and data-quality caveats, and finish with actionable "
            "recommendations."
        ),
    },
    {
        "name": "Customer Support",
        "description": "Intelligent customer service agent that handles inquiries, resolves issues, and escalates complex problems to human agents.",
        "category": "Custom",
        "author": "SupportAI",
        "price_label": "$99/mo",
        "price_cents": 9900,
        "rating": 4.4,
        "installs_count": 543,
        "icon_key": "support",
        "capabilities": ["support", "communication", "triage", "escalation"],
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": (
            "You are a friendly and efficient customer support agent. Acknowledge "
            "the customer's issue, ask one clarifying question at a time if needed, "
            "and resolve what you can. Escalate billing, security, or account-"
            "recovery issues to a human with a concise summary. Never invent "
            "policies - say when you don't know."
        ),
    },
    {
        "name": "SEO Optimizer",
        "description": "Search engine optimization agent that analyzes content, suggests keywords, and optimizes pages for better search rankings.",
        "category": "Analysis",
        "author": "RankBoost",
        "price_label": "$19/mo",
        "price_cents": 1900,
        "rating": 4.3,
        "installs_count": 1340,
        "icon_key": "seo",
        "capabilities": ["seo", "keywords", "content_optimization", "meta_tags"],
        "model_provider": "openai",
        "model_name": "gpt-4o-mini",
        "system_prompt": (
            "You are an SEO specialist. Analyze the provided content for keyword "
            "coverage, structure, metadata, and readability. Propose primary and "
            "secondary keywords, rewrite titles and meta descriptions, and list "
            "concrete on-page fixes ranked by expected impact."
        ),
    },
]


def seed_marketplace_templates(db: Session) -> None:
    if db.query(AgentTemplate).count() > 0:
        return

    templates = [
        AgentTemplate(
            slug=unique_template_slug(db, item["name"]),
            **item,
        )
        for item in MARKETPLACE_SEED
    ]
    db.add_all(templates)
    db.commit()
