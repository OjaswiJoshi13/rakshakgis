"""External data sources, automated ingestion runs, and early warning alerts for RakshakGIS."""

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


class DataSource(Base):
    """External provider data source configuration (IMD, NRSC, USGS, sensors)."""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    source_type = Column(
        String(50), nullable=False
    )  # satellite, weather_api, sensor, manual_report
    provider = Column(
        String(100), nullable=False
    )  # IMD, USGS, NRSC, ISRO, In-situ
    endpoint_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    polling_interval_seconds = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    ingestion_runs = relationship(
        "DataIngestionRun", back_populates="data_source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DataSource(id={self.id}, name='{self.name}', provider='{self.provider}')>"


class DataIngestionRun(Base):
    """Audit log of automated or manual data ingestion batch executions."""

    __tablename__ = "data_ingestion_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data_source_id = Column(
        Integer,
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        String(30), default="in_progress", nullable=False
    )  # in_progress, success, failed, partial
    records_ingested = Column(Integer, default=0, nullable=False)
    records_failed = Column(Integer, default=0, nullable=False)
    started_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    log_details = Column(Text, nullable=True)

    # Relationships
    data_source = relationship("DataSource", back_populates="ingestion_runs")

    def __repr__(self) -> str:
        return f"<DataIngestionRun(id={self.id}, source_id={self.data_source_id}, status='{self.status}')>"


class Alert(Base):
    """Early warning broadcast and threshold breach notifications."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    village_id = Column(
        Integer,
        ForeignKey("villages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    district_id = Column(
        Integer,
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    alert_type = Column(
        String(50), nullable=False, index=True
    )  # rainfall_threshold, landslide_warning, evacuation_notice
    severity = Column(
        String(30), nullable=False
    )  # info, warning, severe, extreme
    headline = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    issued_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    acknowledged_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    village = relationship("Village")
    district = relationship("District")
    acknowledged_by = relationship("User")

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type='{self.alert_type}', severity='{self.severity}')>"
