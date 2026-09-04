"""Composite risk scoring, factor decomposition, and red zone models for RakshakGIS."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class RiskScore(Base):
    """Overall multi-hazard risk assessment score for a village."""

    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = Column(Float, nullable=False)  # 0.0 - 100.0
    band = Column(String(30), nullable=False, index=True)  # low, medium, high, very_high, critical
    hazard_subscore = Column(Float, nullable=False)
    exposure_subscore = Column(Float, nullable=False)
    vulnerability_subscore = Column(Float, nullable=False)
    calculated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    is_current = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    village = relationship("Village", back_populates="risk_scores")
    risk_factors = relationship(
        "RiskFactor", back_populates="risk_score", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RiskScore(id={self.id}, village_id={self.village_id}, score={self.score}, band='{self.band}')>"


class RiskFactor(Base):
    """Detailed component contributing to a village risk score calculation."""

    __tablename__ = "risk_factors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    risk_score_id = Column(
        Integer,
        ForeignKey("risk_scores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    factor_name = Column(String(100), nullable=False)
    weight = Column(Float, nullable=False)
    raw_value = Column(Float, nullable=True)
    normalized_score = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    risk_score = relationship("RiskScore", back_populates="risk_factors")

    def __repr__(self) -> str:
        return f"<RiskFactor(id={self.id}, factor='{self.factor_name}', normalized={self.normalized_score})>"


class RedZone(Base):
    """Officially designated high-risk geographic perimeter or exclusion zone."""

    __tablename__ = "red_zones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    zone_type = Column(String(50), nullable=False)  # landslide_danger, flood_inundation, active_subsidence
    danger_level = Column(String(30), nullable=False)  # very_high, critical, uninhabitable
    geometry = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )
    area_sq_km = Column(Float, nullable=True)
    declared_by_officer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    declared_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    declared_by = relationship("User")

    def __repr__(self) -> str:
        return f"<RedZone(id={self.id}, name='{self.name}', danger_level='{self.danger_level}')>"
