"""The Elli Charger integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant, ServiceCall
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

    coordinator = ElliDataUpdateCoordinator(hass, client, entry.data)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, "download_charging_records"):
        async def handle_download_charging_records(call: ServiceCall) -> None:
            """Download a PDF of charging records and write it to a file."""
            first_coordinator: ElliDataUpdateCoordinator = next(
                iter(hass.data[DOMAIN].values())
            )
            pdf_bytes: bytes = await hass.async_add_executor_job(
                first_coordinator.client.get_charging_records_pdf,
                call.data["station_id"],
                call.data["rfid_card_id"],
                call.data["created_at_after"],
                call.data["created_at_before"],
                call.data.get("pdf_timezone", "Europe/Berlin"),
            )
            output_path: str = call.data.get("output_path", "/config/charging_records.pdf")

            def write_pdf() -> None:
                with open(output_path, "wb") as f:
                    f.write(pdf_bytes)

            await hass.async_add_executor_job(write_pdf)
            _LOGGER.info("Charging records PDF written to %s", output_path)

        hass.services.async_register(
            DOMAIN,
            "download_charging_records",
            handle_download_charging_records,
            schema=vol.Schema({
                vol.Required("station_id"): str,
                vol.Required("rfid_card_id"): str,
                vol.Required("created_at_after"): str,
                vol.Required("created_at_before"): str,
                vol.Optional("pdf_timezone", default="Europe/Berlin"): str,
                vol.Optional("output_path", default="/config/charging_records.pdf"): str,
            }),
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        try:
            coordinator.client.close()
        except Exception:
            _LOGGER.warning("Error closing Elli API client during unload", exc_info=True)

        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "download_charging_records")

    return unload_ok


class ElliDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Elli data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ElliAPIClient,
        config_data: dict,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self._email = config_data[CONF_EMAIL]
        self._password = config_data[CONF_PASSWORD]

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint."""
        try:
            if not self.client.access_token:
                await self.hass.async_add_executor_job(
                    self.client.login, self._email, self._password
                )
            return await self._fetch_data()
        except Exception as err:
            _LOGGER.error("Error communicating with API: %s", err)
            try:
                await self.hass.async_add_executor_job(
                    self.client.login, self._email, self._password
                )
                return await self._fetch_data()
            except Exception as retry_err:
                raise UpdateFailed(f"Error communicating with API: {retry_err}") from retry_err

    async def _fetch_data(self) -> dict:
        """Fetch sessions, stations, RFID cards and accumulated data from the API."""
        sessions = await self.hass.async_add_executor_job(self.client.get_charging_sessions)
        stations = await self.hass.async_add_executor_job(self.client.get_stations)
        await self._merge_firmware_info(stations)

        try:
            rfid_cards = await self.hass.async_add_executor_job(self.client.get_rfid_cards)
        except Exception as err:
            _LOGGER.warning("Could not fetch RFID cards: %s", err)
            rfid_cards = []

        accumulated: dict = {}
        for station in stations:
            try:
                accumulated[station.id] = await self.hass.async_add_executor_job(
                    self.client.get_accumulated_charging, station.id
                )
            except Exception as err:
                _LOGGER.warning("Could not fetch accumulated charging for %s: %s", station.id, err)

        return {"sessions": sessions, "stations": stations, "rfid_cards": rfid_cards, "accumulated": accumulated}

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
