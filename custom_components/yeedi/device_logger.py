"""Logs Ecovacs device states to JSON."""

import json
import logging
from datetime import datetime
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

LOG_FILE = Path("/config/ecovacs_device_log.json")

async def log_device_state(device):
    """Poll a device and save its state to JSON."""
    try:
        # Access info via device.vacuum dict
        device_info = getattr(device, "vacuum", {})
        device_id = device_info.get("did", "unknown_id")
        device_name = device_info.get("nick", device_info.get("deviceName", "Unknown"))

        # You might want other keys if available
        state = {
            "status": device_info.get("status"),
            "battery": device_info.get("battery"),
            "cleaning_mode": device_info.get("mode"),
        }

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "device_id": device_id,
            "name": device_name,
            "state": state,
        }

        if LOG_FILE.exists():
            data = json.loads(LOG_FILE.read_text())
        else:
            data = []

        data.append(entry)
        LOG_FILE.write_text(json.dumps(data, indent=2))

        _LOGGER.info("Logged state for device '%s'", device_name)

    except Exception as e:
        # Fallback for logging
        _LOGGER.error("Error logging device state for device_id '%s': %s", device_id, e)