"""Config flow for Vacuum MapGuard."""

from typing import Any

from homeassistant.components.vacuum import Segment, VacuumEntityFeature
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntityFilterSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    ObjectSelector,
    ObjectSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import voluptuous as vol

from .const import CONF_ORIGINAL_ENTITY_ID, CONF_SOURCE_ID, CONF_START_ROOMS, DOMAIN
from .entity_swap import VACUUM_DOMAIN, get_source, get_vacuum_entity, sorted_by_id

_ROOM_FIELD = "room"


def _find_problem(source: er.RegistryEntry | None) -> str | None:
    """Why the picked entity can't be wrapped, as a key of the `error` translations."""
    if source is None:
        # Entities without a unique ID are not in the registry, so there is nothing to rename.
        return "no_unique_id"
    if source.platform == DOMAIN:
        return "already_wrapped"
    if not (source.supported_features or 0) & VacuumEntityFeature.CLEAN_AREA:
        return "no_clean_area"
    return None


async def _async_get_rooms(hass: HomeAssistant, entity_id: str) -> list[Segment]:
    """The rooms the vacuum reports, in the order Start cleans them without a custom order."""
    try:
        return sorted_by_id(await get_vacuum_entity(hass, entity_id).async_get_segments())
    except HomeAssistantError:
        return []


def _rooms_schema(rooms: list[Segment], chosen: list[str]) -> vol.Schema:
    """A sortable list of rooms, filled with the order Start would clean them in right now."""
    picker = SelectSelector(
        SelectSelectorConfig(
            options=[SelectOptionDict(value=room.id, label=room.name) for room in rooms],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )
    suggestion = chosen or [room.id for room in rooms]
    return vol.Schema(
        {
            vol.Optional(
                CONF_START_ROOMS,
                description={"suggested_value": [{_ROOM_FIELD: room} for room in suggestion]},
            ): ObjectSelector(
                ObjectSelectorConfig(
                    fields={
                        _ROOM_FIELD: {
                            # The dict form, older releases only validate nested selectors that way.
                            "selector": picker.serialize()["selector"],
                            "required": True,
                            "label": "Room",
                        }
                    },
                    multiple=True,
                    label_field=_ROOM_FIELD,
                )
            )
        }
    )


def _chosen_rooms(user_input: dict[str, Any], rooms: list[Segment]) -> dict[str, list[str]]:
    """The options to store. The untouched default list is stored as nothing, so rooms
    added to the map later are still cleaned."""
    chosen = list(dict.fromkeys(item[_ROOM_FIELD] for item in user_input.get(CONF_START_ROOMS, [])))
    if chosen == [room.id for room in rooms]:
        return {}
    return {CONF_START_ROOMS: chosen} if chosen else {}


class MapGuardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Pick the vacuum to wrap, then optionally the rooms `vacuum.start` cleans."""

    VERSION = 1

    def __init__(self) -> None:
        self._source: er.RegistryEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MapGuardOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            source = er.async_get(self.hass).async_get(user_input[CONF_ENTITY_ID])
            if problem := _find_problem(source):
                errors["base"] = problem
            else:
                await self.async_set_unique_id(source.id)
                self._abort_if_unique_id_configured()
                self._source = source
                return await self.async_step_rooms()

        schema = vol.Schema(
            {
                vol.Required(CONF_ENTITY_ID): EntitySelector(
                    EntitySelectorConfig(
                        filter=EntityFilterSelectorConfig(
                            domain=VACUUM_DOMAIN,
                            supported_features=["vacuum.VacuumEntityFeature.CLEAN_AREA"],
                        )
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_rooms(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        source = self._source
        assert source is not None
        rooms = await _async_get_rooms(self.hass, source.entity_id)
        if user_input is None and rooms:
            return self.async_show_form(step_id="rooms", data_schema=_rooms_schema(rooms, []))

        state = self.hass.states.get(source.entity_id)
        return self.async_create_entry(
            title=state.name if state else source.entity_id,
            data={CONF_SOURCE_ID: source.id, CONF_ORIGINAL_ENTITY_ID: source.entity_id},
            options=_chosen_rooms(user_input or {}, rooms),
        )


class MapGuardOptionsFlow(OptionsFlow):
    """Change the rooms and the order `vacuum.start` cleans."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        try:
            entity_id = get_source(self.hass, self.config_entry).entity_id
        except HomeAssistantError:
            return self.async_abort(reason="no_rooms")
        rooms = await _async_get_rooms(self.hass, entity_id)
        if not rooms:
            return self.async_abort(reason="no_rooms")
        if user_input is not None:
            return self.async_create_entry(data=_chosen_rooms(user_input, rooms))

        chosen = self.config_entry.options.get(CONF_START_ROOMS, [])
        return self.async_show_form(step_id="init", data_schema=_rooms_schema(rooms, chosen))
