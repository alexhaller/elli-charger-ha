"""Support for Elli Charger sensors."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN
from .entity import ElliBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elli Charger sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    if coordinator.data and (stations := coordinator.data.get("stations")):
        for station in stations:
            station_id = station.id
            entities.append(ElliWallboxSensor(coordinator, station_id, entry.entry_id))
            entities.append(ElliLastSessionSensor(coordinator, station_id, entry.entry_id))
            entities.append(ElliSessionEnergySensor(coordinator, station_id, entry.entry_id))
            entities.append(ElliSessionPowerSensor(coordinator, station_id, entry.entry_id))
            entities.append(ElliAccumulatedChargingSensor(coordinator, station_id, entry.entry_id))
            entities.append(ElliSessionStartSensor(coordinator, station_id, entry.entry_id))
            entities.append(ElliFirmwareSensor(coordinator, station_id, entry.entry_id))

    if coordinator.data and (rfid_cards := coordinator.data.get("rfid_cards")):
        for card in rfid_cards:
            entities.append(ElliRFIDCardSensor(coordinator, card.id, entry.entry_id))

    async_add_entities(entities)


class ElliBaseSensor(ElliBaseEntity, SensorEntity):
    """Base class for Elli Charger sensors."""


class ElliWallboxSensor(ElliBaseSensor):
    """Representation of an Elli Wallbox sensor."""

    _attr_icon = "mdi:ev-station"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        if station:
            return f"Elli Wallbox {station.name}"
        return f"Elli Wallbox {self._station_id}"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self._is_charging():
            return "Charging"
        if self._has_active_session():
            return "Connected"
        return "Idle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        station = self._get_station()
        if not station:
            return {}

        attrs: dict[str, Any] = {
            "station_id": station.id,
            "name": station.name,
        }
        if station.serial_number:
            attrs["serial_number"] = station.serial_number
        if station.model:
            attrs["model"] = station.model
        if station.firmware_version:
            attrs["firmware_version"] = station.firmware_version

        return attrs


class ElliLastSessionSensor(ElliBaseSensor):
    """Representation of an Elli last/current session sensor."""

    _attr_icon = "mdi:ev-plug-type2"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}_last_session"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        if station:
            return f"Elli Wallbox {station.name} Last Session"
        return f"Elli Wallbox {self._station_id} Last Session"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor (charging state)."""
        session = self._get_latest_session()
        if not session:
            return "idle"
        if session.charging_state:
            return session.charging_state
        if session.lifecycle_state:
            return session.lifecycle_state
        return "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        session = self._get_latest_session()
        if not session:
            return {}

        attrs: dict[str, Any] = {
            "session_id": session.id,
            "station_id": session.station_id,
        }

        if session.energy_consumption_wh is not None:
            attrs["session_energy"] = round(session.energy_consumption_wh / 1000, 2)
        if session.momentary_charging_speed_watts is not None:
            attrs["session_power"] = session.momentary_charging_speed_watts

        if session.lifecycle_state:
            attrs["lifecycle_state"] = session.lifecycle_state
        if session.charging_state:
            attrs["charging_state"] = session.charging_state

        if session.authentication_method:
            attrs["authentication_method"] = session.authentication_method
        if session.rfid_card_serial_number:
            attrs["rfid_card"] = session.rfid_card_serial_number
        if session.connector_id:
            attrs["connector_id"] = session.connector_id

        if session.start_date_time:
            attrs["start_time"] = session.start_date_time
        if session.end_date_time:
            attrs["end_time"] = session.end_date_time
        if session.last_updated:
            attrs["last_updated"] = session.last_updated

        return attrs


class ElliSessionEnergySensor(ElliBaseSensor):
    """Representation of an Elli session energy sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:battery-charging"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}_session_energy"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        if station:
            return f"Elli Wallbox {station.name} Session Energy"
        return f"Elli Wallbox {self._station_id} Session Energy"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor (energy in kWh)."""
        session = self._get_latest_session()
        if session and session.energy_consumption_wh is not None:
            return round(session.energy_consumption_wh / 1000, 2)
        return None


class ElliSessionPowerSensor(ElliBaseSensor):
    """Representation of an Elli session power sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_icon = "mdi:lightning-bolt"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}_session_power"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        if station:
            return f"Elli Wallbox {station.name} Session Power"
        return f"Elli Wallbox {self._station_id} Session Power"

    @property
    def native_value(self) -> float | None:
        """Return the current charging power in Watts."""
        session = self._get_latest_session()
        if session and session.momentary_charging_speed_watts is not None:
            return session.momentary_charging_speed_watts
        return None


class ElliAccumulatedChargingSensor(ElliBaseSensor):
    """Lifetime accumulated energy sensor per wallbox."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_icon = "mdi:battery-charging-100"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}_accumulated"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        label = station.name if station else self._station_id
        return f"Elli Wallbox {label} Accumulated Energy"

    def _get_accumulated(self) -> dict | None:
        """Return accumulated charging data for this station."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("accumulated", {}).get(self._station_id)

    @property
    def native_value(self) -> float | None:
        """Return total energy in kWh, trying common API key patterns."""
        data = self._get_accumulated()
        if not data:
            return None
        for key in ("total_energy_kwh", "energy_kwh", "totalEnergyKwh", "total_energy_wh", "energyWh"):
            if key in data:
                val = data[key]
                if "wh" in key.lower() and "kwh" not in key.lower():
                    return round(val / 1000, 2)
                return val
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose full accumulated data so users can inspect available keys."""
        data = self._get_accumulated()
        return dict(data) if data else {}


class ElliSessionStartSensor(ElliBaseSensor):
    """Sensor exposing the session start time as a proper timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-start"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}_session_start"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        label = station.name if station else self._station_id
        return f"Elli Wallbox {label} Session Start"

    @property
    def native_value(self) -> datetime | None:
        """Return the session start time as a timezone-aware datetime."""
        session = self._get_latest_session()
        if not session or not session.start_date_time:
            return None
        try:
            return datetime.fromisoformat(session.start_date_time.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


class ElliFirmwareSensor(ElliBaseSensor):
    """Diagnostic sensor exposing the wallbox firmware version."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:chip"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_wallbox_{self._station_id}_firmware"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        station = self._get_station()
        label = station.name if station else self._station_id
        return f"Elli Wallbox {label} Firmware"

    @property
    def native_value(self) -> str | None:
        """Return the firmware version string."""
        station = self._get_station()
        return station.firmware_version if station else None


class ElliRFIDCardSensor(CoordinatorEntity, SensorEntity):
    """Sensor representing an RFID card linked to the Elli account."""

    _attr_icon = "mdi:card-account-details"

    def __init__(self, coordinator: DataUpdateCoordinator, card_id: str, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._card_id = card_id
        self._entry_id = entry_id

    def _get_card(self):
        """Return the RFID card object."""
        if not self.coordinator.data:
            return None
        cards = self.coordinator.data.get("rfid_cards", [])
        return next((c for c in cards if c.id == self._card_id), None)

    @property
    def available(self) -> bool:
        """Return False if coordinator failed or card is no longer present."""
        return super().available and self._get_card() is not None

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry_id}_rfid_{self._card_id}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        card = self._get_card()
        if card:
            return f"Elli RFID {card.number}"
        return f"Elli RFID {self._card_id}"

    @property
    def native_value(self) -> str | None:
        """Return the card status."""
        card = self._get_card()
        return card.status if card else None

    @property
    def device_info(self) -> DeviceInfo:
        """Group RFID card sensors under an account-level device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="Elli Account",
            manufacturer="Elli",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional card attributes."""
        card = self._get_card()
        if not card:
            return {}
        attrs: dict[str, Any] = {
            "card_id": card.id,
            "number": card.number,
        }
        if card.public_charging is not None:
            attrs["public_charging"] = card.public_charging
        if card.status:
            attrs["status"] = card.status
        if card.created_at:
            attrs["created_at"] = card.created_at
        if card.updated_at:
            attrs["updated_at"] = card.updated_at
        if card.tenant_name:
            attrs["tenant_name"] = card.tenant_name
        return attrs
