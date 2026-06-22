import unittest

from bs4 import BeautifulSoup

from app.crawler import canonical_url, menu_child_links, tables, text_of


ARTICLE_HTML = """
<html><body>
  <nav>Search eLearn Contact</nav>
  <ol class="breadcrumb"><li>FIAT</li><li>MULTIPLA</li></ol>
  <div class="article">
    <h3>2892452 - Introduction - CURRENT GENERATOR</h3>
    <span class="m-2">The current production system consists of the battery and alternator.</span>
    <h1>Battery</h1>
    <h2>Technical specifications</h2>
    <span class="m-2">Capacity 50Ah</span>
    <span class="m-2">Intensity 250 A</span>
    <h1>ALTERNATOR</h1>
    <span class="m-2">Alternator explanation text.</span>
    <table><tr><th>Item</th><th>Name</th></tr><tr><td>1</td><td>Casing</td></tr></table>
    <span class="m-2"><span class="m-2">1, Casing</span><span class="m-2">2, Rectifier cooler</span></span>
    <img src="/image/schemes/fiat/2033184.png">
  </div>
</body></html>
"""

MENU_HTML = """
<html><body><div><h3>5530 CURRENT GENERATOR</h3>
  <ul class="list-group"><li><a href="/elearn/186/2/2006203/2000602/2001594/2892452">Introduction - CURRENT GENERATOR</a></li></ul>
</div></body></html>
"""

IGNITION_MENU_HTML = """
<html><body><div><h3>5510 ENGINE IGNITION</h3><ul class="list-group">
  <li><a href="http://4cardata.info/elearn/186/2/2006203/2000602/2001599/2892403">5510C coil, ecu, sensors (GPOWER)</a></li>
  <li><a href="http://4cardata.info/elearn/186/2/2006203/2000602/2001599/186003489">5510CD Rpm sensor coil operation check (BIPOWER)</a></li>
  <li><a href="http://4cardata.info/elearn/186/2/2006203/2000602/2001599/186003496">5510CE IGNITION CONTROL SIGNAL CHECK (BIPOWER)</a></li>
  <li><a href="http://4cardata.info/elearn/186/2/2006203/2000602/2001599/186003503">5510CF RPM SIGNAL CHECK (BIPOWER)</a></li>
  <li><a href="http://4cardata.info/elearn/186/2/2006203/2000602/2001599/186003510">5510OC IGNITION COIL RESISTANCE CHECK (BIPOWER)</a></li>
</ul></div></body></html>
"""

LIST_WITH_SITE_CHROME_HTML = """
<html><body><nav>4CarData eLearn Contact</nav><div id="mainContainer">
  <div class="col-lg"><form>English production search</form><ol class="breadcrumb"><li>FIAT</li></ol>
    <ul class="list-group"><li><a href="/elearn/186/2/child">Child article</a></li></ul>
  </div>
</div></body></html>
"""


class CrawlerExtractionTests(unittest.TestCase):
    def test_article_text_uses_content_region_and_preserves_leaf_blocks(self):
        text = text_of(BeautifulSoup(ARTICLE_HTML, "html.parser"))
        for expected in (
            "Battery", "Technical specifications", "Capacity 50Ah", "Intensity 250 A",
            "ALTERNATOR", "Alternator explanation text.", "1, Casing", "2, Rectifier cooler",
        ):
            self.assertIn(expected, text)
        self.assertNotIn("Search eLearn Contact", text)
        self.assertNotIn("FIAT\nMULTIPLA", text)

    def test_tables_are_scoped_to_article_content(self):
        self.assertEqual(
            tables(BeautifulSoup(ARTICLE_HTML, "html.parser")),
            [[['Item', 'Name'], ['1', 'Casing']]],
        )

    def test_list_page_children_are_detected_for_priority_crawling(self):
        soup = BeautifulSoup(MENU_HTML, "html.parser")
        self.assertEqual(
            menu_child_links(soup, "https://4cardata.info/elearn/186/2/2006203/2000602/2001594/2888287"),
            ["https://4cardata.info/elearn/186/2/2006203/2000602/2001594/2892452"],
        )

    def test_all_ignition_index_children_are_detected_and_canonicalized(self):
        links = menu_child_links(
            BeautifulSoup(IGNITION_MENU_HTML, "html.parser"),
            "https://4cardata.info/elearn/186/2/2006203/2000602/2001599/2892402",
        )
        self.assertEqual(len(links), 5)
        self.assertTrue(all(link.startswith("https://4cardata.info/elearn/186/") for link in links))
        self.assertTrue(any(link.endswith("/186003496") for link in links))

    def test_canonical_url_normalizes_legacy_http_links(self):
        self.assertEqual(
            canonical_url("http://4cardata.info/elearn/186/2/example#section"),
            "https://4cardata.info/elearn/186/2/example",
        )

    def test_list_page_text_excludes_site_chrome(self):
        text = text_of(BeautifulSoup(LIST_WITH_SITE_CHROME_HTML, "html.parser"))
        self.assertEqual(text, "Child article")


if __name__ == "__main__":
    unittest.main()
