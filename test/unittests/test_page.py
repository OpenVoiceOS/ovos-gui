import unittest


class TestGuiPage(unittest.TestCase):
    def test_gui_page(self):
        from ovos_gui.page import GuiPage
        uri = __file__
        name = "test"
        persistent = True
        duration = 0
        page = GuiPage(uri, name, persistent, duration)
        self.assertEqual(page.url, uri)
        self.assertEqual(page.name, name)
        self.assertEqual(page.persistent, persistent)
        self.assertEqual(page.duration, 0)
        self.assertFalse(page.active)
