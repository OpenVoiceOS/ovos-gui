import unittest
from os.path import join, dirname, isfile
from ovos_gui.page import GuiPage


class TestGuiPage(unittest.TestCase):
    def test_gui_page_legacy(self):
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
        self.assertEqual(page.id, page.url)
        self.assertEqual(page.get_uri(), page.url)
        self.assertEqual(page.get_uri("qt6", "http://0.0.0.0:80"), page.url)
        self.assertEqual(page.get_uri("qt6", "/var/www/app"), page.url)

    def test_gui_page_from_server(self):
        name = "test_page"
        persistent = False
        duration = 60
        page_id = "test_page"
        namespace = "skill.test"

        page = GuiPage(None, name, persistent, duration, page_id, namespace)
        qt5 = page.get_uri(server_url="localhost:80")
        self.assertEqual(qt5,
                         f"http://localhost:80/{namespace}/qt5/{page_id}.qml")

        qt6 = page.get_uri(server_url="https://files.local")
        self.assertEqual(qt6,
                         f"https://files.local/{namespace}/qt5/{page_id}.qml")

    def test_gui_page_from_local_path(self):
        name = "test"
        persistent = True
        duration = True
        page_id = "test"
        namespace = "skill.test"
        res_dirs = {"all": join(dirname(__file__), "mock_data", "gui")}
        # Modern GUI File organization
        page = GuiPage(None, name, persistent, duration, page_id, namespace,
                       res_dirs)
        qt5 = page.get_uri("qt5")
        qt6 = page.get_uri("qt6")
        self.assertTrue(isfile(qt5))
        self.assertTrue(isfile(qt6))

        qt6_only_name = "six"
        qt6_page = GuiPage(None, qt6_only_name, persistent, duration,
                           qt6_only_name, namespace, res_dirs)
        with self.assertRaises(FileNotFoundError):
            qt6_page.get_uri("qt5")
        qt6 = qt6_page.get_uri("qt6")
        self.assertTrue(isfile(qt6))

        # System page
        system_page = GuiPage(None, "SYSTEM_ImageFrame", False, 30,
                              "SYSTEM_ImageFrame", namespace, res_dirs)
        qt5 = system_page.get_uri("qt5")
        self.assertTrue(isfile(qt5))

        # Legacy GUI File organization
        res_dirs = {"qt5": join(dirname(__file__), "mock_data", "gui", "qt5"),
                    "qt6": join(dirname(__file__), "mock_data", "gui", "qt6")}
        page = GuiPage(None, name, persistent, duration, page_id, namespace,
                       res_dirs)
        qt5 = page.get_uri("qt5")
        qt6 = page.get_uri("qt6")
        self.assertTrue(isfile(qt5))
        self.assertTrue(isfile(qt6))
