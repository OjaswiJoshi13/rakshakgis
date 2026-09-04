"""Hazard layers, observations, and historical disaster event models for RakshakGIS."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Date,
    Text,
    ForeignKey,
    Numeric,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.core.database import Base


class HazardLayer(Base):
    """Spatial GIS hazard raster or vector layer metadata."""

    __tablename__ = "hazard_layers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    hazard_type = Column(String(50), nullable=False, index=True)  # landslide, flood, rainfall, seismic
    source = Column(String(150), nullable=False)
    resolution_m = Column(Float, nullable=True)
    format = Column(String(50), nullable=False)  # GeoTIFF, Vector, GeoJSON
    file_path = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<HazardLayer(id={self.id}, name='{self.name}', hazard_type='{self.hazard_type}')>"


class HazardObservation(Base):
    """Point-in-time hazard observation or sensor reading."""

    __tablename__ = "hazard_observations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    hazard_type = Column(String(50), nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    severity = Column(String(30), nullable=False)  # low, moderate, high, very_high, critical
    intensity_value = Column(Float, nullable=True)
    intensity_unit = Column(String(30), nullable=True)
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    description = Column(Text, nullable=True)
    source_id = Column(
        Integer,
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    village = relationship("Village", back_populates="hazard_observations")
    data_source = relationship("DataSource")

    def __repr__(self) -> str:
        return f"<HazardObservation(id={self.id}, hazard_type='{self.hazard_type}', severity='{self.severity}')>"


class LandslideEvent(Base):
    """Historical or active landslide incident record."""

    __tablename__ = "landslide_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_date = Column(Date, nullable=False, index=True)
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    scar_polygon = Column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )
    volume_m3 = Column(Float, nullable=True)
    trigger_type = Column(String(50), nullable=True)  # rainfall, seismic, anthropogenic
    impact_summary = Column(Text, nullable=True)
    fatalities = Column(Integer, default=0, nullable=False)
    displaced_persons = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    village = relationship("Village")

    def __repr__(self) -> str:
        return f"<LandslideEvent(id={self.id}, date={self.event_date})>"


class FloodEvent(Base):
    """Historical or active flood inundation incident record."""

    __tablename__ = "flood_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_date = Column(Date, nullable=False, index=True)
    inundation_polygon = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )
    peak_water_level_m = Column(Float, nullable=True)
    duration_hours = Column(Float, nullable=True)
    flood_type = Column(String(50), nullable=True)  # flash_flood, riverine, GLOF
    fatalities = Column(Integer, default=0, nullable=False)
    affected_population = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    village = relationship("Village")

    def __repr__(self) -> str:
        return f"<FloodEvent(id={self.id}, date={self.event_date})>"


class RainfallRecord(Base):
    """Weather telemetry station precipitation reading."""

    __tablename__ = "rainfall_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(String(50), nullable=False, index=True)
    station_name = Column(String(100), nullable=False)
    station_location = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    precipitation_mm = Column(Float, nullable=False)
    cumulative_24h_mm = Column(Float, nullable=True)
    cumulative_72h_mm = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<RainfallRecord(id={self.id}, station='{self.station_id}', recorded_at={self.recorded_at})>"


class DisasterEvent(Base):
    """Overall declared disaster occurrence."""

    __tablename__ = "disaster_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(150), nullable=False, index=True)
    disaster_type = Column(String(50), nullable=False, index=True)  # landslide, flood, cloudburst, earthquake
    declared_at = Column(DateTime(timezone=True), nullable=False, index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    severity = Column(String(30), nullable=False)  # minor, moderate, severe, catastrophic
    status = Column(String(30), default="active", nullable=False)  # active, responding, resolved, closed
    epicenter_or_center = Column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    affected_area = Column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=True,
    )
    estimated_losses_inr = Column(Numeric(14, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<DisasterEvent(id={self.id}, title='{self.title}', status='{self.status}')>"
