"""
Build machine-readable dataset manifest for RakshakGIS.
Reads verified SHA256 checksums from data/manifests/raw_files_checksums.json
and generates data/manifests/dataset_manifest.json.
"""

import json
import os

CHECKSUMS_FILE = os.path.join("data", "manifests", "raw_files_checksums.json")
MANIFEST_FILE = os.path.join("data", "manifests", "dataset_manifest.json")

def load_checksums():
    with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Map normalized path to {size_bytes, sha256}
    mapping = {}
    for item in data:
        norm_path = item["path"].replace("\\", "/")
        mapping[norm_path] = item
    return mapping

def generate_manifest():
    checksums = load_checksums()
    
    datasets = []
    
    # 1. Census 2011
    census_path = "data/raw/census/2011-IndiaStateDistSbDistVill-0000.xlsx"
    c_info = checksums.get(census_path, {})
    datasets.append({
        "dataset_id": "census_2011_pca_village",
        "name": "Census of India 2011 - Primary Census Abstract (Village/Town level)",
        "provider": "Office of the Registrar General & Census Commissioner, India (ORGI)",
        "source_type": "static",
        "version": "2011",
        "local_expected_path": census_path,
        "file_type": "xlsx",
        "geographic_scope": "National (All India States, Districts, Sub-districts, Villages)",
        "intended_db_target": "villages, population_profiles",
        "provenance": "Official Census 2011 Primary Census Abstract table 0000",
        "license_or_attribution": "Government Open Data License - India (GODL-India) / Census of India",
        "ingestion_status": "ready_for_ingestion",
        "safe_to_commit": False,
        "download_url": "https://censusindia.gov.in/census.website/data/census-tables",
        "expected_size_bytes": c_info.get("size_bytes"),
        "sha256": c_info.get("sha256"),
        "manual_acquisition_instructions": "Download Census 2011 PCA Village-level dataset from Census of India portal or data.gov.in. Save to data/raw/census/2011-IndiaStateDistSbDistVill-0000.xlsx."
    })

    # 2. LGD States
    lgd_states = "data/raw/lgd/All_Stateof_India_2026-09-07_19-43-08.xlsx"
    s_info = checksums.get(lgd_states, {})
    datasets.append({
        "dataset_id": "lgd_states",
        "name": "Local Government Directory - State Directory",
        "provider": "Ministry of Panchayati Raj, Government of India",
        "source_type": "static",
        "version": "2026",
        "local_expected_path": lgd_states,
        "file_type": "xlsx",
        "geographic_scope": "National (36 States/UTs)",
        "intended_db_target": "regions",
        "provenance": "Local Government Directory (LGD) official portal export",
        "license_or_attribution": "GODL-India / Ministry of Panchayati Raj",
        "ingestion_status": "ready_for_ingestion",
        "safe_to_commit": False,
        "download_url": "https://lgdirectory.gov.in/",
        "expected_size_bytes": s_info.get("size_bytes"),
        "sha256": s_info.get("sha256"),
        "manual_acquisition_instructions": "Export State directory from https://lgdirectory.gov.in/ and save to data/raw/lgd/."
    })

    # 3. LGD Districts
    lgd_districts = "data/raw/lgd/All_Districtof_India_2026-09-07_19-42-42.xlsx"
    d_info = checksums.get(lgd_districts, {})
    datasets.append({
        "dataset_id": "lgd_districts",
        "name": "Local Government Directory - District Directory",
        "provider": "Ministry of Panchayati Raj, Government of India",
        "source_type": "static",
        "version": "2026",
        "local_expected_path": lgd_districts,
        "file_type": "xlsx",
        "geographic_scope": "National (All Districts)",
        "intended_db_target": "districts",
        "provenance": "Local Government Directory (LGD) official portal export",
        "license_or_attribution": "GODL-India / Ministry of Panchayati Raj",
        "ingestion_status": "ready_for_ingestion",
        "safe_to_commit": False,
        "download_url": "https://lgdirectory.gov.in/",
        "expected_size_bytes": d_info.get("size_bytes"),
        "sha256": d_info.get("sha256"),
        "manual_acquisition_instructions": "Export District directory from https://lgdirectory.gov.in/ and save to data/raw/lgd/."
    })

    # 4. LGD Sub-districts
    lgd_subdistricts = "data/raw/lgd/All_Sub_Districtof_India_2026-09-07_19-42-56.xlsx"
    sd_info = checksums.get(lgd_subdistricts, {})
    datasets.append({
        "dataset_id": "lgd_subdistricts",
        "name": "Local Government Directory - Sub-district / Tehsil Directory",
        "provider": "Ministry of Panchayati Raj, Government of India",
        "source_type": "static",
        "version": "2026",
        "local_expected_path": lgd_subdistricts,
        "file_type": "xlsx",
        "geographic_scope": "National (All Sub-districts/Tehsils)",
        "intended_db_target": "blocks",
        "provenance": "Local Government Directory (LGD) official portal export",
        "license_or_attribution": "GODL-India / Ministry of Panchayati Raj",
        "ingestion_status": "ready_for_ingestion",
        "safe_to_commit": False,
        "download_url": "https://lgdirectory.gov.in/",
        "expected_size_bytes": sd_info.get("size_bytes"),
        "sha256": sd_info.get("sha256"),
        "manual_acquisition_instructions": "Export Sub-district directory from https://lgdirectory.gov.in/ and save to data/raw/lgd/."
    })

    # 5. LGD Villages
    lgd_villages = "data/raw/lgd/All_Villagesof_India_2026-09-07_19-42-08.xlsx"
    v_info = checksums.get(lgd_villages, {})
    datasets.append({
        "dataset_id": "lgd_villages",
        "name": "Local Government Directory - Complete Village Directory",
        "provider": "Ministry of Panchayati Raj, Government of India",
        "source_type": "static",
        "version": "2026",
        "local_expected_path": lgd_villages,
        "file_type": "xlsx",
        "geographic_scope": "National (600,000+ Villages)",
        "intended_db_target": "villages",
        "provenance": "Local Government Directory (LGD) official portal export",
        "license_or_attribution": "GODL-India / Ministry of Panchayati Raj",
        "ingestion_status": "ready_for_ingestion",
        "safe_to_commit": False,
        "download_url": "https://lgdirectory.gov.in/",
        "expected_size_bytes": v_info.get("size_bytes"),
        "sha256": v_info.get("sha256"),
        "manual_acquisition_instructions": "Export Village directory from https://lgdirectory.gov.in/ and save to data/raw/lgd/."
    })

    # 6. NCS Seismology
    ncs_path = "data/raw/ncs/Official Website of National Center of Seismology.xlsx"
    ncs_info = checksums.get(ncs_path, {})
    datasets.append({
        "dataset_id": "ncs_seismology",
        "name": "National Centre for Seismology - Earthquake Event Catalog",
        "provider": "National Centre for Seismology (NCS), Ministry of Earth Sciences",
        "source_type": "static",
        "version": "2026",
        "local_expected_path": ncs_path,
        "file_type": "xlsx",
        "geographic_scope": "India & adjoining region (Himalayan / National seismicity)",
        "intended_db_target": "hazard_observations, disaster_events",
        "provenance": "NCS earthquake bulletin export (151 recent events with lat, lon, depth, magnitude)",
        "license_or_attribution": "GODL-India / NCS MoES",
        "ingestion_status": "ready_for_ingestion",
        "safe_to_commit": False,
        "download_url": "https://seismo.gov.in/",
        "expected_size_bytes": ncs_info.get("size_bytes"),
        "sha256": ncs_info.get("sha256"),
        "manual_acquisition_instructions": "Export earthquake records from National Centre for Seismology portal https://seismo.gov.in/ and save to data/raw/ncs/."
    })

    # 7. India OSM Road Network
    osm_path = "data/raw/osm/india-260906.osm.pbf"
    osm_info = checksums.get(osm_path, {})
    datasets.append({
        "dataset_id": "osm_india_roads",
        "name": "OpenStreetMap India Complete Extract (Road Network & Infrastructure)",
        "provider": "OpenStreetMap Contributors / Geofabrik GmbH",
        "source_type": "static",
        "version": "2026-09-06",
        "local_expected_path": osm_path,
        "file_type": "pbf",
        "geographic_scope": "India National",
        "intended_db_target": "road_network, evacuation_routes",
        "provenance": "Geofabrik download mirror for India OSM extract",
        "license_or_attribution": "Open Database License (ODbL) 1.0 - (c) OpenStreetMap contributors",
        "ingestion_status": "ready_for_routing_extraction",
        "safe_to_commit": False,
        "download_url": "https://download.geofabrik.de/asia/india-latest.osm.pbf",
        "expected_size_bytes": osm_info.get("size_bytes"),
        "sha256": osm_info.get("sha256"),
        "manual_acquisition_instructions": "Download india-latest.osm.pbf from https://download.geofabrik.de/asia/india-latest.osm.pbf and save to data/raw/osm/."
    })

    # 8. Survey of India Village Boundaries (Iterate through all SOI ZIPs)
    soi_files = [p for p in checksums.keys() if p.startswith("data/raw/survey_of_india/") and p.endswith(".zip")]
    for s_path in sorted(soi_files):
        fname = os.path.basename(s_path)
        state_name = os.path.splitext(fname)[0].replace("&", "and").replace(" ", "_").lower()
        s_file_info = checksums.get(s_path, {})
        datasets.append({
            "dataset_id": f"soi_village_boundaries_{state_name}",
            "name": f"Survey of India - Village Boundaries ({os.path.splitext(fname)[0].replace('_', ' ')})",
            "provider": "Survey of India (SoI), Department of Science & Technology",
            "source_type": "static",
            "version": "1.0",
            "local_expected_path": s_path,
            "file_type": "zip",
            "geographic_scope": f"State: {os.path.splitext(fname)[0].replace('_', ' ')}",
            "intended_db_target": "villages.boundary (MultiPolygon geometry)",
            "provenance": "Survey of India Nakshe / Bharat Maps portal boundary shapefiles",
            "license_or_attribution": "Survey of India Open Data Policy / National Map Policy",
            "ingestion_status": "ready_for_ingestion",
            "safe_to_commit": False,
            "download_url": "https://indiamaps.gov.in/ or https://onlinemaps.surveyofindia.gov.in/",
            "expected_size_bytes": s_file_info.get("size_bytes"),
            "sha256": s_file_info.get("sha256"),
            "manual_acquisition_instructions": f"Download village boundary shapefile for {os.path.splitext(fname)[0]} from Survey of India portal and place in data/raw/survey_of_india/{fname}."
        })

    # 9. Copernicus DEM Catalogues (Deferred / metadata only)
    cop_files = [p for p in checksums.keys() if p.startswith("data/raw/copernicus/")]
    for c_path in sorted(cop_files):
        fname = os.path.basename(c_path)
        c_file_info = checksums.get(c_path, {})
        datasets.append({
            "dataset_id": f"copernicus_dem_manifest_{fname.replace('.', '_').replace('-', '_')}",
            "name": f"Copernicus GLO-30 Digital Elevation Model Catalogue Manifest ({fname})",
            "provider": "European Space Agency (ESA) / Copernicus Programme",
            "source_type": "deferred_metadata",
            "version": "2024_1",
            "local_expected_path": c_path,
            "file_type": fname.split(".")[-1],
            "geographic_scope": "India (GLO-30 Coverage Tiles)",
            "intended_db_target": "deferred_raster_manifest",
            "provenance": "Copernicus Space Data Open Access Hub / Panda catalogue",
            "license_or_attribution": "Copernicus Open Access Policy",
            "ingestion_status": "deferred_unavailable",
            "safe_to_commit": False,
            "download_url": "https://spacedata.copernicus.eu/",
            "expected_size_bytes": c_file_info.get("size_bytes"),
            "sha256": c_file_info.get("sha256"),
            "manual_acquisition_instructions": "Direct raster download encountered HTTP 403 authorization requirement. Raster DEM tiles are deferred. Do not fabricate elevation or slope in FULL_DATA mode; report DATA_UNAVAILABLE."
        })

    # 10. Live Data Sources (Open-Meteo, CWC Flood, USGS Earthquakes)
    datasets.append({
        "dataset_id": "live_open_meteo_weather",
        "name": "Open-Meteo Weather & Rainfall API",
        "provider": "Open-Meteo (open-source weather API)",
        "source_type": "live",
        "version": "v1",
        "local_expected_path": "LIVE_API (no local static file)",
        "file_type": "json_api",
        "geographic_scope": "Global / India coordinates (lat, lon)",
        "intended_db_target": "weather_observations, dynamic_risk_adjustments",
        "provenance": "Open-Meteo numerical weather prediction models (ECMWF, GFS)",
        "license_or_attribution": "Attribution to Open-Meteo (Non-commercial open-meteo license / CC-BY 4.0)",
        "ingestion_status": "live_provider_adapter",
        "safe_to_commit": True,
        "download_url": "https://api.open-meteo.com/v1/forecast",
        "expected_size_bytes": None,
        "sha256": None,
        "manual_acquisition_instructions": "Live HTTP API endpoint. Requires no API key for standard non-commercial rate limits. Do NOT label Open-Meteo as IMD."
    })

    datasets.append({
        "dataset_id": "live_cwc_flood_observations",
        "name": "Central Water Commission (CWC) Flood Forecasting Table",
        "provider": "Central Water Commission, Ministry of Jal Shakti, Government of India",
        "source_type": "live",
        "version": "daily_table",
        "local_expected_path": "LIVE_ENDPOINT (no local static file)",
        "file_type": "delimited_text",
        "geographic_scope": "National (River basins, flood monitoring stations across India)",
        "intended_db_target": "flood_monitoring_stations, hazard_observations",
        "provenance": "CWC Advanced Flood Forecasting (AFF) live observation table",
        "license_or_attribution": "Government of India / CWC AFF",
        "ingestion_status": "live_provider_adapter",
        "safe_to_commit": True,
        "download_url": "https://aff.india-water.gov.in/textdata/Floodday_table_view_header.txt",
        "expected_size_bytes": None,
        "sha256": None,
        "manual_acquisition_instructions": "Live HTTP endpoint. Fetches daily flood stage, danger level, HFL, and forecast readings."
    })

    datasets.append({
        "dataset_id": "live_usgs_earthquake_feed",
        "name": "USGS Earthquake Hazards Program API",
        "provider": "United States Geological Survey (USGS)",
        "source_type": "live",
        "version": "fdsnws_v1",
        "local_expected_path": "LIVE_API (no local static file)",
        "file_type": "geojson_api",
        "geographic_scope": "Global / Regional bounding box query",
        "intended_db_target": "disaster_events, hazard_observations",
        "provenance": "USGS Real-time Earthquake API (FDSN web service)",
        "license_or_attribution": "US Public Domain",
        "ingestion_status": "live_provider_adapter",
        "safe_to_commit": True,
        "download_url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
        "expected_size_bytes": None,
        "sha256": None,
        "manual_acquisition_instructions": "Live public GeoJSON/JSON API for regional earthquake queries."
    })

    datasets.append({
        "dataset_id": "bhuvan_gsi_landslide_portal",
        "name": "Bhuvan / Geological Survey of India (GSI) Landslide Susceptibility",
        "provider": "Geological Survey of India & NRSC/ISRO",
        "source_type": "deferred_manual",
        "version": "2024",
        "local_expected_path": "PORTAL_ONLY (no verified open machine-readable API)",
        "file_type": "web_portal",
        "geographic_scope": "Himalayan & Western Ghats Landslide Corridors",
        "intended_db_target": "hazard_zones",
        "provenance": "GSI National Landslide Susceptibility Mapping (NLSM) / Bhuvan portal",
        "license_or_attribution": "ISRO / GSI",
        "ingestion_status": "manual_portal_only",
        "safe_to_commit": False,
        "download_url": "https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php?id=landslide",
        "expected_size_bytes": None,
        "sha256": None,
        "manual_acquisition_instructions": "Official landslide inventory/hazard information exists on Bhuvan/GSI portals, but no public unauthenticated REST/WFS endpoint is published. Do NOT fabricate a machine-readable endpoint. Handled via explicit DATA_UNAVAILABLE in FULL_DATA mode unless shapefiles are manually placed in data/raw/landslide/."
    })

    manifest = {
        "manifest_version": "1.0.0",
        "project": "RakshakGIS",
        "description": "Authoritative dataset catalog, checksum registry, and acquisition metadata for disaster decision-support platform.",
        "generated_at": "2026-09-07T23:20:00Z",
        "total_datasets": len(datasets),
        "datasets": datasets
    }

    os.makedirs(os.path.dirname(MANIFEST_FILE), exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest written successfully to {MANIFEST_FILE} with {len(datasets)} datasets.")

if __name__ == "__main__":
    generate_manifest()
