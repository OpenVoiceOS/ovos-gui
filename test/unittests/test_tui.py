import unittest
from unittest import mock
import json


class TestGetWebsocket(unittest.TestCase):
    """Test get_websocket function."""

    def test_get_websocket_returns_client(self):
        """Test get_websocket returns a GUIWebsocketClient."""
        from ovos_gui.tui import get_websocket
        with mock.patch('ovos_gui.tui.GUIWebsocketClient') as mock_client_class:
            mock_client = mock.MagicMock()
            mock_client_class.return_value = mock_client
            result = get_websocket(threaded=False)
            self.assertEqual(result, mock_client)

    def test_get_websocket_with_custom_params(self):
        """Test get_websocket with custom parameters."""
        from ovos_gui.tui import get_websocket
        with mock.patch('ovos_gui.tui.GUIWebsocketClient') as mock_client_class:
            mock_client = mock.MagicMock()
            mock_client_class.return_value = mock_client
            result = get_websocket(host="localhost", port=9999, route="/test", ssl=True, threaded=False)
            mock_client_class.assert_called_once_with("localhost", 9999, "/test", True)
            self.assertEqual(result, mock_client)

    def test_get_websocket_threaded(self):
        """Test get_websocket with threaded=True."""
        from ovos_gui.tui import get_websocket
        with mock.patch('ovos_gui.tui.GUIWebsocketClient') as mock_client_class:
            mock_client = mock.MagicMock()
            mock_client_class.return_value = mock_client
            result = get_websocket(threaded=True)
            mock_client.run_in_thread.assert_called_once()

    def test_get_websocket_default_params(self):
        """Test get_websocket with default parameters."""
        from ovos_gui.tui import get_websocket
        with mock.patch('ovos_gui.tui.GUIWebsocketClient') as mock_client_class:
            mock_client = mock.MagicMock()
            mock_client_class.return_value = mock_client
            result = get_websocket()
            mock_client_class.assert_called_once_with("0.0.0.0", 18181, "/", False)


class TestBcolors(unittest.TestCase):
    """Test bcolors class."""

    def test_bcolors_constants_exist(self):
        """Test bcolors has all color constants."""
        from ovos_gui.tui import bcolors
        self.assertTrue(hasattr(bcolors, 'HEADER'))
        self.assertTrue(hasattr(bcolors, 'OKBLUE'))
        self.assertTrue(hasattr(bcolors, 'OKGREEN'))
        self.assertTrue(hasattr(bcolors, 'WARNING'))
        self.assertTrue(hasattr(bcolors, 'FAIL'))
        self.assertTrue(hasattr(bcolors, 'ENDC'))
        self.assertTrue(hasattr(bcolors, 'BOLD'))
        self.assertTrue(hasattr(bcolors, 'UNDERLINE'))

    def test_bcolors_values_are_strings(self):
        """Test bcolors values are ANSI escape strings."""
        from ovos_gui.tui import bcolors
        self.assertIsInstance(bcolors.HEADER, str)
        self.assertIsInstance(bcolors.ENDC, str)
        self.assertTrue(bcolors.HEADER.startswith('\033['))
        self.assertEqual(bcolors.ENDC, '\033[0m')


class TestGuiDebuggerInit(unittest.TestCase):
    """Test GUIDebugger initialization."""

    def test_init_default(self):
        """Test GUIDebugger initialization with defaults."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        self.assertEqual(debugger.port, 18181)
        self.assertEqual(debugger.mycroft_ip, "0.0.0.0")
        self.assertIsNone(debugger.skill)
        self.assertIsNone(debugger.page)
        self.assertIsNone(debugger.gui_ws)
        self.assertEqual(debugger.name, "guidebugger")
        self.assertFalse(debugger.debug)
        self.assertFalse(debugger.connected)
        self.assertEqual(debugger.buffer, [])
        self.assertEqual(debugger.loaded, [])
        self.assertEqual(debugger.vars, {})

    def test_init_custom_host(self):
        """Test GUIDebugger initialization with custom host."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger(host="127.0.0.1")
        self.assertEqual(debugger.mycroft_ip, "127.0.0.1")

    def test_init_custom_port(self):
        """Test GUIDebugger initialization with custom port."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger(port=9999)
        self.assertEqual(debugger.port, 9999)

    def test_init_custom_name(self):
        """Test GUIDebugger initialization with custom name."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger(name="TestDebugger")
        self.assertEqual(debugger.name, "TestDebugger")

    def test_init_debug_mode(self):
        """Test GUIDebugger initialization with debug=True."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger(debug=True)
        self.assertTrue(debugger.debug)


class TestGuiDebuggerConnect(unittest.TestCase):
    """Test GUIDebugger connect method."""

    def test_connect(self):
        """Test connect method creates websocket."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        with mock.patch('ovos_gui.tui.get_websocket') as mock_get_ws:
            mock_ws = mock.MagicMock()
            mock_get_ws.return_value = mock_ws
            with mock.patch('ovos_gui.tui.LOG'):
                debugger.connect()
            self.assertEqual(debugger.gui_ws, mock_ws)
            mock_ws.on.assert_any_call("open", debugger.on_open)
            mock_ws.on.assert_any_call("message", debugger.on_gui_message)


class TestGuiDebuggerMessageHandling(unittest.TestCase):
    """Test GUIDebugger message handling."""

    def test_on_open(self):
        """Test on_open callback."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_open()
            # Should not raise

    def test_on_gui_message_session_set(self):
        """Test on_gui_message with mycroft.session.set message."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        msg = {
            "type": "mycroft.session.set",
            "namespace": "test.skill",
            "data": {"key": "value"}
        }
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
        self.assertEqual(debugger.skill, "test.skill")
        self.assertEqual(debugger.vars["test.skill"]["key"], "value")

    def test_on_gui_message_list_insert_new_namespace(self):
        """Test on_gui_message with mycroft.session.list.insert message."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        msg = {
            "type": "mycroft.session.list.insert",
            "data": [{"skill_id": "test.skill"}]
        }
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
        self.assertEqual(debugger.skill, "test.skill")
        self.assertEqual(len(debugger.loaded), 1)

    def test_on_gui_message_gui_list_insert_page(self):
        """Test on_gui_message with mycroft.gui.list.insert for page."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.skill = "test.skill"
        debugger.loaded = [["test.skill", ["page1.qml"]]]
        msg = {
            "type": "mycroft.gui.list.insert",
            "data": [{"url": "page2.qml"}],
            "position": 1
        }
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
        self.assertEqual(debugger.page, "page2.qml")
        self.assertEqual(len(debugger.loaded[0][1]), 2)

    def test_on_gui_message_gui_list_insert_no_namespace(self):
        """Test on_gui_message with mycroft.gui.list.insert when no namespace loaded."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.skill = None
        debugger.loaded = []
        msg = {
            "type": "mycroft.gui.list.insert",
            "data": [{"url": "page1.qml"}],
            "position": 0
        }
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
        # Should create a namespace entry
        self.assertEqual(len(debugger.loaded), 1)

    def test_on_gui_message_list_move(self):
        """Test on_gui_message with mycroft.session.list.move message."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.loaded = [["skill1", []], ["skill2", []]]
        msg = {
            "type": "mycroft.session.list.move",
            "from": 1
        }
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
        self.assertEqual(debugger.loaded[0][0], "skill2")

    def test_on_gui_message_list_remove(self):
        """Test on_gui_message with mycroft.session.list.remove message."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.skill = "skill1"
        debugger.loaded = [["skill1", []], ["skill2", []]]
        msg = {
            "type": "mycroft.session.list.remove",
            "position": 0,
            "namespace": "skill1"
        }
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
        self.assertIsNone(debugger.skill)
        self.assertEqual(len(debugger.loaded), 1)

    def test_on_gui_message_events_triggered(self):
        """Test on_gui_message with mycroft.events.triggered message."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.loaded = [["test.skill", ["page1.qml", "page2.qml"]]]
        msg = {
            "type": "mycroft.events.triggered",
            "namespace": "test.skill",
            "event_name": "page_gained_focus",
            "data": {"number": 1}
        }
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
        self.assertEqual(debugger.page, "page2.qml")

    def test_on_gui_message_invalid_json(self):
        """Test on_gui_message with invalid JSON."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        payload = "invalid json{]["
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
            # Should not raise

    def test_on_gui_message_invalid_json_debug(self):
        """Test on_gui_message with invalid JSON in debug mode."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger(debug=True)
        payload = "invalid json{]["
        with mock.patch('ovos_gui.tui.LOG') as mock_log:
            debugger.on_gui_message(payload)
            # Should log exception in debug mode
            mock_log.exception.assert_called_once()
            mock_log.error.assert_called_once()

    def test_on_gui_message_session_set_debug(self):
        """Test on_gui_message with session.set message in debug mode."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger(debug=True)
        msg = {
            "type": "mycroft.session.set",
            "namespace": "test.skill",
            "data": {"key": "value"}
        }
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG') as mock_log:
            debugger.on_gui_message(payload)
            # In debug mode, should log the message
            mock_log.debug.assert_called_once()

    def test_on_message_called(self):
        """Test on_message is called for valid messages."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.on_message = mock.Mock()
        msg = {"type": "test", "data": {}}
        payload = json.dumps(msg)
        with mock.patch('ovos_gui.tui.LOG'):
            debugger.on_gui_message(payload)
        debugger.on_message.assert_called_once()


class TestGuiDebuggerDrawBuffer(unittest.TestCase):
    """Test GUIDebugger draw buffer methods."""

    def test_draw_buffer_with_skill(self):
        """Test _draw_buffer creates buffer with skill."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.skill = "test.skill"
        debugger.page = "page.qml"
        debugger.vars = {"test.skill": {"var1": "value1"}}
        debugger._draw_buffer()
        self.assertGreater(len(debugger.buffer), 0)
        # Check that buffer contains skill name
        buffer_text = " ".join(debugger.buffer)
        self.assertIn("test.skill", buffer_text)

    def test_draw_buffer_without_skill(self):
        """Test _draw_buffer with no active skill."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.skill = None
        debugger._draw_buffer()
        self.assertEqual(debugger.buffer, [])

    def test_draw_buffer_without_page(self):
        """Test _draw_buffer with no active page."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.skill = "test.skill"
        debugger.page = None
        debugger._draw_buffer()
        buffer_text = " ".join(debugger.buffer)
        self.assertIn("None", buffer_text)

    def test_draw(self):
        """Test draw method prints buffer."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        debugger.buffer = ["Line 1", "Line 2"]
        with mock.patch('builtins.print') as mock_print:
            debugger.draw()
            self.assertEqual(mock_print.call_count, 2)


class TestGuiDebuggerHelpers(unittest.TestCase):
    """Test GUIDebugger helper methods."""

    def test_on_new_gui_data(self):
        """Test on_new_gui_data is callable."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        # Should not raise
        debugger.on_new_gui_data({})

    def test_on_message(self):
        """Test on_message is callable."""
        from ovos_gui.tui import GUIDebugger
        debugger = GUIDebugger()
        # Should not raise
        debugger.on_message({"type": "test"})