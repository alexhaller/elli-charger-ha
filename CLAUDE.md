# CLAUDE.md — Elli Charger HA Integration

## Project Overview
See Readme.md

## Code Quality
- Always check Python code with:
-- `ruff check .` — linting
-- `mypy custom_components/` — static type checking
- Fix all reported issues before considering a change complete.
- Always check for latest releases of required packages
- Keep in sync with latest changes, best practices and patterns of Home Assistant and HACS

## Architecture
- `custom_components/elli_charger_ha/__init__.py` — integration setup and `ElliDataUpdateCoordinator`
- `sensor.py` — sensor entities inheriting from `ElliBaseSensor`
- `config_flow.py` — UI-based config and re-auth flow
- `const.py` — shared constants
- `strings.json` + `translations/` — English and German i18n

## Code Conventions
- Python only inside `custom_components/`; JS is for release tooling only
- Use `from __future__ import annotations` at the top of every Python file
- Type hints throughout; module-level `_LOGGER = logging.getLogger(__name__)`
- Follow Home Assistant integration patterns: async setup, `DataUpdateCoordinator`, `ConfigFlow`, `EntityDescription`
- Do not add error handling for scenarios that cannot happen; trust HA framework guarantees
- Keep sensors grouped under a single `DeviceInfo` so they appear as one device in HA