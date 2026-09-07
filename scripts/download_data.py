"""
Automated downloader & manual acquisition guide for RakshakGIS datasets.
Reads data/manifests/dataset_manifest.json and handles downloading automatable datasets
or outputting step-by-step acquisition instructions for portal-restricted sources.
"""

import argparse
import json
import os
import sys
import urllib.request

MANIFEST_PATH = os.path.join("data", "manifests", "dataset_manifest.json")

def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        print(f"[ERROR] Manifest not found: {MANIFEST_PATH}")
        sys.exit(1)
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def download_file(url: str, dest_path: str):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    print(f"Downloading {url} -> {dest_path}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"[SUCCESS] Downloaded to {dest_path}")
        return True
    except Exception as e:
        print(f"[FAILED] Could not download {url}: {e}")
        return False

def run_download(dataset_id: str = None, check_only: bool = False, force: bool = False):
    manifest = load_manifest()
    datasets = manifest.get("datasets", [])

    print("=== RakshakGIS Dataset Acquisition Manager ===")
    
    for ds in datasets:
        ds_id = ds["dataset_id"]
        if dataset_id and ds_id != dataset_id:
            continue

        name = ds["name"]
        source_type = ds.get("source_type", "static")
        local_path = ds.get("local_expected_path", "")
        download_url = ds.get("download_url", "")
        instructions = ds.get("manual_acquisition_instructions", "")

        if source_type in ["live", "deferred_manual"]:
            print(f"\n[{ds_id}] ({name})")
            print(f"  Mode: {source_type}")
            print(f"  Endpoint: {download_url}")
            print(f"  Notes: {instructions}")
            continue

        file_exists = os.path.exists(local_path)
        print(f"\n[{ds_id}] ({name})")
        print(f"  Expected Path: {local_path}")
        print(f"  Status: {'PRESENT' if file_exists else 'MISSING'}")

        if file_exists and not force:
            print("  -> File is already present. Skipping download.")
            continue

        if check_only:
            continue

        # If download URL is a direct downloadable binary/archive (e.g. Geofabrik)
        if download_url and (download_url.endswith(".pbf") or download_url.endswith(".zip") or download_url.endswith(".csv")):
            print(f"  Direct download available: {download_url}")
            download_file(download_url, local_path)
        else:
            print("  Manual portal acquisition required:")
            print(f"  Official Source: {download_url}")
            print(f"  Instructions:    {instructions}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Acquire RakshakGIS datasets")
    parser.add_argument("--dataset", type=str, help="Specific dataset ID to acquire")
    parser.add_argument("--check-only", action="store_true", help="Check status without downloading")
    parser.add_argument("--force", action="store_true", help="Force redownload even if file exists")
    args = parser.parse_args()

    run_download(dataset_id=args.dataset, check_only=args.check_only, force=args.force)
