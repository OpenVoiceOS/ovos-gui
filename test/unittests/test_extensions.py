import unittest
from unittest.mock import patch, Mock

import ovos_gui.extensions
from ovos_utils.fakebus import FakeBus
from ovos_gui.homescreen import HomescreenManager
from ovos_gui.extensions import ExtensionsManager
from .mocks import base_config

PATCH_MODULE = "ovos_gui.extensions"

_MOCK_CONFIG = base_config()
_MOCK_CONFIG.merge(
            {
                'gui': {
                    'extension': 'generic',
                    'generic': {
                        'homescreen_supported': False
                    }
                }
            })


class TestExtensionManager(unittest.TestCase):
    bus = FakeBus()
    name = "TestManager"

    @classmethod
    def setUpClass(cls) -> None:

        ovos_gui.extensions.Configuration = Mock(return_value=_MOCK_CONFIG)

        cls.extension_manager = ExtensionsManager(cls.name, cls.bus)

    def test_00_extensions_manager_init(self):
        self.assertEqual(self.extension_manager.name, self.name)
        self.assertEqual(self.extension_manager.bus, self.bus)
        self.assertIsInstance(self.extension_manager.homescreen_manager, HomescreenManager)
        self.assertEqual(self.extension_manager.homescreen_manager.bus, self.bus)
        self.assertIsInstance(self.extension_manager.active_extension, str)

    @patch("ovos_gui.extensions.OVOSGuiFactory.create")
    def test_activate_extension(self, create):
        mock_extension = Mock()
        mock_extension.preload_gui = False
        mock_extension.permanent = True
        # TODO: Test preload/permanent combinations
        create.return_value = mock_extension
        self.extension_manager.activate_extension("smartspeaker")
        create.assert_called_once()
        # TODO: Check call for mapped plugin name
        self.assertEqual(self.extension_manager.extension, mock_extension)
        mock_extension.bind_homescreen.assert_called_once()
        # TODO: Test messagebus Messages

