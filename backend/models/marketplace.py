from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class AgentTemplate(Base):
    """Marketplace listing: a reusable agent blueprint."""
    __tablename__ = "agent_templates"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    category = Column(String(50), index=True, default="Custom")
    author = Column(String(100), default="Community")

    # Display metadata
    price_label = Column(String(50), default="Free")
    price_cents = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    installs_count = Column(Integer, default=0)
    icon_key = Column(String(50), default="custom")

    # Agent blueprint applied on install
    system_prompt = Column(Text, default="")
    capabilities = Column(JSON, default=list)
    model_provider = Column(String(50), default="openai")
    model_name = Column(String(100), default="gpt-4o-mini")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    config = Column(JSON, default=dict)

    is_public = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    installations = relationship("TemplateInstallation", back_populates="template")


class TemplateInstallation(Base):
    """A user's installation of a marketplace template."""
    __tablename__ = "template_installations"
    __table_args__ = (
        UniqueConstraint("template_id", "user_id", name="uq_template_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("agent_templates.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    installed_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("AgentTemplate", back_populates="installations")
