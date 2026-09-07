"""Himalayan pilot seed script for RakshakGIS development and demo modes.

Strict Security & Governance Constraints:
  1. Only executes when settings.APP_ENV == 'development' and settings.DATA_MODE == 'demo'.
  2. Never executes in production.
  3. No plaintext passwords or secrets in code or database.
  4. Authoritative domain engines:
     - VulnerabilityExposureEngine (M3-09)
     - MultiHazardRiskEngine (M3-08)
     - RiskClassificationEngine (M3-07)
     - RelocationPriorityEngine (M3-12)
     - PermanentRedZoneEngine (M3-10)
     - SiteSuitabilityEngine (M4-02)
     - EvacuationRoutingEngine (M4-05)
     are executed directly to derive scores, classifications, red zones, and evacuation routes.
  5. Deterministic synthetic datasets from M3-02 fixtures are loaded directly.
"""

import logging
from typing import Dict, List, Optional
from shapely.geometry import LineString, shape
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.profiles import get_profile
from app.core.relocation.routing import (
    EvacuationRoutingEngine,
    RouteQuery,
    RouteStatus,
)
from app.core.relocation.suitability import SiteSuitabilityEngine, SiteSuitabilityInput
from app.core.risk.classification.engine import RiskClassificationEngine
from app.core.risk.computation.engine import MultiHazardRiskEngine
from app.core.risk.red_zone.contracts import RedZoneStatus
from app.core.risk.red_zone.engine import PermanentRedZoneEngine
from app.core.risk.relocation_priority.engine import RelocationPriorityEngine
from app.core.risk.vulnerability.contracts import DemographicInput, VulnerabilityInput
from app.core.risk.vulnerability.engine import VulnerabilityExposureEngine
from app.data.synthetic.loader import load_himalayan_pilot_dataset
from app.models.geographic import Block, District, Region, Village
from app.models.governance import User
from app.models.relocation import (
    CandidateSite,
    Infrastructure,
    RelocationPriority,
    Route,
    SiteCapacity,
)
from app.models.risk import RedZone, RiskFactor, RiskScore
from app.models.telemetry import Alert, DataIngestionRun, DataSource
from app.models.vulnerability import PopulationProfile, VulnerabilityProfile

logger = logging.getLogger(__name__)
settings = get_settings()


def seed_himalayan_pilot_data(db: Session, force: bool = False) -> Dict[str, int]:
    """Seed the database with Himalayan pilot dataset and engine-derived results.

    Guarded: Only runs in development/demo mode.
    Idempotent: Skips if data already exists unless force=True.
    """
    if settings.APP_ENV != "development" or settings.DATA_MODE != "demo":
        raise RuntimeError(
            f"Seeding Himalayan pilot data is strictly restricted to development/demo mode. "
            f"Current APP_ENV='{settings.APP_ENV}', DATA_MODE='{settings.DATA_MODE}'."
        )

    village_count = db.query(Village).count()
    if village_count > 0 and not force:
        logger.info("Database already contains %d villages. Skipping seed.", village_count)
        return {"status": "skipped", "existing_villages": village_count}

    logger.info("Starting Himalayan Pilot Data Seeding (APP_ENV=%s, DATA_MODE=%s)...", settings.APP_ENV, settings.DATA_MODE)

    # 1. Load Synthetic Fixtures & Regional Profile
    dataset = load_himalayan_pilot_dataset()
    profile = get_profile("himalayan_pilot")

    # Instantiate authoritative domain engines
    vuln_engine = VulnerabilityExposureEngine(profile=profile)
    risk_engine = MultiHazardRiskEngine(profile=profile)
    risk_classifier = RiskClassificationEngine(profile=profile)
    priority_engine = RelocationPriorityEngine(profile=profile)
    suitability_engine = SiteSuitabilityEngine()
    prz_engine = PermanentRedZoneEngine.from_profile("himalayan_pilot")
    routing_engine = EvacuationRoutingEngine.from_region_profile(
        profile=profile,
        hazard_events=[e.model_dump() for e in dataset.hazard_events],
    )

    counts = {
        "regions": 0,
        "districts": 0,
        "blocks": 0,
        "users": 0,
        "villages": 0,
        "candidate_sites": 0,
        "red_zones": 0,
        "routes": 0,
        "alerts": 0,
        "data_sources": 0,
    }

    # 2. Demo User (district_collector_chamoli)
    # Role: district_officer. Password hash is non-functional placeholder string (Option A).
    demo_user = db.query(User).filter(User.username == "district_collector_chamoli").first()
    if not demo_user:
        demo_user = User(
            username="district_collector_chamoli",
            email="collector@chamoli.gov.in",
            hashed_password="*DEMO_TOKEN_CLEARANCE_ONLY*",
            full_name="District Collector Chamoli",
            role="district_officer",
            department="District Disaster Management Authority",
            is_active=True,
        )
        db.add(demo_user)
        db.flush()
        counts["users"] += 1

    # 3. Administrative Hierarchy: Region, District, Blocks
    region = db.query(Region).filter(Region.code == "uttarakhand_himalayan").first()
    if not region:
        region = Region(
            code="uttarakhand_himalayan",
            name="Uttarakhand",
            state="Uttarakhand",
            metadata_json={"zone": "Western Himalayas", "pilot_corridor": "Joshimath-Pipalkoti"},
        )
        db.add(region)
        db.flush()
        counts["regions"] += 1

    district = db.query(District).filter(District.code == "chamoli").first()
    if not district:
        district = District(
            region_id=region.id,
            code="chamoli",
            name="Chamoli",
            headquarters="Gopeshwar",
            metadata_json={"elevation_range_m": [800, 7816], "risk_class": "Very High Seismic Zone V"},
        )
        db.add(district)
        db.flush()
        counts["districts"] += 1

    # Discover and create blocks dynamically from village tehsils
    block_map: Dict[str, Block] = {}
    for f in dataset.villages.features:
        tehsil_name = getattr(f.properties, "tehsil", "Joshimath") or "Joshimath"
        code = tehsil_name.lower().replace(" ", "_")
        if code not in block_map:
            blk = db.query(Block).filter(Block.code == code).first()
            if not blk:
                blk = Block(
                    district_id=district.id,
                    code=code,
                    name=tehsil_name,
                    metadata_json={"tehsil": tehsil_name},
                )
                db.add(blk)
                db.flush()
                counts["blocks"] += 1
            block_map[code] = blk

    # 4. Ingest Villages, Demographics, Vulnerabilities, Risk Scores, Relocation Priorities
    village_entity_map: Dict[str, Village] = {}
    for f in dataset.villages.features:
        props = f.properties
        tehsil_code = (getattr(props, "tehsil", "Joshimath") or "Joshimath").lower().replace(" ", "_")
        block = block_map.get(tehsil_code, list(block_map.values())[0])

        coords = f.geometry.coordinates
        point_wkt = f"POINT({coords[0]} {coords[1]})"

        hazards = props.hazards
        v_model = Village(
            block_id=block.id,
            census_code=props.census_code or props.id,
            name=props.name,
            location=WKTElement(point_wkt, srid=4326),
            elevation_m=hazards.elevation_m,
            slope_deg=hazards.slope_deg,
            is_active=True,
        )
        db.add(v_model)
        db.flush()
        village_entity_map[props.id] = v_model
        counts["villages"] += 1

        # PopulationProfile
        demo = props.demographics
        pop_profile = PopulationProfile(
            village_id=v_model.id,
            total_population=props.population,
            households=props.households,
            elderly_count=demo.elderly_count,
            children_count=demo.children_count,
            disabled_count=demo.disabled_count,
            livestock_count=demo.livestock_count,
            survey_year=2024,
        )
        db.add(pop_profile)

        # Authoritative Factor D & V Evaluation via VulnerabilityExposureEngine
        exp_res = vuln_engine.score_demographic_exposure(
            DemographicInput(
                total_population=props.population,
                elderly_count=demo.elderly_count,
                children_count=demo.children_count,
                disabled_count=demo.disabled_count,
            ),
            village_id=props.id,
        )

        vuln = props.vulnerability
        soc_res = vuln_engine.score_social_vulnerability(
            VulnerabilityInput(
                social_vulnerability_index=vuln.social_vulnerability_index,
                economic_vulnerability_index=vuln.economic_vulnerability_index,
                structural_vulnerability_index=vuln.structural_vulnerability_index,
                road_connectivity_index=vuln.road_connectivity_index,
            ),
            village_id=props.id,
        )

        vuln_profile = VulnerabilityProfile(
            village_id=v_model.id,
            social_vulnerability_index=vuln.social_vulnerability_index,
            economic_vulnerability_index=vuln.economic_vulnerability_index,
            structural_vulnerability_index=vuln.structural_vulnerability_index,
            road_connectivity_index=vuln.road_connectivity_index,
            composite_vulnerability_score=round((soc_res.normalized_value or 0.0) / 100.0, 4),
            factors_json={
                "poverty_ratio": vuln.poverty_ratio,
                "kuccha_housing_ratio": vuln.kuccha_housing_ratio,
                "demographic_exposure_score": exp_res.normalized_value,
            },
        )
        db.add(vuln_profile)

        # Authoritative MultiHazardRiskEngine Evaluation
        # Physical hazard components derived from geophysical observation indicators
        slope_susceptibility = min(100.0, (hazards.slope_deg / 45.0) * 75.0 + min(25.0, hazards.historical_landslide_count * 5.0))
        hazard_sev = 90.0 if hazards.active_subsidence else min(85.0, slope_susceptibility * 0.85)
        flood_exp = max(10.0, min(80.0, (1500.0 - getattr(hazards, "distance_to_river_m", 500.0)) / 18.0))
        rainfall_int = 50.0  # Baseline monsoon climatology

        risk_res = risk_engine.compute_from_values(
            village_id=props.id,
            hazard_severity=round(hazard_sev, 2),
            flood_exposure=round(flood_exp, 2),
            rainfall_intensity=round(rainfall_int, 2),
            slope_landslide_susceptibility=round(slope_susceptibility, 2),
            infrastructure_vulnerability=round(exp_res.normalized_value or 0.0, 2),
            social_vulnerability=round(soc_res.normalized_value or 0.0, 2),
        )

        # Authoritative Risk Classification Band
        class_res = risk_classifier.classify(risk_res.score, village_id=props.id)

        risk_score = RiskScore(
            village_id=v_model.id,
            score=round(risk_res.score, 2),
            band=class_res.band.value.lower(),
            hazard_subscore=round(hazard_sev, 2),
            exposure_subscore=round(exp_res.normalized_value or 0.0, 2),
            vulnerability_subscore=round(soc_res.normalized_value or 0.0, 2),
            is_current=True,
        )
        db.add(risk_score)
        db.flush()

        # Authoritative RelocationPriorityEngine Evaluation
        p_res = priority_engine.evaluate(
            village_id=props.id,
            village_name=props.name,
            risk=risk_res.score,
            exposure=exp_res.normalized_value or 0.0,
            vulnerability=soc_res.normalized_value or 0.0,
            historical_impact=min(100.0, hazards.historical_landslide_count * 15.0),
            accessibility=min(100.0, props.accessibility.distance_to_motorable_road_km * 10.0),
        )

        priority_band_str = p_res.priority_band.value.upper() if p_res.priority_band else "MONITOR"
        priority_model = RelocationPriority(
            village_id=v_model.id,
            priority_band=priority_band_str,
            priority_score=round(p_res.priority_score or 0.0, 2),
            estimated_households=props.households,
            estimated_people=props.population,
            urgency_reason=p_res.explainability.decision_reason if p_res.explainability else f"Assessed {priority_band_str}",
            is_active=True,
        )
        db.add(priority_model)

    # 5. Ingest Candidate Relocation Sites, Capacities, Infrastructure
    site_entity_map: Dict[str, CandidateSite] = {}
    for f in dataset.candidate_sites.features:
        props = f.properties
        poly_geom = shape(f.geometry.model_dump())
        centroid = poly_geom.centroid

        loc_wkt = f"POINT({centroid.x} {centroid.y})"
        boundary_wkt = poly_geom.wkt

        suitability_data = props.suitability.model_dump()
        suit_input = SiteSuitabilityInput(
            site_id=props.id,
            name=props.name,
            district_id=district.id,
            **suitability_data,
        )
        suit_result = suitability_engine.evaluate(suit_input)

        site_model = CandidateSite(
            name=props.name,
            district_id=district.id,
            location=WKTElement(loc_wkt, srid=4326),
            boundary=WKTElement(boundary_wkt, srid=4326),
            area_sq_m=suitability_data.get("area_sq_m"),
            terrain_slope_deg=suitability_data.get("terrain_slope_deg"),
            elevation_m=suitability_data.get("elevation_m"),
            suitability_score=round(suit_result.overall_score, 2),
            status=props.status or "proposed",
        )
        db.add(site_model)
        db.flush()
        site_entity_map[props.id] = site_model
        counts["candidate_sites"] += 1

        # SiteCapacity
        cap = props.capacity
        water_per_cap = suitability_data.get("water_supply_lpd_per_capita", 70.0)
        total_water = cap.max_population * water_per_cap

        site_cap = SiteCapacity(
            site_id=site_model.id,
            max_households=cap.max_households,
            max_population=cap.max_population,
            allocated_households=0,
            allocated_population=0,
            available_households=cap.available_households,
            available_population=cap.available_population,
            water_supply_lpd=total_water,
            sanitation_units=cap.sanitation_units,
        )
        db.add(site_cap)

        # Infrastructure assets derived from suitability access indicators
        infra_items = [
            ("Water Supply Distribution Node", "water_tank", "operational", f"Perennial gravity feed at {suitability_data.get('water_source_distance_m', 200)}m"),
            ("Primary Access Road Corridor", "road_access", "operational", f"Carriageway width {suitability_data.get('road_width_m', 6.0)}m"),
        ]
        if suitability_data.get("distance_to_health_center_km", 5.0) <= 2.0:
            infra_items.append(("Community First Aid Post", "medical_center", "operational", "On-site primary healthcare post"))
        if suitability_data.get("distance_to_emergency_km", 5.0) <= 2.5:
            infra_items.append(("Helipad & Emergency Relief Staging", "helipad", "operational", "All-weather reinforced landing pad"))

        for name, infra_type, status_str, desc in infra_items:
            infra_model = Infrastructure(
                site_id=site_model.id,
                name=name,
                infra_type=infra_type,
                status=status_str,
                location=WKTElement(loc_wkt, srid=4326),
                capacity_description=desc,
            )
            db.add(infra_model)

    # 6. Authoritative Permanent Red Zone Demarcation (M3-10 Engine)
    logger.info("Executing M3-10 PermanentRedZoneEngine for pilot demarcation...")
    raw_candidates = prz_engine.demarcate_permanent_red_zones(
        [f.model_dump() for f in dataset.villages.features],
        dissolve_overlaps=True,
    )

    for cand in raw_candidates:
        if cand.status == RedZoneStatus.PROPOSED and cand.geometry is not None:
            zone_type_val = cand.zone_type.value if hasattr(cand.zone_type, "value") else str(cand.zone_type)
            danger_val = cand.danger_level.value if hasattr(cand.danger_level, "value") else (str(cand.danger_level) if cand.danger_level else "uninhabitable")

            red_zone = RedZone(
                name=cand.name,
                zone_type=zone_type_val,
                danger_level=danger_val,
                geometry=WKTElement(cand.geometry.wkt, srid=4326),
                area_sq_km=round(cand.area_sq_km, 4) if cand.area_sq_km else None,
                declared_by_officer_id=demo_user.id,
                is_active=True,
                metadata_json=cand.metadata_json or {},
            )
            db.add(red_zone)
            counts["red_zones"] += 1

    # 7. Authoritative Evacuation Routing (M4-05 Engine)
    logger.info("Executing M4-05 EvacuationRoutingEngine for corridor route generation...")
    seeded_route_keys = set()
    for v_feat in dataset.villages.features:
        v_db = village_entity_map.get(v_feat.properties.id)
        if not v_db:
            continue

        v_coords = v_feat.geometry.coordinates

        for s_feat in dataset.candidate_sites.features:
            s_db = site_entity_map.get(s_feat.properties.id)
            if not s_db:
                continue

            pair_key = (v_db.id, s_db.id)
            if pair_key in seeded_route_keys:
                continue

            poly_geom = shape(s_feat.geometry.model_dump())
            dest_coords = (poly_geom.centroid.x, poly_geom.centroid.y)

            route_query = RouteQuery(
                origin=v_coords,
                destination=dest_coords,
                region_profile_id="himalayan_pilot",
            )
            try:
                route_res = routing_engine.route(route_query)
            except Exception as e:
                logger.warning("Routing failed for %s -> %s: %s", v_db.name, s_db.name, e)
                continue

            if (
                route_res.status == RouteStatus.FEASIBLE
                and route_res.primary_route
                and route_res.primary_route.distance_km > 0.0
                and len(route_res.primary_route.geometry) >= 2
            ):
                line_geom = LineString(route_res.primary_route.geometry)
                route_model = Route(
                    name=f"Evacuation Corridor: {v_db.name} to {s_db.name}",
                    origin_village_id=v_db.id,
                    destination_site_id=s_db.id,
                    path=WKTElement(line_geom.wkt, srid=4326),
                    distance_km=round(float(route_res.primary_route.distance_km), 2),
                    estimated_travel_time_min=round(float(route_res.primary_route.estimated_time_minutes or 0.0), 1),
                    route_type="evacuation",
                    safety_score=round(max(0.0, min(100.0, 100.0 - (float(route_res.primary_route.total_hazard_penalty or 0.0) * 5.0))), 1),
                    is_blocked=False,
                    blockage_reason=None,
                )
                db.add(route_model)
                seeded_route_keys.add(pair_key)
                counts["routes"] += 1

                # Cap total routes per village to avoid cartesian explosion
                if sum(1 for (vid, _) in seeded_route_keys if vid == v_db.id) >= 2:
                    break

    # 8. Seed Early Warning Alerts
    alert_templates = [
        ("Sunil", "evacuation_notice", "severe", "Critical Ground Subsidence Detected", "Continuous InSAR ground deformation exceeding 15mm/month detected in Sunil settlement. Immediate evacuation recommended."),
        ("Marwari", "landslide_warning", "severe", "Compound Landslide & Erosion Threat", "Compound risk breach along Alaknanda river terrace; severe toe erosion and slope instability observed."),
        ("Ravigram", "landslide_warning", "warning", "Active Surface Fissure Progression", "Geotechnical sensors reported new surface fissures propagation along upper slope agricultural terraces."),
        ("Urgam", "rainfall_threshold", "warning", "Precipitation Threshold Exceeded", "Automated rain gauge recorded 82mm precipitation in 24 hours, exceeding landslide initiation threshold."),
    ]

    for v_name, a_type, sev, headline, msg in alert_templates:
        matched_v = db.query(Village).filter(Village.name.ilike(f"%{v_name}%")).first()
        alert = Alert(
            village_id=matched_v.id if matched_v else None,
            district_id=district.id,
            alert_type=a_type,
            severity=sev,
            headline=headline,
            message=msg,
            is_acknowledged=False,
        )
        db.add(alert)
        counts["alerts"] += 1

    # 9. Sync Telemetry Data Sources from Provider Registry (IMD, NRSC, USGS, etc.)
    from datetime import datetime, timezone
    from app.core.telemetry.service import TelemetryService

    telemetry_service = TelemetryService()
    synced_sources = telemetry_service.sync_registered_providers(db)
    counts["data_sources"] = len(synced_sources)

    now_utc = datetime.now(timezone.utc)
    for ds in synced_sources:
        existing_run = db.query(DataIngestionRun).filter(DataIngestionRun.data_source_id == ds.id).first()
        if not existing_run:
            run = DataIngestionRun(
                data_source_id=ds.id,
                status="success",
                records_ingested=24,
                records_failed=0,
                started_at=now_utc,
                completed_at=now_utc,
                log_details=f"Automated synchronization successfully completed for {ds.name}.",
            )
            db.add(run)

    db.commit()
    logger.info("Successfully seeded Himalayan Pilot Dataset: %s", counts)
    return counts
