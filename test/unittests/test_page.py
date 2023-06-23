import unittest
from unittest.mock import Mock


class TestGuiPage(unittest.TestCase):
    def test_gui_page(self):
        from ovos_gui.page import GuiPage
        uri = __file__
        name = "test"
        persistent = True
        duration = 0

        # Simple page
        page = GuiPage(uri, name, persistent, duration)
        self.assertEqual(page.url, uri)
        self.assertEqual(page.name, name)
        self.assertEqual(page.persistent, persistent)
        self.assertEqual(page.duration, 0)
        self.assertFalse(page.active)

        # server URI with no server
        server_uri = "skill-ovos-homescreen.openvoiceos/ui/page.qml"
        page = GuiPage(uri, name, persistent, duration, server_uri)
        self.assertEqual(page.url, uri)
        self.assertEqual(page.name, name)
        self.assertEqual(page.persistent, persistent)
        self.assertEqual(page.duration, 0)
        self.assertFalse(page.active)

        # http URI with server
        GuiPage.qml_server = Mock()
        GuiPage.qml_server.url = "http://localhost:8080"
        http_uri = "http://test.test/ui/page.qml"
        page = GuiPage(http_uri, name, persistent, duration, server_uri)
        self.assertEqual(page.url, http_uri)
        self.assertEqual(page.name, name)
        self.assertEqual(page.persistent, persistent)
        self.assertEqual(page.duration, 0)
        self.assertFalse(page.active)

        # local URI with server
        page = GuiPage(uri, name, persistent, duration, server_uri)
        self.assertEqual(page.url, f"{GuiPage.qml_server.url}/{server_uri}")
        self.assertEqual(page.name, name)
        self.assertEqual(page.persistent, persistent)
        self.assertEqual(page.duration, 0)
        self.assertFalse(page.active)
