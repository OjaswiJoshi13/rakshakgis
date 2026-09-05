"""Exception hierarchy for the telemetry and data source freshness subsystem."""

from typing import Optional


class TelemetryError(Exception):
    """Base exception for all telemetry and data source freshness operations."""

    def __init__(self, message: str, source_id: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.source_id = source_id

    def __str__(self) -> str:
        if self.source_id:
            return f"[{self.source_id}] {self.message}"
        return self.message


class DataSourceNotFoundError(TelemetryError):
    """Raised when a requested data source cannot be found by ID or provider key."""

    pass


class InvalidTimestampError(TelemetryError):
    """Raised when an ingestion or observation timestamp is malformed, unparseable, or invalid."""

    pass


class TelemetryConfigError(TelemetryError):
    """Raised when telemetry thresholds or configuration parameters are invalid."""

    pass
