from unittest import TestCase, mock
from unittest.mock import patch
from ovos_gui.extensions import BigscreenExtension
from .mocks import MessageBusMock, base_config
from ovos_config import Configuration
from ovos_bus_client import Message

PATCH_MODULE = "ovos_gui.extensions"

# Add Unit Tests For BigscreenExtension

class TestBigscreenExtension:
    @patch.object(Configuration, 'get')
    def test_bigscreen_close_current_window(self, mock_get):
        config = base_config()
        config.merge(
            {
                'gui': {
                    'extension': 'bigscreen'
                }
            })
        mock_get.return_value = config
        bigscreen = BigscreenExtension(MessageBusMock(), MessageBusMock())
        bigscreen.close_current_window = mock.Mock()
        message_data = Message("gui.namespace.removed", {'skill_id': 'foo'})
        bigscreen.close_current_window(message_data)
        bigscreen.close_current_window.assert_any_call(message_data)

    @patch.object(Configuration, 'get')
    def test_bigscreen_close_window_by_event(self, mock_get):
        config = base_config()
        config.merge(
            {
                'gui': {
                    'extension': 'bigscreen'
                }
            })
        mock_get.return_value = config
        bigscreen = BigscreenExtension(MessageBusMock(), MessageBusMock())
        bigscreen.close_window_by_event = mock.Mock()
        message_data = Message("mycroft.gui.screen.close", {})
        bigscreen.close_window_by_event(message_data)
        bigscreen.close_window_by_event.assert_any_call(message_data)
