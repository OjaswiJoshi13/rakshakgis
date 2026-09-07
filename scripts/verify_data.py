"""
Verify integrity and presence of all datasets registered in data/manifests/dataset_manifest.json.
Calculates SHA-256 hashes for existing raw files and verifies against official recorded checksums.
"""

import hashlib
import json
import os
import sys

MANIFEST_PATH = os.path.join("data", "manifests", "dataset_manifest.json")

def compute_sha256(filepath: str, block_size: int = 65536) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            sha.update(chunk)
    return sha.hexdigest()

def verify_all_datasets(quick: bool = False):
    if not os.path.exists(MANIFEST_PATH):
        print(f"[ERROR] Manifest file not found: {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    datasets = manifest.get("datasets", [])
    print(f"=== RakshakGIS Dataset Verification (Total: {len(datasets)}) ===")
    
    verified_count = 0
    missing_count = 0
    mismatch_count = 0
    skipped_count = 0

    for ds in datasets:
        ds_id = ds["dataset_id"]
        source_type = ds.get("source_type", "static")
        local_path = ds.get("local_expected_path", "")
        expected_sha = ds.get("sha256")
        expected_size = ds.get("expected_size_bytes")

        # Skip non-static or virtual
        if source_type in ["live", "deferred_manual"]:
            print(f"[INFO] {ds_id:<35} | Type: {source_type:<15} | Live/Portal endpoint")
            skipped_count += 1
            continue

        if not os.path.exists(local_path):
            print(f"[MISSING] {ds_id:<35} | Path: {local_path}")
            missing_count += 1
            continue

        actual_size = os.path.getsize(local_path)
        if expected_size and actual_size != expected_size:
            print(f"[SIZE MISMATCH] {ds_id:<35} | Expected: {expected_size} bytes, Actual: {actual_size} bytes")
            mismatch_count += 1
            continue

        if quick or not expected_sha:
            print(f"[OK-SIZE] {ds_id:<35} | Size: {actual_size:,} bytes")
            verified_count += 1
            continue

        actual_sha = compute_sha256(local_path)
        if actual_sha.lower() == expected_sha.lower():
            print(f"[VERIFIED] {ds_id:<35} | SHA256: {actual_sha[:16]}... OK")
            verified_count += 1
        else:
            print(f"[CORRUPT] {ds_id:<35} | Expected SHA: {expected_sha[:16]}..., Actual: {actual_sha[:16]}...")
            mismatch_count += 1

    print("\n--- Summary ---")
    print(f"Verified files: {verified_count}")
    print(f"Missing files:  {missing_count}")
    print(f"Mismatches:     {mismatch_count}")
    print(f"Live / Portal:  {skipped_count}")

    if missing_count > 0 or mismatch_count > 0:
        return False
    return True

if __name__ == "__main__":
    quick_mode = "--quick" in sys.argv
    success = verify_all_datasets(quick=quick_mode)
    sys.exit(0 if success else 1)
