import unittest
from unittest.mock import patch

from ovos_bus_client.message import Message
from ovos_utils.messagebus import FakeBus
from ovos_gui.namespace import NamespaceManager


class TestHomescreenManager(unittest.TestCase):
    from ovos_gui.homescreen import HomescreenManager
    bus = FakeBus()
    gui = NamespaceManager(bus)
    homescreen_manager = HomescreenManager(bus, gui)

    def test_00_homescreen_manager_init(self):
        self.assertEqual(self.homescreen_manager.bus, self.bus)
        self.assertEqual(self.homescreen_manager.gui, self.gui)
        self.assertFalse(self.homescreen_manager.mycroft_ready)
        self.assertIsInstance(self.homescreen_manager.homescreens, list)
        # TODO: Test messagebus handlers

    def test_add_homescreen(self):
        # TODO
        pass

    def test_remove_homescreen(self):
        # TODO
        pass

    def test_get_homescreen(self):
        # TODO
        pass

    def test_handle_get_active_homescreen(self):
        # TODO
        pass

    def test_handle_set_active_homescreen(self):
        # TODO
        pass

    @patch("ovos_gui.homescreen.Configuration")
    def test_get_active_homescreen(self, config):
        config.return_value = {"gui": {"idle_display_skill": "test"}}
        self.assertIsNone(self.homescreen_manager.get_active_homescreen())
        # TODO: Mock `homescreens` and get a value here

    @patch("ovos_gui.homescreen.update_mycroft_config")
    def test_set_active_homescreen(self, update_config):
        test_id = "test_homescreen_id"
        self.homescreen_manager.set_active_homescreen(test_id)
        update_config.assert_called_once_with(
            {"gui": {"idle_display_skill": test_id}},
            bus=self.homescreen_manager.bus)

    def test_reload_homescreens_list(self):
        # TODO
        pass

    def test_show_homescreen_on_add(self):
        # TODO
        pass

    @patch("ovos_gui.homescreen.Configuration")
    @patch("ovos_gui.homescreen.update_mycroft_config")
    def test_disable_active_homescreen(self, update_config, config):
        config.return_value = {"gui": {"idle_display_skill": "test"}}
        self.homescreen_manager.disable_active_homescreen(Message(""))
        update_config.assert_called_once_with(
            {"gui": {"idle_display_skill": None}},
            bus=self.homescreen_manager.bus)

    def test_show_homescreen(self):
        # TODO
        pass

    def test_set_mycroft_ready(self):
        self.homescreen_manager.mycroft_ready = False
        self.homescreen_manager.set_mycroft_ready(Message("mycroft.ready"))
        self.assertTrue(self.homescreen_manager.mycroft_ready)
