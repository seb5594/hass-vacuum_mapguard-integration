"""Vacuum MapGuard: starts a vacuum room by room so a full clean can't redraw its map.

The wrapped vacuum is renamed (`vacuum.robot` -> `vacuum.robot_roborock`) and hidden,
and a proxy entity takes over its entity ID. The proxy passes everything through to
the original, except `vacuum.start`, which cleans all rooms one after another.
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .entity_swap import async_apply_swap, async_restore_source

PLATFORMS = [Platform.VACUUM]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Swap the entity IDs, then start the proxy."""
    await async_apply_swap(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop the proxy. The swap stays in place, a restart must not undo it."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Hand the original vacuum its entity ID back."""
    await async_restore_source(hass, entry)
