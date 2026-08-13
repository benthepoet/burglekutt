import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from export_preview import format_binary_preview, generate_export
from project import Project


class TestExportPreview(unittest.TestCase):
    def test_generate_tileset_export(self):
        project = Project()
        assembly, binary, asm_name, bin_name, label = generate_export(
            project,
            "tileset",
        )
        self.assertIn("PATTERNS", assembly)
        self.assertEqual(len(binary), 256 * 16)
        self.assertEqual(asm_name, "patterns_colors.asm")
        self.assertEqual(label, "PATTERNS / COLORS")

    def test_generate_tile_image_export(self):
        project = Project()
        project.add_tile_image("TITLE", 2, 2)
        assembly, binary, asm_name, bin_name, label = generate_export(
            project,
            "tile_image",
        )
        self.assertIn("TITLE_PATTERNS", assembly)
        self.assertIn("TITLE_COLORS", assembly)
        self.assertIn("TITLE_MAP", assembly)
        self.assertEqual(asm_name, "TITLE.asm")
        self.assertEqual(bin_name, "TITLE.bin")
        self.assertIn("TITLE_MAP", label)
        self.assertTrue(len(binary) > 0)

    def test_format_binary_preview_empty(self):
        text = format_binary_preview(b"")
        self.assertIn("0 bytes", text)

    def test_format_binary_preview_hex_lines(self):
        text = format_binary_preview(bytes(range(20)))
        self.assertIn("0000:", text)
        self.assertIn("0010:", text)


if __name__ == "__main__":
    unittest.main()