"""Application schemas module."""

from app.schemas.alerts import (
    AlertAcknowledgeRequest,
    OperationalAlertRead,
)
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserRead,
)
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMetadata,
    ResponseEnvelope,
)
from app.schemas.red_zones import (
    GeoJSONMultiPolygon,
    RedZoneRead,
)
from app.schemas.villages import (
    VillageDetailRead,
    VillageRead,
)

__all__ = [
    "AlertAcknowledgeRequest",
    "ErrorDetail",
    "ErrorResponse",
    "GeoJSONMultiPolygon",
    "LoginRequest",
    "OperationalAlertRead",
    "PaginatedResponse",
    "PaginationMetadata",
    "RedZoneRead",
    "ResponseEnvelope",
    "TokenResponse",
    "UserRead",
    "VillageDetailRead",
    "VillageRead",
]
