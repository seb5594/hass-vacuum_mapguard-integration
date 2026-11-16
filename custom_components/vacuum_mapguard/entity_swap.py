"""Swap entity IDs so the proxy can take the place of the original vacuum.

Setting up an entry does this, in order:

1. Park the original under a new ID (`vacuum.robot` -> `vacuum.robot_roborock`) and hide it.
2. Wait until Home Assistant has dropped the old state.
3. Register the proxy under the original ID and copy over what the user set up on the
   original (name, icon, area, labels, aliases and the registry options, which hold
   the room-to-area mapping and the voice assistant exposure).

Removing the entry runs the same steps backwards. Every step can be repeated safely,
so a restart in the middle of a swap simply carries on.
"""

import asyncio
from collections.abc import Iterable
import logging

from homeassistant.components.vacuum import DATA_COMPONENT, Segment, StateVacuumEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import CONF_ORIGINAL_ENTITY_ID, CONF_SOURCE_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

VACUUM_DOMAIN = "vacuum"

# A renamed entity loses its old state a few milliseconds later. Wait that long,
# otherwise the proxy would be handed `vacuum.robot_2`.
_STATE_POLL_INTERVAL = 0.1
_STATE_POLL_ATTEMPTS = 100


@callback
def get_source(hass: HomeAssistant, entry: ConfigEntry) -> er.RegistryEntry:
    """Registry entry of the wrapped vacuum, wherever it has been renamed to."""
    source = er.async_get(hass).async_get(entry.data[CONF_SOURCE_ID])
    if source is None:
        raise ConfigEntryError(translation_domain=DOMAIN, translation_key="source_missing")
    return source


def sorted_by_id(segments: Iterable[Segment]) -> list[Segment]:
    """Rooms in ascending ID order, numbers by value (so 2 comes before 10)."""
    return sorted(segments, key=lambda s: (0, int(s.id), s.id) if s.id.isdigit() else (1, 0, s.id))


@callback
def get_vacuum_entity(hass: HomeAssistant, entity_id: str) -> StateVacuumEntity:
    """The loaded entity object of a vacuum, needed for its rooms (segments)."""
    entity = hass.data[DATA_COMPONENT].get_entity(entity_id)
    if entity is None:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="source_unavailable",
            translation_placeholders={"entity_id": entity_id},
        )
    return entity


async def _async_wait_until_state_gone(hass: HomeAssistant, entity_id: str) -> bool:
    for _ in range(_STATE_POLL_ATTEMPTS):
        if hass.states.get(entity_id) is None:
            return True
        await asyncio.sleep(_STATE_POLL_INTERVAL)
    return False


async def async_apply_swap(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Make sure the original is parked and the proxy owns its old entity ID."""
    registry = er.async_get(hass)
    source = get_source(hass, entry)
    original_id = entry.data[CONF_ORIGINAL_ENTITY_ID]

    if source.entity_id == original_id:
        parked_id = registry.async_get_available_entity_id(
            VACUUM_DOMAIN, f"{original_id.partition('.')[2]}_{source.platform}"
        )
        _LOGGER.info("Parking %s as %s", original_id, parked_id)
        source = registry.async_update_entity(
            original_id,
            new_entity_id=parked_id,
            hidden_by=source.hidden_by or er.RegistryEntryHider.INTEGRATION,
        )

    if registry.async_get_entity_id(VACUUM_DOMAIN, DOMAIN, entry.entry_id):
        return
    if not await _async_wait_until_state_gone(hass, original_id):
        # Home Assistant retries the setup later, and the swap is safe to repeat.
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="original_id_busy",
            translation_placeholders={"entity_id": original_id},
        )
    proxy = registry.async_get_or_create(
        VACUUM_DOMAIN,
        DOMAIN,
        entry.entry_id,
        config_entry=entry,
        suggested_object_id=original_id.partition(".")[2],
        get_initial_options=lambda: source.options,
    )
    registry.async_update_entity(
        proxy.entity_id,
        name=source.name,
        icon=source.icon,
        area_id=source.area_id,
        labels=set(source.labels),
        aliases=set(source.aliases),
    )


async def async_restore_source(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Undo the swap: drop the proxy and give the original its entity ID back."""
    registry = er.async_get(hass)
    source = registry.async_get(entry.data[CONF_SOURCE_ID])
    original_id = entry.data[CONF_ORIGINAL_ENTITY_ID]
    if source is None or source.entity_id == original_id:
        return  # Nothing was parked, or the original is gone.

    if proxy_id := registry.async_get_entity_id(VACUUM_DOMAIN, DOMAIN, entry.entry_id):
        registry.async_remove(proxy_id)
    await _async_wait_until_state_gone(hass, original_id)

    # Only undo our own hiding, not one the user chose.
    hidden_by = source.hidden_by
    if hidden_by is er.RegistryEntryHider.INTEGRATION:
        hidden_by = None
    try:
        registry.async_update_entity(
            source.entity_id, new_entity_id=original_id, hidden_by=hidden_by
        )
    except ValueError:
        _LOGGER.error(
            "Could not give %s its old ID %s back, something else uses it now. "
            "Rename it under Settings > Devices & services > Entities.",
            source.entity_id,
            original_id,
        )
