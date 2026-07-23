from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import Base


class OrgRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


ORG_ROLE_HIERARCHY = {
    OrgRole.OWNER: 3,
    OrgRole.ADMIN: 2,
    OrgRole.MEMBER: 1,
    OrgRole.VIEWER: 0,
}


PLAN_DEFAULTS = {
    "free": {"max_agents": 5, "max_members": 3, "monthly_token_limit": 100000, "monthly_task_limit": 100},
    "pro": {"max_agents": 50, "max_members": 25, "monthly_token_limit": 5000000, "monthly_task_limit": 5000},
    "enterprise": {"max_agents": -1, "max_members": -1, "monthly_token_limit": -1, "monthly_task_limit": -1},
}


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(1000), nullable=True)
    logo_url = Column(String(500), nullable=True)

    plan = Column(String(50), default="free")
    max_agents = Column(Integer, default=5)
    max_members = Column(Integer, default=3)
    monthly_token_limit = Column(Integer, default=100000)
    monthly_task_limit = Column(Integer, default=100)

    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    members = relationship("OrgMember", back_populates="organization", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="organization")
    tasks = relationship("Task", back_populates="organization")


class OrgMember(Base):
    __tablename__ = "org_members"
    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_user"),)

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default=OrgRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])


class OrgInvite(Base):
    __tablename__ = "org_invites"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(20), default=OrgRole.MEMBER)
    token = Column(String(64), unique=True, index=True, nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization")
    inviter = relationship("User", foreign_keys=[invited_by])
