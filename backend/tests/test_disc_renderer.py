import unittest

from app.disc_renderer import UnsafeXmlError, render_xml


class DiscRendererTests(unittest.TestCase):
    def test_preserves_links_and_images_with_internal_schemes(self):
        source = """<group><bigtext1>Heading</bigtext1><text>Safe text</text>
        <link><targetid>2891739</targetid><code>4450B10</code><description>Wheel</description></link>
        <svgimage><imageid>2033463</imageid></svgimage>
        <consvgimage><conimageid>2033000</conimageid></consvgimage></group>"""
        rendered = render_xml(source)
        self.assertIn("disc://element/2891739", rendered)
        self.assertIn("disc-asset://2033463", rendered)
        self.assertIn('data-reference-kind="conimageid"', rendered)
        self.assertIn("Safe text", rendered)

    def test_preserves_generic_icon_image_reference(self):
        rendered = render_xml("<group><notes><icon><imageid>767</imageid></icon></notes></group>")
        self.assertIn("disc-asset://767", rendered)

    def test_rejects_dtd_entities_and_active_content(self):
        for source in [
            '<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><group>&e;</group>',
            "<group><script>alert(1)</script></group>",
            "<group><object>ActiveX</object></group>",
        ]:
            with self.subTest(source=source):
                with self.assertRaises(UnsafeXmlError):
                    render_xml(source)

    def test_escapes_source_text(self):
        rendered = render_xml("<group><text>&lt;img src='https://example.test/x'&gt;</text></group>")
        self.assertNotIn("<img src=", rendered)
        self.assertIn("&lt;img", rendered)


if __name__ == "__main__":
    unittest.main()
