# Changelog

## 0.1.0

- Initial release. Requires Home Assistant 2026.3 or newer.
- `vacuum.start` cleans all rooms one after another instead of triggering the vendor's full clean.
- Home Assistant's own "Clean areas" dialog and `vacuum.clean_area` work on the proxy, in the order the rooms were picked.
