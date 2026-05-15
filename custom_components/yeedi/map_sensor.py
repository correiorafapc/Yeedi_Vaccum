from __future__ import annotations
import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from .controller import EcovacsController

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up map sensors for Yeedi/Ecovacs vacuums."""
    controller: EcovacsController = hass.data["ecovacs_test"]["controller"]

    entities = []
    for device_id, device_info in controller.devices.items():
        entities.append(EcovacsMapSensor(controller, device_id, device_info))
    
    async_add_entities(entities)


class EcovacsMapSensor(SensorEntity):
    """Map sensor for a Yeedi/Ecovacs vacuum."""

    def __init__(self, controller: EcovacsController, device_id: str, device_info: dict):
        self.controller = controller
        self.device_id = device_id
        self._name = f"Ecovacs {device_id} Map"
        self._rooms = None
        self._last_map_update = None
        self.device_info_data = device_info

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._last_map_update

    @property
    def extra_state_attributes(self):
        return {
            "rooms": self._rooms
        }

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(self.device_id,)},
            name=self._name,
            manufacturer="Ecovacs/Yeedi",
            model=self.device_info_data.get("class", "Unknown"),
        )

    async def async_update(self):
        """Fetch latest map and rooms from device."""
        device = self.controller.get_device(self.device_id)
        if not device:
            return

        if hasattr(device.capabilities.map, "rooms"):
            rooms_data = await device.capabilities.map.rooms.get_value()
            self._rooms = [room["name"] for room in rooms_data] if rooms_data else []

        if hasattr(device.capabilities.map, "major"):
            map_data = await device.capabilities.map.major.get_value()
            self._last_map_update = datetime.fromtimestamp(map_data["timestamp"]) if map_data else None