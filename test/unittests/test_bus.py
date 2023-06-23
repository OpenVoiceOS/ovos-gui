import unittest
from unittest.mock import patch, Mock


class TestBus(unittest.TestCase):
    @patch("ovos_config.config.Configuration")
    def test_get_gui_websocket_config(self, configuration):
        from ovos_gui.bus import get_gui_websocket_config

        mock_config = {'gui_websocket': {'host': 'test', 'port': 80}}
        configuration.return_value = mock_config

        config = get_gui_websocket_config()
        self.assertEqual(config, mock_config['gui_websocket'])

        configuration.return_value = dict()
        with self.assertRaises(KeyError):
            get_gui_websocket_config()

    def test_create_gui_service(self):
        from ovos_gui.bus import create_gui_service
        # TODO

    @patch("ovos_gui.bus.GUIWebsocketHandler")
    def test_send_message_to_gui(self, handler):
        from ovos_gui.bus import send_message_to_gui
        mock_client = Mock()
        handler.clients = [mock_client]
        message = {"test": True}

        send_message_to_gui(message)
        mock_client.send.assert_called_once_with(message)

    @patch("ovos_gui.bus.GUIWebsocketHandler")
    def test_determine_if_gui_connected(self, handler):
        from ovos_gui.bus import determine_if_gui_connected
        mock_client = Mock()
        self.assertFalse(determine_if_gui_connected())
        handler.clients = [mock_client]
        self.assertTrue(determine_if_gui_connected())


class TestGUIWebsocketHandler(unittest.TestCase):
    from ovos_gui.bus import GUIWebsocketHandler
    # TODO
