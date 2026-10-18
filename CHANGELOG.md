# Changelog

## 0.1.0

- Initial release. Requires Home Assistant 2026.3 or newer.
- `vacuum.start` cleans room by room instead of triggering the vendor's full clean. Which areas it cleans, and in which order, can optionally be set in the integration's options.
- Home Assistant's own "Clean areas" dialog and `vacuum.clean_area` work on the proxy, in the order the rooms were picked.
