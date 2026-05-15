# Yeedi Vacuum for Home Assistant

Custom integration for Yeedi vacuum robots using the Ecovacs cloud. For now I just added my Yeedi vaccum and it is working fine. Need more test.

## Supported Devices
- Yeedi Vac Station (mnx7f4)

## Installation

### Via HACS
1. Add this repo as a custom repository in HACS
2. Search for "Yeedi Vaccum" and install
3. Restart Home Assistant
4. Go to Settings → Integrations → Add → Yeedi Vacuum

### Manual
Copy `custom_components/yeedi_vaccum/` to your HA `config/custom_components/` folder.

## Requirements
- Home Assistant 2026.5+
- deebot-client 18.3.0
- Yeedi account (migrate device to Ecovacs account first). This is the key for the application works. You need to unbind the robot from yeedi account and add at Ecovacs. After you will register the robot will not appear at the application, but you can control by HA using this integration.
