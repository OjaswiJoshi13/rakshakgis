"""Regional scope resolution and geographic utilities for RakshakGIS."""

from app.core.regions.resolver import (
    RegionScope,
    resolve_region_scope,
    apply_region_scope_to_village_query,
)

__all__ = [
    "RegionScope",
    "resolve_region_scope",
    "apply_region_scope_to_village_query",
]
