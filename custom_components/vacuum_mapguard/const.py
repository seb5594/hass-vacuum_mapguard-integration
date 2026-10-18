"""Constants for Vacuum MapGuard."""

DOMAIN = "vacuum_mapguard"

# The wrapped vacuum is tracked by its registry ID: its entity_id is exactly
# what this integration moves around, the registry ID never changes.
CONF_SOURCE_ID = "source_id"
# The entity_id the proxy takes over (for example "vacuum.robot").
CONF_ORIGINAL_ENTITY_ID = "original_entity_id"
