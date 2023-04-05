from unittest import mock
from unittest.mock import patch

from ovos_config import Configuration

from ovos_gui.extensions import ExtensionsManager
from .mocks import MessageBusMock, base_config

PATCH_MODULE = "ovos_gui.extensions"


# Add Unit Tests For ExtensionManager

class TestExtensionManager:
    @patch.object(Configuration, 'get')
    def test_extension_manager_activate(self, mock_get):
        config = base_config()
        config.merge(
            {
                'gui': {
                    'extension': 'generic',
                    'generic': {
                        'homescreen_supported': False
                    }
                }
            })
        mock_get.return_value = config
        extension_manager = ExtensionsManager("ExtensionManager", MessageBusMock(), MessageBusMock())
        extension_manager.activate_extension = mock.Mock()
        extension_manager.activate_extension("generic")
        extension_manager.activate_extension.assert_any_call("generic")
