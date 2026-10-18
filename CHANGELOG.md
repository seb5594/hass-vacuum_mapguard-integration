# Changelog

## 1.1.1

- The room list shows the room names instead of their IDs and no longer has an edit button. Rooms can still be dragged into order and removed.

## 1.1.0

- The room order is a sortable list again. It shows the rooms the vacuum reports, in the order Start cleans them without a custom order (ascending by room ID), so you only drag, delete or add rooms.
- Without a custom order, Start cleans the rooms by ascending room ID.
- Added the Vacuum MapGuard icon and logo.

## 1.0.0

- First stable release. Requires Home Assistant 2026.3 or newer.
- `vacuum.start` cleans room by room instead of triggering the vendor's full clean, so the saved map is left alone.
- Optional room selection and order for `vacuum.start`, picked from the rooms the vacuum reports. Set in the setup flow and changeable under Configure.
- Home Assistant's own "Clean areas" dialog and `vacuum.clean_area` work on the proxy, in the order the areas were picked.
- Listed under Integrations, not as a helper.
