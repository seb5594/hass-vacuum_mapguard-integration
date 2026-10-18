# Changelog

## 1.0.0

- First stable release. Requires Home Assistant 2026.3 or newer.
- `vacuum.start` cleans room by room instead of triggering the vendor's full clean, so the saved map is left alone.
- Optional room selection and order for `vacuum.start`, picked from the rooms the vacuum reports. Set in the setup flow and changeable under Configure.
- Home Assistant's own "Clean areas" dialog and `vacuum.clean_area` work on the proxy, in the order the areas were picked.
- Listed under Integrations, not as a helper.
