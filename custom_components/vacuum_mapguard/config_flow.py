"""Config flow for Vacuum MapGuard."""

from typing import Any

from homeassistant.components.vacuum import VacuumEntityFeature
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntityFilterSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import voluptuous as vol

from .const import CONF_ORIGINAL_ENTITY_ID, CONF_SOURCE_ID, CONF_START_ROOMS, DOMAIN
from .entity_swap import VACUUM_DOMAIN, get_source, get_vacuum_entity


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


async def _async_rooms_schema(hass: HomeAssistant, entity_id: str) -> vol.Schema | None:
    """Optional room picker with the rooms the vacuum itself reports, None without rooms.

    The dropdown lists the rooms in the order they get picked, so that is the order
    `vacuum.start` cleans them in.
    """
    try:
        segments = await get_vacuum_entity(hass, entity_id).async_get_segments()
    except HomeAssistantError:
        return None
    if not segments:
        return None
    options = [SelectOptionDict(value=segment.id, label=segment.name) for segment in segments]
    return vol.Schema(
        {
            vol.Optional(CONF_START_ROOMS): SelectSelector(
                SelectSelectorConfig(
                    options=options, multiple=True, mode=SelectSelectorMode.DROPDOWN
                )
            )
        }
    )


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
        if user_input is None and (
            schema := await _async_rooms_schema(self.hass, source.entity_id)
        ):
            return self.async_show_form(step_id="rooms", data_schema=schema)

        state = self.hass.states.get(source.entity_id)
        return self.async_create_entry(
            title=state.name if state else source.entity_id,
            data={CONF_SOURCE_ID: source.id, CONF_ORIGINAL_ENTITY_ID: source.entity_id},
            options=user_input or {},
        )


class MapGuardOptionsFlow(OptionsFlow):
    """Change the rooms and the order `vacuum.start` cleans."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        try:
            entity_id = get_source(self.hass, self.config_entry).entity_id
        except HomeAssistantError:
            return self.async_abort(reason="no_rooms")
        schema = await _async_rooms_schema(self.hass, entity_id)
        if schema is None:
            return self.async_abort(reason="no_rooms")
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, self.config_entry.options),
        )
