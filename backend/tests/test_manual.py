import unittest

from app.manual import build_manual_tree


class ManualTreeTests(unittest.TestCase):
    def test_groups_pages_and_preserves_relationships(self):
        pages = [
            {"id": 1, "title": "55 ELECTRICAL EQUIPMENT", "breadcrumb": "FIAT > MULTIPLA > 1.6 16V > TEST > 55 ELECTRICAL EQUIPMENT", "category": "FIAT", "parent_page_id": None, "image_count": 0},
            {"id": 2, "title": "5510 ENGINE IGNITION", "breadcrumb": "FIAT > MULTIPLA > 1.6 16V > TEST > 55 ELECTRICAL EQUIPMENT > 5510 ENGINE IGNITION", "category": "FIAT", "parent_page_id": 1, "image_count": 0},
            {"id": 3, "title": "5510CE IGNITION CONTROL SIGNAL CHECK", "breadcrumb": "FIAT > MULTIPLA > 1.6 16V > TEST > 55 ELECTRICAL EQUIPMENT > 5510 ENGINE IGNITION > 5510CE", "category": "FIAT", "parent_page_id": 2, "image_count": 1},
            {"id": 4, "title": "Diesel overview", "breadcrumb": "FIAT > MULTIPLA > 1.9 JTD 8V > DESCRIPTIONS > 10 ENGINE UNIT", "category": "FIAT", "parent_page_id": None, "image_count": 0},
        ]
        tree = build_manual_tree(pages, [(1, 2), (2, 3)])
        self.assertEqual([engine["title"] for engine in tree["engines"]], ["1.6 16V", "1.9 JTD 8V"])
        petrol = tree["engines"][0]
        test = next(section for section in petrol["sections"] if section["title"] == "TEST")
        category = next(item for item in test["categories"] if item["title"] == "55 ELECTRICAL EQUIPMENT")
        ignition = category["pages"][0]["children"][0]
        self.assertEqual(ignition["title"], "5510 ENGINE IGNITION")
        self.assertEqual(ignition["children"][0]["kind"], "article")
        self.assertEqual(ignition["children"][0]["image_count"], 1)

    def test_uses_breadcrumb_grouping_without_parent_ids(self):
        pages = [
            {"id": 10, "title": "5530 CURRENT GENERATOR", "breadcrumb": "FIAT > MULTIPLA > 1.6 16V > TECHNICAL DATA > TIGHTENING TORQUES > 55 ELECTRICAL EQUIPMENT > 5530 CURRENT GENERATOR", "category": "FIAT", "parent_page_id": None, "image_count": 0},
            {"id": 11, "title": "5530 CURRENT GENERATOR", "breadcrumb": "FIAT > MULTIPLA > 1.6 16V > DESCRIPTIONS > 55 ELECTRICAL EQUIPMENT > 5530 CURRENT GENERATOR", "category": "FIAT", "parent_page_id": None, "image_count": 0},
            {"id": 12, "title": "Introduction - CURRENT GENERATOR", "breadcrumb": "FIAT > MULTIPLA > 1.6 16V > DESCRIPTIONS > 55 ELECTRICAL EQUIPMENT > 5530 CURRENT GENERATOR > INTRODUCTION", "category": "FIAT", "parent_page_id": 11, "image_count": 1},
        ]
        tree = build_manual_tree(pages, [(11, 12)])
        section = next(item for item in tree["engines"][0]["sections"] if item["title"] == "TECHNICAL DATA")
        self.assertEqual(section["title"], "TECHNICAL DATA")
        self.assertEqual(section["categories"][0]["title"], "55 ELECTRICAL EQUIPMENT")
        self.assertEqual(section["categories"][0]["pages"][0]["id"], 10)
        related = section["categories"][0]["pages"][0]["children"][0]
        self.assertEqual(related["id"], 12)
        self.assertIn("breadcrumb cross-reference", related["relation"])


if __name__ == "__main__":
    unittest.main()
