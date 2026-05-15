"""Yeedi device capability profiles.

Exports ``YEEDI_DEVICES`` — a mapping of Yeedi device class strings to
``StaticDeviceInfo`` objects — and ``register_yeedi_devices()``, which
tries to inject those profiles into the deebot_client hardware registry if
the registry module is present.

Two-path design
---------------
1. **deebot_client with hardware.deebot** — ``register_yeedi_devices()``
   injects into ``DEVICES`` before ``get_devices()`` is called.
2. **deebot_client without hardware.deebot** — no-op here; the controller
   rescues the device from ``devices.not_supported`` directly using
   ``YEEDI_DEVICES``.
"""

from __future__ import annotations

import logging

from deebot_client.capabilities import (
    Capabilities,
    CapabilityClean,
    CapabilityCleanAction,
    CapabilityCustomCommand,
    CapabilityEvent,
    CapabilityExecute,
    CapabilityLifeSpan,
    CapabilityMap,
    CapabilitySet,
    CapabilitySetEnable,
    CapabilitySettings,
    CapabilitySetTypes,
    CapabilityStats,
    CapabilityWater,
    DeviceType,
)
from deebot_client.commands.json.advanced_mode import GetAdvancedMode, SetAdvancedMode
from deebot_client.commands.json.battery import GetBattery
from deebot_client.commands.json.carpet import (
    GetCarpetAutoFanBoost,
    SetCarpetAutoFanBoost,
)
from deebot_client.commands.json.charge import Charge
from deebot_client.commands.json.charge_state import GetChargeState
from deebot_client.commands.json.clean import Clean, CleanArea, GetCleanInfo
from deebot_client.commands.json.clean_logs import GetCleanLogs
from deebot_client.commands.json.continuous_cleaning import (
    GetContinuousCleaning,
    SetContinuousCleaning,
)
from deebot_client.commands.json.custom import CustomCommand
from deebot_client.commands.json.error import GetError
from deebot_client.commands.json.fan_speed import GetFanSpeed, SetFanSpeed
from deebot_client.commands.json.life_span import GetLifeSpan, ResetLifeSpan
from deebot_client.commands.json.map import (
    GetMajorMap,
    GetMinorMap,
    GetMapSet,
)
from deebot_client.commands.json.multimap_state import (
    GetMultimapState,
    SetMultimapState,
)
from deebot_client.commands.json.network import GetNetInfo
from deebot_client.commands.json.play_sound import PlaySound
from deebot_client.commands.json.pos import GetPos
from deebot_client.commands.json.relocation import SetRelocationState
from deebot_client.commands.json.stats import GetStats, GetTotalStats
from deebot_client.commands.json.volume import GetVolume, SetVolume
from deebot_client.commands.json.water_info import GetWaterInfo, SetWaterInfo
from deebot_client.const import DataType
from deebot_client.events import (
    AdvancedModeEvent,
    AvailabilityEvent,
    BatteryEvent,
    CarpetAutoFanBoostEvent,
    CleanLogEvent,
    ContinuousCleaningEvent,
    CustomCommandEvent,
    ErrorEvent,
    FanSpeedEvent,
    FanSpeedLevel,
    LifeSpan,
    LifeSpanEvent,
    MajorMapEvent,
    MapChangedEvent,
    MapTraceEvent,
    MultimapStateEvent,
    OtaEvent,
    PositionsEvent,
    ReportStatsEvent,
    RoomsEvent,
    StateEvent,
    StatsEvent,
    TotalStatsEvent,
    VolumeEvent,
    water_info,
)
from deebot_client.commands.json.ota import GetOta
from deebot_client.events.map import CachedMapInfoEvent
from deebot_client.events.network import NetworkInfoEvent
from deebot_client.models import StaticDeviceInfo

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Capability factory
# ---------------------------------------------------------------------------

def _build_yeedi_vac_station_capabilities() -> Capabilities:
    """Build Capabilities for the Yeedi Vac Station (class mnx7f4).

    Commands removed because this robot does not respond to them:
      - GetCleanCount / GetCleanPreference  → count/preference set to None
      - GetCachedMapInfo                    → cached_info/rooms use get=[]
      - GetMapTrace                         → trace uses get=[]

    All three map commands that need runtime arguments use CapabilityExecute
    so deebot_client constructs them on-demand rather than polling on startup:
      - minor  → CapabilityExecute(GetMinorMap)  called as GetMinorMap(idx, map_id)
      - set    → CapabilityExecute(GetMapSet)    called as GetMapSet(...) at runtime
    """
    return Capabilities(
        device_type=DeviceType.VACUUM,

        availability=CapabilityEvent(
            AvailabilityEvent, [GetBattery(is_available_check=True)]
        ),
        battery=CapabilityEvent(BatteryEvent, [GetBattery()]),
        charge=CapabilityExecute(Charge),

        clean=CapabilityClean(
            action=CapabilityCleanAction(command=Clean, area=CleanArea),
            continuous=CapabilitySetEnable(
                ContinuousCleaningEvent,
                [GetContinuousCleaning()],
                SetContinuousCleaning,
            ),
            # count / preference omitted — robot returns no response for these
            log=CapabilityEvent(CleanLogEvent, [GetCleanLogs()]),
        ),

        custom=CapabilityCustomCommand(
            event=CustomCommandEvent,
            get=[],
            set=CustomCommand,
        ),

        error=CapabilityEvent(ErrorEvent, [GetError()]),

        fan_speed=CapabilitySetTypes(
            event=FanSpeedEvent,
            get=[GetFanSpeed()],
            set=SetFanSpeed,
            types=(
                FanSpeedLevel.QUIET,
                FanSpeedLevel.NORMAL,
                FanSpeedLevel.MAX,
                FanSpeedLevel.MAX_PLUS,
            ),
        ),

        life_span=CapabilityLifeSpan(
            types=(
                LifeSpan.BRUSH,
                LifeSpan.FILTER,
                LifeSpan.SIDE_BRUSH,
            ),
            event=LifeSpanEvent,
            get=[
                GetLifeSpan(
                    [
                        LifeSpan.BRUSH,
                        LifeSpan.FILTER,
                        LifeSpan.SIDE_BRUSH,
                    ]
                )
            ],
            reset=ResetLifeSpan,
        ),

        map=CapabilityMap(
            # cached_info / rooms: robot pushes these, polling not supported
            cached_info=CapabilityEvent(CachedMapInfoEvent, []),
            changed=CapabilityEvent(MapChangedEvent, []),
            major=CapabilityEvent(MajorMapEvent, [GetMajorMap()]),
            # minor / set: need runtime args — CapabilityExecute so deebot_client
            # calls GetMinorMap(idx, map_id) / GetMapSet(...) on demand
            minor=CapabilityExecute(GetMinorMap),
            set=CapabilityExecute(GetMapSet),
            multi_state=CapabilitySetEnable(
                MultimapStateEvent, [GetMultimapState()], SetMultimapState
            ),
            position=CapabilityEvent(PositionsEvent, [GetPos()]),
            relocation=CapabilityExecute(SetRelocationState),
            rooms=CapabilityEvent(RoomsEvent, []),
            # trace: robot pushes trace events, no polling needed
            trace=CapabilityEvent(MapTraceEvent, []),
        ),

        network=CapabilityEvent(NetworkInfoEvent, [GetNetInfo()]),
        play_sound=CapabilityExecute(PlaySound),

        settings=CapabilitySettings(
            advanced_mode=CapabilitySetEnable(
                AdvancedModeEvent, [GetAdvancedMode()], SetAdvancedMode
            ),
            carpet_auto_fan_boost=CapabilitySetEnable(
                CarpetAutoFanBoostEvent,
                [GetCarpetAutoFanBoost()],
                SetCarpetAutoFanBoost,
            ),
            ota=CapabilityEvent(OtaEvent, [GetOta()]),
            volume=CapabilitySet(VolumeEvent, [GetVolume()], SetVolume),
        ),

        state=CapabilityEvent(StateEvent, [GetChargeState(), GetCleanInfo()]),

        stats=CapabilityStats(
            clean=CapabilityEvent(StatsEvent, [GetStats()]),
            report=CapabilityEvent(ReportStatsEvent, []),
            total=CapabilityEvent(TotalStatsEvent, [GetTotalStats()]),
        ),

        water=CapabilityWater(
            amount=CapabilitySetTypes(
                event=water_info.WaterAmountEvent,
                get=[GetWaterInfo()],
                set=SetWaterInfo,
                types=(
                    water_info.WaterAmount.LOW,
                    water_info.WaterAmount.MEDIUM,
                    water_info.WaterAmount.HIGH,
                    water_info.WaterAmount.ULTRAHIGH,
                ),
            ),
            mop_attached=CapabilityEvent(
                water_info.MopAttachedEvent, [GetWaterInfo()]
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

YEEDI_DEVICES: dict[str, StaticDeviceInfo] = {
    "mnx7f4": StaticDeviceInfo(
        DataType.JSON,
        _build_yeedi_vac_station_capabilities(),
    ),
}


def register_yeedi_devices() -> None:
    """Inject Yeedi profiles into the deebot_client hardware registry if available.

    Also installs a log filter to suppress the "not recognized" warning that
    deebot_client.api_client emits for device classes we already handle via
    the not_supported fallback path in the controller.
    """
    # Patch reportStats parser to handle missing 'cid' (Yeedi protocol quirk).
    # Yeedi sends {'type': 'auto', 'stop': 0} without a cleaning ID; deebot_client
    # requires 'cid' and raises KeyError before firing the Last job event.
    # We inject a synthetic cid so the event fires correctly.
    try:
        from deebot_client.messages.json.stats import ReportStats as _ReportStats

        _orig = _ReportStats._handle_body_data_dict.__func__

        @classmethod  # type: ignore[misc]
        def _patched(cls, event_bus, data):
            if "cid" not in data:
                data = {**data, "cid": "yeedi_auto"}
            return _orig(cls, event_bus, data)

        _ReportStats._handle_body_data_dict = _patched
        _LOGGER.debug("Patched ReportStats._handle_body_data_dict for Yeedi missing-cid")
    except Exception as exc:
        _LOGGER.warning("Could not patch reportStats parser: %s", exc)

    # Path 1: hardware registry injection (deebot_client with hardware.deebot)
    try:
        from deebot_client.hardware.deebot import DEVICES, _load  # type: ignore[import]
        _load()
        for cls, info in YEEDI_DEVICES.items():
            DEVICES.setdefault(cls, info)
        _LOGGER.debug("Injected Yeedi device(s) into deebot_client registry")
    except (ImportError, ModuleNotFoundError):
        _LOGGER.debug(
            "deebot_client.hardware.deebot not present — "
            "Yeedi devices handled via not_supported fallback in controller"
        )

    # Suppress the "Device class X not recognized" warning for classes we
    # already handle — it fires inside get_devices() before our fallback runs
    # and would otherwise appear as a spurious error in HA logs.
    _suppress_known_yeedi_warnings()


def _suppress_known_yeedi_warnings() -> None:
    """Install log filters for known Yeedi protocol quirks.

    Yeedi robots (class mnx7f4) differ from standard Ecovacs in several ways
    that cause harmless but noisy log entries in deebot_client:

    - api_client    : "Device class not recognized" — handled by fallback path
    - map.background_image : "Invalid 7z compressed data" — empty map cells
    - message       : "Could not parse reportStats" — Yeedi omits the 'cid'
                       field that deebot_client expects in reportStats payloads
    - message       : "Could not parse getMinorMap" / "getMapSubSet" — Yeedi
                       pushes map pieces via MQTT during cleaning instead of
                       responding to poll requests; empty-body responses are
                       expected and harmless
    """
    import logging as _logging

    known = set(YEEDI_DEVICES.keys())

    class _ApiClientFilter(_logging.Filter):
        def filter(self, record: _logging.LogRecord) -> bool:
            if "not recognized" in record.getMessage():
                for cls in known:
                    if cls in record.getMessage():
                        return False
            return True

    class _MapPieceFilter(_logging.Filter):
        def filter(self, record: _logging.LogRecord) -> bool:
            msg = record.getMessage()
            if "Invalid 7z compressed data" in msg and "base64_data:" in msg:
                if msg.endswith("base64_data:") or "base64_data: " not in msg:
                    return False
            return True

    class _MessageFilter(_logging.Filter):
        """Suppress known Yeedi protocol parse errors from deebot_client.message."""
        _SUPPRESSED = (
            # Yeedi reportStats omits 'cid' — deebot_client's stats parser
            # requires it but Yeedi sends {'type': 'auto', 'stop': 0} only
            "Could not parse reportStats",
            # Yeedi pushes minor map pieces during cleaning; polling returns
            # empty body {} which deebot_client cannot parse — harmless
            "Could not parse getMinorMap",
            "Could not parse getMapSubSet",
            # getMapSubSet empty-body handler noise
            'getMapSubSet: {}',
        )

        def filter(self, record: _logging.LogRecord) -> bool:
            msg = record.getMessage()
            for pattern in self._SUPPRESSED:
                if pattern in msg:
                    return False
            return True

    api_logger = _logging.getLogger("deebot_client.api_client")
    if not any(isinstance(f, _ApiClientFilter) for f in api_logger.filters):
        api_logger.addFilter(_ApiClientFilter())

    map_logger = _logging.getLogger("deebot_client.map.background_image")
    if not any(isinstance(f, _MapPieceFilter) for f in map_logger.filters):
        map_logger.addFilter(_MapPieceFilter())

    msg_logger = _logging.getLogger("deebot_client.message")
    if not any(isinstance(f, _MessageFilter) for f in msg_logger.filters):
        msg_logger.addFilter(_MessageFilter())

    _LOGGER.debug("Installed log filters for known Yeedi protocol quirks")
