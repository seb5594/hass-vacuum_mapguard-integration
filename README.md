<!-- header:begin (generated from project metadata) -->
<h1 align="center">Vacuum MapGuard</h1>

<p align="center">
  <img src="https://raw.githubusercontent.com/seb5594/hass-vacuum_mapguard-integration/main/custom_components/vacuum_mapguard/brand/logo@2x.png" alt="Vacuum MapGuard" width="246" height="160">
</p>

---

<p align="center">
  <a href="https://paypal.me/seb5594"><img src="https://img.shields.io/static/v1?label=Support&amp;message=PayPal&amp;color=0070BA&amp;logo=paypal&amp;logoColor=white&amp;style=for-the-badge" alt="PayPal" height="40"></a>
  <a href="https://buymeacoffee.com/seb5594"><img src="https://img.shields.io/static/v1?label=Support&amp;message=Buy%20Me%20a%20Coffee&amp;color=FFDD00&amp;logo=buy-me-a-coffee&amp;logoColor=black&amp;style=for-the-badge" alt="Buy Me a Coffee" height="40"></a><br>
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=seb5594&amp;repository=hass-vacuum_mapguard-integration&amp;category=integration"><img src="https://img.shields.io/static/v1?label=HACS&amp;message=Add%20integration&amp;color=41BDF5&amp;logo=homeassistantcommunitystore&amp;logoColor=white&amp;style=for-the-badge" alt="HACS" height="28"></a>
  <a href="https://github.com/seb5594/hass-vacuum_mapguard-integration/actions/workflows/compat.yml"><img src="https://img.shields.io/static/v1?label=home%20assistant&amp;message=%E2%89%A5%202026.3.0&amp;color=1877A5&amp;style=for-the-badge" alt="home assistant" height="28"></a>
  <a href="https://github.com/seb5594/hass-vacuum_mapguard-integration/releases/tag/v1.1.1"><img src="https://img.shields.io/static/v1?label=version&amp;message=1.1.1&amp;color=1877A5&amp;style=for-the-badge" alt="version" height="28"></a>
  <a href="https://github.com/seb5594/hass-vacuum_mapguard-integration/releases"><img src="https://img.shields.io/github/downloads/seb5594/hass-vacuum_mapguard-integration/v1.1.1/total?label=downloads&amp;color=1877A5&amp;style=for-the-badge" alt="downloads" height="28"></a><br>
  <a href="https://github.com/seb5594/hass-vacuum_mapguard-integration/issues"><img src="https://img.shields.io/github/issues/seb5594/hass-vacuum_mapguard-integration?label=issues&amp;style=flat" alt="issues" height="20"></a>
  <img src="https://img.shields.io/static/v1?label=tests&amp;message=5%20passed&amp;color=2F855A&amp;style=flat" alt="tests" height="20">
  <a href="https://github.com/seb5594/hass-vacuum_mapguard-integration/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/seb5594/hass-vacuum_mapguard-integration/ci.yml?branch=main&amp;label=checks&amp;style=flat" alt="checks" height="20"></a>
  <a href="https://github.com/seb5594/hass-vacuum_mapguard-integration#license"><img src="https://img.shields.io/github/license/seb5594/hass-vacuum_mapguard-integration?label=license&amp;style=flat" alt="license" height="20"></a>
</p>
<!-- header:end -->

Makes `vacuum.start` clean your rooms one by one instead of running the vendor's "full clean", so
your saved floor plan stays untouched.

Depending on the vendor and firmware, a full clean can redraw the saved map: a closed door gets
burned into it, rooms merge, the room layout you tuned is gone. Cleaning every room as its own
segment avoids that. Vacuum MapGuard does it whenever something calls `vacuum.start`, so your
dashboards, automations, schedules and voice assistants protect the map without any change.

## Requirements

- Home Assistant 2026.3 or newer, the first release with vacuum rooms ("segments").
- A vacuum whose integration supports cleaning by area. Open the vacuum in Home Assistant: if it
  offers **Clean areas**, it works.

## Installation

1. Add this repository to [HACS](https://hacs.xyz) as a custom repository (category *Integration*),
   or use the button above. Install **Vacuum MapGuard** and restart Home Assistant.
   Without HACS, copy `custom_components/vacuum_mapguard` into your `custom_components` folder.
2. Go to **Settings > Devices & services > Add integration > Vacuum MapGuard**.

## Setup

1. **Pick your vacuum.** Only vacuums that support cleaning by area are listed.
2. **Optional: set the room order.** A list shows the rooms your vacuum reports, with the names
   from the vacuum's own app, in the order Start would clean them without any setting (ascending
   by room ID). Drag a room to move it, remove one to skip it (handy for a balcony or a garage) and
   pick it from the list again to bring it back. Leave the list untouched and Start cleans all
   rooms.

You can change the rooms later under **Settings > Devices & services > Vacuum MapGuard >
Configure**. The change applies right away.

Whether your vacuum really follows the order is up to its firmware.

## What happens to your vacuum

Entity IDs are the glue of every dashboard and automation, so Vacuum MapGuard keeps yours:

| Before | After |
| --- | --- |
| `vacuum.robot` (from your vacuum integration) | `vacuum.robot_roborock`, hidden |
| | `vacuum.robot` (from Vacuum MapGuard) with the same device, name, icon, area, labels, voice assistant exposure and room-to-area assignment |

The new `vacuum.robot` mirrors the original's state, fan speed and attributes and passes every
action through. Only `vacuum.start` is different: when the vacuum is docked, idle, returning or in
an error state, it cleans room by room. A paused vacuum is resumed as usual.

If the vacuum reports no rooms yet (a new robot that has not mapped anything), or rooms of several
maps (a multi-floor setup), a room-by-room run can't be planned. A warning is logged and the normal
start is used.

Deleting the Vacuum MapGuard entry under **Devices & services** undoes all of this and gives the
original its entity ID back.

## One-off runs with Home Assistant's own dialog

The **Clean areas** dialog of the vacuum keeps working. Tap the areas in the order you want and
start the cleaning. The rooms reach the vacuum in the order you tapped them. Use the cogwheel in that
dialog to assign the vacuum's rooms to your areas. The same works in scripts, where the area picker
can be reordered:

```yaml
action: vacuum.clean_area
target:
  entity_id: vacuum.robot
data:
  cleaning_area_id:
    - kitchen
    - hallway
    - bedroom
```

## Good to know

- Your room-to-area assignment is copied once when you add the integration. If the vacuum's rooms
  change later, assign them again in the dialog of the new `vacuum.robot`.
- Don't rename the hidden original. If you did, reload the integration.
- Rooms you added to the map after leaving the list untouched are cleaned too. Once you change the
  list, only the rooms in it are cleaned.
- If every room you picked disappears from the map, Start falls back to cleaning all rooms.

<!-- support:begin (generated, shared text) -->
## Say thanks

All my projects are built in my spare time, just for the fun of it. Still, they take a lot of time and care, and many of the smart home gadgets I buy end up here because I want to make them cloud-free and smart-home ready. Every bit of support means a lot to me.

If my work helped you or turned out to be useful, show your appreciation with a hot drink for my next sleepless night.

[![PayPal](https://img.shields.io/static/v1?label=Support&message=PayPal&color=0070BA&logo=paypal&logoColor=white&style=for-the-badge)](https://paypal.me/seb5594) [![Buy Me a Coffee](https://img.shields.io/static/v1?label=Support&message=Buy%20Me%20a%20Coffee&color=FFDD00&logo=buy-me-a-coffee&logoColor=black&style=for-the-badge)](https://buymeacoffee.com/seb5594)
<!-- support:end -->

<!-- license:begin (generated from the license file) -->
## License

[![license](https://img.shields.io/static/v1?label=license&message=Apache-2.0&color=5B6770&style=flat)](LICENSE)

Published under the [Apache License 2.0](LICENSE).
<!-- license:end -->
