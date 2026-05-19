
# Yeedi Vacuum Integration
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![HACS](https://img.shields.io/badge/HACS-Custom-orange)
![License](https://img.shields.io/badge/license-MIT-green)

Custom Home Assistant integration for Yeedi robot vacuums using the Ecovacs cloud API.

## Features

- Start / stop cleaning
- Return to dock
- Vacuum state monitoring
- Basic device control

## Supported Devices

- Yeedi Vac Station (mnx7f4)

## Installation

### HACS
1. Add this repository as a custom repository in HACS
2. Install the integration
3. Restart Home Assistant

### Manual
Copy the `custom_components/yeedi` folder into your Home Assistant config directory.

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Yeedi Vacuum"
4. Enter your Ecovacs account credentials

## Requirements

- Home Assistant 2026.5+
- deebot-client 18.3.0
- Yeedi device linked to Ecovacs account

## Important Notes

- You must migrate your Yeedi device to an Ecovacs account before using this integration.
- After migration, the device will not appear in the Yeedi app but will be controllable via Home Assistant.

## Disclaimer

This integration is based on Ecovacs cloud APIs and is not officially supported by Yeedi.
