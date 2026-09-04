"""Geographic administrative hierarchy models for RakshakGIS."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class Region(Base):
    """Top-level geographic region (e.g. State / Macro-region)."""

    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, default="Uttarakhand")
    boundary = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    districts = relationship(
        "District", back_populates="region", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Region(id={self.id}, code='{self.code}', name='{self.name}')>"


class District(Base):
    """District administrative boundary within a region."""

    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    region_id = Column(
        Integer,
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    headquarters = Column(String(100), nullable=True)
    boundary = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    region = relationship("Region", back_populates="districts")
    blocks = relationship(
        "Block", back_populates="district", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<District(id={self.id}, code='{self.code}', name='{self.name}')>"


class Block(Base):
    """Block / Tehsil administrative subdivision within a district."""

    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    district_id = Column(
        Integer,
        ForeignKey("districts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    boundary = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    district = relationship("District", back_populates="blocks")
    villages = relationship(
        "Village", back_populates="block", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Block(id={self.id}, code='{self.code}', name='{self.name}')>"


class Village(Base):
    """Village settlement unit with location point and optional boundary."""

    __tablename__ = "villages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    block_id = Column(
        Integer,
        ForeignKey("blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    census_code = Column(String(50), unique=True, nullable=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    boundary = Column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )
    elevation_m = Column(Float, nullable=True)
    slope_deg = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    block = relationship("Block", back_populates="villages")
    population_profile = relationship(
        "PopulationProfile",
        back_populates="village",
        uselist=False,
        cascade="all, delete-orphan",
    )
    vulnerability_profile = relationship(
        "VulnerabilityProfile",
        back_populates="village",
        uselist=False,
        cascade="all, delete-orphan",
    )
    risk_scores = relationship(
        "RiskScore", back_populates="village", cascade="all, delete-orphan"
    )
    hazard_observations = relationship(
        "HazardObservation", back_populates="village"
    )
    relocation_priorities = relationship(
        "RelocationPriority", back_populates="village", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Village(id={self.id}, name='{self.name}')>"
