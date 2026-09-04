"""High-level deterministic loader and accessor for RakshakGIS synthetic datasets."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"

from app.data.synthetic.generator import (
    build_synthetic_dataset,
    serialize_dataset_to_fixtures,
)
from app.data.synthetic.schemas import (
    DatasetMetadata,
    HimalayanPilotDataset,
    SyntheticCandidateSitesFeatureCollection,
    SyntheticHazardEvent,
    SyntheticVillagesFeatureCollection,
)

_CACHED_DATASET: Optional[HimalayanPilotDataset] = None


def ensure_fixtures_exist() -> None:
    """Ensure fixture files exist on disk, generating them deterministically if missing."""
    metadata_path = FIXTURES_DIR / "himalayan_pilot_metadata.json"
    villages_path = FIXTURES_DIR / "villages.geojson"
    sites_path = FIXTURES_DIR / "candidate_sites.geojson"
    events_path = FIXTURES_DIR / "hazard_events.json"

    if (
        not metadata_path.exists()
        or not villages_path.exists()
        or not sites_path.exists()
        or not events_path.exists()
    ):
        dataset = build_synthetic_dataset()
        serialize_dataset_to_fixtures(dataset, FIXTURES_DIR)


def load_himalayan_pilot_dataset(force_regenerate: bool = False) -> HimalayanPilotDataset:
    """Load the complete deterministic synthetic Himalayan pilot dataset.

    Args:
        force_regenerate: If True, regenerates dataset from PRNG and overwrites fixtures.

    Returns:
        HimalayanPilotDataset: Strongly typed, validated, immutable dataset container.
    """
    global _CACHED_DATASET

    if _CACHED_DATASET is not None and not force_regenerate:
        return _CACHED_DATASET

    if force_regenerate:
        dataset = build_synthetic_dataset()
        serialize_dataset_to_fixtures(dataset, FIXTURES_DIR)
        _CACHED_DATASET = dataset
        return dataset

    ensure_fixtures_exist()

    # Load from pre-serialized fixtures
    metadata_path = FIXTURES_DIR / "himalayan_pilot_metadata.json"
    villages_path = FIXTURES_DIR / "villages.geojson"
    sites_path = FIXTURES_DIR / "candidate_sites.geojson"
    events_path = FIXTURES_DIR / "hazard_events.json"

    with open(metadata_path, "r", encoding="utf-8") as f:
        meta_dict = json.load(f)

    with open(villages_path, "r", encoding="utf-8") as f:
        villages_dict = json.load(f)

    with open(sites_path, "r", encoding="utf-8") as f:
        sites_dict = json.load(f)

    with open(events_path, "r", encoding="utf-8") as f:
        events_list = json.load(f)

    dataset = HimalayanPilotDataset(
        metadata=DatasetMetadata(**meta_dict),
        villages=SyntheticVillagesFeatureCollection(**villages_dict),
        candidate_sites=SyntheticCandidateSitesFeatureCollection(**sites_dict),
        hazard_events=[SyntheticHazardEvent(**e) for e in events_list],
    )

    _CACHED_DATASET = dataset
    return dataset


def get_synthetic_villages_geojson() -> Dict[str, Any]:
    """Return the synthetic villages GeoJSON FeatureCollection as a Python dict."""
    ensure_fixtures_exist()
    with open(FIXTURES_DIR / "villages.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


def get_synthetic_candidate_sites_geojson() -> Dict[str, Any]:
    """Return the synthetic candidate sites GeoJSON FeatureCollection as a Python dict."""
    ensure_fixtures_exist()
    with open(FIXTURES_DIR / "candidate_sites.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


def get_synthetic_hazard_events() -> List[Dict[str, Any]]:
    """Return the synthetic hazard events list as Python dicts."""
    ensure_fixtures_exist()
    with open(FIXTURES_DIR / "hazard_events.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_dataset_metadata() -> Dict[str, Any]:
    """Return the dataset metadata as a Python dict."""
    ensure_fixtures_exist()
    with open(FIXTURES_DIR / "himalayan_pilot_metadata.json", "r", encoding="utf-8") as f:
        return json.load(f)
