from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(20), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # API Key for programmatic access
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    api_key_enabled = Column(Boolean, default=False)
    
    # OAuth2 support
    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(255), nullable=True)
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    preferences = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    agents = relationship("Agent", back_populates="owner")
    tasks = relationship("Task", back_populates="creator")
    api_keys = relationship("APIKey", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    
    # Permissions
    scopes = Column(JSON, default=list)  # ["agents:read", "tasks:write", etc.]
    
    # Rate limiting
    rate_limit = Column(Integer, default=100)  # requests per minute
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class AuditLog(Base):
    """Audit trail for all actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Action details
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type = Column(String(50), nullable=False)  # user, agent, task
    resource_id = Column(Integer, nullable=True)
    
    # Request details
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    
    # Changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class Webhook(Base):
    """Webhook configurations for event notifications."""
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=True)  # For signature verification
    
    # Events to trigger on
    events = Column(JSON, nullable=False)  # ["task.completed", "agent.error", etc.]
    
    # Headers
    headers = Column(JSON, default=dict)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
