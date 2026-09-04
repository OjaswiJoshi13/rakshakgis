"""RakshakGIS Database Models registry.

Exports all 29 core domain models to ensure SQLAlchemy metadata discovery.
"""

from app.core.database import Base
from app.models.geographic import Region, District, Block, Village
from app.models.hazards import (
    HazardLayer,
    HazardObservation,
    LandslideEvent,
    FloodEvent,
    RainfallRecord,
    DisasterEvent,
)
from app.models.vulnerability import PopulationProfile, VulnerabilityProfile
from app.models.risk import RiskScore, RiskFactor, RedZone
from app.models.relocation import (
    CandidateSite,
    SiteCapacity,
    Infrastructure,
    RelocationPriority,
    RelocationAssignment,
    Route,
)
from app.models.scenarios import Scenario, ScenarioRun
from app.models.telemetry import DataSource, DataIngestionRun, Alert
from app.models.governance import User, OfficerDecision, AuditLog

__all__ = [
    "Base",
    # Geographic (4)
    "Region",
    "District",
    "Block",
    "Village",
    # Hazards (6)
    "HazardLayer",
    "HazardObservation",
    "LandslideEvent",
    "FloodEvent",
    "RainfallRecord",
    "DisasterEvent",
    # Vulnerability (2)
    "PopulationProfile",
    "VulnerabilityProfile",
    # Risk (3)
    "RiskScore",
    "RiskFactor",
    "RedZone",
    # Relocation (6)
    "CandidateSite",
    "SiteCapacity",
    "Infrastructure",
    "RelocationPriority",
    "RelocationAssignment",
    "Route",
    # Scenarios (2)
    "Scenario",
    "ScenarioRun",
    # Telemetry (3)
    "DataSource",
    "DataIngestionRun",
    "Alert",
    # Governance (3)
    "User",
    "OfficerDecision",
    "AuditLog",
]
