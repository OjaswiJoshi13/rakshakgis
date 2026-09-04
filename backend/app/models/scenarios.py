"""Simulation scenario definition and execution run models for RakshakGIS."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Scenario(Base):
    """What-if simulation scenario parameters (rainfall intensity, seismic trigger, blockage)."""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rainfall_multiplier = Column(Float, default=1.0, nullable=False)
    seismic_intensity_mmi = Column(Float, nullable=True)
    road_blockage_percentage = Column(Float, default=0.0, nullable=False)
    parameters_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    created_by = relationship("User")
    runs = relationship(
        "ScenarioRun", back_populates="scenario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scenario(id={self.id}, name='{self.name}')>"


class ScenarioRun(Base):
    """Execution instance of a simulation scenario with execution metrics and outcomes."""

    __tablename__ = "scenario_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scenario_id = Column(
        Integer,
        ForeignKey("scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    executed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(
        String(30), default="running", nullable=False
    )  # running, completed, failed
    start_time = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    end_time = Column(DateTime(timezone=True), nullable=True)
    simulated_affected_villages = Column(Integer, nullable=True)
    simulated_displaced_population = Column(Integer, nullable=True)
    results_summary_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    scenario = relationship("Scenario", back_populates="runs")
    executed_by = relationship("User")

    def __repr__(self) -> str:
        return f"<ScenarioRun(id={self.id}, scenario_id={self.scenario_id}, status='{self.status}')>"
