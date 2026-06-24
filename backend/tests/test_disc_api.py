import gzip
import unittest

from fastapi import HTTPException
from app.disc_api import _asset_file, build_manual_tree
from app.disc_renderer import UnsafeXmlError, sanitize_svg_bytes
from app.main import app


class DiscApiTests(unittest.TestCase):
    def test_preview_routes_are_registered_without_replacing_production_routes(self):
        paths = {route.path for route in app.routes}
        self.assertTrue({
            "/disc/health", "/disc/manual/fiat-multipla/tree",
            "/disc/elements/{element_id}", "/disc/xml/{xml_id}",
            "/disc/assets/{asset_id}", "/disc/search",
        }.issubset(paths))
        self.assertIn("/api/elearn/{page_id}", paths)

    def test_tree_includes_one_example_from_each_section_type(self):
        sections = []
        elements = []
        for section_type in range(1, 7):
            element_id = 1000 + section_type
            sections.append({"source_section_id": 2000 + section_type, "section_type": section_type,
                             "name": f"Section {section_type}", "root_element_id": element_id})
            elements.append({"source_element_id": element_id, "parent_element_id": 0,
                             "name": f"Root {section_type}", "code": str(section_type),
                             "orders": section_type, "xml_count": 1})
        tree = build_manual_tree(sections, elements)
        self.assertEqual([row["section_type"] for row in tree], [1, 2, 3, 4, 5, 6])
        self.assertTrue(all(row["root"]["xml_count"] == 1 for row in tree))

    def test_asset_id_rejects_path_traversal(self):
        self.assertEqual(_asset_file("2033463").name, "2033463.image")
        with self.assertRaises(HTTPException):
            _asset_file("../../etc/passwd")

    def test_svg_sanitizer_removes_external_and_event_content(self):
        source = b'<svg xmlns="http://www.w3.org/2000/svg"><image href="https://evil.test/x" onload="x()"/><path d="M0 0"/></svg>'
        safe = sanitize_svg_bytes(gzip.compress(source), compressed=True)
        self.assertNotIn(b"evil.test", safe)
        self.assertNotIn(b"onload", safe)
        self.assertIn(b"path", safe)

    def test_svg_sanitizer_rejects_active_elements(self):
        with self.assertRaises(UnsafeXmlError):
            sanitize_svg_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"><script>x()</script></svg>')


if __name__ == "__main__":
    unittest.main()
