"""The proxy vacuum: mirrors the hidden original, but `start` cleans room by room."""

import logging
from typing import Any

from homeassistant.components.vacuum import (
    Segment,
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_SUPPORTED_FEATURES, STATE_UNAVAILABLE
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_START_ROOMS
from .entity_swap import VACUUM_DOMAIN, get_source, get_vacuum_entity, sorted_by_id

_LOGGER = logging.getLogger(__name__)

# `vacuum.start` also means "resume". Only a vacuum that isn't working on anything
# gets the room-by-room run, otherwise a resume would silently restart the job.
_IDLE_ACTIVITIES = {
    VacuumActivity.DOCKED,
    VacuumActivity.IDLE,
    VacuumActivity.RETURNING,
    VacuumActivity.ERROR,
}

# Home Assistant derives these itself, copying them would only clash.
_OWN_ATTRIBUTES = {
    "friendly_name",
    "icon",
    "entity_picture",
    "supported_features",
    "fan_speed",
    "fan_speed_list",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create the proxy for the wrapped vacuum."""
    async_add_entities([MapGuardVacuum(hass, entry)])


class MapGuardVacuum(StateVacuumEntity):
    """Looks like the original and forwards every command to it."""

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        source = get_source(hass, entry)
        self._entry = entry
        self._source_entity_id = source.entity_id
        self._attr_unique_id = entry.entry_id
        self._attr_has_entity_name = source.has_entity_name
        self._attr_name = source.original_name
        # Same device page as the original.
        self.device_entry = dr.async_get(hass).async_get(source.device_id)
        self._attr_available = False

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._source_entity_id], self._handle_source_event
            )
        )
        self._apply_source_state(self.hass.states.get(self._source_entity_id))

    @callback
    def _handle_source_event(self, event: Event[EventStateChangedData]) -> None:
        self._apply_source_state(event.data["new_state"])
        self.async_write_ha_state()

    @callback
    def _apply_source_state(self, state: State | None) -> None:
        """Copy state, features and attributes from the original."""
        self._attr_available = state is not None and state.state != STATE_UNAVAILABLE
        if state is None or not self._attr_available:
            return
        attributes = state.attributes
        try:
            self._attr_activity = VacuumActivity(state.state)
        except ValueError:  # "unknown"
            self._attr_activity = None
        self._attr_supported_features = VacuumEntityFeature(
            attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        )
        self._attr_fan_speed = attributes.get("fan_speed")
        self._attr_fan_speed_list = attributes.get("fan_speed_list", [])
        self._attr_extra_state_attributes = {
            key: value for key, value in attributes.items() if key not in _OWN_ATTRIBUTES
        }

    async def _forward(self, service: str, **data: Any) -> None:
        """Call a vacuum action on the original (never on ourselves)."""
        await self.hass.services.async_call(
            VACUUM_DOMAIN,
            service,
            {ATTR_ENTITY_ID: self._source_entity_id, **data},
            blocking=True,
            context=self._context,
        )

    async def async_stop(self, **kwargs: Any) -> None:
        await self._forward("stop")

    async def async_pause(self) -> None:
        await self._forward("pause")

    async def async_return_to_base(self, **kwargs: Any) -> None:
        await self._forward("return_to_base")

    async def async_locate(self, **kwargs: Any) -> None:
        await self._forward("locate")

    async def async_clean_spot(self, **kwargs: Any) -> None:
        await self._forward("clean_spot")

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        await self._forward("set_fan_speed", fan_speed=fan_speed)

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        data: dict[str, Any] = {"command": command}
        if params is not None:
            data["params"] = params
        await self._forward("send_command", **data)

    async def async_start(self) -> None:
        """Clean room by room, unless this is a resume."""
        if self._attr_activity in _IDLE_ACTIVITIES:
            if segment_ids := await self._async_start_segment_ids():
                await self.async_clean_segments(segment_ids)
                return
            _LOGGER.warning(
                "%s reports no rooms, or rooms of several maps, using its normal start",
                self._source_entity_id,
            )
        await self._forward("start")

    async def _async_start_segment_ids(self) -> list[str]:
        """The rooms chosen in the options, in that order, or else all rooms by ID."""
        segments = await self.async_get_segments()
        known = {segment.id for segment in segments}
        chosen = dict.fromkeys(self._entry.options.get(CONF_START_ROOMS, []))
        if rooms := [room for room in chosen if room in known]:
            return rooms
        # Rooms of several maps (floors) can't be told apart from here, and
        # without rooms there's no saved map yet that needs protecting.
        if len({segment.group for segment in segments}) != 1:
            return []
        return [segment.id for segment in sorted_by_id(segments)]

    # Home Assistant's own "Clean areas" dialog and `vacuum.clean_area` run on these two.
    # The rooms reach the original in the order they were picked.

    async def async_get_segments(self) -> list[Segment]:
        return await get_vacuum_entity(self.hass, self._source_entity_id).async_get_segments()

    async def async_clean_segments(self, segment_ids: list[str], **kwargs: Any) -> None:
        await get_vacuum_entity(self.hass, self._source_entity_id).async_clean_segments(
            segment_ids, **kwargs
        )
