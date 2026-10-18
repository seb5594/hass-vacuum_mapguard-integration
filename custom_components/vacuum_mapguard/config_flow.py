"""Config flow for Vacuum MapGuard."""

from typing import Any

from homeassistant.components.vacuum import VacuumEntityFeature
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ENTITY_ID
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    AreaSelector,
    AreaSelectorConfig,
    EntityFilterSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
)
import voluptuous as vol

from .const import CONF_ORIGINAL_ENTITY_ID, CONF_SOURCE_ID, CONF_START_AREAS, DOMAIN
from .entity_swap import VACUUM_DOMAIN


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


class MapGuardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Pick the vacuum to wrap."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MapGuardOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            entity_id = user_input[CONF_ENTITY_ID]
            source = er.async_get(self.hass).async_get(entity_id)
            if problem := _find_problem(source):
                errors["base"] = problem
            else:
                await self.async_set_unique_id(source.id)
                self._abort_if_unique_id_configured()
                state = self.hass.states.get(entity_id)
                return self.async_create_entry(
                    title=state.name if state else entity_id,
                    data={CONF_SOURCE_ID: source.id, CONF_ORIGINAL_ENTITY_ID: entity_id},
                )

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


class MapGuardOptionsFlow(OptionsFlow):
    """Optionally fix the rooms and the order `vacuum.start` cleans."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(CONF_START_AREAS): AreaSelector(
                    AreaSelectorConfig(multiple=True, reorder=True)
                )
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, self.config_entry.options),
        )
