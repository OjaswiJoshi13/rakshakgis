# RakshakGIS Data Validation & Ingestion Pipelines (Chunk M3-04)

This package establishes the validation, canonicalization, and ingestion foundation that bridges raw external provider data (M3-03) and downstream computational risk engines (M3-05 through M4-06).

> [!IMPORTANT]
> **NO RISK LOGIC IN INGESTION**
> The ingestion pipeline performs **only** structural validation, geographic sanity checks, temporal parsing, intra-batch deduplication, and canonicalization. It does **NOT** calculate hazard indices, multi-hazard risk scores, Red Zone triggers, or relocation suitability. Those responsibilities belong strictly to downstream analytical modules.

---

## 1. Pipeline Stages

```text
Provider / Input Data (ProviderResponse[T] or raw records)
                         ↓
Stage 1: Batch & Envelope Validation (provider_id, mode, SourceCategory)
                         ↓
Stage 2: Record Identity & Required Field Validation (record_id / village_id non-empty)
                         ↓
Stage 3: Temporal Validation (ISO-8601 parseable; zero fabricated timestamps)
                         ↓
Stage 4: Geographic Validation (WGS84 lon [-180, 180], lat [-90, 90]; no NaN/inf; zero clamping)
                         ↓
Stage 5: Numerical Domain Validation (no NaN/inf, non-negative bounds, valid zero preserved)
                         ↓
Stage 6: Category / Severity / Enum Validation
                         ↓
Stage 7: Provenance Validation (provider_id, mode, synthetic flag & disclaimer integrity)
                         ↓
Stage 8: Intra-batch Duplicate Detection (first valid record accepted, subsequent duplicates flagged)
                         ↓
Stage 9: Canonicalization (whitespace stripping, coordinate rounding, canonical ISO time, content hash)
                         ↓
IngestionResult Envelope (accepted records, rejected records, issues, counts, deterministic metadata)
```

---

## 2. Validation vs. Normalization Responsibilities

| Responsibility | Handled By | Behavior |
| :--- | :--- | :--- |
| **Validation** | `app.data.ingestion.validators` | Pure validation checks that flag missing fields, corrupt numbers (NaN/Inf), out-of-bounds coordinates, or invalid severities. Failures are captured as typed `ValidationIssue` objects without silently corrupting data or throwing batch-wide fatal aborts. |
| **Normalization / Canonicalization** | `app.data.ingestion.pipeline` | Applied only to valid records. Formats coordinates to canonical floats (6 decimals), standardizes ISO-8601 timestamps, trims whitespace, computes deterministic content hashes, and constructs typed `Canonical*Record` models. |

---

## 3. Duplicate Record Policy

- Record identifiers (`record_id` for observation telemetry, `village_id` for demographic exposure) must be unique within a batch.
- When an identifier is encountered multiple times within a single batch:
  1. The **first** valid occurrence is accepted and canonicalized.
  2. All **subsequent** occurrences are rejected with `ValidationIssueCode.DUPLICATE_RECORD` and captured in `rejected_records`.
- Records are **never** silently overwritten and **never** silently deduplicated without diagnostic reporting.

---

## 4. Partial-Batch Ingestion Behavior

- Ingestion operates in a resilient partial-batch mode: a single malformed or corrupted record (e.g. invalid timestamp or out-of-bounds coordinate) does **not** abort or invalidate other valid records in the batch.
- The pipeline returns a structured `IngestionResult` envelope detailing:
  - `accepted_records`: List of valid canonical records ready for downstream processing.
  - `rejected_records`: List of rejected records detailing the original index, non-PII summary, and specific `ValidationIssue` reasons.
  - `total_input_count`, `accepted_count`, and `rejected_count`.

---

## 5. Determinism & Metadata

- **Zero Nondeterminism**: Ingestion does not make network calls, generate random numbers, or rely on system clocks for batch identities or content hashes.
- **Deterministic Batch ID**: Derived via a SHA-256 hash of the provider identity, category, and record identifiers (`BATCH-<12-hex>`).
- **Deterministic Timestamp**: If not explicitly passed, `processed_at` is derived from the latest `observed_at` among accepted records, or a fixed ISO epoch default.
- **Deterministic Output Sorting**: Accepted records are sorted by `(observed_at, record_id)` or `village_id`.

---

## 6. Mock vs. Future Live Data Provenance

- All mock adapter feeds (Chunk M3-03) must have `mode: ProviderMode.MOCK` and `is_synthetic: True`.
- Attempts to ingest mock data with `is_synthetic: False` are flagged with `ValidationIssueCode.INVALID_PROVENANCE`.
- Disclaimers and legal notices (`SYNTHETIC_DISCLAIMER`) are strictly preserved across envelopes and individual canonical records.

---

## 7. Rainfall Metadata & Exceedance Flags

As established in Chunk M3-03, the IMD rainfall thresholds (`is_heavy_rain >= 64.5 mm`, `is_very_heavy_rain >= 115.5 mm`) operate with cumulative exceedance semantics. The ingestion pipeline preserves these flags as descriptive observation metadata without altering their semantics or computing risk scores.
