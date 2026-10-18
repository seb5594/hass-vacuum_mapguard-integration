"""Vacuum MapGuard inside a genuine Home Assistant core.

They need Home Assistant and pytest-homeassistant-custom-component. The shared
engine installs both for every release the Compatibility workflow lists; to run them
locally: python .engine/.scripts/ha_matrix.py run 2026.9.4
"""

import pytest

pytest.importorskip("pytest_homeassistant_custom_component")

from homeassistant.components.vacuum import (  # noqa: E402
    Segment,
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow  # noqa: E402
from homeassistant.const import Platform  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.helpers import entity_registry as er  # noqa: E402
from homeassistant.helpers.device_registry import DeviceInfo  # noqa: E402
from homeassistant.setup import async_setup_component  # noqa: E402
from pytest_homeassistant_custom_component.common import (  # noqa: E402
    MockConfigEntry,
    MockModule,
    MockPlatform,
    mock_config_flow,
    mock_integration,
    mock_platform,
)

from custom_components.vacuum_mapguard.const import DOMAIN  # noqa: E402

SOURCE_DOMAIN = "test_source"
THREE_ROOMS = [Segment("1", "Kitchen"), Segment("2", "Hallway"), Segment("3", "Bedroom")]


class FakeVacuum(StateVacuumEntity):
    """A vacuum that supports cleaning by area and records what it is asked to do."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_unique_id = "robot-1"
    _attr_device_info = DeviceInfo(identifiers={(SOURCE_DOMAIN, "robot-1")}, name="Robot")
    _attr_supported_features = (
        VacuumEntityFeature.STATE
        | VacuumEntityFeature.START
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.CLEAN_AREA
    )
    _attr_activity = VacuumActivity.DOCKED

    def __init__(self, segments: list[Segment]) -> None:
        self.segments = segments
        self.calls: list[tuple] = []

    async def async_get_segments(self) -> list[Segment]:
        return self.segments

    async def async_clean_segments(self, segment_ids: list[str], **kwargs) -> None:
        self.calls.append(("clean", segment_ids))

    async def async_start(self) -> None:
        self.calls.append(("start",))

    async def async_pause(self) -> None:
        self.calls.append(("pause",))


class FakeSourceFlow(ConfigFlow):
    """Config flow of the fake vacuum integration, Home Assistant insists on one."""


@pytest.fixture(autouse=True)
def _custom_integrations(enable_custom_integrations):
    """Let Home Assistant find custom_components/vacuum_mapguard."""


@pytest.fixture(autouse=True)
def _source_flow():
    with mock_config_flow(SOURCE_DOMAIN, FakeSourceFlow):
        yield


async def _set_up_source(hass: HomeAssistant, segments=THREE_ROOMS) -> FakeVacuum:
    """Create `vacuum.robot` the way any vacuum integration would."""
    vacuum = FakeVacuum(list(segments))

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        await hass.config_entries.async_forward_entry_setups(entry, [Platform.VACUUM])
        return True

    async def async_setup_platform_entry(hass, entry, async_add_entities) -> None:
        async_add_entities([vacuum])

    mock_integration(hass, MockModule(SOURCE_DOMAIN, async_setup_entry=async_setup_entry))
    mock_platform(hass, f"{SOURCE_DOMAIN}.config_flow", None)
    mock_platform(
        hass,
        f"{SOURCE_DOMAIN}.vacuum",
        MockPlatform(async_setup_entry=async_setup_platform_entry),
    )
    entry = MockConfigEntry(domain=SOURCE_DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return vacuum


def _room_list(room_ids: list[str]) -> list[dict[str, str]]:
    """How the sortable room list of the form is submitted."""
    return [{"room": room_id} for room_id in room_ids]


async def _wrap(
    hass: HomeAssistant, entity_id: str = "vacuum.robot", rooms: list[str] | None = None
) -> ConfigEntry:
    """Run the config flow for a vacuum and let the swap finish."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_id": entity_id}
    )
    if result["type"] == "form" and result["step_id"] == "rooms":
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"start_rooms": _room_list(rooms)} if rooms else {}
        )
    assert result["type"] == "create_entry", result
    await hass.async_block_till_done()
    return result["result"]


async def _call(hass: HomeAssistant, service: str, **data) -> None:
    await hass.services.async_call(
        "vacuum", service, {"entity_id": "vacuum.robot", **data}, blocking=True
    )


async def test_proxy_takes_over_the_entity_id_and_hides_the_original(hass):
    await _set_up_source(hass)
    registry = er.async_get(hass)
    registry.async_update_entity("vacuum.robot", name="Robot Vacuum", icon="mdi:robot-vacuum")
    registry.async_update_entity_options(
        "vacuum.robot", "vacuum", {"area_mapping": {"kitchen": ["1"]}}
    )
    registry.async_update_entity_options("vacuum.robot", "conversation", {"should_expose": True})

    await _wrap(hass)

    proxy = registry.async_get("vacuum.robot")
    parked = registry.async_get("vacuum.robot_test_source")
    assert proxy.platform == DOMAIN
    assert parked.platform == SOURCE_DOMAIN
    assert parked.hidden_by is er.RegistryEntryHider.INTEGRATION
    assert proxy.device_id == parked.device_id
    assert (proxy.name, proxy.icon) == ("Robot Vacuum", "mdi:robot-vacuum")
    assert proxy.options["vacuum"] == {"area_mapping": {"kitchen": ["1"]}}
    assert proxy.options["conversation"] == {"should_expose": True}
    state = hass.states.get("vacuum.robot")
    assert state.state == "docked"
    assert state.attributes["supported_features"] & VacuumEntityFeature.CLEAN_AREA


async def test_proxy_follows_the_original(hass):
    source = await _set_up_source(hass)
    await _wrap(hass)

    source._attr_activity = VacuumActivity.CLEANING
    source.async_write_ha_state()
    await hass.async_block_till_done()

    assert hass.states.get("vacuum.robot").state == "cleaning"


async def test_start_cleans_every_room_in_one_run(hass):
    source = await _set_up_source(hass)
    await _wrap(hass)

    await _call(hass, "start")

    assert source.calls == [("clean", ["1", "2", "3"])]


@pytest.mark.parametrize("activity", [VacuumActivity.PAUSED, VacuumActivity.CLEANING])
async def test_start_resumes_a_vacuum_that_is_busy(hass, activity):
    source = await _set_up_source(hass)
    await _wrap(hass)
    source._attr_activity = activity
    source.async_write_ha_state()
    await hass.async_block_till_done()

    await _call(hass, "start")

    assert source.calls == [("start",)]


@pytest.mark.parametrize(
    "segments",
    [[], [Segment("1", "Kitchen", "Ground floor"), Segment("2", "Attic", "Top floor")]],
    ids=["no rooms", "several maps"],
)
async def test_start_falls_back_to_the_normal_start(hass, segments):
    source = await _set_up_source(hass, segments)
    await _wrap(hass)

    await _call(hass, "start")

    assert source.calls == [("start",)]


async def test_clean_area_keeps_the_picked_order(hass):
    source = await _set_up_source(hass)
    await _wrap(hass)
    er.async_get(hass).async_update_entity_options(
        "vacuum.robot",
        "vacuum",
        {"area_mapping": {"kitchen": ["1"], "hallway": ["2"], "bedroom": ["3"]}},
    )

    await _call(hass, "clean_area", cleaning_area_id=["bedroom", "kitchen"])

    assert source.calls == [("clean", ["3", "1"])]


async def test_start_cleans_the_chosen_rooms_in_the_chosen_order(hass):
    source = await _set_up_source(hass)
    await _wrap(hass, rooms=["3", "1"])

    await _call(hass, "start")

    assert source.calls == [("clean", ["3", "1"])]


SCATTERED_ROOMS = [Segment("10", "Garage"), Segment("3", "Bedroom"), Segment("1", "Kitchen")]


def _suggested_rooms(form: dict) -> list[str]:
    marker = next(key for key in form["data_schema"].schema if key == "start_rooms")
    return [item["room"] for item in marker.description["suggested_value"]]


async def test_config_flow_lists_the_rooms_of_the_vacuum_by_id(hass):
    await _set_up_source(hass, SCATTERED_ROOMS)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_id": "vacuum.robot"}
    )

    assert result["step_id"] == "rooms"
    assert _suggested_rooms(result) == ["1", "3", "10"]
    picker = result["data_schema"].schema["start_rooms"]
    assert picker.config["fields"]["room"]["selector"]["select"]["options"] == [
        {"value": "1", "label": "Kitchen"},
        {"value": "3", "label": "Bedroom"},
        {"value": "10", "label": "Garage"},
    ]


async def test_the_rooms_form_reaches_the_frontend_as_a_sortable_list(hass, hass_client):
    """The frontend gets the form as JSON, with the room names and the default order."""
    assert await async_setup_component(hass, "config", {})
    await _set_up_source(hass, SCATTERED_ROOMS)
    client = await hass_client()

    response = await client.post(
        "/api/config/config_entries/flow", json={"handler": DOMAIN, "show_advanced_options": False}
    )
    flow_id = (await response.json())["flow_id"]
    response = await client.post(
        f"/api/config/config_entries/flow/{flow_id}", json={"entity_id": "vacuum.robot"}
    )
    form = await response.json()

    assert form["step_id"] == "rooms"
    (field,) = form["data_schema"]
    selector = field["selector"]["object"]
    assert selector["multiple"] is True and selector["label_field"] == "room"
    assert [o["label"] for o in selector["fields"]["room"]["selector"]["select"]["options"]] == [
        "Kitchen",
        "Bedroom",
        "Garage",
    ]
    assert field["description"]["suggested_value"] == _room_list(["1", "3", "10"])


async def test_start_without_a_chosen_order_cleans_the_rooms_by_id(hass):
    source = await _set_up_source(hass, SCATTERED_ROOMS)
    await _wrap(hass)

    await _call(hass, "start")

    assert source.calls == [("clean", ["1", "3", "10"])]


async def test_the_untouched_default_list_is_not_stored(hass):
    source = await _set_up_source(hass, SCATTERED_ROOMS)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"entity_id": "vacuum.robot"}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"start_rooms": _room_list(_suggested_rooms(result))}
    )
    await hass.async_block_till_done()

    assert result["options"] == {}
    source.segments.append(Segment("11", "Cellar"))  # A room added to the map later.
    await _call(hass, "start")
    assert source.calls == [("clean", ["1", "3", "10", "11"])]


async def test_rooms_can_be_changed_later_in_the_options(hass):
    source = await _set_up_source(hass)
    entry = await _wrap(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert _suggested_rooms(result) == ["1", "2", "3"]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"start_rooms": _room_list(["2", "3"])}
    )
    assert result["type"] == "create_entry"
    await _call(hass, "start")

    assert source.calls == [("clean", ["2", "3"])]


async def test_start_cleans_every_room_when_the_chosen_rooms_are_gone(hass):
    source = await _set_up_source(hass)
    await _wrap(hass, rooms=["3"])
    source.segments = THREE_ROOMS[:2]  # The room was removed from the map.

    await _call(hass, "start")

    assert source.calls == [("clean", ["1", "2"])]


async def test_options_stop_when_the_vacuum_has_no_rooms(hass):
    await _set_up_source(hass, [])
    entry = await _wrap(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "abort"
    assert result["reason"] == "no_rooms"


async def test_other_actions_are_passed_through(hass):
    source = await _set_up_source(hass)
    await _wrap(hass)

    await _call(hass, "pause")

    assert source.calls == [("pause",)]


async def test_removing_the_entry_gives_the_original_its_id_back(hass):
    await _set_up_source(hass)
    entry = await _wrap(hass)

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    restored = registry.async_get("vacuum.robot")
    assert restored.platform == SOURCE_DOMAIN
    assert restored.hidden_by is None
    assert registry.async_get_entity_id("vacuum", DOMAIN, entry.entry_id) is None


async def test_deleting_the_entry_in_the_ui_gives_the_original_its_id_back(hass, hass_client):
    """The UI removes entries through this REST call."""
    assert await async_setup_component(hass, "config", {})
    await _set_up_source(hass)
    entry = await _wrap(hass)

    client = await hass_client()
    response = await client.delete(f"/api/config/config_entries/entry/{entry.entry_id}")
    await hass.async_block_till_done()

    assert response.status == 200
    assert hass.config_entries.async_get_entry(entry.entry_id) is None
    registry = er.async_get(hass)
    assert registry.async_get("vacuum.robot").platform == SOURCE_DOMAIN
    assert registry.async_get_entity_id("vacuum", DOMAIN, entry.entry_id) is None


async def test_reloading_keeps_the_swap(hass):
    await _set_up_source(hass)
    entry = await _wrap(hass)

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    assert registry.async_get("vacuum.robot").platform == DOMAIN
    assert registry.async_get("vacuum.robot_test_source").platform == SOURCE_DOMAIN
    assert registry.async_get("vacuum.robot_test_source_2") is None


async def test_flow_refuses_vacuums_it_cannot_wrap(hass):
    await _set_up_source(hass)
    await _wrap(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create("vacuum", "plain", "plain-1", suggested_object_id="plain")

    for entity_id, error in [
        ("vacuum.robot", "already_wrapped"),
        ("vacuum.plain", "no_clean_area"),
        ("vacuum.unknown", "no_unique_id"),
    ]:
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"entity_id": entity_id}
        )
        assert result["errors"] == {"base": error}, entity_id
