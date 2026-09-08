"""Semantic region resolution and query scoping for RakshakGIS.

Resolves configured regional identifiers (e.g. 'himalayan_pilot', 'chamoli')
and database region codes ('uttarakhand_himalayan', 'UTTARAKHAND') to strict
database region and district scopes without accidental cross-region leakage.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set
from sqlalchemy.orm import Query, Session

from app.models.geographic import Block, District, Region, Village


@dataclass(frozen=True)
class RegionScope:
    """Resolved geographic scope for filtering administrative and spatial queries."""

    identifier: str
    region_ids: List[int] = field(default_factory=list)
    district_ids: List[int] = field(default_factory=list)
    is_empty: bool = False


# Canonical pilot aliases mapping to Himalayan / Chamoli operational scope
HIMALAYAN_PILOT_ALIASES: Set[str] = {
    "himalayan_pilot",
    "pilot_chamoli",
    "chamoli",
    "uttarakhand",
    "uttarakhand_himalayan",
}


def resolve_region_scope(db: Session, region_id: Optional[str]) -> Optional[RegionScope]:
    """Resolve a raw region identifier into a typed RegionScope.

    Args:
        db: Active SQLAlchemy database session.
        region_id: Raw string identifier, numeric ID, or None.

    Returns:
        None if region_id is None or empty (caller should not filter).
        RegionScope with matched region_ids and district_ids.
        RegionScope(is_empty=True) if identifier is unrecognized or has no data.
    """
    if region_id is None:
        return None

    clean_id = region_id.strip()
    if not clean_id:
        return None

    # 1. Numeric Region ID (e.g. "2" or "4")
    if clean_id.isdigit():
        r_id = int(clean_id)
        reg = db.query(Region).filter(Region.id == r_id).first()
        if not reg:
            return RegionScope(identifier=clean_id, is_empty=True)
        dist_ids = [d.id for d in db.query(District.id).filter(District.region_id == r_id).all()]
        return RegionScope(
            identifier=clean_id,
            region_ids=[r_id],
            district_ids=dist_ids,
            is_empty=len(dist_ids) == 0,
        )

    clean_lower = clean_id.lower()

    # 2. Configured Himalayan Pilot Alias (e.g. 'himalayan_pilot')
    if clean_lower in HIMALAYAN_PILOT_ALIASES:
        # Resolve all pilot regions and Chamoli district records
        pilot_regs = (
            db.query(Region)
            .filter(
                (Region.code.in_(["uttarakhand_himalayan", "UTTARAKHAND", "himalayan_pilot"]))
                | (Region.state.ilike("%uttarakhand%"))
            )
            .all()
        )
        reg_ids = [r.id for r in pilot_regs]

        dist_records = (
            db.query(District)
            .filter(
                (District.region_id.in_(reg_ids))
                | (District.name.ilike("%chamoli%"))
                | (District.code.ilike("%chamoli%"))
            )
            .all()
        )
        dist_ids = [d.id for d in dist_records]

        return RegionScope(
            identifier=clean_id,
            region_ids=reg_ids,
            district_ids=dist_ids,
            is_empty=len(dist_ids) == 0,
        )

    # 3. Direct Region Code Match (e.g. custom region registered in DB)
    direct_reg = (
        db.query(Region)
        .filter(Region.code == clean_id)
        .first()
    )
    if direct_reg:
        dist_ids = [
            d.id for d in db.query(District.id).filter(District.region_id == direct_reg.id).all()
        ]
        return RegionScope(
            identifier=clean_id,
            region_ids=[direct_reg.id],
            district_ids=dist_ids,
            is_empty=len(dist_ids) == 0,
        )

    # 4. Direct District Name / Code Match (e.g. specific district query)
    direct_dist = (
        db.query(District)
        .filter((District.name.ilike(clean_id)) | (District.code.ilike(clean_id)))
        .all()
    )
    if direct_dist:
        d_ids = [d.id for d in direct_dist]
        r_ids = list(set(d.region_id for d in direct_dist if d.region_id))
        return RegionScope(
            identifier=clean_id,
            region_ids=r_ids,
            district_ids=d_ids,
            is_empty=False,
        )

    # 5. Unrecognized identifier -> Return empty scope (prevents accidental data leak)
    return RegionScope(identifier=clean_id, is_empty=True)


def apply_region_scope_to_village_query(
    query: Query, scope: Optional[RegionScope], is_boundary: bool = False
) -> Query:
    """Apply RegionScope filtering to an existing Village SQLAlchemy query.

    Args:
        query: Base Village query.
        scope: Resolved RegionScope (or None).
        is_boundary: If True, ensures boundary is NOT None.

    Returns:
        Scoped query.
    """
    if is_boundary:
        query = query.filter(Village.boundary != None)

    if scope is None:
        return query

    if scope.is_empty:
        # Guarantee 0 records returned
        return query.filter(Village.id == -1)

    # Filter by resolved district IDs through Block
    return (
        query.join(Village.block)
        .join(Block.district)
        .filter(District.id.in_(scope.district_ids))
    )
