"""Static checks that need no Home Assistant installation."""
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = next((ROOT / "custom_components").iterdir())


class IntegrationLayout(unittest.TestCase):
    def test_manifest_domain_matches_folder_and_constants(self):
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        self.assertEqual(manifest["domain"], COMPONENT.name)
        self.assertIn(f'DOMAIN = "{COMPONENT.name}"', (COMPONENT / "const.py").read_text())

    def test_translations_mirror_strings(self):
        strings = json.loads((COMPONENT / "strings.json").read_text())
        english = json.loads((COMPONENT / "translations/en.json").read_text())
        self.assertEqual(strings, english)

    def test_integration_is_listed_with_the_regular_integrations(self):
        # "helper" would hide it from Integrations and bury its options in the entity dialog.
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        self.assertEqual(manifest["integration_type"], "service")

    def test_brand_images_have_the_sizes_home_assistant_expects(self):
        def size(name):
            data = (COMPONENT / "brand" / name).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n", name)
            return struct.unpack(">II", data[16:24])

        self.assertEqual(size("icon.png"), (256, 256))
        self.assertEqual(size("icon@2x.png"), (512, 512))
        self.assertTrue(128 <= min(size("logo.png")) <= 256)
        self.assertTrue(256 <= min(size("logo@2x.png")) <= 512)

    def test_german_translation_has_the_same_keys(self):
        def keys(tree, prefix=""):
            return {f"{prefix}/{k}" for k, v in tree.items()} | {
                key for k, v in tree.items() if isinstance(v, dict) for key in keys(v, f"{prefix}/{k}")
            }

        english = json.loads((COMPONENT / "translations/en.json").read_text())
        german = json.loads((COMPONENT / "translations/de.json").read_text())
        self.assertEqual(keys(german), keys(english))


if __name__ == "__main__":
    unittest.main()
