"""Deterministic region profile registry and resolver for RakshakGIS."""

import threading
from typing import Dict, List, Optional, Union

from app.core.exceptions import NotFoundError
from app.core.profiles.coastal import COASTAL_TEMPLATE_PROFILE
from app.core.profiles.himalayan import HIMALAYAN_PILOT_PROFILE
from app.core.profiles.models import RegionProfile, RegionProfileId
from app.core.profiles.riverine import RIVERINE_TEMPLATE_PROFILE
from app.core.profiles.validation import validate_profile


class UnknownRegionProfileError(NotFoundError):
    """Raised when an unrecognized region profile identifier is requested."""

    default_code = "UNKNOWN_REGION_PROFILE"
    default_status_code = 404

    def __init__(self, identifier: str, available_profiles: Optional[List[str]] = None) -> None:
        self.identifier = identifier
        self.available_profiles = available_profiles or []
        available_str = (
            f" Available profiles: {', '.join(self.available_profiles)}."
            if self.available_profiles
            else ""
        )
        super().__init__(
            message=f"Region profile '{identifier}' not found.{available_str}",
            code=self.default_code,
            details={"requested_profile": identifier, "available_profiles": self.available_profiles},
        )


class RegionProfileRegistry:
    """Thread-safe, deterministic registry and resolver for regional configuration profiles."""

    def __init__(self, load_defaults: bool = True) -> None:
        self._lock = threading.Lock()
        self._profiles: Dict[str, RegionProfile] = {}
        if load_defaults:
            self._load_canonical_defaults()

    def _load_canonical_defaults(self) -> None:
        """Register canonical specification profiles deterministically."""
        validate_profile(HIMALAYAN_PILOT_PROFILE)
        self._profiles[HIMALAYAN_PILOT_PROFILE.id] = HIMALAYAN_PILOT_PROFILE

        validate_profile(RIVERINE_TEMPLATE_PROFILE)
        self._profiles[RIVERINE_TEMPLATE_PROFILE.id] = RIVERINE_TEMPLATE_PROFILE

        validate_profile(COASTAL_TEMPLATE_PROFILE)
        self._profiles[COASTAL_TEMPLATE_PROFILE.id] = COASTAL_TEMPLATE_PROFILE

    def register(self, profile: RegionProfile, overwrite: bool = False) -> None:
        """Validate and register a new or updated regional profile.

        Args:
            profile: The immutable RegionProfile instance to register.
            overwrite: If True, allow replacing an existing profile with the same ID.

        Raises:
            ValueError: If profile ID exists and overwrite is False.
            ProfileValidationError: If the profile fails deterministic validation.
        """
        validate_profile(profile)
        profile_id = profile.id
        with self._lock:
            if not overwrite and profile_id in self._profiles:
                raise ValueError(
                    f"Profile with identifier '{profile_id}' already registered. "
                    "Use overwrite=True to replace."
                )
            self._profiles[profile_id] = profile

    def get(self, identifier: Union[RegionProfileId, str]) -> RegionProfile:
        """Resolve a regional profile by stable identifier or enum.

        Args:
            identifier: RegionProfileId enum or string key.

        Returns:
            The resolved immutable RegionProfile.

        Raises:
            UnknownRegionProfileError: If the identifier is not registered.
        """
        key = (
            identifier.value
            if isinstance(identifier, RegionProfileId)
            else str(identifier).strip().lower()
        )
        with self._lock:
            profile = self._profiles.get(key)
            if profile is None:
                raise UnknownRegionProfileError(
                    identifier=key,
                    available_profiles=sorted(self._profiles.keys()),
                )
            return profile

    def list_profiles(self) -> List[RegionProfile]:
        """Return all registered profiles sorted deterministically by profile ID."""
        with self._lock:
            return [self._profiles[k] for k in sorted(self._profiles.keys())]

    def list_profile_ids(self) -> List[str]:
        """Return all registered profile identifiers in deterministic sorted order."""
        with self._lock:
            return sorted(self._profiles.keys())

    def has_profile(self, identifier: Union[RegionProfileId, str]) -> bool:
        """Check whether a profile identifier is registered."""
        key = (
            identifier.value
            if isinstance(identifier, RegionProfileId)
            else str(identifier).strip().lower()
        )
        with self._lock:
            return key in self._profiles

    def count(self) -> int:
        """Return the count of currently registered profiles."""
        with self._lock:
            return len(self._profiles)


_GLOBAL_REGISTRY = RegionProfileRegistry()


def get_profile(identifier: Union[RegionProfileId, str]) -> RegionProfile:
    """Convenience accessor to resolve a profile from the default global registry."""
    return _GLOBAL_REGISTRY.get(identifier)


def list_profiles() -> List[RegionProfile]:
    """Convenience accessor to list all profiles from the default global registry."""
    return _GLOBAL_REGISTRY.list_profiles()


def list_profile_ids() -> List[str]:
    """Convenience accessor to list all profile IDs from the default global registry."""
    return _GLOBAL_REGISTRY.list_profile_ids()


def register_profile(profile: RegionProfile, overwrite: bool = False) -> None:
    """Convenience accessor to register a profile with the default global registry."""
    _GLOBAL_REGISTRY.register(profile, overwrite=overwrite)
