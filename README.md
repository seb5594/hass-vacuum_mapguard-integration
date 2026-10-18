# Vacuum MapGuard

<!-- badges:begin (generated from project metadata) -->
[![HACS](https://img.shields.io/static/v1?label=HACS&message=Add%20integration&color=41BDF5&style=flat&logo=homeassistantcommunitystore&logoColor=white)](https://my.home-assistant.io/redirect/hacs_repository/?owner=seb5594&repository=hass-vacuum_mapguard-integration&category=integration) ![setup](https://img.shields.io/static/v1?label=setup&message=UI%20config%20flow&color=157F71&style=flat)<br>
![home assistant](https://img.shields.io/static/v1?label=home%20assistant&message=%E2%89%A5%202026.3.0&color=1877A5&style=flat) [![version](https://img.shields.io/static/v1?label=version&message=1.0.0&color=1877A5&style=flat)](https://github.com/seb5594/hass-vacuum_mapguard-integration/releases) [![released](https://img.shields.io/github/release-date-pre/seb5594/hass-vacuum_mapguard-integration?label=released&style=flat)](https://github.com/seb5594/hass-vacuum_mapguard-integration/releases) [![checks](https://img.shields.io/github/actions/workflow/status/seb5594/hass-vacuum_mapguard-integration/ci.yml?branch=main&label=checks&style=flat)](https://github.com/seb5594/hass-vacuum_mapguard-integration/actions/workflows/ci.yml)<br>
[![downloads](https://img.shields.io/github/downloads/seb5594/hass-vacuum_mapguard-integration/total?label=downloads&style=flat)](https://github.com/seb5594/hass-vacuum_mapguard-integration/releases) [![latest release](https://img.shields.io/github/downloads/seb5594/hass-vacuum_mapguard-integration/latest/total?label=latest%20release&style=flat)](https://github.com/seb5594/hass-vacuum_mapguard-integration/releases/latest)<br>
[![stars](https://img.shields.io/github/stars/seb5594/hass-vacuum_mapguard-integration?label=stars&style=flat)](https://github.com/seb5594/hass-vacuum_mapguard-integration/stargazers) [![issues](https://img.shields.io/github/issues/seb5594/hass-vacuum_mapguard-integration?label=issues&style=flat)](https://github.com/seb5594/hass-vacuum_mapguard-integration/issues) [![updated](https://img.shields.io/github/last-commit/seb5594/hass-vacuum_mapguard-integration?label=updated&style=flat)](https://github.com/seb5594/hass-vacuum_mapguard-integration/commits/main)<br>
![tests](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fseb5594%2Fhass-vacuum_mapguard-integration%2Fbadges%2Ftests.json&style=flat) ![HACS zip](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fseb5594%2Fhass-vacuum_mapguard-integration%2Fbadges%2Fzip-size.json&style=flat) ![last build](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2Fseb5594%2Fhass-vacuum_mapguard-integration%2Fbadges%2Flast-build.json&style=flat)
<!-- badges:end -->

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
2. **Optional: choose the rooms and their order.** The dropdown lists the rooms your vacuum
   reports, with the names from the vacuum's own app. Pick the rooms Start should clean in the order
   you want them cleaned. Rooms you leave out are skipped, handy for a balcony or a garage. If you
   pick nothing, Start cleans all rooms in the order the vacuum reports them.

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
- If a room you picked disappears from the map, Start falls back to cleaning all rooms.

<!-- support:begin (generated, shared text) -->
## Say thanks

All my projects are built in my spare time, just for the fun of it. Still, they take a lot of time and care, and many of the smart home gadgets I buy end up here because I want to make them cloud-free and smart-home ready. Every bit of support means a lot to me.

If my work helped you or turned out to be useful, show your appreciation with a hot drink for my next sleepless night.

[![Buy Me a Coffee](https://img.shields.io/static/v1?label=Support&message=Buy%20Me%20a%20Coffee&color=FFDD00&logo=buy-me-a-coffee&logoColor=black&style=for-the-badge)](https://buymeacoffee.com/seb5594) [![PayPal](https://img.shields.io/static/v1?label=Support&message=PayPal&color=0070BA&logo=paypal&logoColor=white&style=for-the-badge)](https://www.paypal.com/donate/?hosted_button_id=QMQPNRENXDN26)
<!-- support:end -->
