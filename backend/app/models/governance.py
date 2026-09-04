"""Platform governance, role-based user entities, officer decision tracing, and audit logs."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """Platform user account for disaster response officials and operators."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(
        String(50), default="viewer", nullable=False, index=True
    )  # admin, district_officer, field_responder, viewer
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    decisions = relationship("OfficerDecision", back_populates="officer")
    audit_logs = relationship("AuditLog", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class OfficerDecision(Base):
    """Traceable decision record made by authorized officers with justification."""

    __tablename__ = "officer_decisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    officer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    decision_type = Column(
        String(50), nullable=False, index=True
    )  # evacuation_order, site_approval, resource_dispatch, zone_declaration
    target_entity_type = Column(
        String(50), nullable=False
    )  # village, candidate_site, red_zone
    target_entity_id = Column(Integer, nullable=False)
    action_taken = Column(String(100), nullable=False)
    rationale = Column(Text, nullable=False)
    overridden_recommendation = Column(Boolean, default=False, nullable=False)
    decision_metadata_json = Column(JSON, nullable=True)
    decided_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    officer = relationship("User", back_populates="decisions")

    def __repr__(self) -> str:
        return f"<OfficerDecision(id={self.id}, type='{self.decision_type}', action='{self.action_taken}')>"


class AuditLog(Base):
    """Immutable audit trail of actions taken across the platform."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, trigger, export
    resource_type = Column(
        String(50), nullable=False, index=True
    )  # e.g. scenario, relocation_assignment, red_zone
    resource_id = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    payload_before_json = Column(JSON, nullable=True)
    payload_after_json = Column(JSON, nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', resource='{self.resource_type}')>"
