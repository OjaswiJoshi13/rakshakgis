"""Automated tests for the RakshakGIS Data Validation and Ingestion Pipeline (Chunk M3-04)."""

import math
import pytest

from app.data.ingestion import (
    BatchValidationError,
    CanonicalFloodRecord,
    CanonicalHazardObservationRecord,
    CanonicalLandslideRecord,
    CanonicalPopulationRecord,
    CanonicalRainfallRecord,
    IngestionPipeline,
    UnsupportedCategoryError,
    ValidationIssueCode,
    ingest_batch,
    ingest_provider_response,
)
from app.data.providers import (
    NormalizedFloodRecord,
    NormalizedHazardObservationRecord,
    NormalizedLandslideRecord,
    NormalizedPopulationRecord,
    NormalizedRainfallRecord,
    ProviderMode,
    ProviderProvenance,
    ProviderQuery,
    SourceCategory,
    get_provider,
)

SAMPLE_PROVENANCE = ProviderProvenance(
    provider_id="mock_imd_rainfall",
    provider_name="Mock IMD Rainfall Adapter",
    mode=ProviderMode.MOCK,
    is_synthetic=True,
    region_id="himalayan_pilot",
)


# =====================================================================
# 1. Valid Category Acceptance & Canonicalization
# =====================================================================


def test_valid_rainfall_record_accepted():
    """Requirement 1: Valid rainfall record is validated, accepted, and canonicalized."""
    rec = NormalizedRainfallRecord(
        record_id="REC-RAIN-001",
        observed_at="2026-08-15T12:00:00Z",
        location_coordinates=(79.5123456, 30.5567891),
        provenance=SAMPLE_PROVENANCE,
        village_id="HIM-VILL-001",
        village_name="  Joshimath Upper  ",
        rainfall_24h_mm=75.5,
        severity="high",
        is_heavy_rain=True,
        is_very_heavy_rain=False,
        description="  Intense cloudburst rain event.  ",
    )

    pipeline = IngestionPipeline()
    result = pipeline.ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[rec],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.total_input_count == 1
    assert result.accepted_count == 1
    assert result.rejected_count == 0
    assert len(result.accepted_records) == 1

    canonical = result.accepted_records[0]
    assert isinstance(canonical, CanonicalRainfallRecord)
    assert canonical.record_id == "REC-RAIN-001"
    assert canonical.rainfall_24h_mm == 75.5
    assert canonical.is_heavy_rain is True
    assert canonical.is_very_heavy_rain is False
    assert canonical.village_name == "Joshimath Upper"  # Whitespace trimmed
    assert canonical.description == "Intense cloudburst rain event."
    assert canonical.location_coordinates == (79.512346, 30.556789)
    assert canonical.canonical_hash is not None
    assert canonical.batch_id == result.metadata.batch_id


def test_valid_flood_record_accepted():
    """Requirement 2: Valid flood record is validated, accepted, and canonicalized."""
    rec = NormalizedFloodRecord(
        record_id="REC-FLD-001",
        observed_at="2026-08-15T13:00:00Z",
        location_coordinates=(79.55, 30.52),
        provenance=SAMPLE_PROVENANCE,
        village_id="HIM-VILL-002",
        village_name="Ravigram",
        flood_type="flash_flood",
        water_level_m_above_danger=2.45,
        severity="critical",
    )

    result = ingest_batch(
        category=SourceCategory.FLOOD,
        records=[rec],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 1
    assert result.rejected_count == 0
    canonical = result.accepted_records[0]
    assert isinstance(canonical, CanonicalFloodRecord)
    assert canonical.water_level_m_above_danger == 2.45
    assert canonical.flood_type == "flash_flood"


def test_valid_landslide_record_accepted():
    """Requirement 3: Valid landslide record is validated, accepted, and canonicalized."""
    rec = NormalizedLandslideRecord(
        record_id="REC-LS-001",
        observed_at="2026-08-15T14:00:00Z",
        location_coordinates=(79.56, 30.51),
        provenance=SAMPLE_PROVENANCE,
        village_id="HIM-VILL-003",
        village_name="Sunil",
        debris_volume_cu_m=1250.0,
        severity="very_high",
        road_blocked=True,
    )

    result = ingest_batch(
        category=SourceCategory.LANDSLIDE,
        records=[rec],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 1
    assert result.rejected_count == 0
    canonical = result.accepted_records[0]
    assert isinstance(canonical, CanonicalLandslideRecord)
    assert canonical.debris_volume_cu_m == 1250.0
    assert canonical.road_blocked is True


def test_valid_hazard_observation_accepted():
    """Requirement 4: Valid hazard observation record is accepted."""
    rec = NormalizedHazardObservationRecord(
        record_id="REC-HAZ-001",
        observed_at="2026-08-15T15:00:00Z",
        location_coordinates=(79.52, 30.54),
        provenance=SAMPLE_PROVENANCE,
        hazard_type="seismic",
        village_id="HIM-VILL-001",
        severity="moderate",
        intensity_value=5.2,
        intensity_unit="mmi",
    )

    result = ingest_batch(
        category=SourceCategory.HAZARD_OBSERVATION,
        records=[rec],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 1
    assert result.rejected_count == 0
    canonical = result.accepted_records[0]
    assert isinstance(canonical, CanonicalHazardObservationRecord)
    assert canonical.hazard_type == "seismic"
    assert canonical.intensity_value == 5.2


def test_valid_population_exposure_record_accepted():
    """Requirement 5: Valid population exposure record is accepted."""
    rec = NormalizedPopulationRecord(
        village_id="HIM-VILL-001",
        village_name="Joshimath",
        region_code="himalayan",
        district_code="chamoli",
        block_code="joshimath",
        location_coordinates=(79.56, 30.55),
        total_population=1200,
        households=240,
        elderly_count=180,
        children_count=220,
        disabled_count=35,
        livestock_count=450,
        provenance=SAMPLE_PROVENANCE,
    )

    result = ingest_batch(
        category=SourceCategory.POPULATION_EXPOSURE,
        records=[rec],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 1
    assert result.rejected_count == 0
    canonical = result.accepted_records[0]
    assert isinstance(canonical, CanonicalPopulationRecord)
    assert canonical.village_id == "HIM-VILL-001"
    assert canonical.total_population == 1200


# =====================================================================
# 2. Validation Rejections & Fault Isolation
# =====================================================================


def test_malformed_timestamp_rejected():
    """Requirement 6: Malformed ISO timestamp is rejected and not silently invented."""
    bad_dict = {
        "record_id": "REC-BAD-TIME",
        "observed_at": "not-a-valid-timestamp",
        "location_coordinates": (79.50, 30.50),
        "rainfall_24h_mm": 50.0,
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[bad_dict],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    issue = result.rejected_records[0].issues[0]
    assert issue.code == ValidationIssueCode.INVALID_TIMESTAMP
    assert issue.field == "observed_at"


def test_invalid_coordinates_rejected():
    """Requirement 7: Coordinates that are not 2-tuples are rejected."""
    bad_dict = {
        "record_id": "REC-BAD-COORD",
        "observed_at": "2026-08-15T12:00:00Z",
        "location_coordinates": [79.50],  # Missing latitude
        "rainfall_24h_mm": 50.0,
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[bad_dict],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    issue = result.rejected_records[0].issues[0]
    assert issue.code == ValidationIssueCode.INVALID_COORDINATES


def test_out_of_range_coordinates_rejected():
    """Requirement 8: Coordinates exceeding WGS84 bounds are rejected (no clamping)."""
    bad_dict = {
        "record_id": "REC-OOB-COORD",
        "observed_at": "2026-08-15T12:00:00Z",
        "location_coordinates": (195.0, -110.0),  # Longitude > 180, Latitude < -90
        "rainfall_24h_mm": 50.0,
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[bad_dict],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    issue = result.rejected_records[0].issues[0]
    assert issue.code == ValidationIssueCode.COORDINATES_OUT_OF_BOUNDS
    assert "clamping is strictly forbidden" in issue.message


def test_nan_and_infinite_numeric_values_rejected():
    """Requirement 9: NaN and Infinite numerical values are rejected."""
    nan_dict = {
        "record_id": "REC-NAN",
        "observed_at": "2026-08-15T12:00:00Z",
        "location_coordinates": (79.50, 30.50),
        "rainfall_24h_mm": float("nan"),
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[nan_dict],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    issue = result.rejected_records[0].issues[0]
    assert issue.code == ValidationIssueCode.INVALID_NUMERIC_VALUE
    assert "cannot be NaN or infinite" in issue.message


def test_invalid_negative_domain_value_rejected():
    """Requirement 10: Negative values in non-negative domains are rejected."""
    neg_dict = {
        "record_id": "REC-NEG",
        "observed_at": "2026-08-15T12:00:00Z",
        "location_coordinates": (79.50, 30.50),
        "rainfall_24h_mm": -12.5,
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[neg_dict],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    issue = result.rejected_records[0].issues[0]
    assert issue.code == ValidationIssueCode.NUMERIC_OUT_OF_DOMAIN
    assert "below allowed minimum" in issue.message


def test_missing_required_identity_rejected():
    """Requirement 11: Missing or empty record identifier is rejected."""
    no_id_dict = {
        "record_id": "",
        "observed_at": "2026-08-15T12:00:00Z",
        "location_coordinates": (79.50, 30.50),
        "rainfall_24h_mm": 10.0,
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[no_id_dict],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.accepted_count == 0
    assert result.rejected_count == 1
    issue = result.rejected_records[0].issues[0]
    assert issue.code in {ValidationIssueCode.MISSING_REQUIRED_FIELD, ValidationIssueCode.INVALID_IDENTITY}


def test_unsupported_category_rejected():
    """Requirement 12: Submitting an invalid/unsupported category raises UnsupportedCategoryError."""
    with pytest.raises(UnsupportedCategoryError):
        ingest_batch(
            category="unsupported_space_weather",  # type: ignore
            records=[],
            provenance=SAMPLE_PROVENANCE,
        )


def test_duplicate_records_detected_deterministically():
    """Requirement 13: Duplicate record IDs within a batch are flagged and rejected."""
    rec1 = {
        "record_id": "REC-DUP-01",
        "observed_at": "2026-08-15T12:00:00Z",
        "location_coordinates": (79.50, 30.50),
        "rainfall_24h_mm": 20.0,
        "provenance": SAMPLE_PROVENANCE,
    }
    rec2 = {
        "record_id": "REC-DUP-01",  # Same ID
        "observed_at": "2026-08-15T12:30:00Z",
        "location_coordinates": (79.50, 30.50),
        "rainfall_24h_mm": 35.0,
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[rec1, rec2],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.total_input_count == 2
    assert result.accepted_count == 1  # First occurrence accepted
    assert result.rejected_count == 1  # Second occurrence rejected
    assert result.rejected_records[0].issues[0].code == ValidationIssueCode.DUPLICATE_RECORD


def test_mixed_valid_and_invalid_batch_preserves_valid_records():
    """Requirement 14: Partial-batch fault isolation — valid records are preserved."""
    valid1 = {
        "record_id": "REC-VALID-1",
        "observed_at": "2026-08-15T10:00:00Z",
        "location_coordinates": (79.40, 30.40),
        "rainfall_24h_mm": 15.0,
        "provenance": SAMPLE_PROVENANCE,
    }
    invalid1 = {
        "record_id": "REC-INVALID-1",
        "observed_at": "invalid_date",
        "location_coordinates": (79.40, 30.40),
        "rainfall_24h_mm": 25.0,
        "provenance": SAMPLE_PROVENANCE,
    }
    valid2 = {
        "record_id": "REC-VALID-2",
        "observed_at": "2026-08-15T11:00:00Z",
        "location_coordinates": (79.45, 30.45),
        "rainfall_24h_mm": 30.0,
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[valid1, invalid1, valid2],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.total_input_count == 3
    assert result.accepted_count == 2
    assert result.rejected_count == 1
    assert [r.record_id for r in result.accepted_records] == ["REC-VALID-1", "REC-VALID-2"]
    assert result.rejected_records[0].record_id == "REC-INVALID-1"


def test_rejected_records_report_diagnostic_issues():
    """Requirement 15: Rejected record entries report index, field, and issue diagnostics."""
    invalid_rec = {
        "record_id": "REC-ERR-REPORT",
        "observed_at": "2026-08-15T10:00:00Z",
        "location_coordinates": (79.40, 30.40),
        "rainfall_24h_mm": -5.0,
        "severity": "invalid_super_critical",
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[invalid_rec],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.rejected_count == 1
    rej = result.rejected_records[0]
    assert rej.index == 0
    assert len(rej.issues) >= 2
    issue_codes = {i.code for i in rej.issues}
    assert ValidationIssueCode.NUMERIC_OUT_OF_DOMAIN in issue_codes
    assert ValidationIssueCode.INVALID_SEVERITY in issue_codes


def test_identical_input_produces_identical_ingestion_output():
    """Requirement 16: Strict determinism — identical input produces bit-for-bit identical result."""
    rec = {
        "record_id": "REC-DET-01",
        "observed_at": "2026-08-15T12:00:00Z",
        "location_coordinates": (79.512345, 30.556789),
        "rainfall_24h_mm": 50.0,
        "provenance": SAMPLE_PROVENANCE,
    }

    pipeline = IngestionPipeline()
    res1 = pipeline.ingest_batch(category=SourceCategory.RAINFALL, records=[rec], provenance=SAMPLE_PROVENANCE)
    res2 = pipeline.ingest_batch(category=SourceCategory.RAINFALL, records=[rec], provenance=SAMPLE_PROVENANCE)

    assert res1.model_dump_json() == res2.model_dump_json()


def test_synthetic_provenance_preserved_with_disclaimer():
    """Requirement 17: Synthetic provenance and disclaimer are strictly preserved."""
    rec = {
        "record_id": "REC-PROV-01",
        "observed_at": "2026-08-15T12:00:00Z",
        "location_coordinates": (79.50, 30.50),
        "rainfall_24h_mm": 10.0,
        "provenance": SAMPLE_PROVENANCE,
    }

    result = ingest_batch(
        category=SourceCategory.RAINFALL,
        records=[rec],
        provenance=SAMPLE_PROVENANCE,
    )

    assert result.provenance.is_synthetic is True
    assert "SIH Problem Statement 26191" in result.provenance.disclaimer
    assert result.accepted_records[0].provenance.is_synthetic is True


# =====================================================================
# 3. Integration with All Five M3-03 Mock Providers
# =====================================================================


def test_all_five_mock_providers_feed_ingestion_pipeline():
    """Requirement 18: Ingestion pipeline directly ingests all 5 M3-03 mock provider outputs."""
    categories = [
        (SourceCategory.RAINFALL, 8),
        (SourceCategory.FLOOD, 6),
        (SourceCategory.LANDSLIDE, 10),
        (SourceCategory.HAZARD_OBSERVATION, 30),
        (SourceCategory.POPULATION_EXPOSURE, 40),
    ]

    pipeline = IngestionPipeline()

    for cat, expected_count in categories:
        provider = get_provider(cat)
        resp = provider.fetch_data(ProviderQuery(category=cat))

        result = pipeline.ingest_provider_response(resp)

        assert result.category == cat
        assert result.total_input_count == expected_count
        assert result.accepted_count == expected_count
        assert result.rejected_count == 0
        assert len(result.validation_issues) == 0
        assert len(result.accepted_records) == expected_count


def test_no_real_person_pii_in_ingestion_output():
    """Requirement 19: Result JSON contains zero real-person PII."""
    pipeline = IngestionPipeline()

    for cat in [
        SourceCategory.RAINFALL,
        SourceCategory.FLOOD,
        SourceCategory.LANDSLIDE,
        SourceCategory.HAZARD_OBSERVATION,
        SourceCategory.POPULATION_EXPOSURE,
    ]:
        provider = get_provider(cat)
        resp = provider.fetch_data(ProviderQuery(category=cat))
        result = pipeline.ingest_provider_response(resp)

        raw_json = result.model_dump_json().lower()
        for pii in ["phone", "email", "aadhaar", "ssn", "mobile", "password"]:
            assert f'"{pii}"' not in raw_json, f"Potential PII field '{pii}' found in {cat}"


def test_m3_02_synthetic_dataset_direct_ingestion():
    """Requirement 20: Validate that M3-02 synthetic dataset fixtures successfully pass ingestion."""
    from app.data.synthetic.loader import load_himalayan_pilot_dataset

    dataset = load_himalayan_pilot_dataset()
    assert len(dataset.hazard_events) == 30
    assert len(dataset.villages.features) == 40

    prov = ProviderProvenance(
        provider_id="mock_fixture_loader",
        provider_name="M3-02 Synthetic Fixture Ingestion",
        mode=ProviderMode.MOCK,
        is_synthetic=True,
        region_id="himalayan_pilot",
    )

    # 1. Ingest hazard events
    hazard_records = [
        NormalizedHazardObservationRecord(
            record_id=f"REC-{e.id}",
            observed_at=e.observed_at,
            location_coordinates=e.location.coordinates,
            provenance=prov,
            hazard_type=e.hazard_type,
            village_id=e.village_id,
            village_name=e.village_name,
            severity=e.severity,
            intensity_value=float(e.intensity_value),
            intensity_unit=e.intensity_unit,
            description=e.description,
        )
        for e in dataset.hazard_events
    ]

    pipeline = IngestionPipeline()
    haz_result = pipeline.ingest_batch(
        category=SourceCategory.HAZARD_OBSERVATION,
        records=hazard_records,
        provenance=prov,
    )
    assert haz_result.total_input_count == 30
    assert haz_result.accepted_count == 30
    assert haz_result.rejected_count == 0

    # 2. Ingest village population records
    village_records = [
        NormalizedPopulationRecord(
            village_id=v.properties.id,
            village_name=v.properties.name,
            region_code=v.properties.region_code,
            district_code=v.properties.district_code,
            block_code=v.properties.block_code,
            location_coordinates=v.geometry.coordinates,
            total_population=v.properties.population,
            households=v.properties.households,
            elderly_count=v.properties.demographics.elderly_count,
            children_count=v.properties.demographics.children_count,
            disabled_count=v.properties.demographics.disabled_count,
            livestock_count=v.properties.demographics.livestock_count,
            provenance=prov,
        )
        for v in dataset.villages.features
    ]

    pop_result = pipeline.ingest_batch(
        category=SourceCategory.POPULATION_EXPOSURE,
        records=village_records,
        provenance=prov,
    )
    assert pop_result.total_input_count == 40
    assert pop_result.accepted_count == 40
    assert pop_result.rejected_count == 0

