"""Base entity for Elli Charger integration."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN


class ElliBaseEntity(CoordinatorEntity):
    """Shared base for all Elli Charger station entities."""

    def __init__(self, coordinator: DataUpdateCoordinator, station_id: str, entry_id: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._station_id = station_id
        self._entry_id = entry_id

    def _get_station(self):
        """Return the station object for this entity."""
        if not self.coordinator.data:
            return None
        stations = self.coordinator.data.get("stations", [])
        return next((s for s in stations if s.id == self._station_id), None)

    def _get_latest_session(self):
        """Return the latest session for this station."""
        if not self.coordinator.data:
            return None
        sessions = self.coordinator.data.get("sessions", [])
        return next((s for s in sessions if s.station_id == self._station_id), None)

    def _has_active_session(self) -> bool:
        """Return True if the station has an active session."""
        session = self._get_latest_session()
        return bool(session and session.lifecycle_state == "active")

    def _is_charging(self) -> bool:
        """Return True if the station is actively charging."""
        session = self._get_latest_session()
        if not session:
            return False
        if session.charging_state and "charging" in session.charging_state.lower():
            return True
        if session.momentary_charging_speed_watts and session.momentary_charging_speed_watts > 0:
            return True
        return False

    @property
    def available(self) -> bool:
        """Return False if coordinator failed or station is no longer present."""
        return super().available and self._get_station() is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Group entities under the wallbox device."""
        station = self._get_station()
        name = station.name if station else self._station_id
        model = station.model if station else None
        sw_version = station.firmware_version if station else None
        return DeviceInfo(
            identifiers={(DOMAIN, self._station_id)},
            name=f"Elli Wallbox {name}",
            manufacturer="Elli",
            model=model,
            sw_version=sw_version,
        )
