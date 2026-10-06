"""yaml_lite edge-case tests: colon-bearing scalars, tabs, inline mappings."""

import unittest

from ai_sales_os.yaml_lite import load


class TestYamlLiteEdge(unittest.TestCase):
    def test_url_in_list_stays_a_scalar(self):
        doc = load("items:\n  - http://example.com:8080/x\n  - new\n")
        self.assertEqual(doc, {"items": ["http://example.com:8080/x", "new"]})

    def test_time_like_scalar_in_list_stays_a_scalar(self):
        doc = load("items:\n  - 12:30\n")
        self.assertEqual(doc, {"items": ["12:30"]})

    def test_quoted_colon_string_in_list_stays_a_scalar(self):
        doc = load('items:\n  - "a: b"\n')
        self.assertEqual(doc, {"items": ["a: b"]})

    def test_inline_mapping_still_works(self):
        doc = load("people:\n  - name: amy\n    age: 3\n")
        self.assertEqual(doc, {"people": [{"name": "amy", "age": 3}]})

    def test_inline_mapping_with_empty_value(self):
        doc = load("items:\n  - key:\n")
        self.assertEqual(doc, {"items": [{"key": None}]})

    def test_tab_indentation_rejected_with_clear_message(self):
        with self.assertRaises(ValueError) as ctx:
            load("key:\n\t- a\n")
        self.assertIn("Tabs", str(ctx.exception))
        self.assertIn("line 2", str(ctx.exception))

    def test_mapping_value_with_colon_unaffected(self):
        doc = load("note: call at 12:30\n")
        self.assertEqual(doc, {"note": "call at 12:30"})


if __name__ == "__main__":
    unittest.main()
