import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from asm_format_schema import list_formats, load_format


class TestAsmFormat(unittest.TestCase):
    def test_list_formats_includes_default(self):
        names = list_formats()
        self.assertIn("ti99_default", names)

    def test_load_default_format(self):
        fmt = load_format("ti99_default")
        self.assertEqual(fmt["byte_keyword"], "BYTE")
        self.assertEqual(fmt["hex_prefix"], ">")
        self.assertEqual(fmt["labels"]["patterns"], "PATTERNS")


if __name__ == "__main__":
    unittest.main()