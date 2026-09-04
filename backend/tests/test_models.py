"""Automated tests for RakshakGIS database models, relationships, spatial schemas, and Alembic migrations."""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, MultiPolygon, Polygon

from app.core.database import Base, SessionLocal
from app.models import (
    Region,
    District,
    Block,
    Village,
    HazardLayer,
    HazardObservation,
    LandslideEvent,
    FloodEvent,
    RainfallRecord,
    DisasterEvent,
    PopulationProfile,
    VulnerabilityProfile,
    CandidateSite,
    SiteCapacity,
    Infrastructure,
    RiskScore,
    RiskFactor,
    RedZone,
    RelocationPriority,
    RelocationAssignment,
    Route,
    Scenario,
    ScenarioRun,
    DataSource,
    DataIngestionRun,
    Alert,
    User,
    OfficerDecision,
    AuditLog,
)

EXPECTED_M2_03_TABLES = {
    "regions",
    "districts",
    "blocks",
    "villages",
    "hazard_layers",
    "hazard_observations",
    "landslide_events",
    "flood_events",
    "rainfall_records",
    "disaster_events",
    "population_profiles",
    "vulnerability_profiles",
    "candidate_sites",
    "site_capacities",
    "infrastructure",
    "risk_scores",
    "risk_factors",
    "red_zones",
    "relocation_priorities",
    "relocation_assignments",
    "routes",
    "scenarios",
    "scenario_runs",
    "alerts",
    "data_sources",
    "data_ingestion_runs",
    "officer_decisions",
    "audit_logs",
    "users",
}


def test_all_models_importable():
    """Verify that all 29 M2-03 domain models can be imported without errors."""
    models = [
        Region,
        District,
        Block,
        Village,
        HazardLayer,
        HazardObservation,
        LandslideEvent,
        FloodEvent,
        RainfallRecord,
        DisasterEvent,
        PopulationProfile,
        VulnerabilityProfile,
        CandidateSite,
        SiteCapacity,
        Infrastructure,
        RiskScore,
        RiskFactor,
        RedZone,
        RelocationPriority,
        RelocationAssignment,
        Route,
        Scenario,
        ScenarioRun,
        DataSource,
        DataIngestionRun,
        Alert,
        User,
        OfficerDecision,
        AuditLog,
    ]
    assert len(models) == 29
    for m in models:
        assert hasattr(m, "__tablename__")
        assert m.__tablename__ in EXPECTED_M2_03_TABLES


def test_sqlalchemy_metadata_contains_all_tables():
    """Verify that Base.metadata contains exactly the 29 expected RakshakGIS tables."""
    metadata_tables = set(Base.metadata.tables.keys())
    assert EXPECTED_M2_03_TABLES.issubset(metadata_tables)
    assert len(metadata_tables) == 29


def test_spatial_geometry_columns_and_srid():
    """Verify PostGIS geometry columns are configured with expected type and SRID 4326."""
    # Village location and boundary
    village_loc = Village.__table__.c.location.type
    assert village_loc.geometry_type == "POINT"
    assert village_loc.srid == 4326

    village_boundary = Village.__table__.c.boundary.type
    assert village_boundary.geometry_type == "POLYGON"
    assert village_boundary.srid == 4326

    # Region, District, Block boundaries
    assert Region.__table__.c.boundary.type.geometry_type == "MULTIPOLYGON"
    assert Region.__table__.c.boundary.type.srid == 4326
    assert District.__table__.c.boundary.type.geometry_type == "MULTIPOLYGON"
    assert District.__table__.c.boundary.type.srid == 4326
    assert Block.__table__.c.boundary.type.geometry_type == "MULTIPOLYGON"
    assert Block.__table__.c.boundary.type.srid == 4326

    # Route path
    assert Route.__table__.c.path.type.geometry_type == "LINESTRING"
    assert Route.__table__.c.path.type.srid == 4326

    # CandidateSite location and boundary
    assert CandidateSite.__table__.c.location.type.geometry_type == "POINT"
    assert CandidateSite.__table__.c.location.type.srid == 4326
    assert CandidateSite.__table__.c.boundary.type.geometry_type == "POLYGON"
    assert CandidateSite.__table__.c.boundary.type.srid == 4326

    # RedZone geometry
    assert RedZone.__table__.c.geometry.type.geometry_type == "MULTIPOLYGON"
    assert RedZone.__table__.c.geometry.type.srid == 4326

    # Hazards
    assert HazardObservation.__table__.c.location.type.geometry_type == "POINT"
    assert FloodEvent.__table__.c.inundation_polygon.type.geometry_type == "MULTIPOLYGON"
    assert LandslideEvent.__table__.c.location.type.geometry_type == "POINT"
    assert LandslideEvent.__table__.c.scar_polygon.type.geometry_type == "POLYGON"
    assert RainfallRecord.__table__.c.station_location.type.geometry_type == "POINT"
    assert Infrastructure.__table__.c.location.type.geometry_type == "POINT"
    assert DisasterEvent.__table__.c.epicenter_or_center.type.geometry_type == "POINT"
    assert DisasterEvent.__table__.c.affected_area.type.geometry_type == "MULTIPOLYGON"


def test_foreign_key_relationships():
    """Verify critical foreign-key relationships defined by the specification."""
    # Administrative hierarchy
    assert "regions.id" in [fk.target_fullname for fk in District.__table__.foreign_keys]
    assert "districts.id" in [fk.target_fullname for fk in Block.__table__.foreign_keys]
    assert "blocks.id" in [fk.target_fullname for fk in Village.__table__.foreign_keys]

    # Village profiles
    assert "villages.id" in [fk.target_fullname for fk in PopulationProfile.__table__.foreign_keys]
    assert "villages.id" in [fk.target_fullname for fk in VulnerabilityProfile.__table__.foreign_keys]
    assert "villages.id" in [fk.target_fullname for fk in RiskScore.__table__.foreign_keys]
    assert "villages.id" in [fk.target_fullname for fk in RelocationPriority.__table__.foreign_keys]

    # Candidate sites & capacities
    assert "candidate_sites.id" in [fk.target_fullname for fk in SiteCapacity.__table__.foreign_keys]
    assert "candidate_sites.id" in [fk.target_fullname for fk in Infrastructure.__table__.foreign_keys]

    # Scenarios & runs
    assert "scenarios.id" in [fk.target_fullname for fk in ScenarioRun.__table__.foreign_keys]

    # Data sources & runs
    assert "data_sources.id" in [fk.target_fullname for fk in DataIngestionRun.__table__.foreign_keys]

    # Users & governance
    assert "users.id" in [fk.target_fullname for fk in OfficerDecision.__table__.foreign_keys]
    assert "users.id" in [fk.target_fullname for fk in AuditLog.__table__.foreign_keys]


def test_database_tables_exist_in_postgres():
    """Verify against live PostgreSQL container that all 29 tables exist in the public schema."""
    with SessionLocal() as session:
        result = session.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public';"
            )
        ).fetchall()
        pg_tables = {row[0] for row in result}
        for table in EXPECTED_M2_03_TABLES:
            assert table in pg_tables, f"Table {table} not found in PostgreSQL"


def test_database_spatial_columns_in_postgis():
    """Verify that all 17 geometry columns are registered in PostGIS geometry_columns view with SRID 4326."""
    with SessionLocal() as session:
        result = session.execute(
            text(
                "SELECT f_table_name, f_geometry_column, type, srid "
                "FROM geometry_columns WHERE f_table_schema = 'public';"
            )
        ).fetchall()
        spatial_cols = {f"{row[0]}.{row[1]}": (row[2], row[3]) for row in result}
        assert len(spatial_cols) == 17
        for col_name, (geom_type, srid) in spatial_cols.items():
            assert srid == 4326, f"Column {col_name} has unexpected SRID {srid}"


def test_alembic_current_migration_head():
    """Verify that alembic_version table contains the current migration revision."""
    with SessionLocal() as session:
        rev = session.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        assert rev is not None
        assert rev == "7f762509fde4"


def test_crud_village_and_spatial_persistence():
    """Test full ORM entity persistence with spatial geometry insertion and querying."""
    session: Session = SessionLocal()
    try:
        # Create test Region
        region = Region(code="TEST_REG", name="Test Region", state="Uttarakhand")
        session.add(region)
        session.flush()

        # Create test District
        district = District(region_id=region.id, code="TEST_DIST", name="Test District")
        session.add(district)
        session.flush()

        # Create test Block
        block = Block(district_id=district.id, code="TEST_BLK", name="Test Block")
        session.add(block)
        session.flush()

        # Create test Village with WGS84 Point (Chamoli approx 79.35, 30.40)
        point_wkt = "SRID=4326;POINT(79.35 30.40)"
        village = Village(
            block_id=block.id,
            census_code="TEST_VILL_01",
            name="Test Village Raini",
            location=point_wkt,
            elevation_m=1950.0,
            slope_deg=28.5,
        )
        session.add(village)
        session.flush()

        # Verify village retrieval and PostGIS spatial calculation
        saved_village = session.query(Village).filter(Village.census_code == "TEST_VILL_01").first()
        assert saved_village is not None
        assert saved_village.name == "Test Village Raini"
        assert saved_village.elevation_m == 1950.0

        # Query geometry using PostGIS ST_AsText
        wkt = session.execute(
            text("SELECT ST_AsText(location) FROM villages WHERE id = :id;"),
            {"id": saved_village.id},
        ).scalar()
        assert wkt == "POINT(79.35 30.4)"

        # Verify village cascade relationship
        pop = PopulationProfile(
            village_id=saved_village.id,
            total_population=450,
            households=95,
        )
        session.add(pop)
        session.commit()

        # Verify relationship access
        refreshed_village = session.query(Village).filter(Village.id == saved_village.id).first()
        assert refreshed_village.population_profile is not None
        assert refreshed_village.population_profile.total_population == 450

    finally:
        # Clean up test records
        session.rollback()
        # Clean up test region which cascades to district -> block -> village -> population_profile
        del_reg = session.query(Region).filter(Region.code == "TEST_REG").first()
        if del_reg:
            session.delete(del_reg)
            session.commit()
        session.close()
