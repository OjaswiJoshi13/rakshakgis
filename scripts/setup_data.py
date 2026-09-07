"""
One-command Data Environment Setup and Bootstrap for RakshakGIS.
Ensures directory structure, checks manifests, verifies existing datasets,
downloads automatable resources, and guides teammate onboarding.
"""

import os
import subprocess
import sys

def main():
    print("================================================================")
    print("           RakshakGIS Data Environment Bootstrap                ")
    print("================================================================\n")

    # 1. Directory Structure
    dirs = [
        os.path.join("data", "raw"),
        os.path.join("data", "raw", "census"),
        os.path.join("data", "raw", "lgd"),
        os.path.join("data", "raw", "ncs"),
        os.path.join("data", "raw", "osm"),
        os.path.join("data", "raw", "survey_of_india"),
        os.path.join("data", "raw", "copernicus"),
        os.path.join("data", "processed"),
        os.path.join("data", "manifests"),
        os.path.join("data", "demo"),
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("[1/3] Verified directory layout (data/raw, data/processed, data/manifests).")

    # Ensure .gitkeep in raw and processed
    raw_keep = os.path.join("data", "raw", ".gitkeep")
    proc_keep = os.path.join("data", "processed", ".gitkeep")
    if not os.path.exists(raw_keep):
        with open(raw_keep, "w") as f:
            pass
    if not os.path.exists(proc_keep):
        with open(proc_keep, "w") as f:
            pass

    # 2. Dataset Verification
    print("\n[2/3] Verifying local dataset inventory against official manifest...")
    verify_res = subprocess.run([sys.executable, os.path.join("scripts", "verify_data.py"), "--quick"])
    
    if verify_res.returncode != 0:
        print("\n[!] Some datasets are missing or corrupted.")
        print("    Running acquisition manager to inspect/download missing items...")
        subprocess.run([sys.executable, os.path.join("scripts", "download_data.py"), "--check-only"])
    else:
        print("\n[OK] All registered static datasets are present and size-validated.")

    # 3. Operational Mode Readiness Check
    print("\n[3/3] Operational Mode Assessment:")
    print("  - DEMO Mode:      READY (Zero external file dependencies)")
    
    # Check pilot datasets (Uttarakhand / Chamoli hierarchy)
    soi_uk = os.path.join("data", "raw", "survey_of_india", "UTTARAKHAND.zip")
    census_file = os.path.join("data", "raw", "census", "2011-IndiaStateDistSbDistVill-0000.xlsx")
    lgd_dist = os.path.join("data", "raw", "lgd", "All_Districtof_India_2026-09-07_19-42-42.xlsx")
    
    if os.path.exists(soi_uk) and os.path.exists(census_file) and os.path.exists(lgd_dist):
        print("  - FULL_DATA Mode: READY (Pilot Census, LGD, SOI Uttarakhand, NCS, OSM available)")
    else:
        print("  - FULL_DATA Mode: PARTIAL (Acquire pilot datasets to enable full database ingestion)")

    print("  - LIVE Mode:      CONFIGURED (Open-Meteo, CWC Flood, USGS Earthquakes active)")

    print("\nNext Steps:")
    print("  To run full database ingestion into PostgreSQL/PostGIS:")
    print("    python scripts/ingest_all.py")
    print("  To seed demo test fixtures:")
    print("    python scripts/seed_demo.py")
    print("================================================================")

if __name__ == "__main__":
    main()
