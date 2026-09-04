"""Candidate relocation sites, site capacity, infrastructure, relocation priorities, assignments, and routes."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class CandidateSite(Base):
    """Candidate safe site identified for rehabilitation/relocation."""

    __tablename__ = "candidate_sites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    district_id = Column(
        Integer,
        ForeignKey("districts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    boundary = Column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )
    area_sq_m = Column(Float, nullable=True)
    terrain_slope_deg = Column(Float, nullable=True)
    elevation_m = Column(Float, nullable=True)
    suitability_score = Column(Float, nullable=True)  # 0.0 - 100.0
    status = Column(String(30), default="proposed", nullable=False)  # proposed, approved, rejected, active
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    district = relationship("District")
    capacities = relationship(
        "SiteCapacity", back_populates="site", cascade="all, delete-orphan"
    )
    infrastructures = relationship(
        "Infrastructure", back_populates="site", cascade="all, delete-orphan"
    )
    assignments = relationship("RelocationAssignment", back_populates="site")

    def __repr__(self) -> str:
        return f"<CandidateSite(id={self.id}, name='{self.name}', status='{self.status}')>"


class SiteCapacity(Base):
    """Capacity metrics and resource limits for a candidate relocation site."""

    __tablename__ = "site_capacities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    site_id = Column(
        Integer,
        ForeignKey("candidate_sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    max_households = Column(Integer, nullable=False, default=0)
    max_population = Column(Integer, nullable=False, default=0)
    allocated_households = Column(Integer, nullable=False, default=0)
    allocated_population = Column(Integer, nullable=False, default=0)
    available_households = Column(Integer, nullable=False, default=0)
    available_population = Column(Integer, nullable=False, default=0)
    water_supply_lpd = Column(Float, nullable=True)  # Liters per day
    sanitation_units = Column(Integer, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    site = relationship("CandidateSite", back_populates="capacities")

    def __repr__(self) -> str:
        return f"<SiteCapacity(site_id={self.site_id}, max_households={self.max_households})>"


class Infrastructure(Base):
    """Critical infrastructure assets (shelters, medical centers, helipads, water tanks)."""

    __tablename__ = "infrastructure"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    site_id = Column(
        Integer,
        ForeignKey("candidate_sites.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(150), nullable=False, index=True)
    infra_type = Column(
        String(50), nullable=False
    )  # medical_center, water_tank, power_substation, helipad, shelter
    status = Column(
        String(30), default="operational", nullable=False
    )  # operational, under_construction, damaged, planned
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    capacity_description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    site = relationship("CandidateSite", back_populates="infrastructures")

    def __repr__(self) -> str:
        return f"<Infrastructure(id={self.id}, name='{self.name}', type='{self.infra_type}')>"


class RelocationPriority(Base):
    """Village relocation urgency score and prioritization categorization."""

    __tablename__ = "relocation_priorities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    priority_band = Column(
        String(30), nullable=False, index=True
    )  # P1_immediate, P2_high, P3_medium, P4_low
    priority_score = Column(Float, nullable=False)
    estimated_households = Column(Integer, nullable=False)
    estimated_people = Column(Integer, nullable=False)
    urgency_reason = Column(Text, nullable=True)
    assessed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    village = relationship("Village", back_populates="relocation_priorities")

    def __repr__(self) -> str:
        return f"<RelocationPriority(village_id={self.village_id}, band='{self.priority_band}')>"


class RelocationAssignment(Base):
    """Official allocation of an affected village population to a candidate safe site."""

    __tablename__ = "relocation_assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    candidate_site_id = Column(
        Integer,
        ForeignKey("candidate_sites.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_households = Column(Integer, nullable=False)
    assigned_population = Column(Integer, nullable=False)
    status = Column(
        String(30), default="draft", nullable=False
    )  # draft, approved, in_transit, completed, cancelled
    approved_by_officer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    village = relationship("Village")
    site = relationship("CandidateSite", back_populates="assignments")
    approved_by = relationship("User")

    def __repr__(self) -> str:
        return f"<RelocationAssignment(id={self.id}, village_id={self.village_id}, site_id={self.candidate_site_id})>"


class Route(Base):
    """Evacuation and access routes connecting vulnerable villages to safe sites."""

    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    origin_village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destination_site_id = Column(
        Integer,
        ForeignKey("candidate_sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    path = Column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True),
        nullable=False,
    )
    distance_km = Column(Float, nullable=False)
    estimated_travel_time_min = Column(Float, nullable=True)
    route_type = Column(
        String(50), default="evacuation", nullable=False
    )  # evacuation, relief, alternate
    safety_score = Column(Float, nullable=True)  # 0.0 - 100.0
    is_blocked = Column(Boolean, default=False, nullable=False, index=True)
    blockage_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    origin_village = relationship("Village")
    destination_site = relationship("CandidateSite")

    def __repr__(self) -> str:
        return f"<Route(id={self.id}, name='{self.name}', distance_km={self.distance_km})>"
