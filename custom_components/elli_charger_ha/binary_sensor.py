"""Support for Elli Charger binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import ElliBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elli Charger binary sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    if coordinator.data and (stations := coordinator.data.get("stations")):
        for station in stations:
            station_id = station.id
            entities.append(ElliChargingBinarySensor(coordinator, station_id, entry.entry_id))
            entities.append(ElliConnectedBinarySensor(coordinator, station_id, entry.entry_id))

    async_add_entities(entities)


class ElliBaseBinarySensor(ElliBaseEntity, BinarySensorEntity):
    """Base class for Elli Charger binary sensors."""


class ElliChargingBinarySensor(ElliBaseBinarySensor):
    """Binary sensor that is on when the wallbox is actively charging."""

    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
    _attr_icon = "mdi:ev-station"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}_charging"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        label = station.name if station else self._station_id
        return f"Elli Wallbox {label} Charging"

    @property
    def is_on(self) -> bool:
        """Return True when the wallbox is actively charging."""
        return self._is_charging()


class ElliConnectedBinarySensor(ElliBaseBinarySensor):
    """Binary sensor that is on when a car is connected to the wallbox."""

    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_icon = "mdi:ev-plug-type2"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}_connected"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        label = station.name if station else self._station_id
        return f"Elli Wallbox {label} Connected"

    @property
    def is_on(self) -> bool:
        """Return True when a car is connected (charging or idle with active session)."""
        return self._has_active_session()
