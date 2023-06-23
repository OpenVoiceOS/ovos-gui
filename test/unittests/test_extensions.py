import unittest
from unittest.mock import patch, Mock

import ovos_gui.extensions
from ovos_utils.messagebus import FakeBus
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
    @patch("ovos_gui.namespace.create_gui_service")
    def setUpClass(cls, create_gui) -> None:
        from ovos_gui.extensions import ExtensionsManager
        from ovos_gui.namespace import NamespaceManager

        ovos_gui.extensions.Configuration = Mock(return_value=_MOCK_CONFIG)

        cls.extension_manager = ExtensionsManager(cls.name, cls.bus,
                                                  NamespaceManager(cls.bus))
        create_gui.assert_called_once_with(cls.extension_manager.gui)

    def test_00_extensions_manager_init(self):
        from ovos_gui.namespace import NamespaceManager
        self.assertEqual(self.extension_manager.name, self.name)
        self.assertEqual(self.extension_manager.bus, self.bus)
        self.assertIsInstance(self.extension_manager.gui, NamespaceManager)
        self.assertEqual(self.extension_manager.gui.core_bus, self.bus)
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

