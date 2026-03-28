# Elli Charger Integration for Home Assistant

## Description

Home Assistant integration for Elli charging stations (wallboxes). Monitor your charging sessions and station status directly in Home Assistant.
This integration uses the [elli-client](https://pypi.org/project/elli-client/) Python package for communication with the Elli API.

## Features

- Real-time charging session monitoring
- Energy consumption tracking (kWh)
- Current charging power (Watts)
- Station status and information
- Automatic token refresh
- Easy configuration through UI

## HACS Installation

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add the repository URL: `https://github.com/alexhaller/elli-charger-ha`
6. Select category: "Integration"
7. Click "Add"
8. Find "Elli Charger" in the integration list
9. Click "Download"
10. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Elli Charger"
4. Enter your Elli account credentials:
   - Email
   - Password

## Sensors

The integration provides the following sensors:

### Station Sensor
- **Name**: `Elli [Station Name]`
- **State**: Connected/Idle
- **Attributes**:
  - Station ID
  - Name
  - Serial Number
  - Model
  - Firmware Version

### Current Session Energy
- **Name**: `Elli Current Session Energy`
- **Unit**: kWh
- **Device Class**: Energy
- **Attributes**:
  - Session ID
  - Station ID
  - Start Time
  - End Time (if completed)
  - Status

### Current Session Power
- **Name**: `Elli Current Session Power`
- **Unit**: W
- **Device Class**: Power
- **Attributes**:
  - Session ID
  - Station ID
  - Status

## Support

- [Report Issues](https://github.com/alexhaller/elli-charger-ha/issues)
- [Feature Requests](https://github.com/alexhaller/elli-charger-ha/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Disclaimer

This integration is not officially supported by Elli or Volkswagen Group Charging GmbH. Use at your own risk.
