# CLAUDE.md — Elli Charger HA Integration

## Project Overview
This is a Home Assistant custom integration for Elli charging stations (wallboxes). It is distributed via HACS and relies on the `elli-client` Python package for API communication.

## Code Quality
- Always check Python code with:
-- `ruff check .` — linting
-- `mypy custom_components/` — static type checking
- Fix all reported issues before considering a change complete.
- Always check for latest releases of required packages

## Architecture
- `custom_components/elli_charger_ha/__init__.py` — integration setup and `ElliDataUpdateCoordinator` (5-minute polling, token refresh)
- `sensor.py` — four sensor entities inheriting from `ElliBaseSensor`
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

## Commit & Release Conventions
Releases are fully automated via Semantic Release triggered on pushes to `main`. Follow Conventional Commits exactly:
- `feat: ...` → minor version bump (new feature)
- `fix: ...` → patch version bump (bug fix)
- `perf: ...` / `revert: ...` → patch version bump
- `docs:`, `chore:`, `style:`, `test:`, `build:`, `ci:` → no release
- Breaking change: add `BREAKING CHANGE:` footer or `!` after type (e.g. `feat!:`) → major bump

Do **not** manually edit `manifest.json` version — Semantic Release updates it automatically.

## No Test Suite
There is no automated test suite. Validate changes by loading the integration in a live or dev Home Assistant instance.

## Key External Dependency
`elli-client` (PyPI) handles all HTTP communication with the Elli API. Avoid reimplementing API logic; extend or wrap the client instead.

## What to Avoid
- Do not add backwards-compatibility shims or re-exports for removed code
- Do not create helpers or abstractions for one-off operations
- Do not add speculative features or configurability beyond what is asked
- Do not skip pre-commit hooks or force-push to `main`
