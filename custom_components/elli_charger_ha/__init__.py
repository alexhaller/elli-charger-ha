"""The Elli Charger integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from elli_client import ElliAPIClient

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

UPDATE_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elli Charger from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = ElliAPIClient()

    try:
        await hass.async_add_executor_job(
            client.login,
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )
    except ValueError as err:
        if "401" in str(err) or "authorization code" in str(err).lower():
            raise ConfigEntryAuthFailed("Invalid credentials") from err
        raise ConfigEntryNotReady("Could not connect to Elli API") from err
    except Exception as err:
        raise ConfigEntryNotReady("Could not connect to Elli API") from err

    coordinator = ElliDataUpdateCoordinator(hass, client, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        try:
            coordinator.client.close()
        except Exception:
            _LOGGER.warning("Error closing Elli API client during unload", exc_info=True)

    return unload_ok


class ElliDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Elli data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ElliAPIClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self._entry = entry

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint."""
        try:
            sessions = await self.hass.async_add_executor_job(
                self.client.get_charging_sessions
            )
            stations = await self.hass.async_add_executor_job(
                self.client.get_stations
            )
            await self._merge_firmware_info(stations)
            return {"sessions": sessions, "stations": stations}
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _merge_firmware_info(self, stations: list) -> None:
        """Fetch firmware info and merge it into the station list."""
        try:
            firmware_stations = await self.hass.async_add_executor_job(
                self.client.get_firmware_info
            )
            firmware_map = {
                s.id: s.installed_firmware
                for s in firmware_stations
                if s.installed_firmware
            }
            for station in stations:
                if station.id in firmware_map:
                    station.installed_firmware = firmware_map[station.id]
                    station.firmware_version = firmware_map[station.id].version
        except Exception as fw_err:
            _LOGGER.warning("Could not fetch firmware info: %s", fw_err)
