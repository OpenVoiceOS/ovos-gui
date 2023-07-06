import unittest
from unittest.mock import patch, Mock

import ovos_gui.bus


class TestBus(unittest.TestCase):
    @patch("ovos_gui.bus.Configuration")
    def test_get_gui_websocket_config(self, configuration):
        from ovos_gui.bus import get_gui_websocket_config

        mock_config = {'gui_websocket': {'host': 'test', 'port': 80}}
        configuration.return_value = mock_config

        config = get_gui_websocket_config()
        self.assertEqual(config, mock_config['gui_websocket'])

        configuration.return_value = dict()
        with self.assertRaises(KeyError):
            get_gui_websocket_config()

    @patch("ovos_gui.bus.create_daemon")
    @patch("ovos_gui.bus.ioloop")
    def test_create_gui_service(self, ioloop, create_daemon):
        from ovos_gui.bus import create_gui_service
        ioloop_instance = Mock()
        ioloop.IOLoop.instance.return_value = ioloop_instance
        mock_nsmanager = Mock()
        application = create_gui_service(mock_nsmanager)
        create_daemon.assert_called_once_with(ioloop_instance.start)
        self.assertEqual(application.settings.get("namespace_manager"),
                         mock_nsmanager)

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
    mock_nsmanager = Mock()

    class WebSocketMock:
        def __init__(self, *args, **kwargs):
            ns_manager = TestGUIWebsocketHandler.mock_nsmanager
            application_mock = Mock()
            application_mock.settings = {"namespace_manager": ns_manager}
            self.application = application_mock

    @classmethod
    def setUpClass(cls):
        from ovos_gui.bus import GUIWebsocketHandler
        ovos_gui.bus.WebSocketHandler = cls.WebSocketMock
        cls.handler = GUIWebsocketHandler()

    def test_00_websocket_init(self):
        self.assertEqual(self.handler.framework, "qt5")
        self.assertEqual(self.handler.ns_manager, self.mock_nsmanager)

    def test_on_open(self):
        # TODO
        pass

    def test_on_close(self):
        # TODO
        pass

    def test_get_client_pages(self):
        from ovos_gui.namespace import Namespace
        test_namespace = Namespace("test")
        page_1 = Mock()
        page_1.get_uri.return_value = "page_1_uri"
        page_2 = Mock()
        page_2.get_uri.return_value = "page_2_uri"
        test_namespace.pages = [page_1, page_2]

        # Test no server_url
        self.handler.ns_manager.qml_server = None
        pages = self.handler.get_client_pages(test_namespace)
        page_1.get_uri.assert_called_once_with(self.handler.framework, None)
        page_2.get_uri.assert_called_once_with(self.handler.framework, None)
        self.assertEqual(pages, ["page_1_uri", "page_2_uri"])

        # Test with server_url
        self.handler.ns_manager.qml_server = Mock()
        self.handler.ns_manager.qml_server.url = "server_url"
        pages = self.handler.get_client_pages(test_namespace)
        page_1.get_uri.assert_called_with(self.handler.framework, "server_url")
        page_2.get_uri.assert_called_with(self.handler.framework, "server_url")
        self.assertEqual(pages, ["page_1_uri", "page_2_uri"])

    def test_synchronize(self):
        # TODO
        pass

    def test_on_message(self):
        # TODO
        pass

    def test_write_message(self):
        # TODO
        pass

    def test_send_gui_pages(self):
        real_send = self.handler.send
        self.handler.send = Mock()
        test_ns = "test_namespace"
        test_pos = 0

        from ovos_gui.page import GuiPage
        page_1 = GuiPage(None, "", False, False)
        page_1.get_uri = Mock(return_value="page_1")

        page_2 = GuiPage(None, "", False, False)
        page_2.get_uri = Mock(return_value="page_2")

        # Test no server_url
        self.handler.ns_manager.qml_server = None
        self.handler._framework = "qt5"
        self.handler.send_gui_pages([page_1, page_2], test_ns, test_pos)
        page_1.get_uri.assert_called_once_with("qt5", None)
        page_2.get_uri.assert_called_once_with("qt5", None)
        self.handler.send.assert_called_once_with(
            {"type": "mycroft.gui.list.insert",
             "namespace": test_ns,
             "position": test_pos,
             "data": [{"url": "page_1"}, {"url": "page_2"}]})

        # Test with server_url
        self.handler.ns_manager.qml_server = Mock()
        self.handler.ns_manager.qml_server.url = "server_url"
        self.handler._framework = "qt6"
        test_pos = 3
        self.handler.send_gui_pages([page_2, page_1], test_ns, test_pos)
        page_1.get_uri.assert_called_with("qt6", "server_url")
        page_2.get_uri.assert_called_with("qt6", "server_url")
        self.handler.send.assert_called_with(
            {"type": "mycroft.gui.list.insert",
             "namespace": test_ns,
             "position": test_pos,
             "data": [{"url": "page_2"}, {"url": "page_1"}]})

        self.handler.send = real_send

    def test_send(self):
        # TODO
        pass

    def test_check_origin(self):
        self.assertTrue(self.handler.check_origin("test"))
        self.assertTrue(self.handler.check_origin(""))
