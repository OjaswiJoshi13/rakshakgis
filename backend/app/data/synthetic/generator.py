"""Deterministic generator for RakshakGIS synthetic Himalayan pilot dataset."""

import json
import math
from pathlib import Path
import random
from typing import Any, Dict, List, Tuple

from app.data.synthetic.constants import (
    DETERMINISTIC_SEED,
    PILOT_BLOCKS,
    PILOT_CANDIDATE_SITES,
    PILOT_DISTRICT_CODE,
    PILOT_DISTRICT_NAME,
    PILOT_REGION_CODE,
    PILOT_REGION_PROFILE_ID,
    PILOT_VILLAGE_NAMES,
    SYNTHETIC_DISCLAIMER,
)
from app.data.synthetic.schemas import (
    CandidateSiteCapacity,
    CandidateSiteSuitabilityInputs,
    DatasetMetadata,
    GeoJSONPoint,
    GeoJSONPolygon,
    HimalayanPilotDataset,
    SyntheticCandidateSiteFeature,
    SyntheticCandidateSiteProperties,
    SyntheticCandidateSitesFeatureCollection,
    SyntheticHazardEvent,
    SyntheticProvenance,
    SyntheticVillageFeature,
    SyntheticVillageProperties,
    SyntheticVillagesFeatureCollection,
    VillageAccessibility,
    VillageDemographics,
    VillageHazards,
    VillageInfrastructure,
    VillageVulnerabilityIndicators,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _create_synthetic_provenance() -> SyntheticProvenance:
    """Standardized synthetic provenance metadata."""
    return SyntheticProvenance(
        is_synthetic=True,
        data_source="DEMO_SYNTHETIC_GENERATOR",
        pilot_region=PILOT_REGION_PROFILE_ID,
        generator_seed=DETERMINISTIC_SEED,
        disclaimer=SYNTHETIC_DISCLAIMER,
    )


def _generate_bounding_polygon(
    center_lon: float, center_lat: float, area_sq_m: float
) -> GeoJSONPolygon:
    """Generate a deterministic 5-vertex closed polygon bounding the site area.

    1 degree latitude ~= 111,320 meters.
    1 degree longitude at 30.5° N ~= 111,320 * cos(30.5°) ~= 96,000 meters.
    """
    side_m = math.sqrt(area_sq_m)
    half_side_m = side_m / 2.0

    delta_lat = half_side_m / 111320.0
    delta_lon = half_side_m / (111320.0 * math.cos(math.radians(center_lat)))

    # Closed ring: SW -> SE -> NE -> NW -> SW
    p_sw = (round(center_lon - delta_lon, 6), round(center_lat - delta_lat, 6))
    p_se = (round(center_lon + delta_lon, 6), round(center_lat - delta_lat, 6))
    p_ne = (round(center_lon + delta_lon, 6), round(center_lat + delta_lat, 6))
    p_nw = (round(center_lon - delta_lon, 6), round(center_lat + delta_lat, 6))

    return GeoJSONPolygon(type="Polygon", coordinates=[[p_sw, p_se, p_ne, p_nw, p_sw]])


def generate_villages(rng: random.Random) -> SyntheticVillagesFeatureCollection:
    """Generate exactly 40 deterministic synthetic villages across 4 pilot blocks."""
    features: List[SyntheticVillageFeature] = []

    # Coordinate base ranges by block within Chamoli district
    block_coords = {
        "joshimath": {"lon": (79.5200, 79.6800), "lat": (30.5100, 30.6100)},
        "dasholi": {"lon": (79.3200, 79.4600), "lat": (30.3800, 30.4800)},
        "karnaprayag": {"lon": (79.1800, 79.3100), "lat": (30.2200, 30.3300)},
        "ghat": {"lon": (79.4100, 79.5600), "lat": (30.2400, 30.3500)},
    }

    # Geology classifications
    geology_types = [
        ("debris_mantled_slope", "Vaikrita_Group_Schist"),
        ("colluvial_scree", "Garhwal_Group_Quartzite"),
        ("morainic_gravel", "Central_Crystalline_Gneiss"),
        ("fluvial_terrace_alluvium", "Chamoli_Metavolcanic_Formation"),
    ]

    for idx, v_meta in enumerate(PILOT_VILLAGE_NAMES, start=1):
        v_id = f"HIM-VILL-{idx:03d}"
        b_code = v_meta["block"]
        b_info = PILOT_BLOCKS[b_code]

        # Deterministic coordinates within block box
        c_box = block_coords[b_code]
        lon = round(rng.uniform(c_box["lon"][0], c_box["lon"][1]), 5)
        lat = round(rng.uniform(c_box["lat"][0], c_box["lat"][1]), 5)

        # Elevation and slope dependent on block
        if b_code == "joshimath":
            elevation = round(rng.uniform(1800.0, 2650.0), 1)
            slope = round(rng.uniform(22.0, 41.5), 1)
            subsidence = idx in [1, 2, 4, 6]  # Sunil, Ravigram, Manohar Bagh, Singhdhar
            hist_landslides = rng.randint(2, 6)
            dist_road = round(rng.uniform(0.5, 4.5), 1)
            road_type = "unpaved" if dist_road > 2.0 else "paved"
            evacuation_cond = "critical_chokepoints" if slope > 32.0 else "poor"
            winter_cutoff = elevation > 2200.0
        elif b_code == "dasholi":
            elevation = round(rng.uniform(1350.0, 1950.0), 1)
            slope = round(rng.uniform(14.0, 28.0), 1)
            subsidence = False
            hist_landslides = rng.randint(0, 3)
            dist_road = round(rng.uniform(0.2, 2.8), 1)
            road_type = "paved" if dist_road < 1.5 else "unpaved"
            evacuation_cond = "fair" if slope < 22.0 else "poor"
            winter_cutoff = False
        elif b_code == "karnaprayag":
            elevation = round(rng.uniform(920.0, 1380.0), 1)
            slope = round(rng.uniform(8.0, 21.0), 1)
            subsidence = False
            hist_landslides = rng.randint(0, 2)
            dist_road = round(rng.uniform(0.1, 1.8), 1)
            road_type = "paved"
            evacuation_cond = "good" if slope < 14.0 else "fair"
            winter_cutoff = False
        else:  # ghat
            elevation = round(rng.uniform(1450.0, 2250.0), 1)
            slope = round(rng.uniform(18.0, 36.0), 1)
            subsidence = False
            hist_landslides = rng.randint(1, 4)
            dist_road = round(rng.uniform(1.0, 6.0), 1)
            road_type = "footpath" if dist_road > 3.0 else "unpaved"
            evacuation_cond = "poor"
            winter_cutoff = elevation > 1900.0

        # Population & Household metrics
        population = rng.randint(190, 920)
        households = max(35, int(population / rng.uniform(4.2, 4.8)))
        elderly = int(population * rng.uniform(0.09, 0.15))
        children = int(population * rng.uniform(0.14, 0.21))
        disabled = max(2, int(population * rng.uniform(0.015, 0.035)))
        livestock = int(households * rng.uniform(0.8, 1.8))

        # Vulnerability Indicators
        soil_type, geo_form = geology_types[idx % len(geology_types)]
        soc_vuln = round(rng.uniform(0.25, 0.78), 3)
        econ_vuln = round(rng.uniform(0.30, 0.82), 3)
        struct_vuln = round(rng.uniform(0.35, 0.85), 3)
        road_conn = round(max(0.1, 1.0 - (dist_road / 7.0)), 3)
        poverty_ratio = round(rng.uniform(0.18, 0.45), 3)
        kuccha_ratio = round(rng.uniform(0.20, 0.65), 3)

        # Infrastructure Presence
        has_school = rng.random() > 0.15
        has_health = rng.random() > 0.55
        has_piped_water = rng.random() > 0.25
        has_electricity = rng.random() > 0.08
        has_telecom = rng.random() > 0.12

        dist_river = round(rng.uniform(80.0, 1500.0), 1)

        feature = SyntheticVillageFeature(
            type="Feature",
            id=v_id,
            geometry=GeoJSONPoint(type="Point", coordinates=(lon, lat)),
            properties=SyntheticVillageProperties(
                id=v_id,
                name=v_meta["name"],
                region_code=PILOT_REGION_CODE,
                district_code=PILOT_DISTRICT_CODE,
                district_name=PILOT_DISTRICT_NAME,
                block_code=b_code,
                block_name=b_info["name"],
                census_code=v_meta["census_code"],
                population=population,
                households=households,
                demographics=VillageDemographics(
                    elderly_count=elderly,
                    children_count=children,
                    disabled_count=disabled,
                    livestock_count=livestock,
                ),
                vulnerability=VillageVulnerabilityIndicators(
                    social_vulnerability_index=soc_vuln,
                    economic_vulnerability_index=econ_vuln,
                    structural_vulnerability_index=struct_vuln,
                    road_connectivity_index=road_conn,
                    poverty_ratio=poverty_ratio,
                    kuccha_housing_ratio=kuccha_ratio,
                ),
                infrastructure=VillageInfrastructure(
                    has_primary_school=has_school,
                    has_health_subcenter=has_health,
                    has_piped_water=has_piped_water,
                    has_electricity=has_electricity,
                    has_telecom_coverage=has_telecom,
                ),
                accessibility=VillageAccessibility(
                    distance_to_motorable_road_km=dist_road,
                    road_type=road_type,
                    evacuation_route_condition=evacuation_cond,
                    is_winter_cutoff_prone=winter_cutoff,
                ),
                hazards=VillageHazards(
                    elevation_m=elevation,
                    slope_deg=slope,
                    historical_landslide_count=hist_landslides,
                    active_subsidence=subsidence,
                    distance_to_river_m=dist_river,
                    soil_type=soil_type,
                    geological_formation=geo_form,
                ),
                provenance=_create_synthetic_provenance(),
            ),
        )
        features.append(feature)

    return SyntheticVillagesFeatureCollection(
        type="FeatureCollection",
        name="synthetic_himalayan_villages",
        features=features,
    )


def generate_candidate_sites() -> SyntheticCandidateSitesFeatureCollection:
    """Generate exactly 12 deterministic candidate relocation sites with closed polygons."""
    features: List[SyntheticCandidateSiteFeature] = []

    for s in PILOT_CANDIDATE_SITES:
        s_id = s["id"]
        center_lon, center_lat = s["coords"]
        area = s["area_sq_m"]

        polygon = _generate_bounding_polygon(center_lon, center_lat, area)

        feature = SyntheticCandidateSiteFeature(
            type="Feature",
            id=s_id,
            geometry=polygon,
            properties=SyntheticCandidateSiteProperties(
                id=s_id,
                name=s["name"],
                district_code=PILOT_DISTRICT_CODE,
                district_name=PILOT_DISTRICT_NAME,
                block_code=s["block"],
                site_type=s["site_type"],
                status=s["status"],
                suitability=CandidateSiteSuitabilityInputs(
                    area_sq_m=area,
                    terrain_slope_deg=s["terrain_slope_deg"],
                    elevation_m=s["elevation_m"],
                    soil_stability=s["soil_stability"],
                    hazard_buffer_distance_m=s["hazard_buffer_distance_m"],
                    road_width_m=s["road_width_m"],
                    distance_to_highway_km=s["distance_to_highway_km"],
                    all_weather_access=s["all_weather_access"],
                    water_supply_lpd_per_capita=s["water_supply_lpd_per_capita"],
                    water_source_distance_m=s["water_source_distance_m"],
                    perennial_water_source=s["perennial_water_source"],
                    distance_to_health_center_km=s["distance_to_health_center_km"],
                    distance_to_school_km=s["distance_to_school_km"],
                    distance_to_emergency_km=s["distance_to_emergency_km"],
                    distance_to_market_km=s["distance_to_market_km"],
                    distance_to_farmland_km=s["distance_to_farmland_km"],
                    livelihood_potential=s["livelihood_potential"],
                    expansion_potential=s["expansion_potential"],
                    suitability_category=s["suitability_category"],
                    rejection_reason=s["rejection_reason"],
                ),
                capacity=CandidateSiteCapacity(
                    max_households=s["max_households"],
                    max_population=s["max_population"],
                    allocated_households=0,
                    allocated_population=0,
                    available_households=s["max_households"],
                    available_population=s["max_population"],
                    sanitation_units=s["sanitation_units"],
                ),
                provenance=_create_synthetic_provenance(),
            ),
        )
        features.append(feature)

    return SyntheticCandidateSitesFeatureCollection(
        type="FeatureCollection",
        name="synthetic_himalayan_candidate_sites",
        features=features,
    )


def generate_hazard_events(
    villages: SyntheticVillagesFeatureCollection, rng: random.Random
) -> List[SyntheticHazardEvent]:
    """Generate 30 deterministic synthetic hazard incident observations."""
    events: List[SyntheticHazardEvent] = []

    # Deterministic incident templates
    event_templates = [
        # 10 Landslide Incidents
        {
            "hazard_type": "landslide",
            "village_idx": 1,  # Sunil
            "date": "2024-07-18T14:30:00Z",
            "severity": "critical",
            "intensity": 18500.0,
            "unit": "cu_m_debris_volume",
            "desc": "Rain-triggered rotational debris slump across uphill road corridor; 120m highway cut off.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 3,  # Marwari
            "date": "2024-08-04T09:15:00Z",
            "severity": "very_high",
            "intensity": 8200.0,
            "unit": "cu_m_debris_volume",
            "desc": "Translational rockslide from fractured gneiss escarpment; blocked local drainage channel.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 4,  # Manohar Bagh
            "date": "2024-08-11T21:00:00Z",
            "severity": "critical",
            "intensity": 24000.0,
            "unit": "cu_m_debris_volume",
            "desc": "Active ground fissures and foundation subsidence following 48-hour continuous downpour.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 8,  # Helang
            "date": "2024-08-22T06:45:00Z",
            "severity": "high",
            "intensity": 4500.0,
            "unit": "cu_m_debris_volume",
            "desc": "Debris flow in seasonal gully washing out pedestrian bridge and power transmission pole.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 11,  # Tapovan
            "date": "2025-07-02T11:20:00Z",
            "severity": "very_high",
            "intensity": 12000.0,
            "unit": "cu_m_debris_volume",
            "desc": "Slope toe failure along river bank during high discharge pulse.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 16,  # Tangani
            "date": "2025-07-19T17:50:00Z",
            "severity": "critical",
            "intensity": 31000.0,
            "unit": "cu_m_debris_volume",
            "desc": "Major chronic landslide zone reactivation on NH-58 corridor; road blocked for 3 days.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 20,  # Birahi
            "date": "2025-08-08T03:10:00Z",
            "severity": "high",
            "intensity": 6200.0,
            "unit": "cu_m_debris_volume",
            "desc": "Shallow mudflow encroaching on terraced agricultural fields.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 24,  # Mandal
            "date": "2025-08-15T16:00:00Z",
            "severity": "moderate",
            "intensity": 2100.0,
            "unit": "cu_m_debris_volume",
            "desc": "Localized cut-slope slip along forest access route.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 36,  # Sitel
            "date": "2026-07-10T12:00:00Z",
            "severity": "very_high",
            "intensity": 15400.0,
            "unit": "cu_m_debris_volume",
            "desc": "Debris avalanche into Nandakini tributary causing temporary backwater pooling.",
        },
        {
            "hazard_type": "landslide",
            "village_idx": 38,  # Sutol
            "date": "2026-07-28T08:30:00Z",
            "severity": "high",
            "intensity": 5800.0,
            "unit": "cu_m_debris_volume",
            "desc": "Steep scree chute slip damaging water supply pipeline.",
        },
        # 8 Extreme / Heavy Rainfall Readings
        {
            "hazard_type": "rainfall",
            "village_idx": 2,  # Ravigram
            "date": "2024-07-17T23:59:00Z",
            "severity": "critical",
            "intensity": 142.5,
            "unit": "mm_per_24h",
            "desc": "Very heavy rainfall exceeding IMD critical threshold (115.5 mm); surface runoff saturation.",
        },
        {
            "hazard_type": "rainfall",
            "village_idx": 9,  # Urgam
            "date": "2024-08-10T23:59:00Z",
            "severity": "very_high",
            "intensity": 88.0,
            "unit": "mm_per_24h",
            "desc": "Heavy localized monsoon rainfall exceeding IMD warning threshold (64.5 mm).",
        },
        {
            "hazard_type": "rainfall",
            "village_idx": 12,  # Reni
            "date": "2025-06-25T23:59:00Z",
            "severity": "critical",
            "intensity": 165.0,
            "unit": "mm_per_24h",
            "desc": "Cloudburst event in upper Rishi Ganga catchment delivering torrential precipitation.",
        },
        {
            "hazard_type": "rainfall",
            "village_idx": 19,  # Pipalkoti
            "date": "2025-07-18T23:59:00Z",
            "severity": "high",
            "intensity": 78.5,
            "unit": "mm_per_24h",
            "desc": "Sustained monsoon rain exceeding IMD heavy rainfall mark (64.5 mm).",
        },
        {
            "hazard_type": "rainfall",
            "village_idx": 26,  # Gopeshwar Dealdhar
            "date": "2025-08-07T23:59:00Z",
            "severity": "very_high",
            "intensity": 118.0,
            "unit": "mm_per_24h",
            "desc": "Very heavy rainfall surpassing IMD 115.5 mm trigger; urban drainage surcharge.",
        },
        {
            "hazard_type": "rainfall",
            "village_idx": 30,  # Simli
            "date": "2025-08-14T23:59:00Z",
            "severity": "high",
            "intensity": 72.0,
            "unit": "mm_per_24h",
            "desc": "Heavy rainfall triggering rise in Pindar river gauge.",
        },
        {
            "hazard_type": "rainfall",
            "village_idx": 37,  # Kanol
            "date": "2026-07-09T23:59:00Z",
            "severity": "critical",
            "intensity": 155.0,
            "unit": "mm_per_24h",
            "desc": "Cloudburst pulse causing intense slope gullying and boulder transport.",
        },
        {
            "hazard_type": "rainfall",
            "village_idx": 39,  # Pagna
            "date": "2026-07-27T23:59:00Z",
            "severity": "high",
            "intensity": 82.5,
            "unit": "mm_per_24h",
            "desc": "High intensity rainfall event saturating colluvial soil mantle.",
        },
        # 6 Seismic Events
        {
            "hazard_type": "seismic",
            "village_idx": 1,  # Sunil
            "date": "2024-09-05T04:12:30Z",
            "severity": "critical",
            "intensity": 7.2,
            "unit": "mmi_intensity",
            "desc": "Seismic tremor exceeding critical threshold MMI VII; widespread plaster cracks in masonry.",
        },
        {
            "hazard_type": "seismic",
            "village_idx": 5,  # Parsari
            "date": "2024-09-05T04:12:30Z",
            "severity": "very_high",
            "intensity": 6.8,
            "unit": "mmi_intensity",
            "desc": "Significant ground motion shaking Zone V fault lines; partial wall collapse in older structures.",
        },
        {
            "hazard_type": "seismic",
            "village_idx": 17,  # Gulabkoti
            "date": "2025-03-14T18:44:10Z",
            "severity": "high",
            "intensity": 5.8,
            "unit": "mmi_intensity",
            "desc": "Moderate regional earthquake centered on Main Central Thrust (MCT).",
        },
        {
            "hazard_type": "seismic",
            "village_idx": 21,  # Batula
            "date": "2025-03-14T18:44:10Z",
            "severity": "high",
            "intensity": 5.5,
            "unit": "mmi_intensity",
            "desc": "Strong ground vibration felt across Dasholi block valleys.",
        },
        {
            "hazard_type": "seismic",
            "village_idx": 29,  # Umra Narayan
            "date": "2026-01-20T02:08:45Z",
            "severity": "very_high",
            "intensity": 6.4,
            "unit": "mmi_intensity",
            "desc": "Alaknanda lineament seismic event triggering minor rockfalls along road cuttings.",
        },
        {
            "hazard_type": "seismic",
            "village_idx": 33,  # Langasu
            "date": "2026-01-20T02:08:45Z",
            "severity": "high",
            "intensity": 5.9,
            "unit": "mmi_intensity",
            "desc": "Deep crustal tremor causing noticeable shaking of hillside settlements.",
        },
        # 6 Flash Flood / River Inundation Events
        {
            "hazard_type": "flash_flood",
            "village_idx": 3,  # Marwari
            "date": "2024-07-20T19:30:00Z",
            "severity": "critical",
            "intensity": 3.8,
            "unit": "meters_above_danger_level",
            "desc": "Alaknanda flash flood surge submerging riverside pedestrian paths and low terraces.",
        },
        {
            "hazard_type": "flash_flood",
            "village_idx": 11,  # Tapovan
            "date": "2024-08-15T15:40:00Z",
            "severity": "very_high",
            "intensity": 2.6,
            "unit": "meters_above_danger_level",
            "desc": "Dhauliganga torrent surge eroding toe of valley slopes and scouring bridge piers.",
        },
        {
            "hazard_type": "flash_flood",
            "village_idx": 12,  # Reni
            "date": "2025-06-26T02:15:00Z",
            "severity": "critical",
            "intensity": 4.5,
            "unit": "meters_above_danger_level",
            "desc": "Glacial lake runoff and debris surge inundating confluence zone.",
        },
        {
            "hazard_type": "flash_flood",
            "village_idx": 20,  # Birahi
            "date": "2025-08-08T06:00:00Z",
            "severity": "high",
            "intensity": 1.9,
            "unit": "meters_above_danger_level",
            "desc": "Birahi Ganga river discharge peak overtopping protective gabion revetment.",
        },
        {
            "hazard_type": "flash_flood",
            "village_idx": 30,  # Simli
            "date": "2025-08-15T04:20:00Z",
            "severity": "high",
            "intensity": 1.7,
            "unit": "meters_above_danger_level",
            "desc": "Pindar river flood pulse washing through low-lying agricultural benches.",
        },
        {
            "hazard_type": "flash_flood",
            "village_idx": 36,  # Sitel
            "date": "2026-07-10T14:15:00Z",
            "severity": "very_high",
            "intensity": 2.9,
            "unit": "meters_above_danger_level",
            "desc": "Nandakini river sudden hydrograph spike following cloudburst in upper reach.",
        },
    ]

    village_map = {f.properties.id: f for f in villages.features}

    for e_idx, t in enumerate(event_templates, start=1):
        e_id = f"HIM-EVT-{e_idx:03d}"
        v_key = f"HIM-VILL-{t['village_idx']:03d}"
        v_feat = village_map[v_key]

        # Offset location slightly from village center for realism
        v_lon, v_lat = v_feat.geometry.coordinates
        offset_lon = round(v_lon + rng.uniform(-0.003, 0.003), 5)
        offset_lat = round(v_lat + rng.uniform(-0.003, 0.003), 5)

        event = SyntheticHazardEvent(
            id=e_id,
            village_id=v_key,
            village_name=v_feat.properties.name,
            hazard_type=t["hazard_type"],
            observed_at=t["date"],
            severity=t["severity"],
            intensity_value=t["intensity"],
            intensity_unit=t["unit"],
            location=GeoJSONPoint(type="Point", coordinates=(offset_lon, offset_lat)),
            description=t["desc"],
            provenance=_create_synthetic_provenance(),
        )
        events.append(event)

    return events


def build_synthetic_dataset() -> HimalayanPilotDataset:
    """Build complete deterministic synthetic Himalayan pilot dataset."""
    rng = random.Random(DETERMINISTIC_SEED)

    villages = generate_villages(rng)
    sites = generate_candidate_sites()
    events = generate_hazard_events(villages, rng)

    metadata = DatasetMetadata(
        dataset_id="rakshakgis_himalayan_pilot_v1",
        version="1.0.0",
        source_type="synthetic",
        generation_method="deterministic_prng",
        generator_seed=DETERMINISTIC_SEED,
        pilot_region_profile=PILOT_REGION_PROFILE_ID,
        village_count=len(villages.features),
        candidate_site_count=len(sites.features),
        hazard_event_count=len(events),
        geographic_bounding_box={
            "min_lon": 79.10,
            "max_lon": 79.85,
            "min_lat": 30.20,
            "max_lat": 30.70,
        },
        disclaimer=SYNTHETIC_DISCLAIMER,
    )

    return HimalayanPilotDataset(
        metadata=metadata,
        villages=villages,
        candidate_sites=sites,
        hazard_events=events,
    )


def serialize_dataset_to_fixtures(
    dataset: HimalayanPilotDataset, target_dir: Path = FIXTURES_DIR
) -> Dict[str, Path]:
    """Serialize the dataset into individual deterministic GeoJSON / JSON files."""
    target_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = target_dir / "himalayan_pilot_metadata.json"
    villages_path = target_dir / "villages.geojson"
    sites_path = target_dir / "candidate_sites.geojson"
    events_path = target_dir / "hazard_events.json"

    # Write metadata JSON
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(dataset.metadata.model_dump(), f, indent=2, sort_keys=True)

    # Write villages GeoJSON
    with open(villages_path, "w", encoding="utf-8") as f:
        json.dump(dataset.villages.model_dump(), f, indent=2)

    # Write candidate sites GeoJSON
    with open(sites_path, "w", encoding="utf-8") as f:
        json.dump(dataset.candidate_sites.model_dump(), f, indent=2)

    # Write hazard events JSON
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(
            [e.model_dump() for e in dataset.hazard_events], f, indent=2, sort_keys=True
        )

    return {
        "metadata": metadata_path,
        "villages": villages_path,
        "candidate_sites": sites_path,
        "hazard_events": events_path,
    }


if __name__ == "__main__":
    print(f"Generating deterministic synthetic dataset with seed {DETERMINISTIC_SEED}...")
    ds = build_synthetic_dataset()
    written = serialize_dataset_to_fixtures(ds)
    print(f"Successfully generated and serialized synthetic dataset:")
    print(f"  Villages count: {len(ds.villages.features)}")
    print(f"  Candidate sites count: {len(ds.candidate_sites.features)}")
    print(f"  Hazard events count: {len(ds.hazard_events)}")
    for name, path in written.items():
        print(f"  - {name}: {path} ({path.stat().st_size} bytes)")
